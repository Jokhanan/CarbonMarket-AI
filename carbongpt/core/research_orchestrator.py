import json
import logging

from carbongpt.core.openai_client import DEFAULT_MODEL as MODEL, UPGRADE_MODEL
from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

LAYER_GENERAL_CONTEXT = "general_context"
LAYER_METHODOLOGY_RULES = "methodology_rules"
LAYER_TECHNICAL_PARAMETERS = "technical_parameters"
LAYER_PROJECT_DOCUMENTS = "project_documents"
LAYER_KNOWLEDGE_BASE = "knowledge_base"
LAYER_REGULATORY_WEB = "regulatory_web"
LAYER_DEPENDENCIES = "dependencies"
LAYER_COMPLIANCE = "compliance"

FIELD_LAYER_MAP = {
    "country": LAYER_GENERAL_CONTEXT,
    "region": LAYER_GENERAL_CONTEXT,
    "district": LAYER_GENERAL_CONTEXT,
    "gps_coordinates": LAYER_GENERAL_CONTEXT,
    "climate_zone": LAYER_GENERAL_CONTEXT,
    "geography": LAYER_GENERAL_CONTEXT,
    "altitude": LAYER_GENERAL_CONTEXT,
    "population": LAYER_GENERAL_CONTEXT,
    "administrative_context": LAYER_GENERAL_CONTEXT,
    "target_population": LAYER_GENERAL_CONTEXT,
    "number_of_beneficiaries": LAYER_GENERAL_CONTEXT,

    "baseline_scenario": LAYER_METHODOLOGY_RULES,
    "additionality_justification": LAYER_METHODOLOGY_RULES,
    "monitoring_approach": LAYER_METHODOLOGY_RULES,
    "calculation_method": LAYER_METHODOLOGY_RULES,
    "project_boundary": LAYER_METHODOLOGY_RULES,
    "leakage_approach": LAYER_METHODOLOGY_RULES,
    "safeguards": LAYER_METHODOLOGY_RULES,
    "sectoral_scope": LAYER_METHODOLOGY_RULES,
    "activity_type": LAYER_METHODOLOGY_RULES,

    "fnrb": LAYER_TECHNICAL_PARAMETERS,
    "fNRB": LAYER_TECHNICAL_PARAMETERS,
    "ncv": LAYER_TECHNICAL_PARAMETERS,
    "NCV": LAYER_TECHNICAL_PARAMETERS,
    "emission_factor": LAYER_TECHNICAL_PARAMETERS,
    "baseline_efficiency": LAYER_TECHNICAL_PARAMETERS,
    "project_efficiency": LAYER_TECHNICAL_PARAMETERS,
    "baseline_fuel_consumption": LAYER_TECHNICAL_PARAMETERS,
    "grid_emission_factor": LAYER_TECHNICAL_PARAMETERS,
    "annual_er_estimate": LAYER_TECHNICAL_PARAMETERS,
    "total_er_estimate": LAYER_TECHNICAL_PARAMETERS,
    "baseline_fuel": LAYER_TECHNICAL_PARAMETERS,
    "project_fuel": LAYER_TECHNICAL_PARAMETERS,
}

INTAKE_CARDS = [
    "proponent", "project_overview", "technology", "location",
    "baseline_additionality", "emission_reductions", "monitoring",
    "sdgs", "stakeholders", "safeguards", "crediting_dates",
    "prior_consideration", "legal_compliance",
]

GENERAL_CONTEXT_FIELDS = [
    "country", "region", "district", "gps_coordinates",
    "climate_zone", "geography", "target_population",
    "number_of_beneficiaries",
]

TECHNICAL_PARAM_FIELDS = [
    "fnrb", "fNRB", "ncv", "NCV", "emission_factor",
    "baseline_efficiency", "project_efficiency",
    "baseline_fuel_consumption", "grid_emission_factor",
    "annual_er_estimate", "total_er_estimate",
    "baseline_fuel", "project_fuel",
]


def _call_openai(messages, model=None, temperature=0.3):
    from carbongpt.core.openai_client import call_openai
    system_prompt = "\n".join(m["content"] for m in messages if m.get("role") == "system")
    user_prompt = "\n".join(m["content"] for m in messages if m.get("role") != "system")
    try:
        result = call_openai(
            system_prompt, user_prompt, max_tokens=2000, temperature=temperature,
            model_override=model or MODEL,
        )
        return result.strip()
    except Exception as e:
        logger.error("OpenAI call failed in research orchestrator: %s", e)
        return ""


def analyze_gaps(project_id, doc_type="pdd"):
    from carbongpt.repository.store import get_user_project
    project = get_user_project(project_id)
    if not project:
        return {"gaps": [], "summary": "Project not found"}

    intake = project.get("project_intake") or {}
    methodology = project.get("methodology") or ""
    standard = project.get("standard") or ""

    gaps = []

    core_fields = {
        "project_name": project.get("project_name"),
        "country": project.get("country"),
        "methodology": methodology,
        "standard": standard,
    }
    for field, val in core_fields.items():
        if not val or val == "[Not specified]":
            layer = FIELD_LAYER_MAP.get(field, LAYER_GENERAL_CONTEXT)
            gaps.append({
                "field": field,
                "card": "core",
                "layer": layer,
                "description": f"Missing {field.replace('_', ' ')}",
                "current_value": val or "",
            })

    for card in INTAKE_CARDS:
        card_data = intake.get(card)
        if card_data is None:
            gaps.append({
                "field": card,
                "card": card,
                "layer": _classify_card_layer(card),
                "description": f"Entire '{card.replace('_', ' ')}' section is empty",
                "current_value": "",
            })
            continue
        if isinstance(card_data, dict):
            for key, val in card_data.items():
                if key.startswith("_"):
                    continue
                if _is_empty(val):
                    layer = FIELD_LAYER_MAP.get(key, _classify_card_layer(card))
                    gaps.append({
                        "field": f"{card}.{key}",
                        "card": card,
                        "layer": layer,
                        "description": f"Missing {key.replace('_', ' ')} in {card.replace('_', ' ')}",
                        "current_value": "",
                    })

    meth_params = intake.get("methodology_parameters") or {}
    if isinstance(meth_params, dict):
        for key, val in meth_params.items():
            if key.startswith("_"):
                continue
            if _is_empty(val):
                layer = LAYER_TECHNICAL_PARAMETERS if key.lower() in [f.lower() for f in TECHNICAL_PARAM_FIELDS] else LAYER_METHODOLOGY_RULES
                gaps.append({
                    "field": f"methodology_parameters.{key}",
                    "card": "methodology_parameters",
                    "layer": layer,
                    "description": f"Missing methodology parameter: {key}",
                    "current_value": "",
                })

    summary = f"Found {len(gaps)} gap(s) across {len(set(g['layer'] for g in gaps))} research layer(s)"
    return {"gaps": gaps, "summary": summary, "project_id": project_id}


def research_gap(project_id, gap, project_info=None):
    if project_info is None:
        from carbongpt.repository.store import get_user_project
        project = get_user_project(project_id)
        if not project:
            return {"error": "Project not found"}
        project_info = _build_project_info(project)

    layer = gap.get("layer", LAYER_GENERAL_CONTEXT)
    field = gap.get("field", "")
    methodology = project_info.get("methodology", "")

    result = None
    if layer == LAYER_GENERAL_CONTEXT:
        result = _research_general_context(project_id, field, project_info)
    elif layer == LAYER_METHODOLOGY_RULES:
        result = _research_methodology_rules(project_id, field, methodology, project_info)
    elif layer == LAYER_TECHNICAL_PARAMETERS:
        result = _research_technical_parameter(project_id, field, methodology, project_info)
    elif layer == LAYER_PROJECT_DOCUMENTS:
        result = _research_project_documents(project_id, field, project_info)
    elif layer == LAYER_KNOWLEDGE_BASE:
        result = _research_knowledge_base(project_id, field, methodology, project_info)
    elif layer == LAYER_REGULATORY_WEB:
        result = _research_regulatory_web(field, methodology, project_info)
    elif layer == LAYER_DEPENDENCIES:
        result = _research_dependencies(project_id, field, methodology)
    elif layer == LAYER_COMPLIANCE:
        result = _research_compliance(project_id, field, methodology, project_info)
    else:
        result = _research_general_context(project_id, field, project_info)

    if result is None:
        result = {"value": None, "sources": [], "confidence": 0.0, "layer": layer, "admissible": False}

    result["field"] = field
    result["layer"] = layer
    _save_research_result(project_id, result)
    return result


def run_research_session(project_id, doc_type="pdd", max_gaps=20):
    import time as _time

    gap_analysis = analyze_gaps(project_id, doc_type)
    gaps = gap_analysis.get("gaps", [])

    if not gaps:
        return {"results": [], "summary": "No gaps found — all fields are populated"}

    from carbongpt.repository.store import get_user_project
    project = get_user_project(project_id)
    project_info = _build_project_info(project) if project else {}

    session_start = _time.time()
    session_timeout = 90
    max_per_session = min(max_gaps, 15)

    results = []
    researched_count = 0
    for gap in gaps[:max_per_session]:
        if _time.time() - session_start > session_timeout:
            logger.info("Research session timed out after %d gaps", researched_count)
            break
        try:
            researched_count += 1
            result = research_gap(project_id, gap, project_info)
            if result and result.get("value"):
                results.append(result)
        except Exception as e:
            logger.warning("Research failed for gap %s: %s", gap.get("field"), e)

    summary = f"Researched {researched_count} of {len(gaps)} gaps, found {len(results)} suggestion(s)"
    return {"results": results, "summary": summary, "total_gaps": len(gaps)}


CORE_PROJECT_FIELDS = {"project_name", "country", "methodology", "standard", "description"}


def confirm_research_result(result_id, project_id):
    from carbongpt.repository.store import get_user_project, update_user_project

    with get_cursor() as cur:
        cur.execute(
            "UPDATE research_results SET status = 'confirmed' WHERE id = %s AND project_id = %s RETURNING result_data, field_path",
            (result_id, project_id),
        )
        row = cur.fetchone()

    if not row:
        return {"error": "Research result not found"}

    result_data = row.get("result_data") or {}
    if isinstance(result_data, str):
        try:
            result_data = json.loads(result_data)
        except (json.JSONDecodeError, TypeError):
            result_data = {}

    field_path = row.get("field_path") or ""
    value = result_data.get("value") if isinstance(result_data, dict) else None

    if not value or not field_path:
        return {"confirmed": True, "field": field_path, "value": value, "note": "No value to apply"}

    project = get_user_project(project_id)
    if not project:
        return {"error": "Project not found"}

    base_field = field_path.split(".")[0]
    if base_field in CORE_PROJECT_FIELDS:
        update_kwargs = {base_field: value}
        update_user_project(project_id, **update_kwargs)
    else:
        intake = project.get("project_intake") or {}
        _set_nested_value(intake, field_path, value)
        update_user_project(project_id, project_intake=intake)

    return {"confirmed": True, "field": field_path, "value": value}


def reject_research_result(result_id, project_id):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE research_results SET status = 'rejected' WHERE id = %s AND project_id = %s",
            (result_id, project_id),
        )
    return {"rejected": True}


def get_research_results(project_id, status=None):
    with get_cursor() as cur:
        if status:
            cur.execute(
                "SELECT * FROM research_results WHERE project_id = %s AND status = %s ORDER BY created_at DESC",
                (project_id, status),
            )
        else:
            cur.execute(
                "SELECT * FROM research_results WHERE project_id = %s ORDER BY created_at DESC",
                (project_id,),
            )
        rows = cur.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "layer": r["research_layer"],
            "field": r["field_path"],
            "query": r["query"],
            "result_data": r["result_data"],
            "sources": r["sources"],
            "confidence": r["confidence"],
            "status": r["status"],
            "created_at": str(r["created_at"]) if r.get("created_at") else None,
        })
    return results


def _research_general_context(project_id, field_name, project_info):
    country = project_info.get("country", "")
    region = project_info.get("region", "")
    project_name = project_info.get("project_name", "")

    doc_result = _search_project_docs_for_field(project_id, field_name)
    if doc_result:
        return doc_result

    clean_field = field_name.split(".")[-1].replace("_", " ")
    location_ctx = f"{region}, {country}" if region else country

    if not location_ctx:
        return _make_result(None, [], 0.0, LAYER_GENERAL_CONTEXT, False,
                            note="Cannot research without country information")

    search_query = f"{location_ctx} {clean_field} carbon project"
    web_results = _do_web_search(search_query)

    context_parts = []
    sources = []
    if web_results:
        for wr in web_results[:3]:
            context_parts.append(f"- {wr.get('title', '')}: {wr.get('snippet', '')}")
            if wr.get("url"):
                sources.append({"type": "web", "reference": wr["title"], "url": wr["url"]})

    if not context_parts:
        context_parts.append(f"Use general knowledge about {location_ctx}")
        sources.append({"type": "llm_knowledge", "reference": "AI general knowledge"})

    prompt = f"""You are a carbon project research assistant. Find the following information:

Field needed: {clean_field}
Location context: {location_ctx}
Project: {project_name}

Web search results:
{chr(10).join(context_parts)}

Provide a factual, concise answer for the "{clean_field}" field.
If the information is about coordinates, provide in decimal degrees format.
If about climate, describe the climate zone classification.
If about population or beneficiaries, provide a reasonable estimate with source.

Return ONLY a JSON object:
{{"value": "<the answer>", "confidence": <0.0-1.0>, "source_note": "<where this info comes from>"}}"""

    raw = _call_openai([{"role": "user", "content": prompt}])
    parsed = _parse_json_response(raw)
    if parsed and parsed.get("value"):
        if parsed.get("source_note"):
            sources.append({"type": "ai_synthesis", "reference": parsed["source_note"]})
        return _make_result(parsed["value"], sources, parsed.get("confidence", 0.5), LAYER_GENERAL_CONTEXT, True)

    return _make_result(None, [], 0.0, LAYER_GENERAL_CONTEXT, False)


def _research_methodology_rules(project_id, field_name, methodology_code, project_info):
    if not methodology_code:
        return _make_result(None, [], 0.0, LAYER_METHODOLOGY_RULES, False,
                            note="No methodology assigned to project")

    doc_result = _search_project_docs_for_field(project_id, field_name)

    kb_chunks = _search_methodology_knowledge(methodology_code, field_name)

    standard_chunks = _search_knowledge_base(field_name, project_info.get("standard", ""))

    context_parts = []
    sources = []

    if doc_result and doc_result.get("value"):
        context_parts.append(f"From project documents: {doc_result['value']}")
        sources.extend(doc_result.get("sources", []))

    if kb_chunks:
        for chunk in kb_chunks[:3]:
            context_parts.append(f"From methodology knowledge ({chunk.get('chunk_type', '')}): {chunk.get('content', '')[:500]}")
            sources.append({"type": "methodology_kb", "reference": f"{methodology_code} - {chunk.get('title', chunk.get('chunk_key', ''))}"})

    if standard_chunks:
        for chunk in standard_chunks[:2]:
            context_parts.append(f"From standard requirements: {chunk.get('content', '')[:500]}")
            sources.append({"type": "knowledge_base", "reference": chunk.get("metadata", {}).get("document_name", "Standard document")})

    if not context_parts:
        return _make_result(None, [], 0.0, LAYER_METHODOLOGY_RULES, False,
                            note=f"No methodology rules found for {field_name}")

    clean_field = field_name.split(".")[-1].replace("_", " ")
    prompt = f"""You are a carbon methodology expert. Based on the following methodology knowledge, determine the correct answer for:

Field: {clean_field}
Methodology: {methodology_code}
Standard: {project_info.get('standard', '')}

Context:
{chr(10).join(context_parts)}

Rules:
- Only state what the methodology explicitly allows or requires
- If multiple options are allowed, list them all
- If the methodology does not address this field, say so clearly
- Do not invent rules that are not in the source material

Return ONLY a JSON object:
{{"value": "<answer or list of allowed options>", "confidence": <0.0-1.0>, "options": ["<option1>", "<option2>"], "rule_reference": "<section or clause reference>"}}"""

    raw = _call_openai([{"role": "user", "content": prompt}], model=UPGRADE_MODEL)
    parsed = _parse_json_response(raw)
    if parsed and parsed.get("value"):
        if parsed.get("rule_reference"):
            sources.append({"type": "methodology_rule", "reference": parsed["rule_reference"]})
        return _make_result(parsed["value"], sources, parsed.get("confidence", 0.6),
                            LAYER_METHODOLOGY_RULES, True, options=parsed.get("options"))

    return _make_result(None, sources, 0.0, LAYER_METHODOLOGY_RULES, False)


def _research_technical_parameter(project_id, param_name, methodology_code, project_info):
    doc_result = _search_project_docs_for_field(project_id, param_name)

    kb_chunks = []
    if methodology_code:
        kb_chunks = _search_methodology_knowledge(methodology_code, param_name, chunk_types=["parameters", "default_values", "equations"])

    source_priorities = _get_source_priorities(methodology_code, param_name)

    context_parts = []
    sources = []
    options = []

    if doc_result and doc_result.get("value"):
        context_parts.append(f"From project documents (highest priority): {doc_result['value']}")
        sources.extend(doc_result.get("sources", []))
        options.append({"value": doc_result["value"], "source": "Project measurement/document", "rank": 1})

    try:
        from carbongpt.core.tool_defaults import get_defaults_for_methodology
        country = project_info.get("country", "")
        settings = project_info.get("project_settings") or {}
        tool33_result = get_defaults_for_methodology(
            methodology_code or "",
            country=country,
            baseline_fuel=settings.get("baseline_fuel"),
            project_fuel=settings.get("project_fuel"),
        )
        tool33_params = tool33_result.get("parameters", {})
        param_lower = param_name.lower().replace("_", "").replace(" ", "")
        for pkey, pval in tool33_params.items():
            if not isinstance(pval, dict):
                continue
            pkey_norm = pkey.lower().replace("_", "").replace(" ", "")
            if pkey_norm == param_lower or param_lower in pkey_norm or pkey_norm in param_lower:
                val_str = str(pval.get("value", ""))
                src = pval.get("source", "CDM TOOL33 / IPCC")
                context_parts.append(f"From CDM TOOL33/IPCC defaults (high priority): {pkey} = {val_str} {pval.get('unit', '')} ({src})")
                sources.append({"type": "tool33_default", "reference": src})
                options.append({"value": val_str, "source": f"CDM TOOL33/IPCC default ({src})", "rank": 2})
    except Exception as e:
        logger.warning("TOOL33 lookup in research orchestrator failed: %s", e)

    if kb_chunks:
        for chunk in kb_chunks[:4]:
            content = chunk.get("content", "")[:600]
            structured = chunk.get("structured_data", {})
            context_parts.append(f"From methodology ({chunk.get('chunk_type', '')}): {content}")
            sources.append({"type": "methodology_kb", "reference": f"{methodology_code} - {chunk.get('title', chunk.get('chunk_key', ''))}"})
            if structured and isinstance(structured, dict):
                defaults = structured.get("defaults_by_context") or structured.get("default_value")
                if defaults:
                    if isinstance(defaults, list):
                        for d in defaults[:5]:
                            options.append({"value": str(d), "source": f"Methodology default ({methodology_code})", "rank": 3})
                    else:
                        options.append({"value": str(defaults), "source": f"Methodology default ({methodology_code})", "rank": 3})

    country = project_info.get("country", "")
    if country and param_name.lower() in ["fnrb", "ncv", "emission_factor", "grid_emission_factor", "baseline_efficiency"]:
        web_results = _do_web_search(f"{country} {param_name.replace('_', ' ')} IPCC default value carbon")
        if web_results:
            for wr in web_results[:2]:
                context_parts.append(f"Web: {wr.get('title', '')}: {wr.get('snippet', '')}")
                sources.append({"type": "web", "reference": wr.get("title", ""), "url": wr.get("url", "")})

    if not context_parts:
        return _make_result(None, [], 0.0, LAYER_TECHNICAL_PARAMETERS, False,
                            note=f"No data found for parameter {param_name}")

    clean_param = param_name.split(".")[-1].replace("_", " ")
    prompt = f"""You are a carbon project technical parameter expert. Research the following parameter:

Parameter: {clean_param}
Methodology: {methodology_code or 'Not specified'}
Country: {country or 'Not specified'}

Available data:
{chr(10).join(context_parts)}

STRICT RULES:
- NEVER invent or fabricate parameter values
- Only report values that appear in the source material
- If multiple valid options exist, list ALL of them with their sources
- Indicate the source hierarchy: project measurement > national inventory > IPCC default > methodology default
- If no reliable value is found, say so explicitly

Return ONLY a JSON object:
{{"value": "<best available value with unit>", "confidence": <0.0-1.0>, "options": [{{"value": "<val>", "source": "<source>", "rank": <1-5>}}], "unit": "<unit>", "source_note": "<primary source>"}}"""

    raw = _call_openai([{"role": "user", "content": prompt}], model=UPGRADE_MODEL)
    parsed = _parse_json_response(raw)
    if parsed and parsed.get("value"):
        if parsed.get("options"):
            options.extend(parsed["options"])
        if parsed.get("source_note"):
            sources.append({"type": "ai_synthesis", "reference": parsed["source_note"]})
        return _make_result(parsed["value"], sources, parsed.get("confidence", 0.4),
                            LAYER_TECHNICAL_PARAMETERS, True, options=options, unit=parsed.get("unit"))

    return _make_result(None, sources, 0.0, LAYER_TECHNICAL_PARAMETERS, False, options=options if options else None)


def _research_project_documents(project_id, field_name, project_info):
    return _search_project_docs_for_field(project_id, field_name)


def _research_knowledge_base(project_id, field_name, methodology_code, project_info):
    standard = project_info.get("standard", "")
    chunks = _search_knowledge_base(field_name, standard)
    if not chunks:
        return _make_result(None, [], 0.0, LAYER_KNOWLEDGE_BASE, False)

    sources = []
    context = []
    for chunk in chunks[:3]:
        context.append(chunk.get("content", "")[:500])
        sources.append({"type": "knowledge_base", "reference": chunk.get("metadata", {}).get("document_name", "Standard document")})

    clean_field = field_name.split(".")[-1].replace("_", " ")
    prompt = f"""Based on the following carbon standard knowledge, what is the requirement or guidance for "{clean_field}"?

Context:
{chr(10).join(context)}

Return ONLY a JSON object:
{{"value": "<concise answer>", "confidence": <0.0-1.0>}}"""

    raw = _call_openai([{"role": "user", "content": prompt}])
    parsed = _parse_json_response(raw)
    if parsed and parsed.get("value"):
        return _make_result(parsed["value"], sources, parsed.get("confidence", 0.5), LAYER_KNOWLEDGE_BASE, True)

    return _make_result(None, [], 0.0, LAYER_KNOWLEDGE_BASE, False)


def _research_regulatory_web(field_name, methodology_code, project_info):
    clean_field = field_name.split(".")[-1].replace("_", " ")
    standard = project_info.get("standard", "")

    query = f"{standard} {methodology_code} {clean_field} latest requirements 2025 2026"
    web_results = _do_web_search(query)

    if not web_results:
        return _make_result(None, [], 0.0, LAYER_REGULATORY_WEB, False)

    sources = [{"type": "web", "reference": wr.get("title", ""), "url": wr.get("url", "")} for wr in web_results[:3]]
    context = [f"- {wr.get('title', '')}: {wr.get('snippet', '')}" for wr in web_results[:3]]

    prompt = f"""Based on recent web search results, what is the latest regulatory information about "{clean_field}" for {standard} {methodology_code}?

Search results:
{chr(10).join(context)}

Return ONLY a JSON object:
{{"value": "<finding>", "confidence": <0.0-1.0>, "is_current": true/false}}"""

    raw = _call_openai([{"role": "user", "content": prompt}])
    parsed = _parse_json_response(raw)
    if parsed and parsed.get("value"):
        return _make_result(parsed["value"], sources, parsed.get("confidence", 0.4), LAYER_REGULATORY_WEB, True)

    return _make_result(None, [], 0.0, LAYER_REGULATORY_WEB, False)


def _research_dependencies(project_id, param_name, methodology_code):
    if not methodology_code:
        return _make_result(None, [], 0.0, LAYER_DEPENDENCIES, False)

    kb_chunks = _search_methodology_knowledge(methodology_code, param_name, chunk_types=["equations", "parameters", "quantification"])

    if not kb_chunks:
        return _make_result(None, [], 0.0, LAYER_DEPENDENCIES, False,
                            note=f"No equation dependencies found for {param_name}")

    sources = []
    context = []
    for chunk in kb_chunks[:5]:
        context.append(f"{chunk.get('chunk_type', '')}: {chunk.get('content', '')[:500]}")
        sources.append({"type": "methodology_kb", "reference": f"{methodology_code} - {chunk.get('title', chunk.get('chunk_key', ''))}"})

    clean_param = param_name.split(".")[-1].replace("_", " ")
    prompt = f"""Analyze the dependency chain for the parameter "{clean_param}" in methodology {methodology_code}.

Methodology knowledge:
{chr(10).join(context)}

Identify:
1. Which equations use this parameter
2. Which other parameters this depends on
3. Which CDM tools or external references are needed to determine this parameter
4. The calculation chain from inputs to this parameter

Return ONLY a JSON object:
{{"value": "<dependency summary>", "confidence": <0.0-1.0>, "equations": ["<eq1>"], "depends_on": ["<param1>", "<param2>"], "tools_needed": ["<tool1>"]}}"""

    raw = _call_openai([{"role": "user", "content": prompt}], model=UPGRADE_MODEL)
    parsed = _parse_json_response(raw)
    if parsed and parsed.get("value"):
        return _make_result(parsed["value"], sources, parsed.get("confidence", 0.6),
                            LAYER_DEPENDENCIES, True,
                            equations=parsed.get("equations"),
                            depends_on=parsed.get("depends_on"),
                            tools_needed=parsed.get("tools_needed"))

    return _make_result(None, [], 0.0, LAYER_DEPENDENCIES, False)


def _research_compliance(project_id, field_name, methodology_code, project_info):
    if not methodology_code:
        return _make_result(None, [], 0.0, LAYER_COMPLIANCE, False)

    kb_chunks = _search_methodology_knowledge(methodology_code, field_name,
                                               chunk_types=["applicability", "monitoring", "safeguards", "parameters"])

    standard_chunks = _search_knowledge_base(field_name, project_info.get("standard", ""))

    sources = []
    context = []
    if kb_chunks:
        for chunk in kb_chunks[:3]:
            context.append(f"Methodology rule ({chunk.get('chunk_type', '')}): {chunk.get('content', '')[:500]}")
            sources.append({"type": "methodology_kb", "reference": f"{methodology_code} - {chunk.get('title', chunk.get('chunk_key', ''))}"})

    if standard_chunks:
        for chunk in standard_chunks[:2]:
            context.append(f"Standard requirement: {chunk.get('content', '')[:500]}")
            sources.append({"type": "knowledge_base", "reference": chunk.get("metadata", {}).get("document_name", "Standard")})

    if not context:
        return _make_result(None, [], 0.0, LAYER_COMPLIANCE, False)

    clean_field = field_name.split(".")[-1].replace("_", " ")
    prompt = f"""As a carbon compliance expert, assess the compliance requirements for "{clean_field}" under methodology {methodology_code}.

Compliance context:
{chr(10).join(context)}

Determine:
1. What sources are acceptable for this parameter/field
2. Are there vintage or geographic restrictions
3. What documentation is required as evidence
4. Is this parameter subject to validation/verification checks

Return ONLY a JSON object:
{{"value": "<compliance assessment>", "confidence": <0.0-1.0>, "acceptable_sources": ["<source1>"], "restrictions": ["<restriction1>"], "evidence_required": "<what evidence>", "is_admissible": true/false}}"""

    raw = _call_openai([{"role": "user", "content": prompt}], model=UPGRADE_MODEL)
    parsed = _parse_json_response(raw)
    if parsed and parsed.get("value"):
        return _make_result(parsed["value"], sources, parsed.get("confidence", 0.6),
                            LAYER_COMPLIANCE, parsed.get("is_admissible", True),
                            acceptable_sources=parsed.get("acceptable_sources"),
                            restrictions=parsed.get("restrictions"),
                            evidence_required=parsed.get("evidence_required"))

    return _make_result(None, [], 0.0, LAYER_COMPLIANCE, False)


def _search_project_docs_for_field(project_id, field_name):
    try:
        from carbongpt.core.project_doc_index import search_project_chunks
        clean_field = field_name.split(".")[-1].replace("_", " ")
        chunks = search_project_chunks(project_id, clean_field, limit=5)
        if not chunks:
            return None

        sources = [{"type": "project_document", "reference": c.get("section_title", f"Document chunk {c.get('chunk_index', '')}")} for c in chunks[:3]]
        context = "\n".join(c.get("content", "")[:400] for c in chunks[:3])

        prompt = f"""Extract the value for "{clean_field}" from the following project document excerpts:

{context}

If the information is found, return ONLY a JSON object:
{{"value": "<extracted value>", "confidence": <0.0-1.0>, "found": true}}

If not found, return:
{{"value": null, "confidence": 0, "found": false}}"""

        raw = _call_openai([{"role": "user", "content": prompt}])
        parsed = _parse_json_response(raw)
        if parsed and parsed.get("found") and parsed.get("value"):
            return _make_result(parsed["value"], sources, parsed.get("confidence", 0.7), LAYER_PROJECT_DOCUMENTS, True)
    except Exception as e:
        logger.warning("Project doc search failed for %s: %s", field_name, e)

    return None


def _search_methodology_knowledge(methodology_code, field_name, chunk_types=None):
    try:
        clean_field = field_name.split(".")[-1].replace("_", " ")
        with get_cursor() as cur:
            if chunk_types:
                placeholders = ",".join(["%s"] * len(chunk_types))
                cur.execute(
                    f"""SELECT chunk_type, chunk_key, title, content, structured_data, confidence
                       FROM methodology_knowledge
                       WHERE methodology_code = %s AND chunk_type IN ({placeholders})
                       ORDER BY confidence DESC
                       LIMIT 10""",
                    (methodology_code, *chunk_types),
                )
            else:
                cur.execute(
                    """SELECT chunk_type, chunk_key, title, content, structured_data, confidence
                       FROM methodology_knowledge
                       WHERE methodology_code = %s
                       ORDER BY confidence DESC
                       LIMIT 10""",
                    (methodology_code,),
                )
            rows = cur.fetchall()

        if not rows:
            return []

        scored = []
        for row in rows:
            content_lower = (row.get("content", "") + " " + (row.get("title", "") or "")).lower()
            field_terms = clean_field.lower().split()
            match_score = sum(1 for term in field_terms if term in content_lower) / max(len(field_terms), 1)
            if match_score > 0.2 or not chunk_types:
                scored.append(row)

        return scored[:5] if scored else rows[:3]
    except Exception as e:
        logger.warning("Methodology knowledge search failed: %s", e)
        return []


def _search_knowledge_base(field_name, standard):
    try:
        from carbongpt.core.knowledge_retrieval import retrieve_section_context
        clean_field = field_name.split(".")[-1].replace("_", " ")
        chunks = retrieve_section_context(
            section_title=clean_field,
            section_text=clean_field,
            standard=standard or "GoldStandard",
        )
        return chunks
    except Exception as e:
        logger.warning("Knowledge base search failed: %s", e)
        return []


def _do_web_search(query):
    try:
        from carbongpt.core.web_intelligence import web_search
        return web_search(query, num_results=5)
    except Exception as e:
        logger.warning("Web search failed: %s", e)
        return []


def _get_source_priorities(methodology_code, param_name):
    try:
        with get_cursor() as cur:
            cur.execute(
                """SELECT source_rank, source_type, source_description, is_admissible
                   FROM research_source_priority
                   WHERE (methodology_code = %s OR methodology_code IS NULL)
                     AND (parameter_name = %s OR parameter_name IS NULL)
                   ORDER BY source_rank ASC""",
                (methodology_code, param_name),
            )
            return cur.fetchall()
    except Exception:
        return []


def _save_research_result(project_id, result):
    try:
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO research_results (project_id, research_layer, field_path, query, result_data, sources, confidence, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')""",
                (
                    project_id,
                    result.get("layer", LAYER_GENERAL_CONTEXT),
                    result.get("field", ""),
                    result.get("field", ""),
                    json.dumps(result),
                    json.dumps(result.get("sources", [])),
                    result.get("confidence", 0.0),
                ),
            )
    except Exception as e:
        logger.warning("Failed to save research result: %s", e)


def _build_project_info(project):
    intake = project.get("project_intake") or {}
    location = intake.get("location") or {}
    return {
        "project_name": project.get("project_name", ""),
        "country": project.get("country", ""),
        "region": location.get("region", ""),
        "standard": project.get("standard", ""),
        "methodology": project.get("methodology", ""),
        "doc_type": project.get("doc_type", "pdd"),
    }


def _classify_card_layer(card_name):
    card_layer_map = {
        "proponent": LAYER_GENERAL_CONTEXT,
        "project_overview": LAYER_GENERAL_CONTEXT,
        "technology": LAYER_METHODOLOGY_RULES,
        "location": LAYER_GENERAL_CONTEXT,
        "baseline_additionality": LAYER_METHODOLOGY_RULES,
        "emission_reductions": LAYER_TECHNICAL_PARAMETERS,
        "monitoring": LAYER_METHODOLOGY_RULES,
        "sdgs": LAYER_GENERAL_CONTEXT,
        "stakeholders": LAYER_GENERAL_CONTEXT,
        "safeguards": LAYER_METHODOLOGY_RULES,
        "crediting_dates": LAYER_GENERAL_CONTEXT,
        "prior_consideration": LAYER_METHODOLOGY_RULES,
        "legal_compliance": LAYER_REGULATORY_WEB,
    }
    return card_layer_map.get(card_name, LAYER_GENERAL_CONTEXT)


def _is_empty(val):
    if val is None:
        return True
    if isinstance(val, str) and val.strip() in ("", "[Not specified]", "None", "N/A"):
        return True
    if isinstance(val, (list, dict)) and len(val) == 0:
        return True
    return False


def _set_nested_value(data, path, value):
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _make_result(value, sources, confidence, layer, admissible, note=None, **extra):
    result = {
        "value": value,
        "sources": sources,
        "confidence": confidence,
        "layer": layer,
        "admissible": admissible,
    }
    if note:
        result["note"] = note
    result.update(extra)
    return result


def _parse_json_response(raw_text):
    if not raw_text:
        return None
    try:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{[^{}]*\}', raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None
