import json
import logging
import os

import requests as http_client

logger = logging.getLogger(__name__)

MODEL = os.getenv("CARBONGPT_AI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def _call_openai(system_prompt, user_prompt, response_format=None, max_tokens=6000):
    from carbongpt.core.openai_client import call_openai
    return call_openai(
        system_prompt, user_prompt,
        response_format=response_format,
        max_tokens=max_tokens,
        temperature=0.1,
        model_override=MODEL,
    )


CALC_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "emission_calculation",
        "strict": False,
        "schema": {
            "type": "object",
            "properties": {
                "calculation_method": {"type": "string"},
                "methodology_code": {"type": "string"},
                "crediting_period_years": {"type": "integer"},
                "annual_calculations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "year": {"type": "integer"},
                            "baseline_emissions_tco2e": {"type": "number"},
                            "project_emissions_tco2e": {"type": "number"},
                            "leakage_tco2e": {"type": "number"},
                            "net_emission_reductions_tco2e": {"type": "number"},
                            "calculation_steps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "step": {"type": "string"},
                                        "formula": {"type": "string"},
                                        "values": {"type": "string"},
                                        "result": {"type": "string"},
                                    },
                                },
                            },
                        },
                        "required": ["year", "baseline_emissions_tco2e", "project_emissions_tco2e",
                                     "leakage_tco2e", "net_emission_reductions_tco2e"],
                    },
                },
                "total_emission_reductions_tco2e": {"type": "number"},
                "average_annual_reductions_tco2e": {"type": "number"},
                "parameters_used": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "parameter": {"type": "string"},
                            "value": {"type": "string"},
                            "unit": {"type": "string"},
                            "source": {"type": "string"},
                        },
                    },
                },
                "assumptions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "monitoring_parameters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "parameter": {"type": "string"},
                            "unit": {"type": "string"},
                            "frequency": {"type": "string"},
                            "method": {"type": "string"},
                        },
                    },
                },
                "narrative_explanation": {"type": "string"},
            },
            "required": ["calculation_method", "annual_calculations",
                         "total_emission_reductions_tco2e", "parameters_used"],
        },
    },
}


CALC_SYSTEM_PROMPT = """You are an expert carbon credit calculation engine. You must calculate emission reductions using the EXACT equations and parameters from the methodology.

CRITICAL RULES:
1. APPLY THE METHODOLOGY'S EQUATIONS EXACTLY as specified — do not simplify or substitute different formulas. Use every term in the equation; do not drop multipliers like NCV, fNRB, or unit conversion factors.
2. Use the exact parameter symbols and values provided. Where a user provides a value, use it. Where a methodology default exists, use it.
3. Show ALL calculation steps with actual numbers substituted into the exact equations.
4. Be conservative in all assumptions (as required by carbon standards).
5. If a required parameter value is missing and no default exists, state this clearly and use the most conservative reasonable assumption.
6. Calculate for EACH YEAR of the crediting period.
7. For leakage: use the methodology's specified approach (e.g., 5% default discount factor means ER_net = ER_gross * 0.95).
8. All results must be in tCO2e.
9. UNIT CONVERSION: If the equations compute per-day values, convert to annual by multiplying by 365 (or the actual days in the monitoring period). Show this conversion explicitly.
10. CALCULATED PARAMETERS: Some parameters are computed from other parameters (e.g. SFS = P_b - P_p, SE = P * EF * NCV). Compute these from their input values rather than expecting them as direct inputs.
11. Cross-check: the ratio of baseline to project emissions should be consistent with the efficiency improvement ratio.
12. AGING/DEGRADATION: If the methodology specifies a cumulative usage rate that decreases with technology age, apply this per-year adjustment when computing annual totals.

IMPORTANT: Your calculation steps should be detailed enough that a carbon auditor can verify each number. Show the complete chain from raw inputs to final ER_y."""


def run_calculation(parsed_methodology, user_inputs, method_id=None, crediting_years=7, project_info=None):
    if not parsed_methodology:
        raise ValueError("No parsed methodology provided")

    method = None
    if method_id and parsed_methodology.get("calculation_methods"):
        method = next(
            (m for m in parsed_methodology["calculation_methods"] if m["method_id"] == method_id),
            None
        )
    if not method and parsed_methodology.get("calculation_methods"):
        method = parsed_methodology["calculation_methods"][0]

    user_prompt = f"## Methodology: {parsed_methodology.get('methodology_code', 'Unknown')}\n"
    user_prompt += f"## Methodology Name: {parsed_methodology.get('methodology_name', '')}\n\n"

    if method:
        user_prompt += f"## Selected Calculation Method: {method['method_name']}\n"
        if method.get("description"):
            user_prompt += f"Description: {method['description']}\n"
        if method.get("applicability"):
            user_prompt += f"Applicability: {method['applicability']}\n"
        if method.get("scale_restrictions"):
            user_prompt += f"Scale: {method['scale_restrictions']}\n"
        if method.get("sub_variants"):
            user_prompt += "Sub-variants:\n"
            for sv in method["sub_variants"]:
                user_prompt += f"  - {sv.get('variant_name', '')}: {sv.get('condition', '')}\n"
        user_prompt += "\n### EQUATIONS TO APPLY (use these EXACTLY):\n"
        for eq in method.get("equations", []):
            user_prompt += f"\n{eq.get('equation_id', '')}"
            if eq.get("equation_label"):
                user_prompt += f" — {eq['equation_label']}"
            user_prompt += f":\n  {eq.get('formula_text', '')}\n"
            if eq.get("output_symbol"):
                user_prompt += f"  Computes: {eq['output_symbol']}"
                if eq.get("output_unit"):
                    user_prompt += f" ({eq['output_unit']})"
                user_prompt += "\n"
            if eq.get("is_per_unit"):
                user_prompt += f"  Per-unit basis: {eq['is_per_unit']}\n"
            if eq.get("formula_description"):
                user_prompt += f"  Description: {eq['formula_description']}\n"
            if eq.get("variables"):
                user_prompt += "  Variables:\n"
                for var in eq["variables"]:
                    user_prompt += f"    - {var.get('symbol', '?')}: {var.get('name', '?')} ({var.get('unit', '?')})\n"
        user_prompt += "\n"

    user_prompt += "### ALL PARAMETERS FROM METHODOLOGY:\n"
    for p in parsed_methodology.get("parameters", []):
        sym = p.get('symbol') or p.get('parameter_id') or '?'
        line = f"- {sym} [{p.get('parameter_id', '')}] ({p.get('name', '')}): {p.get('unit', '')}"
        if p.get("default_value"):
            line += f" [Default: {p['default_value']}]"
        if p.get("source"):
            line += f" [Source: {p['source']}]"
        if p.get("category") == "calculated" and p.get("calculation_formula"):
            line += f" [CALCULATED: {p['calculation_formula']}]"
        if p.get("depends_on"):
            line += f" [Depends on: {', '.join(p['depends_on'])}]"
        if p.get("description"):
            line += f" — {p['description']}"
        user_prompt += line + "\n"

    defaults = parsed_methodology.get("default_values", {})
    if defaults:
        user_prompt += "\n### DEFAULT VALUES FROM METHODOLOGY:\n"
        for k, v in defaults.items():
            user_prompt += f"- {k}: {v}\n"

    if parsed_methodology.get("leakage_approach"):
        user_prompt += f"\n### LEAKAGE APPROACH:\n{parsed_methodology['leakage_approach']}\n"

    if parsed_methodology.get("temporal_granularity"):
        user_prompt += f"\n### TEMPORAL GRANULARITY:\n{parsed_methodology['temporal_granularity']}\n"

    if parsed_methodology.get("aging_or_degradation"):
        user_prompt += f"\n### AGING/DEGRADATION:\n{parsed_methodology['aging_or_degradation']}\n"

    user_prompt += f"\n### CREDITING PERIOD: {crediting_years} years\n"

    user_prompt += "\n### PROJECT-SPECIFIC VALUES PROVIDED BY USER:\n"
    if user_inputs:
        for param_symbol, value in user_inputs.items():
            try:
                numeric_val = float(str(value).replace(",", ""))
                user_prompt += f"- {param_symbol} = {numeric_val}\n"
            except (ValueError, TypeError):
                user_prompt += f"- {param_symbol} = {value}\n"
    else:
        user_prompt += "(No user inputs provided — use all methodology defaults where available)\n"

    if project_info:
        user_prompt += "\n### PROJECT CONTEXT:\n"
        if project_info.get("name"):
            user_prompt += f"- Project: {project_info['name']}\n"
        if project_info.get("country"):
            user_prompt += f"- Country: {project_info['country']}\n"
        if project_info.get("description"):
            user_prompt += f"- Description: {project_info['description']}\n"

    user_prompt += (
        "\n\nPerform the COMPLETE emission reduction calculation for each year of the crediting period. "
        "Apply the exact equations listed above. Show all steps with actual numbers. "
        "List every parameter value used and its source (user input, methodology default, or assumption)."
    )

    result = _call_openai(CALC_SYSTEM_PROMPT, user_prompt, response_format=CALC_SCHEMA, max_tokens=6000)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        logger.error("Failed to parse calculation result as JSON")
        return {"error": "Failed to parse calculation", "raw": result}


def format_calculation_narrative(calc_result):
    if not calc_result or calc_result.get("error"):
        return "Calculation failed. Please check inputs and try again."

    lines = []
    lines.append(f"Calculation Method: {calc_result.get('calculation_method', 'N/A')}")
    lines.append(f"Methodology: {calc_result.get('methodology_code', 'N/A')}")
    lines.append("")

    if calc_result.get("narrative_explanation"):
        lines.append(calc_result["narrative_explanation"])
        lines.append("")

    lines.append("Parameters Used:")
    for p in calc_result.get("parameters_used", []):
        source = f" (Source: {p['source']})" if p.get("source") else ""
        lines.append(f"  {p.get('parameter', '?')}: {p.get('value', '?')} {p.get('unit', '')}{source}")
    lines.append("")

    if calc_result.get("assumptions"):
        lines.append("Assumptions:")
        for a in calc_result["assumptions"]:
            lines.append(f"  - {a}")
        lines.append("")

    lines.append("Annual Emission Reductions:")
    lines.append(f"  {'Year':<6} {'Baseline':>14} {'Project':>14} {'Leakage':>12} {'Net ER':>14}")
    lines.append(f"  {'':->6} {'':->14} {'':->14} {'':->12} {'':->14}")
    for yr in calc_result.get("annual_calculations", []):
        lines.append(
            f"  {yr.get('year', '?'):<6} "
            f"{yr.get('baseline_emissions_tco2e', 0):>13,.1f} "
            f"{yr.get('project_emissions_tco2e', 0):>13,.1f} "
            f"{yr.get('leakage_tco2e', 0):>11,.1f} "
            f"{yr.get('net_emission_reductions_tco2e', 0):>13,.1f}"
        )
    lines.append("")
    total = calc_result.get("total_emission_reductions_tco2e", 0)
    avg = calc_result.get("average_annual_reductions_tco2e", 0)
    lines.append(f"Total Emission Reductions: {total:,.1f} tCO2e")
    lines.append(f"Average Annual Reductions: {avg:,.1f} tCO2e/year")

    return "\n".join(lines)
