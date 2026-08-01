"""
ai_review.py — AI-powered section-by-section review using OpenAI.

Uses the internal guide (subsection requirements) to prompt an LLM
for structured compliance analysis of each subsection, then runs a
global summary call.

Supports multiple document types via the guide registry.

Uses raw requests library instead of the openai SDK to minimize
memory/thread overhead.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

from carbongpt.guides import load_guide, DOC_TYPE_LABELS
from carbongpt.tools.parse_docx import parse_docx
from carbongpt.tools.section_mapper import map_sections
from carbongpt.tools.rule_engine import _normalize_text, _get_section_text
from carbongpt.core.knowledge_retrieval import retrieve_section_context, format_context_for_prompt
from carbongpt.core.compliance_checker import check_document_compliance, format_compliance_findings_for_prompt
from carbongpt.core.openai_client import DEFAULT_MODEL as MODEL


STANDARD_LABELS: dict[str, str] = {
    "GoldStandard": "Gold Standard",
    "Verra": "Verra VCS",
}


def _build_section_system_prompt(doc_type_label: str, standard: str = "GoldStandard") -> str:
    std_label = STANDARD_LABELS.get(standard, standard)
    return (
        f"You are a compliance auditor for {std_label} carbon credit {doc_type_label}s. "
        "You review document sections against BOTH the template guide requirements AND "
        "any relevant standard/methodology requirements provided as reference material. "
        "RULES:\n"
        "- Never invent numbers, statistics, or facts.\n"
        "- If information is missing, say 'missing' and ask a question.\n"
        "- Any suggested text must be clearly marked as '[DRAFT]' and must not fabricate data.\n"
        "- Be specific about what is present and what is absent.\n"
        "- When reference material from standards or methodologies is provided, check whether "
        "the section content meets those specific requirements (eligibility criteria, calculation "
        "methods, monitoring parameters, baseline requirements, etc.).\n"
        "- Flag any inconsistency between the document and the methodology/standard requirements.\n"
        "- Score from 0 to 100 based on how completely the subsection meets ALL requirements "
        "(both template structure and methodology/standard compliance)."
    )


def _build_global_system_prompt(doc_type_label: str, standard: str = "GoldStandard") -> str:
    std_label = STANDARD_LABELS.get(standard, standard)
    return (
        f"You are a senior compliance auditor summarizing a {std_label} {doc_type_label} review. "
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


def _get_api_key() -> str:
    # Kept as a pre-flight check so callers fail before doing per-section
    # work, not mid-way through. Text generation now needs ANTHROPIC_API_KEY.
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
    return api_key


def _build_section_prompt(
    subsection_id: str,
    subsection_guide: dict,
    section_text: str,
    reference_context: str = "",
) -> str:
    must_include = "\n".join(f"  - {item}" for item in subsection_guide.get("must_include", []))
    failure_modes = "\n".join(f"  - {item}" for item in subsection_guide.get("failure_modes", []))
    examples = "\n".join(f"  - {item}" for item in subsection_guide.get("examples", []))

    prompt = (
        f"## Subsection {subsection_id}: {subsection_guide['title']}\n\n"
        f"### Guide Requirements (must include):\n{must_include}\n\n"
        f"### Common Failure Modes:\n{failure_modes}\n\n"
        f"### Good Examples:\n{examples}\n\n"
    )

    if reference_context:
        prompt += reference_context + "\n\n"

    prompt += (
        f"### Document Text:\n\"\"\"\n{section_text}\n\"\"\"\n\n"
        "Evaluate this subsection against the guide requirements"
    )

    if reference_context:
        prompt += (
            " AND the reference material from standards/methodologies above. "
            "Check whether the document meets methodology-specific requirements "
            "(eligibility, calculations, monitoring parameters, baseline approach). "
            "Flag any gaps or inconsistencies with the methodology."
        )
    else:
        prompt += "."

    prompt += (
        " Identify issues, suggest fixes, and ask questions about missing information. "
        "Provide a completeness score from 0 to 100."
    )

    return prompt


def _build_global_prompt(section_reviews: list[dict], doc_type_label: str) -> str:
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
        f"Below are per-section review results for a {doc_type_label}.\n\n"
        f"{section_summary}\n\n"
        "Provide a global summary covering overall risk, top issues, "
        "top priority actions, and any cross-section coherence flags."
    )


def _call_openai_structured(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    schema_name: str,
) -> dict:
    # `api_key` is kept for backward compatibility with existing callers —
    # text generation now goes through carbongpt.core.openai_client, which
    # manages ANTHROPIC_API_KEY itself (see CLAUDE.md §5).
    from carbongpt.core.openai_client import call_openai
    response_format = {
        "type": "json_schema",
        "json_schema": {"name": schema_name, "strict": True, "schema": schema},
    }
    content = call_openai(
        system_prompt, user_prompt, response_format=response_format,
        temperature=0.2, model_override=MODEL,
    )
    return json.loads(content)


def review_section(
    api_key: str,
    subsection_id: str,
    subsection_guide: dict,
    section_text: str,
    doc_type_label: str = "Monitoring Report",
    standard: str = "GoldStandard",
    reference_context: str = "",
) -> dict:
    prompt = _build_section_prompt(subsection_id, subsection_guide, section_text, reference_context)
    system_prompt = _build_section_system_prompt(doc_type_label, standard)
    result = _call_openai_structured(
        api_key=api_key,
        system_prompt=system_prompt,
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


def review_global(
    api_key: str,
    section_reviews: list[dict],
    doc_type_label: str = "Monitoring Report",
    standard: str = "GoldStandard",
) -> dict:
    prompt = _build_global_prompt(section_reviews, doc_type_label)
    system_prompt = _build_global_system_prompt(doc_type_label, standard)
    return _call_openai_structured(
        api_key=api_key,
        system_prompt=system_prompt,
        user_prompt=prompt,
        schema=GLOBAL_SUMMARY_SCHEMA,
        schema_name="global_summary",
    )


METHODOLOGY_SECTION_KEYWORDS = {
    "methodology", "applicability", "baseline", "additionality",
    "reference", "title and reference", "deviations", "quantification",
    "emission", "calculation", "leakage", "eligibility",
}


def _is_methodology_section(sub_id: str, sub_guide: dict) -> bool:
    title_lower = sub_guide.get("title", "").lower()
    return any(kw in title_lower for kw in METHODOLOGY_SECTION_KEYWORDS)


def run_ai_review(
    doc_path: str,
    standard: str = "GoldStandard",
    doc_type: str = "MR",
) -> dict:
    guide = load_guide(standard, doc_type)
    doc_type_label = DOC_TYPE_LABELS.get(doc_type, doc_type)

    parsed = parse_docx(doc_path)
    sections: dict[str, str] = parsed["sections"]
    found_headings = list(sections.keys())

    subsections = guide.get_subsections()
    parent_sections = guide.get_parent_sections()

    section_map = map_sections(parent_sections, found_headings, threshold=85)

    full_text = "\n".join(sections.values())
    compliance_findings = check_document_compliance(full_text, standard)
    compliance_context = format_compliance_findings_for_prompt(compliance_findings)
    if compliance_findings:
        logger.info("Found %d compliance rule matches for this document", len(compliance_findings))

    api_key = _get_api_key()
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

        try:
            logger.info("Reviewing subsection %s ...", sub_id)
            context_chunks = retrieve_section_context(
                sub_guide["title"], text, standard, doc_type
            )
            reference_context = format_context_for_prompt(context_chunks)
            if reference_context:
                logger.info("  Retrieved %d reference chunks for %s", len(context_chunks), sub_id)

            section_compliance = ""
            if compliance_context and _is_methodology_section(sub_id, sub_guide):
                section_compliance = compliance_context
                logger.info("  Injecting %d compliance alerts into %s", len(compliance_findings), sub_id)

            combined_context = reference_context + section_compliance
            review = review_section(api_key, sub_id, sub_guide, text, doc_type_label, standard, combined_context)
            per_section_reviews.append(review)
        except Exception as exc:
            logger.error("Failed to review subsection %s: %s", sub_id, exc)
            per_section_reviews.append({
                "section_id": sub_id,
                "section_title": sub_guide["title"],
                "completeness_score": 0,
                "issues": [f"AI review error: {exc}"],
                "suggested_fixes": [],
                "questions_for_user": [],
            })

    try:
        logger.info("Running global summary ...")
        global_summary = review_global(api_key, per_section_reviews, doc_type_label, standard)
    except Exception as exc:
        logger.error("Failed to generate global summary: %s", exc)
        global_summary = {
            "overall_risk": "HIGH",
            "top_issues": [f"AI global review error: {exc}"],
            "top_actions": [],
            "coherence_flags": [],
        }

    result = {
        "per_section_reviews": per_section_reviews,
        "global_summary": global_summary,
    }

    if compliance_findings:
        result["compliance_alerts"] = compliance_findings

    return result
