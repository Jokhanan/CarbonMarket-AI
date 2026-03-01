import json
import logging
import os
import re
from collections import defaultdict

import requests as http_client

from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

PARSE_MODEL = os.getenv("CARBONGPT_PARSE_MODEL", "gpt-4o")
STRUCTURE_MODEL = os.getenv("CARBONGPT_STRUCTURE_MODEL", "gpt-4o-mini")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

CHUNK_TYPES = [
    "applicability", "method_selection", "equations", "parameters",
    "default_values", "sampling", "monitoring", "safeguards",
    "tools_referenced", "definitions", "leakage", "quantification", "general",
]

SECTION_TYPE_PATTERNS = {
    "applicability": [
        r'(?i)\bapplicab',
        r'(?i)\bscope\b.*\bapplicab',
        r'(?i)\bentry into force\b',
        r'(?i)\bsafeguard',
        r'(?i)\beligib',
    ],
    "definitions": [
        r'(?i)\bdefinition',
        r'(?i)\bglossary\b',
        r'(?i)\bterminology\b',
        r'(?i)\babbreviation',
    ],
    "quantification": [
        r'(?i)\bquantif.*(?:ghg|emission|reduction|removal)',
        r'(?i)\bbaseline\s+(?:emission|scenario)',
        r'(?i)\bproject\s+emission',
        r'(?i)\bnet\s+(?:reduction|removal|ghg)',
    ],
    "equations": [
        r'(?:Eq\.|Equation)\s*[\(\[]?\d',
        r'(?i)\bformula\b',
        r'Where:\s*$',
    ],
    "parameters": [
        r'(?i)Data\s*/?\s*[Pp]arameter',
        r'(?i)Data\s+unit\s*:',
        r'(?i)Source\s+of\s+data\s*:',
        r'(?i)Monitoring\s+frequency\s*:',
        r'(?i)QA/QC\s+procedures?\s*:',
    ],
    "default_values": [
        r'(?i)\bdefault\s+value',
        r'(?i)IPCC\s+(?:default|guideline|table)',
        r'(?i)\bnet\s+calorific\s+value',
        r'(?i)\bemission\s+factor.*default',
    ],
    "sampling": [
        r'(?i)\bsampling\b.*(?:approach|method|procedure|guidance)',
        r'(?i)\bKitchen\s+Performance\s+Test',
        r'(?i)\bKPT\b',
        r'(?i)\bWater\s+Boiling\s+Test',
        r'(?i)\bWBT\b',
        r'(?i)\bControlled\s+Cooking\s+Test',
        r'(?i)\bsample\s+size',
        r'(?i)\bconfidence\s+interval',
    ],
    "monitoring": [
        r'(?i)\bmonitoring\b.*(?:plan|procedure|requirement|parameter)',
        r'(?i)\bdata.*monitored\b',
        r'(?i)\bverification\b.*(?:period|frequency)',
        r'(?i)\bparameters?\s+monitored\b',
    ],
    "leakage": [
        r'(?i)\bleakage\b',
    ],
    "safeguards": [
        r'(?i)\bsafeguard',
        r'(?i)\benvironmental\s+(?:impact|integrity)',
        r'(?i)\bsustainable\s+development',
    ],
    "tools_referenced": [
        r'(?i)\bCDM\s+(?:Tool|TOOL)',
        r'(?i)\bmethodological\s+tool\b',
        r'(?i)\breferenced?\s+(?:tool|standard|methodology)',
    ],
    "method_selection": [
        r'(?i)\bmethod\s+\d\b',
        r'(?i)\bapproach\s+\d\b',
        r'(?i)\boption\s+\d\b.*(?:baseline|calculation|emission)',
    ],
}

PARAMETER_BLOCK_PATTERNS = [
    r'Data/parameter\s+ID\s+\w+\s+\d+',
    r'Data/parameter\s+ID\s*:?\s*\w+',
    r'Data\s*/\s*[Pp]arameter\s*:',
    r'Data\s*/\s*[Pp]arameter\s+table\s+\d+',
    r'Data/parameter\s*\[[\w\d]+\]',
]

EQUATION_PATTERNS = [
    r'(?:Eq\.|Equation)\s*[\(\[]?\s*(\d+[a-z]?)',
    r'(?:Equation)\s*\((\d+)\)',
]


def _call_openai(system_prompt, user_prompt, response_format=None, max_tokens=4000, model=None):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    payload = {
        "model": model or STRUCTURE_MODEL,
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
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _get_document_sections(document_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, section_number, title, content, section_order, word_count
            FROM document_sections
            WHERE document_id = %s
            ORDER BY section_order
        """, (document_id,))
        return [dict(r) for r in cur.fetchall()]


def _score_section_for_type(content, title, chunk_type):
    score = 0
    text_to_check = (title or "") + "\n" + content[:3000]
    patterns = SECTION_TYPE_PATTERNS.get(chunk_type, [])
    for pattern in patterns:
        matches = re.findall(pattern, text_to_check)
        score += len(matches) * 3
    return score


def _count_pattern_matches(content, patterns):
    total = 0
    for pattern in patterns:
        total += len(re.findall(pattern, content))
    return total


def detect_document_structure(document_id, methodology_code=None):
    from carbongpt.repository.store import get_methodology_structure, save_methodology_structure

    cached = get_methodology_structure(document_id)
    if cached:
        return cached["detected_format"], cached.get("section_map", {})

    sections = _get_document_sections(document_id)
    if not sections:
        raise ValueError(f"No sections found for document {document_id}")

    full_text = "\n".join(s["content"] for s in sections)

    parameter_style = "narrative"
    parameter_id_pattern = None

    for pattern in PARAMETER_BLOCK_PATTERNS:
        matches = re.findall(pattern, full_text)
        if len(matches) >= 2:
            if "Data/parameter ID" in pattern or "Data/parameter\\s+ID" in pattern:
                parameter_style = "named_id_blocks"
                id_matches = re.findall(r'Data/parameter\s+ID\s+(\w+\s+\d+)', full_text)
                if id_matches:
                    prefix = id_matches[0].split()[0]
                    parameter_id_pattern = f"{prefix} \\d+"
            elif "table" in pattern.lower():
                parameter_style = "tabular"
            elif "[" in pattern:
                parameter_style = "labeled_blocks"
                id_matches = re.findall(r'Data/parameter\s*\[([\w\d]+)\]', full_text)
                if id_matches:
                    parameter_id_pattern = f"[{id_matches[0][:2]}\\d+]"
            else:
                parameter_style = "labeled_blocks"
            break

    has_methods = bool(re.search(r'(?i)(?:Method|Approach)\s+\d\s*[.:]', full_text))
    has_options = bool(re.search(r'(?i)Option\s+\d\s*[.:]', full_text))

    equation_count = len(re.findall(r'(?:Eq\.|Equation)\s*[\(\[]?\s*\d', full_text))
    has_where_blocks = bool(re.search(r'(?m)^Where:\s*$', full_text)) or \
                       bool(re.search(r'(?m)Where:\s*$', full_text))

    equation_style = "numbered" if equation_count > 0 else "inline"

    param_marker_count = _count_pattern_matches(full_text, [
        r'(?i)Data\s*/?\s*[Pp]arameter',
        r'(?i)Data\s+unit\s*:',
    ])

    section_map = {}
    for sec in sections:
        title = (sec.get("title") or "").strip()
        content = sec.get("content", "")
        if len(content) < 30:
            continue

        best_type = "general"
        best_score = 0

        for chunk_type in CHUNK_TYPES:
            if chunk_type == "general":
                continue
            score = _score_section_for_type(content, title, chunk_type)

            title_lower = title.lower()
            if chunk_type == "applicability" and any(w in title_lower for w in ["applicab", "scope", "eligib"]):
                score += 15
            elif chunk_type == "definitions" and "definition" in title_lower:
                score += 15
            elif chunk_type == "monitoring" and "monitor" in title_lower:
                score += 15
            elif chunk_type == "leakage" and "leakage" in title_lower:
                score += 15
            elif chunk_type == "quantification" and any(w in title_lower for w in ["quantif", "baseline emission", "project emission", "net reduction"]):
                score += 15
            elif chunk_type == "sampling" and any(w in title_lower for w in ["sampl", "kpt", "wbt", "test"]):
                score += 15
            elif chunk_type == "parameters" and any(w in title_lower for w in ["data and parameter", "parameter available", "parameter monitored"]):
                score += 15
            elif chunk_type == "equations" and any(w in title_lower for w in ["equation", "formula"]):
                score += 15
            elif chunk_type == "safeguards" and "safeguard" in title_lower:
                score += 15

            if score > best_score:
                best_score = score
                best_type = chunk_type

        if best_score < 3:
            param_density = _count_pattern_matches(content, PARAMETER_BLOCK_PATTERNS)
            eq_density = _count_pattern_matches(content, [r'(?:Eq\.|Equation)\s*[\(\[]?\s*\d'])
            if param_density >= 2:
                best_type = "parameters"
            elif eq_density >= 1:
                best_type = "equations"

        section_map[str(sec["id"])] = best_type

    detected_format = {
        "parameter_style": parameter_style,
        "parameter_id_pattern": parameter_id_pattern,
        "equation_style": equation_style,
        "equation_count": equation_count,
        "has_methods": has_methods,
        "has_options": has_options,
        "has_where_blocks": has_where_blocks,
        "param_marker_count": param_marker_count,
        "total_sections": len(sections),
        "total_chars": len(full_text),
    }

    if methodology_code:
        save_methodology_structure(document_id, methodology_code, detected_format, section_map)

    return detected_format, section_map


def _split_parameter_blocks(content, section_id, detected_format):
    chunks = []
    param_style = detected_format.get("parameter_style", "narrative")

    if param_style == "named_id_blocks":
        blocks = re.split(r'(?=Data/parameter\s+ID\s+\w+\s+\d+)', content)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            id_match = re.match(r'Data/parameter\s+ID\s+(\w+\s+\d+)', block)
            if id_match:
                param_id = id_match.group(1).strip()
                symbol_match = re.search(r'Data\s*/\s*Parameter\s*:\s*(.+?)(?:\n|$)', block)
                symbol = symbol_match.group(1).strip() if symbol_match else param_id
                chunks.append({
                    "chunk_type": "parameters",
                    "chunk_key": f"param_{param_id.replace(' ', '_')}",
                    "title": f"Parameter {param_id}: {symbol}",
                    "content": block,
                    "source_section_ids": [section_id],
                })
            else:
                if len(block) > 100:
                    chunks.append({
                        "chunk_type": "parameters",
                        "chunk_key": f"param_preamble_{section_id}",
                        "title": "Parameter section preamble",
                        "content": block,
                        "source_section_ids": [section_id],
                    })

    elif param_style == "labeled_blocks":
        blocks = re.split(r'(?=Data\s*/?\s*[Pp]arameter\s*(?:\[[\w\d]+\]|:))', content)
        for i, block in enumerate(blocks):
            block = block.strip()
            if not block or len(block) < 50:
                continue
            label_match = re.match(r'Data\s*/?\s*[Pp]arameter\s*(?:\[([\w\d]+)\]|:\s*(.+?)(?:\n|$))', block)
            if label_match:
                param_id = label_match.group(1) or label_match.group(2) or f"param_{i}"
                param_id = param_id.strip()
                chunks.append({
                    "chunk_type": "parameters",
                    "chunk_key": f"param_{param_id.replace(' ', '_').replace('/', '_')}",
                    "title": f"Parameter: {param_id}",
                    "content": block,
                    "source_section_ids": [section_id],
                })
            elif len(block) > 100:
                chunks.append({
                    "chunk_type": "parameters",
                    "chunk_key": f"param_block_{section_id}_{i}",
                    "title": "Parameter block",
                    "content": block,
                    "source_section_ids": [section_id],
                })

    elif param_style == "tabular":
        blocks = re.split(r'(?=Data\s*/?\s*[Pp]arameter\s+table\s+\d+)', content)
        for i, block in enumerate(blocks):
            block = block.strip()
            if not block or len(block) < 50:
                continue
            table_match = re.match(r'Data\s*/?\s*[Pp]arameter\s+table\s+(\d+)', block)
            table_num = table_match.group(1) if table_match else str(i)
            chunks.append({
                "chunk_type": "parameters",
                "chunk_key": f"param_table_{table_num}",
                "title": f"Parameter Table {table_num}",
                "content": block,
                "source_section_ids": [section_id],
            })

    else:
        if _count_pattern_matches(content, [r'(?i)Data\s*/?\s*[Pp]arameter']) >= 1:
            chunks.append({
                "chunk_type": "parameters",
                "chunk_key": f"param_narrative_{section_id}",
                "title": "Parameters (narrative)",
                "content": content,
                "source_section_ids": [section_id],
            })

    return chunks


def split_into_knowledge_chunks(document_id, detected_format, section_map):
    sections = _get_document_sections(document_id)
    if not sections:
        return []

    chunks = []
    chunk_keys_used = set()

    type_groups = defaultdict(list)
    for sec in sections:
        sec_type = section_map.get(str(sec["id"]), "general")
        type_groups[sec_type].append(sec)

    for sec_type, sec_list in type_groups.items():
        for sec in sec_list:
            content = sec.get("content", "").strip()
            if len(content) < 30:
                continue
            title = (sec.get("title") or "").strip()
            section_id = sec["id"]

            if sec_type == "parameters":
                param_chunks = _split_parameter_blocks(content, section_id, detected_format)
                if param_chunks:
                    for pc in param_chunks:
                        if pc["chunk_key"] not in chunk_keys_used:
                            chunks.append(pc)
                            chunk_keys_used.add(pc["chunk_key"])
                    continue

            base_key = f"{sec_type}_{section_id}"
            if base_key in chunk_keys_used:
                base_key = f"{sec_type}_{section_id}_{len(chunk_keys_used)}"
            chunk_keys_used.add(base_key)

            chunks.append({
                "chunk_type": sec_type,
                "chunk_key": base_key,
                "title": title or f"{sec_type.replace('_', ' ').title()} section",
                "content": content,
                "source_section_ids": [section_id],
            })

    logger.info("Split document %d into %d knowledge chunks", document_id, len(chunks))
    type_counts = defaultdict(int)
    for c in chunks:
        type_counts[c["chunk_type"]] += 1
    logger.info("Chunk type distribution: %s", dict(type_counts))

    return chunks


STRUCTURE_EXTRACTION_PROMPT = """You are a carbon methodology expert. Analyze the following methodology text chunks and extract the calculation structure.

Return a JSON object (valid json) with:
{
  "methodology_code": "string",
  "methodology_name": "string - exact name from document",
  "calculation_methods": [
    {
      "method_id": "method_1",
      "method_name": "EXACT name from document",
      "description": "brief description",
      "applicability": "when to use this method",
      "scale_restrictions": "e.g. micro or small-scale only",
      "equation_ids": ["Eq. 1", "Eq. 2"]
    }
  ],
  "leakage_approach": "description of leakage handling",
  "monitoring_requirements_summary": "brief summary"
}

CRITICAL: Copy method names VERBATIM from the document. Do NOT paraphrase."""


EQUATION_EXTRACTION_PROMPT = """You are a carbon methodology expert. Extract all equations from this methodology text and return the result as valid json.

For each equation, provide:
{
  "equations": [
    {
      "equation_id": "Exact ID from doc (e.g. 'Eq. 1')",
      "equation_label": "What this equation calculates (e.g. 'Emission Reductions ER_y')",
      "formula_text": "EXACT formula using document notation. Use SUM_x(...) for summations. Preserve ALL subscripts.",
      "formula_description": "brief explanation",
      "method_id": "which method uses this equation (e.g. 'method_1')",
      "variables": [
        {"symbol": "exact symbol", "name": "full name", "unit": "unit"}
      ]
    }
  ]
}

CRITICAL: Copy formulas EXACTLY as they appear. Use x for multiplication. Preserve all subscripts."""


PARAMETER_EXTRACTION_PROMPT = """You are a carbon methodology expert. Extract structured parameter data from this parameter block and return as valid json.

Return a JSON object:
{
  "parameters": [
    {
      "parameter_id": "exact ID from document (e.g. 'ICS 8', 'EA1', 'Table 1')",
      "symbol": "exact symbol (e.g. 'EF_b,f,CO2', 'NCV_b,fuel')",
      "name": "full parameter name",
      "unit": "unit of measurement",
      "description": "what this parameter represents",
      "source": "data source as specified",
      "default_value": "raw text of default if specified",
      "default_numeric": null,
      "defaults_by_context": [
        {"context_key": "e.g. wood", "value": 0.0156, "unit": "TJ/ton", "source": "Methodology default", "notes": ""}
      ],
      "monitoring_frequency": "how often monitored",
      "category": "one of: methodology_default, monitored, calculated, project_input, qualitative",
      "equation_role": "one of: input, intermediate, output, none",
      "is_monitored": false,
      "is_user_input": false,
      "is_calculated": false,
      "is_default_available": true,
      "applicable_methods": ["method_1"]
    }
  ]
}

CRITICAL RULES:
- Copy parameter IDs, symbols, and names EXACTLY from the document
- Set category correctly: methodology_default for values from IPCC/methodology with defaults, monitored for field survey values, calculated for derived values, project_input for developer-specified values
- Extract ALL default values with their context keys
- Do NOT hallucinate parameters not in the text"""


CONTEXT_EXTRACTION_PROMPT = """You are a carbon methodology expert. From the following methodology text, extract all context dimensions — choices that affect which default values or calculation paths apply. Return as valid json.

Return:
{
  "context_dimensions": [
    {
      "dimension_key": "e.g. baseline_fuel, gwp_version, project_fuel, leakage_option",
      "label": "human-readable label",
      "options": ["option1", "option2"],
      "description": "what this dimension controls",
      "affects_parameters": ["list of parameter IDs affected"]
    }
  ]
}

Look for:
- Fuel type options (wood, charcoal, LPG, etc.)
- GWP version options (AR4, AR5, AR6)
- Method/approach selection options
- Scale classifications (micro, small, large)
- Leakage calculation options
- Regional default options"""


def extract_structured_data(chunks, methodology_code, detected_format):
    equation_chunks = [c for c in chunks if c["chunk_type"] in ("equations", "quantification")]
    parameter_chunks = [c for c in chunks if c["chunk_type"] == "parameters"]
    applicability_chunks = [c for c in chunks if c["chunk_type"] in ("applicability", "method_selection")]

    methods_data = None
    if equation_chunks or applicability_chunks:
        combined_text = "\n\n---\n\n".join(
            c["content"][:8000] for c in (equation_chunks + applicability_chunks)
        )[:20000]

        try:
            result = _call_openai(
                STRUCTURE_EXTRACTION_PROMPT,
                f"Methodology code: {methodology_code}\n\n{combined_text}",
                response_format={"type": "json_object"},
                max_tokens=3000,
                model=STRUCTURE_MODEL,
            )
            methods_data = json.loads(result)
            logger.info("Pass 1 (structure): Extracted %d methods for %s",
                        len(methods_data.get("calculation_methods", [])), methodology_code)
        except Exception as e:
            logger.error("Pass 1 failed for %s: %s", methodology_code, e)
            methods_data = {}

    equations_data = {"equations": []}
    if equation_chunks:
        eq_text = "\n\n---\n\n".join(c["content"][:10000] for c in equation_chunks)[:25000]
        try:
            result = _call_openai(
                EQUATION_EXTRACTION_PROMPT,
                f"Methodology code: {methodology_code}\n\n{eq_text}",
                response_format={"type": "json_object"},
                max_tokens=6000,
                model=PARSE_MODEL,
            )
            equations_data = json.loads(result)
            logger.info("Pass 2 (equations): Extracted %d equations for %s",
                        len(equations_data.get("equations", [])), methodology_code)
        except Exception as e:
            logger.error("Pass 2 failed for %s: %s", methodology_code, e)

    all_parameters = []
    for pc in parameter_chunks:
        try:
            result = _call_openai(
                PARAMETER_EXTRACTION_PROMPT,
                f"Methodology code: {methodology_code}\n\n{pc['content'][:12000]}",
                response_format={"type": "json_object"},
                max_tokens=4000,
                model=PARSE_MODEL,
            )
            param_data = json.loads(result)
            params = param_data.get("parameters", [])
            all_parameters.extend(params)

            pc["structured_data"] = param_data
            logger.info("Pass 3 (params): Extracted %d parameters from chunk '%s'",
                        len(params), pc.get("chunk_key", "?"))
        except Exception as e:
            logger.error("Pass 3 failed for chunk '%s': %s", pc.get("chunk_key", "?"), e)

    context_data = {"context_dimensions": []}
    context_text_parts = []
    for c in applicability_chunks:
        context_text_parts.append(c["content"][:5000])
    for pc in parameter_chunks[:5]:
        context_text_parts.append(pc["content"][:3000])
    if context_text_parts:
        context_text = "\n\n---\n\n".join(context_text_parts)[:15000]
        try:
            result = _call_openai(
                CONTEXT_EXTRACTION_PROMPT,
                f"Methodology code: {methodology_code}\n\n{context_text}",
                response_format={"type": "json_object"},
                max_tokens=2000,
                model=STRUCTURE_MODEL,
            )
            context_data = json.loads(result)
            logger.info("Pass 4 (context): Extracted %d dimensions for %s",
                        len(context_data.get("context_dimensions", [])), methodology_code)
        except Exception as e:
            logger.error("Pass 4 failed for %s: %s", methodology_code, e)

    for c in chunks:
        if c["chunk_type"] in ("equations", "quantification") and methods_data:
            c["structured_data"] = {
                **(c.get("structured_data") or {}),
                "methods": methods_data.get("calculation_methods", []),
                "leakage_approach": methods_data.get("leakage_approach"),
                "monitoring_summary": methods_data.get("monitoring_requirements_summary"),
            }
        if c["chunk_type"] in ("equations", "quantification") and equations_data.get("equations"):
            existing = c.get("structured_data") or {}
            existing["equations"] = equations_data["equations"]
            c["structured_data"] = existing
        if c["chunk_type"] in ("applicability", "method_selection") and context_data.get("context_dimensions"):
            existing = c.get("structured_data") or {}
            existing["context_dimensions"] = context_data["context_dimensions"]
            c["structured_data"] = existing

    return {
        "methods": methods_data,
        "equations": equations_data,
        "parameters": all_parameters,
        "context_dimensions": context_data.get("context_dimensions", []),
    }


def build_methodology_knowledge(document_id, methodology_code, force=False):
    from carbongpt.repository.store import (
        save_knowledge_chunk, delete_methodology_knowledge, get_knowledge_chunks
    )

    if not force:
        existing = get_knowledge_chunks(methodology_code)
        if existing and len(existing) > 5:
            logger.info("Knowledge base already exists for %s (%d chunks), skipping. Use force=True to rebuild.",
                        methodology_code, len(existing))
            return {"status": "cached", "chunks": len(existing)}

    logger.info("Building methodology knowledge for %s from document %d", methodology_code, document_id)

    if force:
        delete_methodology_knowledge(methodology_code)

    detected_format, section_map = detect_document_structure(document_id, methodology_code)
    logger.info("Detected format: %s", json.dumps(detected_format, indent=2))

    chunks = split_into_knowledge_chunks(document_id, detected_format, section_map)
    if not chunks:
        raise ValueError(f"No chunks extracted from document {document_id}")

    extracted = extract_structured_data(chunks, methodology_code, detected_format)

    saved_count = 0
    for chunk in chunks:
        try:
            save_knowledge_chunk(
                methodology_code=methodology_code,
                document_id=document_id,
                chunk_type=chunk["chunk_type"],
                chunk_key=chunk["chunk_key"],
                title=chunk.get("title"),
                content=chunk["content"],
                structured_data=chunk.get("structured_data") or {},
                source_section_ids=chunk.get("source_section_ids"),
                extraction_method="ai_assisted" if chunk.get("structured_data") else "programmatic",
            )
            saved_count += 1
        except Exception as e:
            logger.error("Failed to save chunk %s: %s", chunk.get("chunk_key"), e)

    _save_backward_compatible(methodology_code, document_id, extracted)

    type_counts = defaultdict(int)
    for c in chunks:
        type_counts[c["chunk_type"]] += 1

    return {
        "status": "completed",
        "methodology_code": methodology_code,
        "document_id": document_id,
        "total_chunks": saved_count,
        "chunk_types": dict(type_counts),
        "parameters_extracted": len(extracted.get("parameters", [])),
        "equations_extracted": len(extracted.get("equations", {}).get("equations", [])),
        "methods_found": len(extracted.get("methods", {}).get("calculation_methods", [])),
        "context_dimensions": len(extracted.get("context_dimensions", [])),
        "detected_format": detected_format,
    }


def _save_backward_compatible(methodology_code, document_id, extracted):
    from carbongpt.repository.store import save_parsed_methodology

    methods_data = extracted.get("methods") or {}
    equations_data = extracted.get("equations") or {}
    parameters = extracted.get("parameters", [])
    context_dims = extracted.get("context_dimensions", [])

    calc_methods = methods_data.get("calculation_methods", [])
    equations_list = equations_data.get("equations", [])

    for method in calc_methods:
        method_id = method.get("method_id", "")
        method_eqs = [e for e in equations_list if e.get("method_id") == method_id]
        if not method_eqs:
            method_eqs = [e for e in equations_list
                          if method_id in str(e.get("method_id", ""))]
        method["equations"] = method_eqs

    if not calc_methods and equations_list:
        calc_methods = [{
            "method_id": "method_1",
            "method_name": "Default calculation method",
            "description": "",
            "applicability": "",
            "equations": equations_list,
        }]

    parsed_data = {
        "methodology_code": methodology_code,
        "methodology_name": methods_data.get("methodology_name", methodology_code),
        "calculation_methods": calc_methods,
        "parameters": parameters,
        "context_dimensions": context_dims,
        "leakage_approach": methods_data.get("leakage_approach", ""),
        "monitoring_requirements_summary": methods_data.get("monitoring_requirements_summary", ""),
        "_source": "methodology_knowledge_base",
    }

    save_parsed_methodology(
        methodology_code=methodology_code,
        parsed_data=parsed_data,
        document_id=document_id,
        model_used=f"{PARSE_MODEL}+{STRUCTURE_MODEL}",
        status="completed",
    )
    logger.info("Saved backward-compatible parsed data for %s", methodology_code)


def get_methodology_knowledge(methodology_code, chunk_type=None):
    from carbongpt.repository.store import get_knowledge_chunks
    chunks = get_knowledge_chunks(methodology_code, chunk_type)

    organized = defaultdict(list)
    for chunk in chunks:
        ct = chunk["chunk_type"]
        organized[ct].append({
            "chunk_key": chunk["chunk_key"],
            "title": chunk["title"],
            "content": chunk["content"],
            "structured_data": chunk["structured_data"] if isinstance(chunk["structured_data"], dict)
                              else json.loads(chunk["structured_data"]) if chunk["structured_data"] else {},
            "extraction_method": chunk["extraction_method"],
            "confidence": chunk["confidence"],
            "version": chunk["version"],
        })

    return dict(organized)


def get_knowledge_as_parsed_format(methodology_code):
    from carbongpt.repository.store import get_parsed_methodology
    cached = get_parsed_methodology(methodology_code)
    if cached and cached.get("parsed_data"):
        data = cached["parsed_data"]
        if isinstance(data, str):
            data = json.loads(data)
        return data
    return None


def batch_build_knowledge(force=False, limit=None):
    with get_cursor() as cur:
        cur.execute("""
            SELECT DISTINCT d.id as doc_id, d.title, m.code as methodology_code
            FROM documents d
            JOIN document_sections ds ON ds.document_id = d.id
            LEFT JOIN methodologies m ON (
                d.title ILIKE '%' || m.code || '%'
                OR d.reference_id ILIKE '%' || m.code || '%'
            )
            WHERE d.category = 'methodology'
            GROUP BY d.id, d.title, m.code
            HAVING COUNT(ds.id) > 3
            ORDER BY d.title
        """)
        docs = cur.fetchall()

    if limit:
        docs = docs[:limit]

    results = {"processed": 0, "skipped": 0, "failed": 0, "errors": []}

    for doc in docs:
        meth_code = doc["methodology_code"] or doc["title"]
        try:
            result = build_methodology_knowledge(doc["doc_id"], meth_code, force=force)
            if result["status"] == "cached":
                results["skipped"] += 1
            else:
                results["processed"] += 1
        except Exception as e:
            logger.error("Batch KB build failed for %s: %s", meth_code, e)
            results["failed"] += 1
            results["errors"].append({"code": meth_code, "error": str(e)})

    return results
