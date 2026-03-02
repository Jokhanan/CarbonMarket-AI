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

SECTION_INTAKE_MAP = {
    "A": ["project_overview", "technology", "location"],
    "B": ["baseline_additionality", "emission_reductions", "monitoring"],
    "B.6": ["sdgs"],
    "C": ["project_overview"],
    "D": ["safeguards"],
    "E": ["stakeholders"],
}


def _format_project_context(project_info):
    intake = project_info.get("project_intake") or {}
    if not intake:
        return ""

    parts = []

    card_formatters = {
        "project_overview": ("Project Overview", [
            ("objective", "Project Objective"),
            ("summary", "Project Summary"),
            ("start_date", "Start Date"),
            ("scale", "Project Scale"),
            ("num_units", "Number of Units"),
        ]),
        "technology": ("Technology & Approach", [
            ("description", "Technology Description"),
            ("manufacturer", "Manufacturer"),
            ("model", "Model"),
            ("fuel_baseline", "Baseline Fuel"),
            ("fuel_project", "Project Fuel"),
            ("distribution_method", "Distribution Method"),
        ]),
        "location": ("Location & Beneficiaries", [
            ("regions", "Regions"),
            ("coordinates", "Coordinates"),
            ("target_population", "Target Population"),
            ("beneficiaries", "Beneficiaries"),
        ]),
        "baseline_additionality": ("Baseline & Additionality", [
            ("baseline_scenario", "Baseline Scenario"),
            ("additionality_justification", "Additionality Justification"),
            ("barriers", "Barriers"),
            ("common_practice", "Common Practice Analysis"),
        ]),
        "monitoring": ("Monitoring Plan", [
            ("monitoring_approach", "Monitoring Approach"),
            ("key_parameters", "Key Parameters"),
            ("sampling_approach", "Sampling Approach"),
            ("qa_qc", "QA/QC Procedures"),
        ]),
        "emission_reductions": ("Emission Reductions", [
            ("annual_er_estimate", "Annual ER Estimate"),
            ("total_er_estimate", "Total ER Estimate"),
            ("calculation_approach", "Calculation Approach"),
            ("er_summary", "ER Summary"),
        ]),
        "sdgs": ("SDGs & Co-benefits", [
            ("selected_sdgs", "Selected SDGs"),
        ]),
        "stakeholders": ("Stakeholder Engagement", [
            ("consultation_summary", "Consultation Summary"),
            ("grievance_mechanism", "Grievance Mechanism"),
            ("gender_assessment", "Gender Assessment"),
        ]),
        "safeguards": ("Safeguards", [
            ("environmental_safeguards", "Environmental Safeguards"),
            ("social_safeguards", "Social Safeguards"),
            ("do_no_harm", "Do No Harm Assessment"),
        ]),
    }

    for card_key, (card_title, fields) in card_formatters.items():
        card_data = intake.get(card_key)
        if not card_data or not isinstance(card_data, dict):
            continue
        card_lines = []
        for field_key, field_label in fields:
            val = card_data.get(field_key)
            if not val:
                continue
            if isinstance(val, list):
                if val and isinstance(val[0], dict):
                    items = []
                    for item in val:
                        item_parts = [f"{k}: {v}" for k, v in item.items() if v]
                        if item_parts:
                            items.append(", ".join(item_parts))
                    val = "; ".join(items)
                else:
                    val = ", ".join(str(v) for v in val)
            card_lines.append(f"  - {field_label}: {val}")
        if card_lines:
            parts.append(f"**{card_title}:**\n" + "\n".join(card_lines))

    if not parts:
        return ""
    return "### Detailed Project Data (from intake form):\n" + "\n\n".join(parts) + "\n"


def _get_relevant_intake_cards(section_id):
    for prefix in sorted(SECTION_INTAKE_MAP.keys(), key=len, reverse=True):
        if section_id == prefix or section_id.startswith(prefix + "."):
            return SECTION_INTAKE_MAP[prefix]
    first_letter = section_id.split(".")[0] if section_id else ""
    if first_letter in SECTION_INTAKE_MAP:
        return SECTION_INTAKE_MAP[first_letter]
    return list(SECTION_INTAKE_MAP.get("A", []) + SECTION_INTAKE_MAP.get("B", []))


def _format_filtered_project_context(project_info, section_id):
    intake = project_info.get("project_intake") or {}
    if not intake:
        return ""
    relevant_cards = _get_relevant_intake_cards(section_id)
    filtered_intake = {k: v for k, v in intake.items() if k in relevant_cards}
    if not filtered_intake:
        return _format_project_context(project_info)
    filtered_info = dict(project_info)
    filtered_info["project_intake"] = filtered_intake
    return _format_project_context(filtered_info)


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


def _get_methodology_context(methodology_code):
    if not methodology_code:
        return ""
    try:
        from carbongpt.repository.store import get_methodology
        meth = get_methodology(methodology_code)
        if not meth:
            return ""
        parts = [f"METHODOLOGY REFERENCE: {meth['code']}"]
        if meth.get("name"):
            parts.append(f"Full name: {meth['name']}")
        if meth.get("standard"):
            parts.append(f"Standard: {meth['standard']}")
        if meth.get("category"):
            parts.append(f"Category: {meth['category']}")
        if meth.get("sector"):
            parts.append(f"Sector: {meth['sector']}")
        if meth.get("applicability"):
            parts.append(f"Applicability conditions: {meth['applicability']}")
        if meth.get("status") == "deprecated":
            parts.append(f"WARNING: This methodology is deprecated. Superseded by: {meth.get('superseded_by', 'unknown')}")
        if meth.get("project_count"):
            parts.append(f"Used in {meth['project_count']} registered projects globally")
        return "\n".join(parts)
    except Exception as e:
        logger.warning("Methodology lookup failed: %s", e)
        return ""


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
    methodology_context = ""
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

    try:
        methodology_context = _get_methodology_context(project_info.get("methodology"))
    except Exception as e:
        logger.warning("Methodology DB lookup failed: %s", e)

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

    intake_context = _format_filtered_project_context(project_info, section_id)
    if intake_context:
        user_prompt += intake_context + "\n"

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

    if methodology_context:
        user_prompt += (
            "### Methodology database reference:\n"
            f"{methodology_context}\n\n"
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

    intake_context = _format_project_context(project_info)
    if intake_context:
        user_prompt += intake_context + "\n"

    methodology_context = _get_methodology_context(project_info.get("methodology"))
    if methodology_context:
        user_prompt += (
            "### Methodology database reference:\n"
            f"{methodology_context}\n\n"
            "Use this methodology information to check applicability conditions "
            "and ensure the project properly addresses methodology requirements.\n\n"
        )

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
