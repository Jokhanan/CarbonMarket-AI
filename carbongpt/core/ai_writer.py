import json
import logging
import os

import requests as http_client

from carbongpt.guides import load_guide, DOC_TYPE_LABELS, GUIDE_REGISTRY
from carbongpt.core.knowledge_retrieval import retrieve_section_context, format_context_for_prompt

logger = logging.getLogger(__name__)

MODEL = os.getenv("CARBONGPT_AI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

STANDARD_LABELS = {
    "GoldStandard": "Gold Standard",
    "Verra": "Verra VCS",
}

STANDARD_DOC_TYPE_MAP = {
    "GoldStandard": {
        "pdd": "PDD",
        "mr": "MR",
        "poa_dd": "PoA-DD",
        "vpa_dd": "VPA-DD",
    },
    "Verra": {
        "pdd": "VCS-PD",
        "mr": "VCS-MR",
        "valver": "VCS-ValVer",
    },
}


def get_guide_doc_type(standard, project_doc_type):
    mapping = STANDARD_DOC_TYPE_MAP.get(standard, {})
    return mapping.get(project_doc_type)


def get_sections_for_doc_type(standard, project_doc_type):
    guide_dt = get_guide_doc_type(standard, project_doc_type)
    if not guide_dt:
        return None
    try:
        guide = load_guide(standard, guide_dt)
        subsections = guide.SUBSECTIONS
        sections = []
        for sid, info in subsections.items():
            sections.append({
                "id": sid,
                "title": info.get("title", ""),
                "parent_section": info.get("parent_section", ""),
                "must_include": info.get("must_include", []),
            })
        return sections
    except Exception as e:
        logger.error("Failed to load guide for %s/%s: %s", standard, project_doc_type, e)
        return None


def _get_api_key():
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    return api_key


def _call_openai(system_prompt, user_prompt, response_format=None, max_tokens=4000):
    api_key = _get_api_key()
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }
    if response_format:
        payload["response_format"] = response_format
    resp = http_client.post(
        OPENAI_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def generate_section_draft(
    standard,
    project_doc_type,
    section_id,
    project_info,
    existing_pdd_text=None,
    reference_docs_text=None,
    user_instructions=None,
):
    guide_dt = get_guide_doc_type(standard, project_doc_type)
    if not guide_dt:
        raise ValueError(f"No guide mapping for {standard}/{project_doc_type}")

    guide = load_guide(standard, guide_dt)
    subsection = guide.SUBSECTIONS.get(section_id)
    if not subsection:
        raise ValueError(f"Section {section_id} not found in guide")

    std_label = STANDARD_LABELS.get(standard, standard)
    doc_label = DOC_TYPE_LABELS.get(guide_dt, guide_dt)

    knowledge_context = ""
    try:
        methodology = project_info.get("methodology", "")
        if methodology:
            search_query = f"{methodology} {subsection['title']}"
            chunks = retrieve_section_context(
                section_title=subsection["title"],
                section_text=search_query,
                standard=standard,
                max_results=5,
            )
            if chunks:
                knowledge_context = format_context_for_prompt(chunks)
    except Exception as e:
        logger.warning("Knowledge retrieval failed for writing: %s", e)

    system_prompt = (
        f"You are an expert carbon project developer and technical writer specialized in {std_label} projects. "
        f"You are helping draft a {doc_label} document.\n\n"
        "RULES:\n"
        "- Write professional, technical content appropriate for submission to the standard body.\n"
        "- Use specific, concrete language. Avoid vague or generic statements.\n"
        "- Where project-specific data is needed but not provided, insert clear placeholders like [INSERT: specific data needed].\n"
        "- Follow the methodology's requirements precisely when writing calculations or parameter descriptions.\n"
        "- Reference the correct standard sections and methodology clauses.\n"
        "- Do NOT fabricate quantitative data, emission factors, or measurement results.\n"
        "- Write in the professional style expected by VVBs (Validation/Verification Bodies)."
    )

    must_include = "\n".join(f"  - {item}" for item in subsection.get("must_include", []))
    examples = "\n".join(f"  - {ex}" for ex in subsection.get("examples", []))

    user_prompt = f"## Task: Draft section {section_id}: {subsection['title']}\n\n"
    user_prompt += f"### Section Requirements (must include):\n{must_include}\n\n"

    if examples:
        user_prompt += f"### Example of good content:\n{examples}\n\n"

    user_prompt += "### Project Information:\n"
    user_prompt += f"- Project name: {project_info.get('name', '[Not specified]')}\n"
    user_prompt += f"- Standard: {std_label}\n"
    user_prompt += f"- Country: {project_info.get('country', '[Not specified]')}\n"
    if project_info.get("methodology"):
        user_prompt += f"- Methodology: {project_info['methodology']}\n"
    if project_info.get("description"):
        user_prompt += f"- Project description: {project_info['description']}\n"
    user_prompt += "\n"

    if existing_pdd_text:
        pdd_excerpt = existing_pdd_text[:6000]
        user_prompt += (
            "### Existing Project Description (PDD) content for reference:\n"
            "Use this to ensure consistency with the project design.\n"
            f'"""\n{pdd_excerpt}\n"""\n\n'
        )

    if reference_docs_text:
        ref_excerpt = reference_docs_text[:4000]
        user_prompt += (
            "### Additional reference documents provided by the user:\n"
            f'"""\n{ref_excerpt}\n"""\n\n'
        )

    if knowledge_context:
        user_prompt += (
            "### Relevant methodology/standard requirements from the knowledge base:\n"
            f"{knowledge_context}\n\n"
        )

    if user_instructions:
        user_prompt += f"### Additional instructions from the user:\n{user_instructions}\n\n"

    user_prompt += (
        f"Write the complete content for section {section_id}: {subsection['title']}. "
        "Make it ready for inclusion in the document. Use proper formatting with sub-headings where appropriate."
    )

    result = _call_openai(system_prompt, user_prompt, max_tokens=4000)
    return result


def explain_section(standard, project_doc_type, section_id):
    guide_dt = get_guide_doc_type(standard, project_doc_type)
    if not guide_dt:
        raise ValueError(f"No guide mapping for {standard}/{project_doc_type}")

    guide = load_guide(standard, guide_dt)
    subsection = guide.SUBSECTIONS.get(section_id)
    if not subsection:
        raise ValueError(f"Section {section_id} not found in guide")

    std_label = STANDARD_LABELS.get(standard, standard)
    doc_label = DOC_TYPE_LABELS.get(guide_dt, guide_dt)

    must_include = "\n".join(f"  - {item}" for item in subsection.get("must_include", []))
    failure_modes = "\n".join(f"  - {item}" for item in subsection.get("failure_modes", []))
    examples = "\n".join(f"  - {ex}" for ex in subsection.get("examples", []))

    system_prompt = (
        f"You are a carbon project development trainer explaining {std_label} requirements "
        "to a project developer who may be new to the standard. "
        "Explain clearly, practically, and concisely. Give real-world tips."
    )

    user_prompt = (
        f"Explain what is needed for section {section_id}: {subsection['title']} "
        f"in a {std_label} {doc_label}.\n\n"
        f"Requirements:\n{must_include}\n\n"
        f"Common mistakes:\n{failure_modes}\n\n"
        f"Examples:\n{examples}\n\n"
        "Explain in plain language:\n"
        "1. What this section is about and why it matters\n"
        "2. What information the developer needs to gather\n"
        "3. Tips for writing it well\n"
        "4. Common mistakes to avoid"
    )

    return _call_openai(system_prompt, user_prompt, max_tokens=2000)


def review_with_context(
    standard,
    project_doc_type,
    document_text,
    project_info,
    pdd_text=None,
    reference_texts=None,
):
    guide_dt = get_guide_doc_type(standard, project_doc_type)
    if not guide_dt:
        raise ValueError(f"No guide mapping for {standard}/{project_doc_type}")

    std_label = STANDARD_LABELS.get(standard, standard)
    doc_label = DOC_TYPE_LABELS.get(guide_dt, guide_dt)

    system_prompt = (
        f"You are a senior {std_label} compliance auditor reviewing a {doc_label}. "
        "You have deep expertise in carbon project development and the specific methodology.\n\n"
        "RULES:\n"
        "- Check every section against the standard's requirements.\n"
        "- If a PDD/project description is provided, check consistency between documents.\n"
        "- Flag missing parameters, inconsistent data, incomplete calculations.\n"
        "- Be specific about what is wrong and how to fix it.\n"
        "- Score each section 0-100 and provide an overall assessment.\n"
        "- Format your response as a structured JSON."
    )

    user_prompt = "## Document to Review:\n"
    doc_excerpt = document_text[:12000]
    user_prompt += f'"""\n{doc_excerpt}\n"""\n\n'

    user_prompt += "### Project Information:\n"
    user_prompt += f"- Project: {project_info.get('name', 'Unknown')}\n"
    user_prompt += f"- Standard: {std_label}\n"
    user_prompt += f"- Methodology: {project_info.get('methodology', 'Not specified')}\n"
    user_prompt += f"- Country: {project_info.get('country', 'Not specified')}\n\n"

    if pdd_text:
        pdd_excerpt = pdd_text[:6000]
        user_prompt += (
            "### Project Description (PDD) for cross-reference:\n"
            "Check that the document being reviewed is consistent with this PDD.\n"
            f'"""\n{pdd_excerpt}\n"""\n\n'
        )

    if reference_texts:
        ref_excerpt = reference_texts[:4000]
        user_prompt += (
            "### Additional reference documents:\n"
            f'"""\n{ref_excerpt}\n"""\n\n'
        )

    user_prompt += (
        "Provide a thorough review. For each major section:\n"
        "1. Score (0-100)\n"
        "2. Issues found\n"
        "3. Specific fixes needed\n"
        "4. Questions for the developer\n\n"
        "End with an overall assessment (LOW/MEDIUM/HIGH risk) and top 5 priority actions."
    )

    review_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "document_review",
            "strict": False,
            "schema": {
                "type": "object",
                "properties": {
                    "overall_risk": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                    "overall_score": {"type": "integer"},
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "section": {"type": "string"},
                                "score": {"type": "integer"},
                                "issues": {"type": "array", "items": {"type": "string"}},
                                "fixes": {"type": "array", "items": {"type": "string"}},
                                "questions": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "pdd_consistency": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Inconsistencies between this document and the PDD",
                    },
                    "priority_actions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["overall_risk", "overall_score", "sections", "priority_actions"],
            },
        },
    }

    result = _call_openai(system_prompt, user_prompt, response_format=review_schema, max_tokens=6000)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"raw_review": result, "overall_risk": "UNKNOWN", "sections": [], "priority_actions": []}
