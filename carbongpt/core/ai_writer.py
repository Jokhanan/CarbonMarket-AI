import json
import logging

from carbongpt.guides import load_guide, DOC_TYPE_LABELS, GUIDE_REGISTRY
from carbongpt.core.knowledge_retrieval import (
    retrieve_section_context, format_context_for_prompt,
    map_section_to_domain, map_section_to_purpose, retrieve_section_exemplar,
)
from carbongpt.core.openai_client import DEFAULT_MODEL as MODEL, UPGRADE_MODEL

logger = logging.getLogger(__name__)

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

    import copy as _copy
    intake = _copy.deepcopy(intake)

    _meth_settings = project_info.get("methodology_settings") or {}
    if isinstance(_meth_settings, str):
        try:
            import json as _j
            _meth_settings = _j.loads(_meth_settings)
        except Exception:
            _meth_settings = {}

    _po = intake.setdefault("project_overview", {})
    _tech = intake.setdefault("technology", {})
    _loc = intake.setdefault("location", {})

    if not _tech.get("fuel_baseline") and _meth_settings.get("baseline_fuel"):
        _tech["fuel_baseline"] = _meth_settings["baseline_fuel"]
    if not _tech.get("fuel_project") and _meth_settings.get("project_fuel"):
        _tech["fuel_project"] = _meth_settings["project_fuel"]

    if not _tech.get("baseline_scenario") and _tech.get("fuel_baseline"):
        _tech["baseline_scenario"] = _tech["fuel_baseline"]
    if not _tech.get("project_scenario") and _tech.get("fuel_project"):
        _tech["project_scenario"] = _tech["fuel_project"]

    if not _loc.get("regions") and project_info.get("region"):
        _loc["regions"] = project_info["region"]
    _lat = project_info.get("latitude")
    _lon = project_info.get("longitude")
    if not _loc.get("coordinates") and _lat is not None and _lon is not None:
        try:
            _loc["coordinates"] = f"{float(_lat):.4f}, {float(_lon):.4f}"
        except (TypeError, ValueError):
            pass

    if not _po.get("scale") and _meth_settings.get("scale_classification"):
        _po["scale"] = _meth_settings["scale_classification"]

    _num_dev = _po.get("num_devices")
    if _num_dev is not None and not _po.get("num_units"):
        try:
            _po["num_units"] = f"{int(_num_dev):,} devices"
        except (TypeError, ValueError):
            pass

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

    _sdg_data = intake.get("sdgs", {})
    if _sdg_data and isinstance(_sdg_data, dict):
        _selected = _sdg_data.get("selected_sdgs", [])
        if _selected:
            _sdg_lines = []
            for _s in _selected:
                _gn = _s.get("goal_number", "")
                _contrib = _s.get("contribution_description", "")
                _inds = _s.get("indicators", [])
                _line = f"  - SDG {_gn}"
                if _inds and isinstance(_inds, list):
                    _ind = _inds[0]
                    _ind_name = _ind.get("indicator_name", "")
                    _bl_val = _ind.get("baseline_value", "")
                    _pj_val = _ind.get("project_value", "")
                    _tier = _ind.get("evidence_tier", "")
                    _meas = _ind.get("measurement_approach", "")
                    if _ind_name:
                        _line += f": {_ind_name}"
                    if _bl_val or _pj_val:
                        _line += f" | Baseline: {_bl_val or 'N/A'}, Project: {_pj_val or 'N/A'}"
                    if _tier:
                        _line += f" ({_tier})"
                    if _meas and _meas != _contrib:
                        _line += f"\n    Measurement: {_meas}"
                elif _contrib:
                    _line += f": {_contrib}"
                _sdg_lines.append(_line)
            if _sdg_lines:
                parts.append("**SDGs & Co-benefits:**\n" + "\n".join(_sdg_lines))
        intake.pop("sdgs", None)

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


def _format_confirmed_parameters_context(project_info):
    project_id = project_info.get("id")
    if not project_id:
        return ""
    try:
        from carbongpt.core.parameter_engine import get_parameters_as_dict, get_fuel_display_label
        params = get_parameters_as_dict(project_id)
        if not params:
            return ""

        confirmed_lines = []
        default_lines = []
        for key, pdata in sorted(params.items()):
            val = pdata.get("value")
            if val is None or (isinstance(val, str) and not val.strip()):
                continue
            unit = pdata.get("unit", "")
            source = pdata.get("source_type", "default")
            p_status = pdata.get("param_status", "default")
            reference = pdata.get("source_reference", "")
            if key in ("baseline_fuel",) and isinstance(val, str):
                display_val = get_fuel_display_label(val)
                line = f"  - {key}: {display_val} (canonical: {val})"
            elif isinstance(val, float):
                line = f"  - {key}: {val:g}"
            else:
                line = f"  - {key}: {val}"
            if unit:
                line += f" {unit}"
            line += f" (source: {source}"
            if reference:
                line += f", reference: {reference}"
            line += ")"
            if p_status == "confirmed":
                confirmed_lines.append(line)
            else:
                default_lines.append(line)

        parts = []
        if confirmed_lines:
            parts.append(
                "### PRIORITY 1 -- Confirmed Project Calculation Values\n"
                "These are the authoritative parameter values for this project. "
                "Use these exact values in all calculations, equations, and references. "
                "If these differ from generic methodology defaults below, use THESE values.\n\n"
                + "\n".join(confirmed_lines)
            )
        if default_lines:
            parts.append(
                "### Project Parameter Defaults (not yet confirmed)\n"
                "These values are auto-populated defaults. They may be used as reasonable estimates "
                "but should be noted as provisional where referenced in calculations.\n\n"
                + "\n".join(default_lines)
            )

        if not parts:
            return ""
        return "\n\n".join(parts) + "\n"
    except Exception as e:
        logger.warning("Failed to format confirmed parameters context: %s", e)
        return ""


def _format_selected_scenario_context(project_info):
    try:
        project_id = project_info.get("id")
        selected_id = project_info.get("selected_scenario_id")
        if not project_id or not selected_id:
            return ""

        from carbongpt.core.er_simulator import get_selected_scenario
        detail = get_selected_scenario(project_id)
        if not detail:
            return ""

        scenario = detail["scenario"]
        years = detail["years"]
        summary = scenario.get("results_summary") or {}
        if isinstance(summary, str):
            import json as _json
            try:
                summary = _json.loads(summary)
            except Exception:
                summary = {}

        if not summary:
            return ""

        lines = [
            f"  - Scenario Name: {scenario.get('name', 'Unknown')}",
            f"  - Total Emission Reductions: {summary.get('total_er', 0):,.0f} tCO2e",
            f"  - Average Annual ER: {summary.get('average_annual_er', 0):,.0f} tCO2e/yr",
            f"  - Crediting Period: {scenario.get('crediting_years', 7)} years",
            f"  - Methodology: {scenario.get('methodology_code', '')}",
        ]

        for y in years[:3]:
            net_er = float(y.get("net_er", 0))
            lines.append(f"  - Year {y['year_number']}: {net_er:,.0f} tCO2e net ER")
        if len(years) > 3:
            lines.append(f"  - ... ({len(years)} years total)")

        overrides = scenario.get("parameter_overrides") or {}
        if isinstance(overrides, str):
            import json as _json
            try:
                overrides = _json.loads(overrides)
            except Exception:
                overrides = {}
        clean_overrides = {k: v for k, v in overrides.items() if not str(k).startswith("__")}
        if clean_overrides:
            lines.append("")
            lines.append("  Key scenario assumptions:")
            for k, v in clean_overrides.items():
                lines.append(f"  - {k}: {v}")

        return (
            "### Selected Scenario Results (for PDD drafting)\n"
            "These are the emission reduction projections from the project's selected scenario. "
            "Use these numbers when writing ER estimation, monitoring plan, and financial sections. "
            "Reference the methodology and calculation approach.\n\n"
            + "\n".join(lines) + "\n"
        )
    except Exception as e:
        logger.warning("Failed to format selected scenario context: %s", e)
        return ""


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
    for key, val in meth_params.items():
        if not val or not str(val).strip():
            continue
        if key.startswith("tool33_"):
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
    return "### PRIORITY 2 -- Project Identity and Methodology Choices\n" + "\n\n".join(parts) + "\n"


def _format_tool33_defaults_context(project_info):
    methodology = project_info.get("methodology", "")
    if not methodology:
        return ""
    try:
        from carbongpt.core.tool_defaults import get_defaults_for_methodology
        country = project_info.get("country", "")
        settings = project_info.get("project_settings") or {}
        defaults = get_defaults_for_methodology(
            methodology,
            country=country,
            baseline_fuel=settings.get("baseline_fuel"),
            project_fuel=settings.get("project_fuel"),
        )
        parts = []
        params = defaults.get("parameters", {})
        if params:
            param_lines = []
            for pkey, pval in params.items():
                if not isinstance(pval, dict):
                    continue
                if "value" not in pval and "unit" not in pval:
                    sub_items = []
                    for sk, sv in pval.items():
                        if isinstance(sv, dict) and "value" in sv:
                            sub_items.append(f"{sk}={sv['value']}")
                    if sub_items:
                        param_lines.append(f"  - {pkey}: {', '.join(sub_items)}")
                    continue
                val = pval.get("value", "")
                unit = pval.get("unit", "")
                src = pval.get("source", "")
                param_lines.append(f"  - {pkey}: {val} {unit} (Source: {src})")
            if param_lines:
                parts.append("**Reference Default Values (CDM TOOL33 / IPCC):**\n" + "\n".join(param_lines))

        equations = defaults.get("equations", [])
        if equations:
            eq_lines = []
            for eq in equations:
                eq_lines.append(f"  - {eq.get('name', '')}: {eq.get('formula', '')} -- {eq.get('description', '')}")
            if eq_lines:
                parts.append("**Key Methodology Equations:**\n" + "\n".join(eq_lines))

        if not parts:
            return ""
        return (
            "### PRIORITY 3 -- Methodology Reference Defaults (CDM TOOL33, IPCC)\n"
            "These are official reference ranges and equations from the methodology and IPCC guidelines. "
            "Use as citation sources. If the Confirmed Project Values (PRIORITY 1) above provide "
            "specific values, use THOSE instead of these generic defaults.\n\n"
            + "\n\n".join(parts) + "\n"
        )
    except Exception as e:
        logger.warning("TOOL33 context formatting failed: %s", e)
        return ""


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


PROJECT_TYPE_KEYWORDS = {
    "cookstove": ["cookstove", "stove", "ics", "improved cook", "clean cooking"],
    "solar": ["solar", "photovoltaic", "pv"],
    "wind": ["wind", "wind farm", "wind power"],
    "hydro": ["hydro", "hydroelectric", "hydropower"],
    "landfill_biogas_waste": ["landfill", "lfg", "biogas", "waste", "wastewater", "rdf", "msw"],
}


def _infer_project_type(project_info):
    text = " ".join([
        project_info.get("name", ""),
        project_info.get("description", ""),
        project_info.get("methodology", ""),
    ]).lower()
    for ptype, keywords in PROJECT_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return ptype
    return "other"


def _get_methodology_context(methodology_code):
    """
    Returns methodology context for AI prompting.

    Priority order:
      1. Indexed Methodology Pack — curated project examples, methodology doc
         chunks, and DOE findings retrieved via pack-scoped vector search.
      2. Legacy fallback — methodology_library DB lookup (metadata only).

    If no indexed pack exists, or if pack retrieval fails for any reason,
    the legacy path is used transparently.  No regression is possible.
    """
    if not methodology_code:
        return ""
    # ── Pack-first path ──────────────────────────────────────────────────────
    try:
        pack_context = _get_pack_context(methodology_code)
        if pack_context:
            return pack_context
    except Exception as exc:
        logger.warning(
            "Pack context retrieval failed for %s, using legacy fallback: %s",
            methodology_code, exc,
        )
    # ── Legacy fallback ──────────────────────────────────────────────────────
    return _get_methodology_context_legacy(methodology_code)


def _get_methodology_context_legacy(methodology_code):
    """Original metadata-only lookup from methodology_library."""
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
            parts.append(
                f"WARNING: This methodology is deprecated. "
                f"Superseded by: {meth.get('superseded_by', 'unknown')}"
            )
        if meth.get("project_count"):
            parts.append(f"Used in {meth['project_count']} registered projects globally")
        return "\n".join(parts)
    except Exception as exc:
        logger.warning("Methodology legacy lookup failed: %s", exc)
        return ""


def _get_pack_context(methodology_code: str) -> str:
    """
    Return rich context from an indexed Methodology Pack.
    Returns empty string if no indexed pack exists for this methodology.
    Uses text-based chunk retrieval (keyword fallback) if embeddings are
    unavailable, so it never raises.
    """
    try:
        from carbongpt.repository.pack_store import (
            get_indexed_pack_for_methodology,
            list_pack_documents,
            list_findings,
        )
        pack = get_indexed_pack_for_methodology(methodology_code)
        if not pack:
            return ""

        pack_id = pack["id"]
        parts = [
            f"--- METHODOLOGY PACK: {pack['methodology_code']}"
            + (f" {pack['methodology_version']}" if pack.get("methodology_version") else "")
            + (f" ({pack['registry'].upper()})" if pack.get("registry") else "")
            + " ---"
        ]

        # Retrieve text chunks from the pack (methodology docs first, then examples)
        docs = list_pack_documents(pack_id)
        meth_docs = [d for d in docs if d["document_role"] == "METHODOLOGY_DOC"
                     and d.get("doc_ingestion_status") == "ingested"]
        pdd_docs  = [d for d in docs if d["document_role"] == "PDD"
                     and d.get("doc_ingestion_status") == "ingested"]
        mr_docs   = [d for d in docs if d["document_role"] == "MR"
                     and d.get("doc_ingestion_status") == "ingested"]

        # Include a brief methodology doc note (from metadata; chunks via vector if available)
        if meth_docs:
            parts.append(
                f"[METHODOLOGY DOCUMENT] {meth_docs[0].get('filename', '')} — "
                f"methodology document ingested and available for context."
            )

        # Summarise available examples without pulling full chunks
        # (full vector chunk retrieval is done by the knowledge_retrieval module)
        if pdd_docs:
            countries = sorted({d["project_country"] for d in pdd_docs if d.get("project_country")})
            parts.append(
                f"[PACK EXAMPLES] {len(pdd_docs)} PDDs available"
                + (f" — countries: {', '.join(countries[:5])}" if countries else "")
            )
        if mr_docs:
            parts.append(f"[PACK EXAMPLES] {len(mr_docs)} Monitoring Reports available")

        # Include a sample of DOE findings (most valuable for review grounding)
        findings = list_findings(pack_id)
        if findings:
            parts.append(f"[DOE FINDINGS — {len(findings)} total from real projects]")
            shown = 0
            for f in findings[:5]:
                ref = f.get("finding_reference") or f.get("finding_type", "")
                sec = f.get("section_reference", "")
                text = (f.get("finding_text") or "")[:300]
                parts.append(
                    f"  {ref}"
                    + (f" ({sec})" if sec else "")
                    + f": {text}"
                )
                shown += 1
            if len(findings) > shown:
                parts.append(f"  ... and {len(findings) - shown} more findings in pack.")

        return "\n".join(parts)
    except Exception as exc:
        logger.warning("Pack context assembly failed for %s: %s", methodology_code, exc)
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


COMPLEX_CONTENT_FORMATS = {"equations_and_prose", "parameter_blocks"}

COMPLEX_SECTION_PATTERNS = [
    "additionality", "baseline", "emission", "quantification",
    "calculation", "monitoring_plan", "leakage",
]

COMPLEX_SECTION_IDS = {
    "B.3", "B.4", "B.5", "B.6", "B.6.1", "B.6.2", "B.7",
    "2.3", "2.4", "2.5", "3.1", "3.2", "3.3", "3.4", "4.1", "4.2", "4.3", "4.4",
}

MIN_WORDS_FOR_ESCALATION = 200


def _select_model_for_section(section_id, content_format="prose", section_title=""):
    if content_format in COMPLEX_CONTENT_FORMATS:
        return UPGRADE_MODEL

    if section_id in COMPLEX_SECTION_IDS:
        return UPGRADE_MODEL

    title_lower = section_title.lower()
    for pattern in COMPLEX_SECTION_PATTERNS:
        if pattern in title_lower:
            return UPGRADE_MODEL

    return MODEL


def _call_openai(system_prompt, user_prompt, response_format=None, max_tokens=4000, model_override=None):
    from carbongpt.core.openai_client import call_openai
    return call_openai(
        system_prompt, user_prompt,
        response_format=response_format,
        max_tokens=max_tokens,
        temperature=0.4,
        model_override=model_override or MODEL,
    )


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


def _draft_parameter_block(parameter_id, project_info):
    """SPEC-06 T5: looks up one methodology_parameters row and drafts its
    template block through the closed-fact-set pipeline
    (parameter_block_drafting.py). Scoped to RECH v5.0 only for now
    (methodology_code='407') — matching this session's periemeter across
    SPEC-06 T1-T6. project_info['methodology'] is a stale free-text field
    (e.g. project id=12 has 'TPDDTEC', not '407') and this codebase has no
    reliable project -> methodology_version_id resolver yet; generalizing
    beyond RECH is future work, not assumed here.

    Returns (block_text, model_used, fact_set) — the fact_set is returned
    too so callers (e.g. a demo script) can show it alongside the result.
    """
    from carbongpt.repository.db import get_cursor
    from carbongpt.repository.parameter_block_drafting import (
        build_parameter_fact_set,
        generate_parameter_block_content,
    )

    with get_cursor() as cur:
        cur.execute(
            "SELECT id, version, document_name FROM methodology_version_history "
            "WHERE methodology_code = '407' AND is_current = true"
        )
        meth_row = cur.fetchone()
        if meth_row is None:
            raise ValueError("RECH (407) has no current version ingested — cannot source a parameter block")

        cur.execute(
            "SELECT * FROM methodology_parameters WHERE methodology_version_id = %s AND parameter_id = %s",
            (meth_row["id"], parameter_id),
        )
        param_row = cur.fetchone()
        if param_row is None:
            raise ValueError(
                f"Parameter {parameter_id!r} not found in methodology_parameters for RECH v{meth_row['version']} "
                "— run rech_parameter_extractor.extract_rech_parameters()/store_rech_parameters() first"
            )

    fact_set = build_parameter_fact_set(
        dict(param_row), methodology_code="407", methodology_version=meth_row["version"],
        document_name=meth_row["document_name"], document_language=project_info.get("document_language"),
    )
    text, model = generate_parameter_block_content(fact_set)
    return text, model, fact_set


def generate_section_draft(
    standard,
    project_doc_type,
    section_id,
    project_info,
    existing_pdd_text=None,
    reference_docs_text=None,
    user_instructions=None,
    parameter_id=None,
):
    guide_dt = get_guide_doc_type(standard, project_doc_type)
    if not guide_dt:
        raise ValueError(f"No guide mapping for {standard}/{project_doc_type}")

    guide = load_guide(standard, guide_dt)
    subsection = guide.SUBSECTIONS.get(section_id)
    if not subsection:
        raise ValueError(f"Section {section_id} not found in guide")

    # SPEC-06 T5 integration (03.08.2026): a parameter_blocks-format
    # section (SPEC-05 field_type='parameter_block') is not free-form
    # prose — it's N repetitions of a fixed patron, one per methodology
    # parameter (SPEC-06 T3/T5). Drafting it with the generic prompt below
    # gave the model nothing sourced to cite and it invented methodology/
    # tool references (found testing this session, docs/STATUS.md) — the
    # same mechanism that produced the unsourced charcoal EF before
    # SPEC-01. When a specific parameter_id is requested, route through
    # the closed-fact-set pipeline instead (same discipline as SPEC-04's
    # defendability arguments): the model sees only that one parameter's
    # already-sourced fields, and a mechanical validator rejects anything
    # else. Without a parameter_id, falls through to the generic path
    # below (unchanged) — this integration only applies when the caller
    # is actually asking for one parameter's block.
    if subsection.get("content_format") == "parameter_blocks" and parameter_id:
        text, _model, _fact_set = _draft_parameter_block(parameter_id, project_info)
        return text

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

    try:
        domain = map_section_to_domain(section_id, subsection.get("title", ""))
        if domain:
            _project_type = _infer_project_type(project_info)
            _purpose = map_section_to_purpose(section_id, subsection.get("title", ""))
            exemplar_text = retrieve_section_exemplar(
                section_domain=domain,
                standard=standard,
                methodology_code=project_info.get("methodology"),
                project_type=_project_type,
                section_purpose=_purpose,
            )
            if exemplar_text:
                user_prompt += exemplar_text + "\n"
    except Exception as e:
        logger.debug("Exemplar retrieval skipped: %s", e)

    user_prompt += "### Project Information:\n"
    user_prompt += f"- Project name: {project_info.get('name', '[Not specified]')}\n"
    user_prompt += f"- Standard: {std_label}\n"
    user_prompt += f"- Country: {project_info.get('country', '[Not specified]')}\n"
    if project_info.get("methodology"):
        user_prompt += f"- Methodology: {project_info['methodology']}\n"
    if project_info.get("description"):
        user_prompt += f"- Project description: {project_info['description']}\n"
    user_prompt += "\n"

    confirmed_params_context = _format_confirmed_parameters_context(project_info)
    if confirmed_params_context:
        user_prompt += confirmed_params_context + "\n"

    selected_scenario_context = _format_selected_scenario_context(project_info)
    if selected_scenario_context:
        user_prompt += selected_scenario_context + "\n"

    intake_context = _format_filtered_project_context(project_info, section_id)
    if intake_context:
        user_prompt += intake_context + "\n"

    meth_params_context = _format_methodology_parameters_context(project_info)
    if meth_params_context:
        user_prompt += meth_params_context + "\n"

    tool33_context = _format_tool33_defaults_context(project_info)
    if tool33_context:
        user_prompt += tool33_context + "\n"

    if existing_pdd_text:
        pdd_excerpt = existing_pdd_text[:25000]
        if len(existing_pdd_text) > 25000:
            pdd_excerpt += "\n[... PDD text truncated ...]"
        user_prompt += (
            "### Existing Project Description (PDD):\n"
            "This is the registered PDD for this project. Extract and use specific data, parameters, "
            "baseline descriptions, technology details, and monitoring plan from this document. "
            "Ensure consistency with the project design.\n"
            f'"""\n{pdd_excerpt}\n"""\n\n'
        )

    if reference_docs_text:
        max_ref_chars = 30000
        ref_excerpt = reference_docs_text[:max_ref_chars]
        if len(reference_docs_text) > max_ref_chars:
            ref_excerpt += "\n[... document text truncated ...]"
        user_prompt += (
            "### Project Documents (uploaded by the user):\n"
            "IMPORTANT: These documents contain real project data, field measurements, survey results, "
            "and technical details. Extract and USE specific data points, findings, values, and facts "
            "from these documents when writing this section. Do NOT ignore this content — it is the "
            "primary source of project-specific intelligence. Reference specific data, numbers, and "
            "conclusions from these documents rather than writing generic text.\n\n"
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

    project_brief = (project_info.get("project_intake") or {}).get("_project_brief")
    if project_brief:
        user_prompt += (
            "### Project Brief (consistent facts for all sections):\n"
            f"{project_brief}\n\n"
        )

    format_closing = _get_format_closing_instruction(content_format)
    user_prompt += (
        f"Write the complete content for section {section_id}: {subsection['title']}. "
        f"Make it ready for inclusion in the document. {format_closing}"
    )

    selected_model = _select_model_for_section(section_id, content_format, subsection.get("title", ""))
    logger.info("Section %s: using model %s (format=%s)", section_id, selected_model, content_format)

    result = _call_openai(system_prompt, user_prompt, max_tokens=4000, model_override=selected_model)

    word_count = len(result.split())
    if selected_model == MODEL and word_count < MIN_WORDS_FOR_ESCALATION:
        logger.info("Section %s output too short (%d words), escalating to %s", section_id, word_count, UPGRADE_MODEL)
        result = _call_openai(system_prompt, user_prompt, max_tokens=4000, model_override=UPGRADE_MODEL)

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
        pdd_excerpt = pdd_text[:20000]
        if len(pdd_text) > 20000:
            pdd_excerpt += "\n[... PDD text truncated ...]"
        user_prompt += (
            "### Project Description (PDD) for cross-reference:\n"
            "Check that the document being reviewed is consistent with this PDD. "
            "Use specific data, parameters, and claims from the PDD to verify the reviewed document.\n"
            f'"""\n{pdd_excerpt}\n"""\n\n'
        )

    if reference_texts:
        max_ref_chars = 20000
        ref_excerpt = reference_texts[:max_ref_chars]
        if len(reference_texts) > max_ref_chars:
            ref_excerpt += "\n[... document text truncated ...]"
        user_prompt += (
            "### Project Documents (uploaded by the user):\n"
            "These contain real project data, field measurements, and technical details. "
            "Use this data to verify claims and check consistency in the document being reviewed.\n\n"
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


def extract_document_intelligence(parsed_text, file_name, doc_type):
    if not parsed_text or not parsed_text.strip():
        return None

    DOC_TYPE_LABELS = {
        "pdd": "Project Design Document (PDD)",
        "mr": "Monitoring Report",
        "poa_dd": "Programme of Activities Design Document",
        "vpa_dd": "VPA Design Document",
        "valver": "Validation/Verification Report",
        "reference": "Reference Document",
        "research": "Research Paper/Report",
        "field_data": "Field Data / Survey / Test Report",
        "other": "Supporting Document",
    }
    doc_label = DOC_TYPE_LABELS.get(doc_type, "Document")

    system_prompt = (
        "You are a carbon project intelligence analyst. Your job is to extract ALL useful "
        "data, facts, and findings from project documents.\n\n"
        "You must be thorough — extract every piece of information that could be useful for "
        "writing carbon project documents (PDD, MR, PoA-DD, VPA-DD, or validation reports).\n\n"
        "Return a structured summary organized into clear categories. Use bullet points. "
        "Include specific numbers, measurements, percentages, dates, and names — not vague summaries.\n\n"
        "If the document contains tables with data, extract the key values.\n"
        "If the document contains test results, extract all results and parameters.\n"
        "If the document contains survey data, extract sample sizes, key findings, and statistics."
    )

    chunk_size = 30000
    text = parsed_text.strip()
    if len(text) > chunk_size:
        half = chunk_size // 2
        text_to_process = text[:half] + "\n\n[... middle section omitted ...]\n\n" + text[-half:]
        truncated = True
    else:
        text_to_process = text
        truncated = False

    user_prompt = (
        f"Extract all useful intelligence from this {doc_label}.\n"
        f"File: {file_name}\n\n"
        "Organize your extraction into these categories (skip any category that has no relevant data):\n\n"
        "**Project Overview**: Project name, developer, location, country, start date, scale, sector\n"
        "**Technology**: Device/system type, manufacturer, model, specifications, efficiency, fuel type\n"
        "**Baseline Data**: Baseline practice, fuel consumption, energy sources, current situation\n"
        "**Test Results & Measurements**: Kitchen performance test results, water boiling test results, "
        "emission factors, thermal efficiency, specific fuel consumption, any measured values\n"
        "**Survey Data**: Sample size, methodology, key findings, demographics, usage patterns\n"
        "**Emission Factors & Parameters**: All emission factors, default values, conversion factors, "
        "fraction of non-renewable biomass (fNRB), net calorific values, any quantitative parameters\n"
        "**Emission Reductions**: Baseline emissions, project emissions, leakage, net ERs, calculation approach\n"
        "**Monitoring Data**: Monitored parameters, values, data collection methods, sampling approach\n"
        "**Stakeholder & Social**: Consultation outcomes, grievance mechanisms, gender considerations\n"
        "**Regulatory & Compliance**: Legal approvals, permits, host country authorizations\n"
        "**Key Dates**: Project start, crediting period, monitoring period, validation/verification dates\n"
        "**Other Important Facts**: Anything else relevant for carbon project documentation\n\n"
        "Be specific — extract actual values, not descriptions of what the document contains.\n"
    )
    if truncated:
        user_prompt += f"Note: The document has been truncated ({len(parsed_text):,} total characters). Extract everything from what is provided.\n"
    user_prompt += f'\n"""\n{text_to_process}\n"""'

    import time as _time
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            result = _call_openai(system_prompt, user_prompt, max_tokens=4000)
            if result and len(result) > 8000:
                result = result[:8000] + "\n\n[... summary trimmed to 8000 chars ...]"
            return result
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "rate" in err_str.lower()
            if is_rate_limit and attempt < max_retries:
                wait = (attempt + 1) * 5
                logger.info("Rate limited on extraction for %s, retrying in %ds (attempt %d/%d)", file_name, wait, attempt + 1, max_retries)
                _time.sleep(wait)
                continue
            logger.warning("Document intelligence extraction failed for %s: %s", file_name, e)
            raise


INTAKE_FIELD_SCHEMA = {
    "proponent": {
        "organization_name": "Organization / company name of the project developer or proponent",
        "contact_person": "Name of the primary contact person",
        "email": "Contact email address",
        "phone": "Contact phone number",
        "address": "Physical address of the organization",
        "other_entities": "Other entities or organizations involved and their roles",
    },
    "project_overview": {
        "start_date": "Project start date (YYYY-MM-DD format)",
        "scale": "Project scale (Micro-scale, Small-scale, or Large-scale)",
        "num_units": "Number of units, devices, or installations",
        "activity_type": "Type of activity (Greenfield, Switch from existing, Capacity addition, Energy efficiency)",
        "sectoral_scope": "Sectoral scope number and description",
    },
    "technology": {
        "description": "Technology or measure description",
        "manufacturer": "Manufacturer or supplier name",
        "model": "Model name or number",
        "fuel_baseline": "Baseline fuel type or energy source",
        "fuel_project": "Project fuel type or energy source",
        "distribution_method": "Distribution or deployment method",
    },
    "location": {
        "regions": "Geographic regions, provinces, or districts",
        "coordinates": "GPS coordinates or geographic boundaries",
        "target_population": "Target population or community description",
        "beneficiaries": "Number of beneficiaries or households",
    },
    "baseline_additionality": {
        "baseline_scenario": "Description of the baseline scenario",
        "additionality_justification": "Additionality justification or barriers",
        "barriers": "Barriers to implementation without carbon finance",
    },
    "emission_reductions": {
        "annual_er_estimate": "Estimated annual emission reductions (tCO2e/year)",
        "total_er_estimate": "Total estimated emission reductions over crediting period",
        "calculation_approach": "Approach used for ER calculations",
    },
    "monitoring": {
        "monitoring_approach": "Overall monitoring approach or plan description",
        "key_parameters": "Key monitored parameters and their data sources",
        "sampling_approach": "Sampling methodology and sample size",
    },
    "stakeholders": {
        "consultation_summary": "Summary of stakeholder consultations conducted",
        "grievance_mechanism": "Grievance redress mechanism description",
    },
    "safeguards": {
        "environmental_safeguards": "Environmental and social safeguard measures",
        "gender_considerations": "Gender-related considerations and impacts",
    },
    "prior_consideration": {
        "awareness_date": "Date of awareness of carbon finance (YYYY-MM-DD)",
        "funding_sources": "Other funding sources and financial need justification",
    },
    "legal_compliance": {
        "regulatory_compliance": "Regulatory approvals and compliance status",
        "host_country_authorization": "Host country authorization or letter of approval",
    },
    "monitoring_period": {
        "monitoring_period_start": "Start date of the monitoring period",
        "monitoring_period_end": "End date of the monitoring period",
        "implementation_status": "Implementation status during monitoring period",
        "active_units": "Number of active units or installations during the period",
        "deviations": "Deviations from the registered PDD methodology",
    },
    "emission_factors": {
        "fnrb": "Fraction of non-renewable biomass (fNRB) value",
        "ncv_baseline": "Net calorific value of baseline fuel",
        "ncv_project": "Net calorific value of project fuel",
        "ef_baseline": "Emission factor for baseline scenario",
        "ef_project": "Emission factor for project scenario",
        "thermal_efficiency_baseline": "Thermal efficiency of baseline device/system",
        "thermal_efficiency_project": "Thermal efficiency of project device/system",
    },
    "test_results": {
        "wbt_results": "Water Boiling Test results and key metrics",
        "kpt_results": "Kitchen Performance Test results and key metrics",
        "cct_results": "Controlled Cooking Test results and key metrics",
        "sfc_baseline": "Specific fuel consumption - baseline",
        "sfc_project": "Specific fuel consumption - project",
    },
}


def extract_structured_intelligence(parsed_text, file_name, doc_type):
    if not parsed_text or not parsed_text.strip():
        return None

    field_descriptions = []
    for category, fields in INTAKE_FIELD_SCHEMA.items():
        for field_key, description in fields.items():
            field_descriptions.append(f'  - category: "{category}", field_key: "{field_key}", description: "{description}"')
    fields_list = "\n".join(field_descriptions)

    DOC_TYPE_LABELS = {
        "pdd": "Project Design Document (PDD)",
        "mr": "Monitoring Report",
        "poa_dd": "Programme of Activities Design Document",
        "vpa_dd": "VPA Design Document",
        "valver": "Validation/Verification Report",
        "reference": "Reference Document",
        "research": "Research Paper/Report",
        "field_data": "Field Data / Survey / Test Report",
        "other": "Supporting Document",
    }
    doc_label = DOC_TYPE_LABELS.get(doc_type, "Document")

    system_prompt = (
        "You are a carbon project data extraction specialist. Your job is to extract specific, "
        "structured data points from project documents and map them to predefined fields.\n\n"
        "You MUST return valid JSON — an array of objects. Each object has:\n"
        '  - "category": the category key (string)\n'
        '  - "field_key": the field key (string)\n'
        '  - "value": the extracted value (string — always a string, even for numbers)\n'
        '  - "confidence": "high", "medium", or "low"\n\n'
        "Rules:\n"
        "- Only extract data points you can find explicitly stated in the document\n"
        "- Use exact values from the document — numbers, dates, names, measurements\n"
        "- Set confidence to 'high' when the value is clearly stated, 'medium' when inferred from context, "
        "'low' when uncertain or partially available\n"
        "- Do NOT make up or infer values that are not in the document\n"
        "- For numeric fields, include units (e.g., '50,000 stoves', '35.2%', '1.5 tCO2e/year')\n"
        "- Return ONLY the JSON array — no markdown, no explanation, no code fences\n"
    )

    chunk_size = 30000
    text = parsed_text.strip()
    if len(text) > chunk_size:
        half = chunk_size // 2
        text_to_process = text[:half] + "\n\n[... middle section omitted ...]\n\n" + text[-half:]
    else:
        text_to_process = text

    user_prompt = (
        f"Extract structured data from this {doc_label} (file: {file_name}).\n\n"
        f"Map each extracted value to one of these fields:\n{fields_list}\n\n"
        "Return a JSON array of objects. Example:\n"
        '[{"category": "technology", "field_key": "description", "value": "Improved biomass cookstove", "confidence": "high"}]\n\n'
        f'Document text:\n"""\n{text_to_process}\n"""'
    )

    import time as _time
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            result = _call_openai(system_prompt, user_prompt, max_tokens=4000)
            if not result:
                return None

            cleaned = result.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines)

            data = json.loads(cleaned)
            if not isinstance(data, list):
                logger.warning("Structured extraction for %s returned non-list: %s", file_name, type(data))
                return None

            validated = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                cat = item.get("category", "")
                fkey = item.get("field_key", "")
                val = item.get("value", "")
                conf = item.get("confidence", "medium")
                if not cat or not fkey or not val:
                    continue
                if cat not in INTAKE_FIELD_SCHEMA:
                    continue
                if fkey not in INTAKE_FIELD_SCHEMA[cat]:
                    continue
                if conf not in ("high", "medium", "low"):
                    conf = "medium"
                validated.append({
                    "category": cat,
                    "field_key": fkey,
                    "value": str(val).strip(),
                    "confidence": conf,
                    "source": file_name,
                })

            logger.info("Structured extraction for %s: %d data points", file_name, len(validated))
            return validated

        except json.JSONDecodeError as e:
            logger.warning("JSON parse failed for structured extraction of %s: %s", file_name, e)
            if attempt < max_retries:
                _time.sleep(2)
                continue
            return None
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "rate" in err_str.lower()
            if is_rate_limit and attempt < max_retries:
                wait = (attempt + 1) * 5
                logger.info("Rate limited on structured extraction for %s, retrying in %ds", file_name, wait)
                _time.sleep(wait)
                continue
            logger.warning("Structured intelligence extraction failed for %s: %s", file_name, e)
            return None


def generate_project_brief(project_info, doc_chunks=None):
    intake = project_info.get("project_intake") or {}
    intake_context = _format_project_context(project_info)

    chunks_text = ""
    if doc_chunks:
        chunk_parts = []
        for c in doc_chunks[:5]:
            chunk_parts.append(c.get("content", ""))
        chunks_text = "\n---\n".join(chunk_parts)

    system_prompt = (
        "You are an expert carbon project analyst. Generate a concise Project Brief (max 500 words) "
        "that summarizes the key facts of this carbon project. This brief will be used as shared context "
        "across all sections of the project document to ensure consistency.\n\n"
        "RULES:\n"
        "- Include ONLY facts that are stated in the provided data. Do NOT invent details.\n"
        "- Cover: project name, developer, country/region, technology, methodology, baseline scenario, "
        "scale, crediting period, estimated emission reductions, and key monitoring parameters.\n"
        "- Use specific numbers, dates, and names — not generic descriptions.\n"
        "- If a fact is not available, do not mention it.\n"
        "- Write in third person, present tense, factual style."
    )

    user_prompt = "Generate the Project Brief from this data:\n\n"
    user_prompt += f"Project: {project_info.get('name', 'Unknown')}\n"
    user_prompt += f"Standard: {project_info.get('standard', 'Unknown')}\n"
    user_prompt += f"Methodology: {project_info.get('methodology', 'Unknown')}\n"
    user_prompt += f"Country: {project_info.get('country', 'Unknown')}\n\n"

    if intake_context:
        user_prompt += f"### Intake Data:\n{intake_context}\n\n"

    if chunks_text:
        user_prompt += f"### Key Document Extracts:\n{chunks_text[:8000]}\n\n"

    user_prompt += "Write the Project Brief (max 500 words):"

    return _call_openai(system_prompt, user_prompt, max_tokens=1500)


def validate_document_consistency(sections_dict, project_info):
    if not sections_dict or len(sections_dict) < 2:
        return {"facts_extracted": [], "contradictions": [], "missing_required": [], "suggestions": []}

    sections_text = ""
    for sid, sdata in sections_dict.items():
        title = sdata.get("section_title", sid)
        text = sdata.get("generated_text", "") or sdata.get("user_text", "")
        if text:
            sections_text += f"\n## Section {sid}: {title}\n{text[:3000]}\n"

    if not sections_text.strip():
        return {"facts_extracted": [], "contradictions": [], "missing_required": [], "suggestions": []}

    system_prompt = (
        "You are a senior carbon project compliance auditor. Analyze all sections of this document "
        "and check for internal consistency.\n\n"
        "Extract key facts stated across sections and flag any contradictions.\n"
        "Return a JSON object with these keys:\n"
        "- facts_extracted: list of {fact, sections_referenced, value} for key facts\n"
        "- contradictions: list of {description, section_a, section_b, value_a, value_b, severity} "
        "where severity is 'high', 'medium', or 'low'\n"
        "- missing_required: list of {field, description} for important fields that appear nowhere\n"
        "- suggestions: list of strings with improvement recommendations\n\n"
        "Key facts to check: crediting period dates/length, methodology name/version, "
        "country/region, emission reduction estimates, baseline scenario description, "
        "technology type, monitoring parameters, project scale, emission factors."
    )

    user_prompt = f"Project: {project_info.get('name', 'Unknown')}\n"
    user_prompt += f"Methodology: {project_info.get('methodology', 'Unknown')}\n\n"
    user_prompt += f"Document sections:\n{sections_text[:25000]}\n\n"
    user_prompt += "Analyze for consistency and return JSON:"

    result = _call_openai(
        system_prompt, user_prompt,
        response_format={"type": "json_object"},
        max_tokens=4000,
        model_override=UPGRADE_MODEL,
    )

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        logger.warning("Consistency validation returned non-JSON")
        return {"facts_extracted": [], "contradictions": [], "missing_required": [], "suggestions": [result]}


def validate_section_output(section_text, guide_section):
    if not section_text or not guide_section:
        return {"covered": [], "missing": [], "has_placeholders": False, "word_count": 0, "quality_score": 0.0}

    must_include = guide_section.get("must_include", [])
    word_count = len(section_text.split())
    has_placeholders = "[INSERT" in section_text or "[PLACEHOLDER" in section_text or "[TBD" in section_text

    text_lower = section_text.lower()
    covered = []
    missing = []
    for item in must_include:
        key_words = [w.lower() for w in item.split() if len(w) > 3][:5]
        matches = sum(1 for w in key_words if w in text_lower)
        if key_words and matches / len(key_words) >= 0.4:
            covered.append(item)
        else:
            missing.append(item)

    total = len(must_include) if must_include else 1
    coverage_ratio = len(covered) / total
    length_score = min(1.0, word_count / 300)
    placeholder_penalty = 0.1 if has_placeholders else 0.0
    quality_score = round((coverage_ratio * 0.7 + length_score * 0.3) - placeholder_penalty, 2)

    return {
        "covered": covered,
        "missing": missing,
        "has_placeholders": has_placeholders,
        "word_count": word_count,
        "quality_score": max(0.0, quality_score),
    }
