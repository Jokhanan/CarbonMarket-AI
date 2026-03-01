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


PARSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "methodology_parse",
        "strict": False,
        "schema": {
            "type": "object",
            "properties": {
                "methodology_code": {"type": "string"},
                "methodology_name": {"type": "string"},
                "calculation_methods": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "method_id": {"type": "string"},
                            "method_name": {"type": "string"},
                            "description": {"type": "string"},
                            "applicability": {"type": "string"},
                            "equations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "equation_id": {"type": "string"},
                                        "equation_label": {"type": "string"},
                                        "formula_text": {"type": "string"},
                                        "formula_description": {"type": "string"},
                                    },
                                    "required": ["equation_id", "formula_text"],
                                },
                            },
                        },
                        "required": ["method_id", "method_name", "equations"],
                    },
                },
                "parameters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "parameter_id": {"type": "string"},
                            "symbol": {"type": "string"},
                            "name": {"type": "string"},
                            "unit": {"type": "string"},
                            "description": {"type": "string"},
                            "source": {"type": "string"},
                            "default_value": {"type": "string"},
                            "monitoring_frequency": {"type": "string"},
                            "is_monitored": {"type": "boolean"},
                            "is_user_input": {"type": "boolean"},
                        },
                        "required": ["parameter_id", "symbol", "name", "unit"],
                    },
                },
                "default_values": {
                    "type": "object",
                    "description": "Default emission factors and constants from the methodology",
                },
                "leakage_approach": {"type": "string"},
                "monitoring_requirements_summary": {"type": "string"},
            },
            "required": ["methodology_code", "methodology_name", "calculation_methods", "parameters"],
        },
    },
}


def _normalize_meth_code(code):
    import re
    code = code.strip()
    code = re.sub(r'\s+[Vv]?\d+(\.\d+)?$', '', code)
    code = code.replace("GS-", "").replace("gs-", "")
    return code


def get_methodology_text(methodology_code):
    from carbongpt.repository.db import get_cursor
    base_code = _normalize_meth_code(methodology_code)

    with get_cursor() as cur:
        search_terms = [f"%{base_code}%", f"%{methodology_code}%"]
        for term in search_terms:
            cur.execute("""
                SELECT d.id, d.title,
                       (SELECT string_agg(ds.content, E'\n\n' ORDER BY ds.section_order)
                        FROM document_sections ds WHERE ds.document_id = d.id) as full_text
                FROM documents d
                WHERE d.category = 'methodology'
                  AND (d.title ILIKE %s OR d.reference_id ILIKE %s)
                ORDER BY LENGTH(
                    (SELECT string_agg(ds.content, '' ORDER BY ds.section_order)
                     FROM document_sections ds WHERE ds.document_id = d.id)
                ) DESC
                LIMIT 1
            """, (term, term))
            row = cur.fetchone()
            if row and row.get("full_text"):
                return {"doc_id": row["id"], "title": row["title"], "text": row["full_text"]}
    return None


def parse_methodology(methodology_code, methodology_text=None):
    if not methodology_text:
        doc = get_methodology_text(methodology_code)
        if not doc:
            from carbongpt.repository.store import get_methodology
            meth = get_methodology(methodology_code)
            if meth and meth.get("applicability"):
                methodology_text = (
                    f"Methodology: {meth['code']} - {meth.get('name', '')}\n"
                    f"Standard: {meth.get('standard', '')}\n"
                    f"Category: {meth.get('category', '')}\n"
                    f"Applicability: {meth.get('applicability', '')}\n"
                    f"Description: {meth.get('description', '')}"
                )
            else:
                raise ValueError(f"No methodology document found for {methodology_code}")
        else:
            methodology_text = doc["text"]

    text_for_ai = methodology_text[:25000]

    system_prompt = (
        "You are an expert carbon methodology analyst. Your task is to parse a carbon credit "
        "methodology document and extract its complete calculation framework.\n\n"
        "Extract:\n"
        "1. All calculation methods (e.g., Method 1, Method 2, Method 3) with their equations\n"
        "2. All parameters with their symbols, units, descriptions, default values, and whether "
        "they need to be monitored or provided by the user\n"
        "3. Default emission factors and constants specified in the methodology\n"
        "4. Leakage calculation approach\n"
        "5. Monitoring requirements summary\n\n"
        "For each equation, provide the formula as a readable mathematical expression.\n"
        "For parameters, mark is_user_input=true for values the project developer must provide "
        "(e.g., number of devices, usage hours, fuel consumption), and is_monitored=true for "
        "values that need periodic monitoring.\n"
        "Include ALL default values mentioned (IPCC defaults, methodology defaults, etc.)."
    )

    user_prompt = (
        f"Parse the following methodology and extract the complete calculation framework:\n\n"
        f"---\n{text_for_ai}\n---"
    )

    result = _call_openai(system_prompt, user_prompt, response_format=PARSE_SCHEMA, max_tokens=6000)
    try:
        parsed = json.loads(result)
        return parsed
    except json.JSONDecodeError:
        logger.error("Failed to parse methodology AI response as JSON")
        return {"raw": result, "error": "Failed to parse response"}


def get_calculation_inputs(parsed_methodology, method_id=None):
    if not parsed_methodology or "parameters" not in parsed_methodology:
        return []

    params = parsed_methodology["parameters"]
    user_inputs = [p for p in params if p.get("is_user_input", False)]

    if method_id and parsed_methodology.get("calculation_methods"):
        method = next(
            (m for m in parsed_methodology["calculation_methods"] if m["method_id"] == method_id),
            None
        )
        if method:
            eq_text = " ".join(e.get("formula_text", "") for e in method.get("equations", []))
            relevant = []
            for p in user_inputs:
                sym = p.get("symbol", "")
                if sym and sym in eq_text:
                    relevant.append(p)
            if relevant:
                return relevant

    return user_inputs
