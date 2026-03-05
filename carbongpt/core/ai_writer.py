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
    "A": ["proponent", "project_overview", "crediting_dates", "technology", "location", "prior_consideration", "legal_compliance"],
    "A.1": ["proponent", "project_overview", "crediting_dates"],
    "A.2": ["technology", "location"],
    "A.3": ["technology"],
    "A.4": ["project_overview", "crediting_dates"],
    "A.5": ["prior_consideration"],
    "B": ["baseline_additionality", "emission_reductions", "monitoring", "prior_consideration", "legal_compliance"],
    "B.5": ["baseline_additionality", "prior_consideration"],
    "B.6": ["sdgs"],
    "C": ["project_overview", "crediting_dates"],
    "D": ["safeguards"],
    "E": ["stakeholders", "proponent"],
    "1": ["proponent", "project_overview", "crediting_dates", "legal_compliance"],
    "1.6": ["proponent"],
    "1.7": ["proponent"],
    "1.8": ["legal_compliance"],
    "1.9": ["crediting_dates"],
    "1.15": ["legal_compliance"],
    "1.16": ["legal_compliance"],
    "2": ["baseline_additionality", "technology"],
    "3": ["emission_reductions", "monitoring"],
    "4": ["monitoring"],
    "programme": ["programme", "management_system", "eligibility"],
    "vpa_details": ["vpa_details", "technology", "location"],
    "monitoring_period": ["monitoring_period", "implementation_status", "data_collection", "calibration_data_quality"],
    "forward_action_requests": ["forward_action_requests"],
    "deviations": ["deviations"],
    "results": ["results", "emission_reductions"],
}


def _format_project_context(project_info):
    intake = project_info.get("project_intake") or {}
    if not intake:
        return ""

    parts = []

    card_formatters = {
        "proponent": ("Project Developer / Proponent", [
            ("organization_name", "Organization Name"),
            ("contact_person", "Contact Person"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("address", "Address"),
            ("other_entities", "Other Entities Involved"),
        ]),
        "project_overview": ("Project Overview", [
            ("objective", "Project Objective"),
            ("summary", "Project Summary"),
            ("start_date", "Start Date"),
            ("scale", "Project Scale"),
            ("num_units", "Number of Units"),
            ("activity_type", "Activity Type"),
            ("sectoral_scope", "Sectoral Scope"),
        ]),
        "crediting_dates": ("Crediting Period & Project Dates", [
            ("crediting_start", "Crediting Period Start"),
            ("crediting_length_years", "Crediting Period Length (years)"),
            ("crediting_end", "Crediting Period End"),
            ("operational_lifetime", "Operational Lifetime (years)"),
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
        "prior_consideration": ("Prior Consideration & Financial Need", [
            ("awareness_date", "Date of Awareness of Carbon Finance"),
            ("evidence", "Prior Consideration Evidence"),
            ("financial_need", "Financial Need / Investment Barrier"),
            ("funding_sources", "Funding Sources"),
        ]),
        "legal_compliance": ("Legal & Compliance", [
            ("ownership", "GHG Emission Reduction Ownership"),
            ("regulatory_compliance", "Regulatory Compliance"),
            ("double_counting", "Double Counting Declaration"),
            ("audit_history", "Audit History"),
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
        "programme": ("Programme Description (PoA)", [
            ("objective", "Programme Objective"),
            ("geographic_scope", "Geographic Scope"),
            ("cme_name", "CME Name"),
            ("cme_details", "CME Details"),
            ("target_vpas", "Target Number of VPAs"),
            ("duration", "Programme Duration"),
            ("first_submission_date", "Date of First Submission"),
        ]),
        "management_system": ("Management System (PoA)", [
            ("description", "Management System Description"),
            ("multiple_technologies", "Multiple Technologies / Measures"),
            ("qa_qc", "Programme-Level QA/QC"),
        ]),
        "eligibility": ("Eligibility & Inclusion (PoA)", [
            ("criteria", "Eligibility Criteria"),
            ("inclusion_process", "Inclusion Process"),
            ("approval_mechanism", "Approval Mechanism"),
        ]),
        "vpa_details": ("VPA Details", [
            ("eligibility_justification", "Eligibility Justification"),
            ("start_date", "VPA Start Date"),
            ("baseline_scenario", "VPA Baseline Scenario"),
        ]),
        "monitoring_period": ("Monitoring Period", [
            ("start_date", "Period Start"),
            ("end_date", "Period End"),
            ("period_number", "Period Number"),
        ]),
        "implementation_status": ("Implementation Status", [
            ("status_description", "Status Description"),
            ("units_active", "Active Units"),
            ("units_decommissioned", "Decommissioned Units"),
            ("training_activities", "Training Activities"),
        ]),
        "forward_action_requests": ("Forward Action Requests", [
            ("previous_fars", "FARs from Previous Verification"),
            ("response", "Response to FARs"),
        ]),
        "data_collection": ("Data Collection", [
            ("num_units", "Number of Units"),
            ("collection_summary", "Collection Summary"),
            ("data_highlights", "Data Highlights"),
        ]),
        "calibration_data_quality": ("Calibration & Data Quality", [
            ("calibration_records", "Calibration Records"),
            ("data_sources", "Data Sources"),
        ]),
        "deviations": ("Deviations & Changes", [
            ("methodology_deviations", "Methodology Deviations"),
            ("period_changes", "Period Changes"),
        ]),
        "results": ("Emission Reduction Results", [
            ("baseline_emissions", "Baseline Emissions"),
            ("project_emissions", "Project Emissions"),
            ("leakage", "Leakage"),
            ("net_er", "Net Emission Reductions"),
        ]),
        "scope": ("Assessment Scope (ValVer)", [
            ("assessment_type", "Assessment Type"),
            ("scope_description", "Scope Description"),
        ]),
        "assessment": ("Assessment Methodology (ValVer)", [
            ("methodology", "Assessment Methodology"),
            ("site_visit", "Site Visit"),
            ("interviews", "Interviews"),
        ]),
        "findings": ("Key Findings (ValVer)", [
            ("summary", "Findings Summary"),
            ("cars", "CARs"),
            ("cls", "CLs"),
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


def _format_methodology_parameters_context(project_info):
    intake = project_info.get("project_intake") or {}
    meth_params = intake.get("methodology_parameters")
    if not meth_params or not isinstance(meth_params, dict):
        return ""

    settings = project_info.get("project_settings") or {}

    parts = []

    settings_lines = []
    for k, v in settings.items():
        if v and k not in ("calculation_method",):
            settings_lines.append(f"  - {k.replace('_', ' ').title()}: {v}")
    if settings.get("calculation_method"):
        settings_lines.append(f"  - Selected Calculation Method: {settings['calculation_method']}")
    if settings_lines:
        parts.append("**Methodology Choices:**\n" + "\n".join(settings_lines))

    pi_lines = []
    mon_lines = []
    def_lines = []
    qual_lines = []
    for key, val in meth_params.items():
        if not val or not str(val).strip():
            continue
        label = key.replace("_", " ").title()
        if key.startswith("mon_"):
            mon_lines.append(f"  - {label[4:]}: {val}")
        elif key.startswith("def_"):
            def_lines.append(f"  - {label[4:]}: {val}")
        else:
            pi_lines.append(f"  - {label}: {val}")

    if pi_lines:
        parts.append("**Project-Specific Parameters:**\n" + "\n".join(pi_lines))
    if mon_lines:
        parts.append("**Monitoring Parameters:**\n" + "\n".join(mon_lines))
    if def_lines:
        parts.append("**Methodology Default Overrides:**\n" + "\n".join(def_lines))

    if not parts:
        return ""
    return "### Methodology-Specific Data (from methodology setup):\n" + "\n\n".join(parts) + "\n"


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


FORMAT_SYSTEM_GUIDANCE = {
    "table": (
        "\n\nFORMAT REQUIREMENT: This section must use markdown tables with clear column headers. "
        "Present structured information in table format. "
        "Each row should represent one item (condition, parameter, entity, etc.) with columns for key attributes. "
        "Include brief introductory or contextual prose before the table where appropriate."
    ),
    "parameter_blocks": (
        "\n\nFORMAT REQUIREMENT: Present each parameter as a clearly delineated structured block. "
        "Each block must include fields on separate lines: Parameter name, Symbol (if applicable), Unit, "
        "Value applied, Source of data (with traceable reference), and Purpose of data. "
        "Organize parameters under SDG headings where applicable, with SDG 13 first. "
        "Include introductory prose and any necessary narrative context between parameter blocks."
    ),
    "checklist": (
        "\n\nFORMAT REQUIREMENT: Present as a structured checklist or assessment table. "
        "Each item should have a clear Yes/No/NA indicator followed by a brief justification or description. "
        "Use a consistent format for all items (e.g., markdown table or structured list with indicators). "
        "Include introductory context and summary remarks where appropriate."
    ),
    "equations_and_prose": (
        "\n\nFORMAT REQUIREMENT: Combine narrative explanation with mathematical equations. "
        "Include equations using standard notation (e.g., ER_y = BE_y - PE_y - LE_y). "
        "Define all variables after each equation. "
        "Show sample calculations with actual parameter values substituted into the equations. "
        "Organize calculations under SDG headings where applicable, with SDG 13 first. "
        "Reference supporting spreadsheets where calculations are performed."
    ),
    "summary_table": (
        "\n\nFORMAT REQUIREMENT: Present results in a markdown summary table with clear column headers, "
        "row-by-row data (e.g., by year or by SDG), and totals/averages where applicable. "
        "Include units in column headers. "
        "Include introductory prose before the table and any required narrative context after it."
    ),
}

FORMAT_CLOSING_INSTRUCTIONS = {
    "table": "Present the core information using markdown tables, with introductory context as needed.",
    "parameter_blocks": "Present each parameter as a structured block, with narrative context between blocks as needed.",
    "checklist": "Present the assessment as a structured checklist, with introductory and summary prose as needed.",
    "equations_and_prose": "Include equations with variable definitions and sample calculations, combined with explanatory narrative.",
    "summary_table": "Present the summary in a markdown table, with introductory and contextual prose as needed.",
    "prose": "Use proper formatting with sub-headings where appropriate. Include markdown tables where the format instructions specify them.",
}


def _get_format_system_guidance(content_format):
    return FORMAT_SYSTEM_GUIDANCE.get(content_format, "")


def _get_format_closing_instruction(content_format):
    return FORMAT_CLOSING_INSTRUCTIONS.get(content_format, "Use proper formatting with sub-headings where appropriate.")


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

    content_format = subsection.get("content_format", "prose")
    format_instructions = subsection.get("format_instructions", "")
    template_scaffold = subsection.get("template_scaffold", "")

    format_guidance = _get_format_system_guidance(content_format)

    scaffold_rule = ""
    if template_scaffold:
        scaffold_rule = (
            "\n- TEMPLATE COMPLIANCE: A template scaffold is provided below. You MUST use the EXACT table structure, "
            "column headers, and row labels from the scaffold. Fill in the [...] placeholders with project-specific data. "
            "You may add or remove rows as needed but do NOT change the column headers or field labels. "
            "This scaffold comes directly from the official standard template document."
        )

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
        "- Write in the professional style expected by VVBs (Validation/Verification Bodies).\n"
        f"{scaffold_rule}"
        f"{format_guidance}"
    )

    must_include = "\n".join(f"  - {item}" for item in subsection.get("must_include", []))
    examples = "\n".join(f"  - {ex}" for ex in subsection.get("examples", []))

    user_prompt = f"## Task: Draft section {section_id}: {subsection['title']}\n\n"
    user_prompt += f"### Section Requirements (must include):\n{must_include}\n\n"

    if format_instructions:
        user_prompt += f"### Required Format:\n{format_instructions}\n\n"

    if template_scaffold:
        user_prompt += (
            "### Official Template Scaffold (use this exact structure):\n"
            "Fill in the [...] placeholders with project-specific data. "
            "Do not change the column headers or field labels.\n\n"
            f"{template_scaffold}\n\n"
        )

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

    meth_params_context = _format_methodology_parameters_context(project_info)
    if meth_params_context:
        user_prompt += meth_params_context + "\n"

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

    findings_context = ""
    try:
        methodology = project_info.get("methodology", "")
        if methodology:
            from carbongpt.core.findings_extractor import get_findings_context_for_section
            findings_context = get_findings_context_for_section(methodology, subsection["title"])
    except Exception as e:
        logger.warning("Findings context retrieval failed: %s", e)

    if findings_context:
        user_prompt += (
            findings_context + "\n"
            "Address these known VVB concern areas proactively in your writing. "
            "Ensure the content you produce would not trigger these findings.\n\n"
        )

    if user_instructions:
        user_prompt += f"### Additional instructions from the user:\n{user_instructions}\n\n"

    format_closing = _get_format_closing_instruction(content_format)
    user_prompt += (
        f"Write the complete content for section {section_id}: {subsection['title']}. "
        f"Make it ready for inclusion in the document. {format_closing}"
    )

    result = _call_openai(system_prompt, user_prompt, max_tokens=4000)
    return result


def generate_full_document(
    standard,
    project_doc_type,
    project_info,
    existing_pdd_text=None,
    reference_docs_text=None,
    user_instructions=None,
    progress_callback=None,
):
    guide_dt = get_guide_doc_type(standard, project_doc_type)
    if not guide_dt:
        raise ValueError(f"No guide mapping for {standard}/{project_doc_type}")

    guide = load_guide(standard, guide_dt)
    subsections = guide.SUBSECTIONS
    section_ids = list(subsections.keys())
    total = len(section_ids)
    results = []

    for idx, section_id in enumerate(section_ids):
        if progress_callback:
            progress_callback(idx, total, section_id, subsections[section_id].get("title", ""))

        try:
            text = generate_section_draft(
                standard=standard,
                project_doc_type=project_doc_type,
                section_id=section_id,
                project_info=project_info,
                existing_pdd_text=existing_pdd_text,
                reference_docs_text=reference_docs_text,
                user_instructions=user_instructions,
            )
            results.append({
                "section_id": section_id,
                "section_title": subsections[section_id].get("title", ""),
                "generated_text": text,
                "status": "success",
            })
        except Exception as e:
            logger.error("Failed to generate section %s: %s", section_id, e)
            results.append({
                "section_id": section_id,
                "section_title": subsections[section_id].get("title", ""),
                "generated_text": "",
                "status": "error",
                "error": str(e),
            })

    if progress_callback:
        progress_callback(total, total, "", "Complete")

    return results


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

    findings_review_context = ""
    try:
        methodology = project_info.get("methodology", "")
        if methodology:
            from carbongpt.core.findings_extractor import get_findings_review_context
            findings_review_context = get_findings_review_context(methodology)
    except Exception as e:
        logger.warning("Findings review context retrieval failed: %s", e)

    if findings_review_context:
        user_prompt += (
            findings_review_context + "\n"
            "Use these known VVB finding patterns to identify similar issues in the document being reviewed. "
            "Flag any sections that would likely trigger these findings during validation/verification.\n\n"
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
