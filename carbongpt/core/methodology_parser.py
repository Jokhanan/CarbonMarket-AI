import json
import logging
import os
import re

import requests as http_client

logger = logging.getLogger(__name__)

PARSE_MODEL = os.getenv("CARBONGPT_PARSE_MODEL", "gpt-4o")
CALC_MODEL = os.getenv("CARBONGPT_AI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

MAX_CONTEXT_CHARS = 80000


def _call_openai(system_prompt, user_prompt, response_format=None, max_tokens=8000, model=None):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    payload = {
        "model": model or CALC_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }
    if response_format:
        payload["response_format"] = response_format
    resp = http_client.post(
        OPENAI_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=180,
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
                            "method_id": {"type": "string", "description": "e.g. 'method_1', 'method_2'"},
                            "method_name": {
                                "type": "string",
                                "description": "The EXACT name from the document, e.g. 'Method 1. Baseline and project fuel(s) are identical and emission reductions are exclusively from improved efficiency'",
                            },
                            "description": {"type": "string"},
                            "applicability": {"type": "string"},
                            "scale_restrictions": {"type": "string", "description": "e.g. 'micro or small-scale only', 'all scales'"},
                            "equations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "equation_id": {"type": "string", "description": "Exact ID from doc, e.g. 'Eq. 1', 'Eq. 3'"},
                                        "equation_label": {"type": "string", "description": "What this equation calculates, e.g. 'Emission Reductions (ER_y)', 'Baseline Emissions (BE_y)'"},
                                        "formula_text": {
                                            "type": "string",
                                            "description": "The EXACT mathematical formula using the document's notation with subscripts, e.g. 'ER_y = SUM_b,p(N_b,p,y * U_p,y * SFS_p,b,y * NCV_b,fuel * (f_NRB,b,y * EF_b,f,CO2 + EF_b,f,nonCO2)) - SUM_p(LE_p,y)'",
                                        },
                                        "formula_description": {"type": "string"},
                                        "variables": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "symbol": {"type": "string"},
                                                    "name": {"type": "string"},
                                                    "unit": {"type": "string"},
                                                },
                                            },
                                            "description": "All variables used in this specific equation, with their exact symbols from the document",
                                        },
                                    },
                                    "required": ["equation_id", "formula_text", "variables"],
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
                            "parameter_id": {
                                "type": "string",
                                "description": "The exact ID from the document, e.g. 'ICS 1', 'ICS 14', 'AMS-II.G_param1'",
                            },
                            "symbol": {
                                "type": "string",
                                "description": "The exact symbol from the document, e.g. 'N_b,p,y', 'SFC_b,y', 'f_NRB,b,y'",
                            },
                            "name": {"type": "string"},
                            "unit": {"type": "string"},
                            "description": {"type": "string"},
                            "source": {"type": "string", "description": "Data source as specified in the methodology"},
                            "default_value": {"type": "string", "description": "Methodology or IPCC default value if specified"},
                            "monitoring_frequency": {"type": "string"},
                            "applicable_methods": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Which methods use this parameter, e.g. ['method_1', 'method_2'] or ['all']",
                            },
                            "is_monitored": {"type": "boolean"},
                            "is_user_input": {"type": "boolean", "description": "True if the project developer must provide this value (project-specific data)"},
                            "is_calculated": {"type": "boolean", "description": "True if this is calculated from other parameters"},
                            "is_default_available": {"type": "boolean", "description": "True if a methodology/IPCC default exists"},
                        },
                        "required": ["parameter_id", "symbol", "name", "unit"],
                    },
                },
                "default_values": {
                    "type": "object",
                    "description": "All default emission factors and constants from the methodology, with their exact values and sources",
                },
                "leakage_approach": {"type": "string"},
                "monitoring_requirements_summary": {"type": "string"},
            },
            "required": ["methodology_code", "methodology_name", "calculation_methods", "parameters"],
        },
    },
}


SYSTEM_PROMPT = """You are an expert carbon methodology analyst specializing in GHG emission reduction methodologies from Gold Standard, Verra VCS, CDM, and other carbon standards.

Your task is to parse a carbon credit methodology document and extract its COMPLETE and EXACT calculation framework.

CRITICAL RULES — follow these exactly:
1. USE EXACT NAMES: Method names must be copied VERBATIM from the document. Do NOT paraphrase or simplify them.
   - WRONG: "Method 1: Improved Biomass Cookstoves"
   - RIGHT: "Method 1. Baseline and project fuel(s) are identical and emission reductions are exclusively from improved efficiency"

2. USE EXACT EQUATIONS: Copy the mathematical formulas exactly as they appear, preserving all subscripts and summation signs.
   - WRONG: "ER = (BC - PC) * EF"
   - RIGHT: "ER_y = SUM_b,p(N_b,p,y × U_p,y × SFS_p,b,y × NCV_b,fuel × (f_NRB,b,y × EF_b,f,CO2 + EF_b,f,nonCO2)) - SUM_p(LE_p,y)"
   Use SUM_x(...) notation for summation signs. Use × for multiplication. Preserve ALL subscripts.

3. USE EXACT PARAMETER IDS AND SYMBOLS: Copy parameter identifiers exactly as they appear in the document's parameter tables.
   - If the doc uses "ICS 14" as the parameter ID, use "ICS 14"
   - If the doc uses "SFC_b,y" as the symbol, use "SFC_b,y"
   - Do NOT invent parameter names that don't exist in the document

4. CAPTURE ALL EQUATIONS for each method: If a method uses multiple equations (e.g., separate BE, PE, and ER equations), list them ALL.

5. INCLUDE DEFAULT VALUES: Extract all methodology defaults and IPCC defaults mentioned (emission factors, net calorific values, etc.) with their exact values.

6. LINK PARAMETERS TO METHODS: For each parameter, indicate which calculation methods use it.

7. DISTINGUISH PARAMETER TYPES:
   - is_user_input=true: Values the project developer must provide from project-specific data (e.g., number of devices deployed, fuel consumption from field tests)
   - is_monitored=true: Values that require periodic monitoring/surveys during the crediting period
   - is_calculated=true: Values computed from other parameters (e.g., SFS calculated from baseline and project fuel consumption tests)
   - is_default_available=true: Values where the methodology provides a default (e.g., IPCC emission factors, default NCV)

8. DO NOT HALLUCINATE: If something is not in the document, do not make it up. Only extract what is explicitly stated."""


def _normalize_meth_code(code):
    code = code.strip()
    code = re.sub(r'\s+[Vv]?\d+(\.\d+)?$', '', code)
    code = code.replace("GS-", "").replace("gs-", "")
    return code


def _score_section_relevance(content):
    patterns = [
        (r'(?:Eq\.|Equation)\s*\d', 10),
        (r'emission\s+reduct', 5),
        (r'(?:Method|Approach)\s+\d', 8),
        (r'(?:baseline|project)\s+(?:emission|fuel|scenario)', 5),
        (r'(?:SFC|SFS|NCV|EF|ER|BE|PE|LE|SE)[\s_]', 6),
        (r'Data/parameter\s+ID', 8),
        (r'Data\s*/\s*Parameter:', 7),
        (r'Source of data:', 5),
        (r'Monitoring frequency:', 5),
        (r'Default.*(?:value|factor)', 5),
        (r'tCO\s*2\s*e?', 3),
        (r'IPCC\s+default', 6),
        (r'leakage', 4),
        (r'crediting\s+period', 3),
        (r'non-renewable\s+biomass|f_NRB|fNRB', 6),
        (r'calorific\s+value', 5),
        (r'GHG\s+(?:emission|reduction)', 4),
        (r'calculation|quantif', 3),
    ]
    score = 0
    content_lower = content.lower()
    for pattern, weight in patterns:
        matches = re.findall(pattern, content_lower, re.IGNORECASE)
        score += len(matches) * weight
    return score


def _extract_relevant_text(sections, max_chars=MAX_CONTEXT_CHARS):
    scored = []
    for sec in sections:
        content = sec.get("content", "")
        if len(content) < 20:
            continue
        score = _score_section_relevance(content)
        scored.append((score, sec["section_order"], content))

    scored.sort(key=lambda x: x[0], reverse=True)

    selected = []
    total_chars = 0
    for score, order, content in scored:
        if total_chars + len(content) > max_chars:
            remaining = max_chars - total_chars
            if remaining > 2000:
                selected.append((order, content[:remaining]))
                total_chars += remaining
            break
        selected.append((order, content))
        total_chars += len(content)

    selected.sort(key=lambda x: x[0])
    return "\n\n---\n\n".join(text for _, text in selected)


def get_methodology_sections(methodology_code):
    from carbongpt.repository.db import get_cursor
    base_code = _normalize_meth_code(methodology_code)

    with get_cursor() as cur:
        search_terms = [f"%{base_code}%", f"%{methodology_code}%"]
        for term in search_terms:
            cur.execute("""
                SELECT d.id, d.title
                FROM documents d
                WHERE d.category = 'methodology'
                  AND (d.title ILIKE %s OR d.reference_id ILIKE %s)
                ORDER BY LENGTH(
                    (SELECT COALESCE(string_agg(ds.content, '' ORDER BY ds.section_order), '')
                     FROM document_sections ds WHERE ds.document_id = d.id)
                ) DESC
                LIMIT 1
            """, (term, term))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    SELECT section_order, title, content
                    FROM document_sections
                    WHERE document_id = %s
                    ORDER BY section_order
                """, (row["id"],))
                sections = cur.fetchall()
                if sections:
                    return {
                        "doc_id": row["id"],
                        "title": row["title"],
                        "sections": [dict(s) for s in sections],
                    }
    return None


def get_methodology_text(methodology_code):
    result = get_methodology_sections(methodology_code)
    if result:
        full_text = "\n\n".join(s["content"] for s in result["sections"])
        return {"doc_id": result["doc_id"], "title": result["title"], "text": full_text}
    return None


def get_or_parse_methodology(methodology_code):
    from carbongpt.repository.store import get_parsed_methodology
    cached = get_parsed_methodology(methodology_code)
    if cached and cached.get("parsed_data"):
        data = cached["parsed_data"]
        if isinstance(data, str):
            data = json.loads(data)
        return data

    return parse_methodology_and_save(methodology_code)


def parse_methodology_and_save(methodology_code, methodology_text=None, force=False):
    from carbongpt.repository.store import save_parsed_methodology

    if not force:
        from carbongpt.repository.store import get_parsed_methodology
        cached = get_parsed_methodology(methodology_code)
        if cached and cached.get("parsed_data"):
            data = cached["parsed_data"]
            if isinstance(data, str):
                data = json.loads(data)
            return data

    sections_data = None
    doc_id = None
    if not methodology_text:
        sections_data = get_methodology_sections(methodology_code)
        if sections_data:
            methodology_text = _extract_relevant_text(sections_data["sections"])
            doc_title = sections_data["title"]
            doc_id = sections_data["doc_id"]
        else:
            raise ValueError(
                f"No methodology document found for '{methodology_code}'. "
                f"Upload the methodology document to the repository first, then try again."
            )
    else:
        doc_title = methodology_code

    text_for_ai = methodology_text[:MAX_CONTEXT_CHARS]
    logger.info("Sending %d chars to AI for methodology %s (doc: %s)", len(text_for_ai), methodology_code, doc_title)

    user_prompt = (
        f"Parse the following carbon credit methodology document and extract the COMPLETE "
        f"calculation framework. Remember: use EXACT names, equations, and parameter IDs "
        f"from the document. Do NOT simplify or paraphrase.\n\n"
        f"Methodology code: {methodology_code}\n"
        f"Document title: {doc_title}\n\n"
        f"--- METHODOLOGY DOCUMENT ---\n{text_for_ai}\n--- END ---"
    )

    try:
        result = _call_openai(SYSTEM_PROMPT, user_prompt, response_format=PARSE_SCHEMA, max_tokens=12000, model=PARSE_MODEL)
        parsed = json.loads(result)
        save_parsed_methodology(
            methodology_code=methodology_code,
            parsed_data=parsed,
            document_id=doc_id,
            model_used=PARSE_MODEL,
            status="completed",
        )
        return parsed
    except json.JSONDecodeError:
        logger.error("Failed to parse methodology AI response as JSON for %s", methodology_code)
        save_parsed_methodology(
            methodology_code=methodology_code,
            parsed_data={"error": "JSON parse failure"},
            document_id=doc_id,
            model_used=PARSE_MODEL,
            status="failed",
            error="AI response was not valid JSON",
        )
        return {"error": "Failed to parse response"}
    except Exception as e:
        logger.error("Methodology parse failed for %s: %s", methodology_code, e)
        save_parsed_methodology(
            methodology_code=methodology_code,
            parsed_data={"error": str(e)},
            document_id=doc_id,
            model_used=PARSE_MODEL,
            status="failed",
            error=str(e),
        )
        raise


def parse_methodology(methodology_code, methodology_text=None):
    return parse_methodology_and_save(methodology_code, methodology_text)


def batch_parse_methodologies(codes=None, force=False):
    from carbongpt.repository.db import get_cursor

    if codes is None:
        with get_cursor() as cur:
            cur.execute("""
                SELECT DISTINCT d.title, d.id
                FROM documents d
                JOIN document_sections ds ON ds.document_id = d.id
                WHERE d.category = 'methodology'
                ORDER BY d.title
            """)
            docs = cur.fetchall()
    else:
        docs = [{"title": c, "id": None} for c in codes]

    results = {"parsed": 0, "skipped": 0, "failed": 0, "errors": []}

    for doc in docs:
        code = doc["title"]
        if not force:
            from carbongpt.repository.store import get_parsed_methodology
            existing = get_parsed_methodology(code)
            if existing and existing.get("parse_status") == "completed":
                results["skipped"] += 1
                continue

        try:
            logger.info("Batch parsing: %s", code)
            parse_methodology_and_save(code, force=True)
            results["parsed"] += 1
        except Exception as e:
            logger.error("Batch parse failed for %s: %s", code, e)
            results["failed"] += 1
            results["errors"].append({"code": code, "error": str(e)})

    return results


def get_calculation_inputs(parsed_methodology, method_id=None):
    if not parsed_methodology or "parameters" not in parsed_methodology:
        return []

    params = parsed_methodology["parameters"]

    if method_id and parsed_methodology.get("calculation_methods"):
        method = next(
            (m for m in parsed_methodology["calculation_methods"] if m["method_id"] == method_id),
            None
        )
        if method:
            eq_symbols = set()
            for eq in method.get("equations", []):
                for var in eq.get("variables", []):
                    eq_symbols.add(var.get("symbol", ""))
                formula = eq.get("formula_text", "")
                eq_symbols.update(re.findall(r'[A-Za-z_][A-Za-z_0-9,]+', formula))

            relevant = []
            for p in params:
                applicable = p.get("applicable_methods", [])
                if applicable and method_id not in applicable and "all" not in applicable:
                    continue

                sym = p.get("symbol", "")
                sym_base = sym.split("_")[0] if "_" in sym else sym

                if p.get("is_user_input") or p.get("is_monitored"):
                    if not applicable or method_id in applicable or "all" in applicable:
                        if sym in eq_symbols or sym_base in {s.split("_")[0] for s in eq_symbols}:
                            relevant.append(p)
                            continue

                if sym in eq_symbols or sym_base in {s.split("_")[0] for s in eq_symbols}:
                    if p.get("is_user_input") or (not p.get("is_default_available") and not p.get("is_calculated")):
                        relevant.append(p)

            if relevant:
                return relevant

    return [p for p in params if p.get("is_user_input", False)]
