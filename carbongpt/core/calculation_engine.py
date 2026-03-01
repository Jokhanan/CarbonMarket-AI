import json
import logging
import os

import requests as http_client

logger = logging.getLogger(__name__)

MODEL = os.getenv("CARBONGPT_AI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def _call_openai(system_prompt, user_prompt, response_format=None, max_tokens=4000):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
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

    system_prompt = (
        "You are an expert carbon credit calculation engine. Given a methodology's equations, "
        "parameters, and user-provided project data, you must calculate the emission reductions "
        "for each year of the crediting period.\n\n"
        "RULES:\n"
        "- Apply the methodology's equations exactly as specified\n"
        "- Use IPCC and methodology default values where specified\n"
        "- Show all calculation steps with actual numbers\n"
        "- Be conservative in assumptions (as required by carbon standards)\n"
        "- If a value is missing, use the most conservative default or state the assumption\n"
        "- Calculate for each year of the crediting period\n"
        "- Include leakage calculations (use 5% default if no specific method given)\n"
        "- Provide a clear narrative explanation of the calculation\n"
        "- All results must be in tCO2e"
    )

    user_prompt = f"## Methodology: {parsed_methodology.get('methodology_code', 'Unknown')}\n"
    user_prompt += f"## Methodology Name: {parsed_methodology.get('methodology_name', '')}\n\n"

    if method:
        user_prompt += f"## Calculation Method: {method['method_name']}\n"
        if method.get("description"):
            user_prompt += f"Description: {method['description']}\n"
        if method.get("applicability"):
            user_prompt += f"Applicability: {method['applicability']}\n"
        user_prompt += "\n### Equations:\n"
        for eq in method.get("equations", []):
            user_prompt += f"- {eq.get('equation_id', '')}: {eq.get('formula_text', '')}\n"
            if eq.get("formula_description"):
                user_prompt += f"  ({eq['formula_description']})\n"
        user_prompt += "\n"

    user_prompt += "### All Methodology Parameters:\n"
    for p in parsed_methodology.get("parameters", []):
        line = f"- {p['symbol']} ({p['name']}): {p['unit']}"
        if p.get("default_value"):
            line += f" [Default: {p['default_value']}]"
        if p.get("description"):
            line += f" - {p['description']}"
        user_prompt += line + "\n"

    defaults = parsed_methodology.get("default_values", {})
    if defaults:
        user_prompt += "\n### Default Values from Methodology:\n"
        for k, v in defaults.items():
            user_prompt += f"- {k}: {v}\n"

    if parsed_methodology.get("leakage_approach"):
        user_prompt += f"\n### Leakage Approach:\n{parsed_methodology['leakage_approach']}\n"

    user_prompt += f"\n### Crediting Period: {crediting_years} years\n"

    user_prompt += "\n### Project-Specific Inputs Provided by User:\n"
    for param_id, value in user_inputs.items():
        user_prompt += f"- {param_id}: {value}\n"

    if project_info:
        user_prompt += "\n### Project Context:\n"
        if project_info.get("name"):
            user_prompt += f"- Project: {project_info['name']}\n"
        if project_info.get("country"):
            user_prompt += f"- Country: {project_info['country']}\n"
        if project_info.get("description"):
            user_prompt += f"- Description: {project_info['description']}\n"

    user_prompt += (
        "\n\nPerform the complete emission reduction calculation for each year of the crediting period. "
        "Show all steps with actual numbers. Provide the results in the structured format."
    )

    result = _call_openai(system_prompt, user_prompt, response_format=CALC_SCHEMA, max_tokens=6000)
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
