"""
ai_review.py — AI-powered section-by-section review using OpenAI.

Uses the internal guide (subsection requirements) to prompt an LLM
for structured compliance analysis of each subsection, then runs a
global summary call.
"""

import json
import os
from typing import Any

from openai import OpenAI

from carbongpt.guides.gs_mr_perfcert_v1_2 import (
    get_subsections,
    get_parent_sections,
    get_subsections_for_parent,
)
from carbongpt.tools.parse_docx import parse_docx
from carbongpt.tools.section_mapper import map_sections
from carbongpt.tools.rule_engine import _normalize_text, _get_section_text


MODEL = os.getenv("CARBONGPT_AI_MODEL", "gpt-4o-mini")


SECTION_REVIEW_SYSTEM = (
    "You are a compliance auditor for Gold Standard carbon credit monitoring reports. "
    "You review document sections against specific guide requirements. "
    "RULES:\n"
    "- Never invent numbers, statistics, or facts.\n"
    "- If information is missing, say 'missing' and ask a question.\n"
    "- Any suggested text must be clearly marked as '[DRAFT]' and must not fabricate data.\n"
    "- Be specific about what is present and what is absent.\n"
    "- Score from 0 to 100 based on how completely the subsection meets requirements."
)


GLOBAL_SUMMARY_SYSTEM = (
    "You are a senior compliance auditor summarizing a Gold Standard monitoring report review. "
    "Based on per-section review results, provide a global summary. "
    "RULES:\n"
    "- Never invent numbers or facts.\n"
    "- Focus on cross-section coherence and overall document quality.\n"
    "- Rate overall risk as LOW, MEDIUM, or HIGH."
)


SECTION_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "completeness_score": {
            "type": "integer",
            "description": "Score from 0 to 100 indicating how completely this subsection meets the guide requirements.",
        },
        "issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of specific issues found in this subsection.",
        },
        "suggested_fixes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Actionable suggestions to fix issues. Mark any draft text with [DRAFT].",
        },
        "questions_for_user": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Questions to ask the document author about missing or unclear information.",
        },
    },
    "required": ["completeness_score", "issues", "suggested_fixes", "questions_for_user"],
    "additionalProperties": False,
}


GLOBAL_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_risk": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH"],
            "description": "Overall risk level of the document.",
        },
        "top_issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top issues across all sections.",
        },
        "top_actions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top priority actions for the document author.",
        },
        "coherence_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Cross-section coherence issues (contradictions, missing links, etc).",
        },
    },
    "required": ["overall_risk", "top_issues", "top_actions", "coherence_flags"],
    "additionalProperties": False,
}


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)


def _build_section_prompt(
    subsection_id: str,
    subsection_guide: dict,
    section_text: str,
) -> str:
    must_include = "\n".join(f"  - {item}" for item in subsection_guide.get("must_include", []))
    failure_modes = "\n".join(f"  - {item}" for item in subsection_guide.get("failure_modes", []))
    examples = "\n".join(f"  - {item}" for item in subsection_guide.get("examples", []))

    return (
        f"## Subsection {subsection_id}: {subsection_guide['title']}\n\n"
        f"### Guide Requirements (must include):\n{must_include}\n\n"
        f"### Common Failure Modes:\n{failure_modes}\n\n"
        f"### Good Examples:\n{examples}\n\n"
        f"### Document Text:\n\"\"\"\n{section_text}\n\"\"\"\n\n"
        "Evaluate this subsection against the guide requirements. "
        "Identify issues, suggest fixes, and ask questions about missing information. "
        "Provide a completeness score from 0 to 100."
    )


def _build_global_prompt(section_reviews: list[dict]) -> str:
    summaries = []
    for review in section_reviews:
        sid = review["section_id"]
        title = review["section_title"]
        score = review["completeness_score"]
        issues = review.get("issues", [])
        issue_text = "; ".join(issues) if issues else "None"
        summaries.append(f"- {sid} ({title}): score={score}, issues=[{issue_text}]")

    section_summary = "\n".join(summaries)
    return (
        "Below are per-section review results for a Gold Standard Monitoring Report.\n\n"
        f"{section_summary}\n\n"
        "Provide a global summary covering overall risk, top issues, "
        "top priority actions, and any cross-section coherence flags."
    )


def _call_openai_structured(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    schema_name: str,
) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        },
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return json.loads(content)


def review_section(
    client: OpenAI,
    subsection_id: str,
    subsection_guide: dict,
    section_text: str,
) -> dict:
    prompt = _build_section_prompt(subsection_id, subsection_guide, section_text)
    result = _call_openai_structured(
        client=client,
        system_prompt=SECTION_REVIEW_SYSTEM,
        user_prompt=prompt,
        schema=SECTION_REVIEW_SCHEMA,
        schema_name="section_review",
    )
    return {
        "section_id": subsection_id,
        "section_title": subsection_guide["title"],
        "completeness_score": result["completeness_score"],
        "issues": result["issues"],
        "suggested_fixes": result["suggested_fixes"],
        "questions_for_user": result["questions_for_user"],
    }


def review_global(client: OpenAI, section_reviews: list[dict]) -> dict:
    prompt = _build_global_prompt(section_reviews)
    return _call_openai_structured(
        client=client,
        system_prompt=GLOBAL_SUMMARY_SYSTEM,
        user_prompt=prompt,
        schema=GLOBAL_SUMMARY_SCHEMA,
        schema_name="global_summary",
    )


def run_ai_review(doc_path: str) -> dict:
    parsed = parse_docx(doc_path)
    sections: dict[str, str] = parsed["sections"]
    found_headings = list(sections.keys())

    subsections = get_subsections()
    parent_sections = get_parent_sections()

    section_map = map_sections(parent_sections, found_headings, threshold=85)

    client = _get_client()
    per_section_reviews: list[dict] = []

    for sub_id, sub_guide in subsections.items():
        parent = sub_guide["parent_section"]
        raw_text = _get_section_text(parent, sections, section_map)

        if raw_text is None:
            per_section_reviews.append({
                "section_id": sub_id,
                "section_title": sub_guide["title"],
                "completeness_score": 0,
                "issues": [f"Parent section '{parent}' not found in document."],
                "suggested_fixes": [f"Add section '{parent}' to the document."],
                "questions_for_user": [],
            })
            continue

        text = _normalize_text(raw_text)
        if not text.strip():
            per_section_reviews.append({
                "section_id": sub_id,
                "section_title": sub_guide["title"],
                "completeness_score": 0,
                "issues": [f"Section '{parent}' exists but contains no text."],
                "suggested_fixes": [f"Populate section '{parent}' with required content."],
                "questions_for_user": [],
            })
            continue

        review = review_section(client, sub_id, sub_guide, text)
        per_section_reviews.append(review)

    global_summary = review_global(client, per_section_reviews)

    return {
        "per_section_reviews": per_section_reviews,
        "global_summary": global_summary,
    }
