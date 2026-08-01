import json
import logging
import re
from collections import defaultdict

from carbongpt.repository.db import get_cursor
from carbongpt.core.openai_client import PARSE_MODEL, STRUCTURE_MODEL

logger = logging.getLogger(__name__)

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
    from carbongpt.core.openai_client import call_openai
    return call_openai(
        system_prompt, user_prompt, response_format=response_format,
        max_tokens=max_tokens, temperature=0.1, model_override=model or STRUCTURE_MODEL,
    )


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

Methodologies typically define multiple calculation methods based on the relationship between baseline and project fuels/technologies. Look for:
- "Method 1", "Method 2", "Method 3" or similar numbered options
- Methods distinguished by whether baseline and project fuels are the same or different
- Methods distinguished by whether emission factors are the same or different
- Scale-based options (micro, small, large)
- SUB-VARIANTS within a method (e.g. Method 3 may have fossil fuel vs non-fossil fuel cases with different formulas)

Return a JSON object (valid json) with:
{
  "methodology_code": "string",
  "methodology_name": "string - exact name from document",
  "calculation_methods": [
    {
      "method_id": "method_1",
      "method_name": "EXACT name or description from document including the distinguishing condition",
      "description": "brief description of when this method applies",
      "applicability": "specific conditions (e.g. baseline and project fuels are identical)",
      "scale_restrictions": "e.g. micro or small-scale only",
      "equation_ids": ["Eq. 1", "Eq. 2"],
      "sub_variants": [
        {
          "variant_id": "e.g. method_3_ff",
          "variant_name": "e.g. Method 3 - Fossil Fuel case",
          "condition": "when this variant applies",
          "equation_differences": "how the equations differ from the base method"
        }
      ]
    }
  ],
  "leakage_approach": "description including specific default values (e.g. '5% discount factor' or 'Option 1: 5% default, Option 2: project-specific calculation')",
  "monitoring_requirements_summary": "brief summary",
  "temporal_granularity": "how the methodology handles time (e.g. 'per-day calculation scaled to annual', 'annual', 'monthly batches with aging')",
  "aging_or_degradation": "description of any aging, degradation, or usage rate decay over the technology lifetime (e.g. 'cumulative usage rate decreases from 0.9 in year 1 to 0.5 in year 5')"
}

CRITICAL: Extract ALL distinct calculation methods/options. Copy method names VERBATIM. If a method is described as 'Method 1: Baseline and project fuel(s) are identical', capture that exactly. Do NOT merge methods into one. If a method has sub-variants (e.g. fossil vs non-fossil fuel), list them in sub_variants."""


EQUATION_EXTRACTION_PROMPT = """You are a carbon methodology expert. Extract ALL equations needed to perform a complete, step-by-step emission reduction calculation from this methodology text. Return the result as valid json.

WHAT TO EXTRACT — the complete calculation chain for each method:

1. MAIN EQUATION per method: The top-level formula that computes ER_y (emission reductions per year). Each method will have its OWN main equation with different terms. Extract each one separately with its correct method_id.

2. INTERMEDIATE EQUATIONS: Sub-equations that compute values used by the main equation. Examples:
   - Baseline emissions: BE_y = N x U x SE_b,CO2 x fNRB + SE_b,nonCO2 (or using SFC and NCV depending on method)
   - Project emissions: PE_y = N x U x SE_p,CO2 x fNRB + SE_p,nonCO2
   - Specific emissions: SE_b,CO2 = P_b x EF_b,CO2 x NCV_b
   - Fuel savings: SFS = P_b - P_p (baseline consumption minus project consumption)

3. LEAKAGE EQUATION: How leakage is computed (e.g. LE_y = ER_y_before_leakage x (1 - leakage_discount_factor), where default discount factor = 0.95 for 5% leakage)

4. CALCULATED PARAMETERS: When a parameter's value is defined by a formula (e.g. "SFS is calculated as the difference between baseline and project fuel consumption"), that IS an equation. Extract it.

5. UNIT CONVERSION: If the methodology calculates per-day and converts to annual (x 365) or monthly (x 30.42), capture those conversion steps.

6. AGING/DEGRADATION: Any formula that adjusts values based on technology age (e.g. cumulative usage rate decay, SFC degradation over time).

Return:
{
  "equations": [
    {
      "equation_id": "Exact ID from doc if available, otherwise 'derived_N'",
      "equation_label": "What this equation calculates (e.g. 'Emission reductions per day - Method 1')",
      "formula_text": "Mathematical formula preserving ALL terms. Use * for multiplication. Use SUM_b,p(...) for summations. Preserve exact subscripts from document. Do NOT simplify or omit terms.",
      "formula_description": "When this equation is used, which method it belongs to, and what it computes",
      "method_id": "which method uses this (method_1, method_2, method_3, or 'all'). IMPORTANT: each method's main equation must have its OWN method_id, not 'all'",
      "output_symbol": "the symbol this equation computes (e.g. 'ER_y', 'BE_y', 'SFS_b,p,y')",
      "output_unit": "unit of the result (e.g. 'tCO2e/day', 'kg/technology/day')",
      "variables": [
        {"symbol": "exact symbol with subscripts", "name": "full name", "unit": "unit"}
      ],
      "is_per_unit": "what the equation calculates per (e.g. 'per day per technology', 'per year total')"
    }
  ]
}

CRITICAL RULES:
- Extract the COMPLETE formula for each method's main equation with ALL multiplicative terms. Do not drop terms like NCV or fNRB.
- Each method gets its OWN main equation with method_id = "method_1", "method_2", etc. Only use "all" for equations genuinely shared across all methods.
- Include leakage equations — they are part of the calculation chain.
- If a method has sub-variants (e.g. fossil fuel vs non-fossil fuel), extract equations for each variant.
- Verify: can you trace from raw inputs (EF, NCV, SFC, N, U, fNRB) to final ER_y using ONLY the equations you extracted? If not, you are missing equations."""


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
        {"context_key": "e.g. wood", "value": 0.0156, "unit": "TJ/ton", "source": "IPCC 2006 Guidelines Table 1.2", "notes": ""}
      ],
      "monitoring_frequency": "how often monitored",
      "category": "one of: methodology_default, monitored, calculated, project_input, qualitative",
      "equation_role": "one of: input, intermediate, output, none",
      "is_monitored": false,
      "is_user_input": false,
      "is_calculated": false,
      "is_default_available": true,
      "applicable_methods": ["method_1"],
      "calculation_formula": "if category is 'calculated', the formula used to compute this parameter (e.g. 'SFS_b,p,y = P_b,y - P_p,y'). null if not calculated.",
      "depends_on": ["list of parameter symbols this parameter depends on, e.g. ['P_b,y', 'P_p,y'] for SFS"]
    }
  ]
}

CRITICAL RULES:
- Copy parameter IDs, symbols, and names EXACTLY from the document
- Set category correctly:
  * methodology_default: values from IPCC/methodology tables with known defaults (EF, NCV, GWP values)
  * monitored: values obtained from field surveys/testing (SFC, fuel consumption from KPT/WBT)
  * calculated: values computed from OTHER parameters using a formula (SFS = P_b - P_p, SE = P * EF * NCV). Set calculation_formula and depends_on for these.
  * project_input: values specified by the project developer (N, crediting period, stove type)
  * qualitative: non-numeric descriptive parameters
- For CALCULATED parameters: always provide the calculation_formula showing how it is computed from other parameters. This is essential for the calculation engine.
- Extract ALL default values with context keys. Use ONLY context values explicitly stated in the document (e.g. specific fuel types: wood, charcoal, LPG). Do not invent context keys.
- Do NOT hallucinate parameters or default values not in the text"""


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

Look for context dimensions EXPLICITLY mentioned in the text:
- Fuel type options (wood, charcoal, LPG, etc.) — only include fuel types actually listed
- GWP version options (AR4, AR5, AR6) — only if the document references multiple AR versions
- Method/approach selection options
- Scale classifications — only if the methodology distinguishes them
- Leakage calculation options — only if multiple options are described
- Stove type or technology type options — only if default values vary by type

CRITICAL RULES:
- ONLY extract dimensions that are EXPLICITLY described in the provided text with specific named options
- Do NOT invent dimensions like "regional_defaults" unless the document actually lists specific regions with different default values
- Each option must be a value ACTUALLY found in the document text, not a generic placeholder
- If you are unsure whether a dimension exists, do NOT include it"""


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
    eq_source_chunks = equation_chunks[:]
    calc_param_chunks = [c for c in parameter_chunks if any(
        kw in c.get("content", "").lower()
        for kw in ["calculated", "equation", "formula", "=", "where:", "computed"]
    )]
    eq_source_chunks.extend(calc_param_chunks[:10])
    method_chunks = [c for c in chunks if c["chunk_type"] == "method_selection"]
    eq_source_chunks.extend(method_chunks)
    eq_bearing_chunks = [c for c in chunks
                         if c["chunk_type"] not in ("equations", "quantification", "parameters", "method_selection")
                         and re.search(r'(?:Eq\.|Equation)\s*[\(\[]?\s*\d', c.get("content", ""))]
    eq_source_chunks.extend(eq_bearing_chunks)

    def _eq_chunk_priority(c):
        content = c.get("content", "")
        eq_matches = len(re.findall(r'(?:Eq\.|Equation)\s*[\(\[]?\s*\d', content))
        where_matches = len(re.findall(r'(?m)Where:\s*$', content))
        return -(eq_matches * 10 + where_matches * 5)

    eq_source_chunks.sort(key=_eq_chunk_priority)

    if eq_source_chunks:
        eq_text = "\n\n---\n\n".join(c["content"][:8000] for c in eq_source_chunks)[:40000]
        try:
            result = _call_openai(
                EQUATION_EXTRACTION_PROMPT,
                f"Methodology code: {methodology_code}\n\n{eq_text}",
                response_format={"type": "json_object"},
                max_tokens=8000,
                model=PARSE_MODEL,
            )
            equations_data = json.loads(result)
            logger.info("Pass 2 (equations): Extracted %d equations for %s",
                        len(equations_data.get("equations", [])), methodology_code)
        except Exception as e:
            logger.error("Pass 2 failed for %s: %s", methodology_code, e)

    all_parameters = []
    param_batches = []
    current_batch = []
    current_batch_size = 0
    BATCH_CHAR_LIMIT = 10000

    for pc in parameter_chunks:
        pc_len = len(pc.get("content", ""))
        if current_batch and (current_batch_size + pc_len > BATCH_CHAR_LIMIT):
            param_batches.append(current_batch)
            current_batch = [pc]
            current_batch_size = pc_len
        else:
            current_batch.append(pc)
            current_batch_size += pc_len
    if current_batch:
        param_batches.append(current_batch)

    logger.info("Pass 3 (params): Processing %d parameter chunks in %d batches",
                len(parameter_chunks), len(param_batches))

    for batch_idx, batch in enumerate(param_batches):
        combined_content = "\n\n---NEXT PARAMETER---\n\n".join(
            pc["content"][:6000] for pc in batch
        )
        try:
            result = _call_openai(
                PARAMETER_EXTRACTION_PROMPT,
                f"Methodology code: {methodology_code}\n\n{combined_content}",
                response_format={"type": "json_object"},
                max_tokens=6000,
                model=PARSE_MODEL,
            )
            param_data = json.loads(result)
            params = param_data.get("parameters", [])
            all_parameters.extend(params)

            for pc in batch:
                pc["structured_data"] = param_data
            logger.info("Pass 3 (params): Batch %d/%d extracted %d parameters from %d chunks",
                        batch_idx + 1, len(param_batches), len(params), len(batch))
        except Exception as e:
            logger.error("Pass 3 batch %d failed: %s", batch_idx + 1, e)

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


def _verify_extraction_completeness(extracted):
    issues = []
    methods = (extracted.get("methods") or {}).get("calculation_methods", [])
    equations = (extracted.get("equations") or {}).get("equations", [])
    parameters = extracted.get("parameters", [])

    if not methods:
        issues.append("NO_METHODS: No calculation methods extracted")
    if not equations:
        issues.append("NO_EQUATIONS: No equations extracted")

    for method in methods:
        mid = method.get("method_id", "?")
        method_eqs = [e for e in equations if e.get("method_id") == mid]
        shared_eqs = [e for e in equations if e.get("method_id") in ("all", "shared", "")]
        total_eqs = len(method_eqs) + len(shared_eqs)
        if total_eqs == 0:
            issues.append(f"METHOD_NO_EQUATIONS: {mid} has no equations assigned")

        has_main_eq = any(
            "ER" in (e.get("output_symbol") or e.get("equation_label") or "")
            for e in method_eqs + shared_eqs
        )
        if not has_main_eq:
            issues.append(f"METHOD_NO_MAIN_EQ: {mid} has no main ER equation")

    has_leakage = any(
        "leakage" in (e.get("equation_label") or "").lower()
        or "LE" in (e.get("output_symbol") or "")
        for e in equations
    )
    if not has_leakage:
        issues.append("NO_LEAKAGE_EQ: No leakage equation found")

    calculated_params = [p for p in parameters if p.get("category") == "calculated"]
    for p in calculated_params:
        if not p.get("calculation_formula"):
            issues.append(f"CALC_NO_FORMULA: Calculated param {p.get('parameter_id', '?')} ({p.get('symbol', '?')}) has no formula")

    eq_output_symbols = set()
    for e in equations:
        sym = e.get("output_symbol")
        if sym:
            eq_output_symbols.add(sym)

    eq_input_symbols = set()
    for e in equations:
        for v in e.get("variables", []):
            sym = v.get("symbol")
            if sym:
                eq_input_symbols.add(sym)

    param_symbols = {p.get("symbol") for p in parameters if p.get("symbol")}

    undefined_inputs = eq_input_symbols - eq_output_symbols - param_symbols
    undefined_filtered = {s for s in undefined_inputs if s and len(s) > 1 and not s.startswith("SUM")}
    if undefined_filtered:
        issues.append(f"UNDEFINED_INPUTS: Equation variables not matched to parameters or other equations: {sorted(undefined_filtered)[:10]}")

    for issue in issues:
        logger.warning("Verification: %s", issue)

    return {
        "issues": issues,
        "summary": {
            "methods": len(methods),
            "equations": len(equations),
            "parameters": len(parameters),
            "calculated_params": len(calculated_params),
            "has_leakage_eq": has_leakage,
            "undefined_inputs": len(undefined_filtered),
        },
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

    verification = _verify_extraction_completeness(extracted)
    logger.info("Verification for %s: %d issues, summary=%s",
                methodology_code, len(verification["issues"]), verification["summary"])

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
        "verification": verification,
    }


def _save_backward_compatible(methodology_code, document_id, extracted):
    from carbongpt.repository.store import save_parsed_methodology

    methods_data = extracted.get("methods") or {}
    equations_data = extracted.get("equations") or {}
    parameters = extracted.get("parameters", [])
    context_dims = extracted.get("context_dimensions", [])

    calc_methods = methods_data.get("calculation_methods", [])
    equations_list = equations_data.get("equations", [])

    seen_eq_ids = set()
    unique_equations = []
    for e in equations_list:
        eq_id = e.get("equation_id", "")
        if eq_id and eq_id not in seen_eq_ids:
            seen_eq_ids.add(eq_id)
            unique_equations.append(e)
        elif not eq_id:
            unique_equations.append(e)
    equations_list = unique_equations

    shared_eqs = [e for e in equations_list if e.get("method_id") in ("all", "shared", "")]

    for method in calc_methods:
        method_id = method.get("method_id", "")
        method_eqs = [e for e in equations_list
                      if e.get("method_id") == method_id
                      and e.get("method_id") not in ("all", "shared", "")]
        if not method_eqs:
            method_eqs = [e for e in equations_list
                          if e.get("method_id") not in ("all", "shared", "")
                          and method_id in str(e.get("method_id", ""))]
        method_eqs = method_eqs + [e for e in shared_eqs if e not in method_eqs]
        method["equations"] = method_eqs

    unmatched_eqs = [e for e in equations_list
                     if e.get("method_id") not in ("all", "shared", "")
                     and not any(e in m.get("equations", []) for m in calc_methods)]
    if unmatched_eqs:
        empty_methods = [m for m in calc_methods if len(m.get("equations", [])) <= len(shared_eqs)]
        if empty_methods:
            empty_methods[0]["equations"].extend(unmatched_eqs)
        elif calc_methods:
            calc_methods[0]["equations"].extend(unmatched_eqs)

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
        "temporal_granularity": methods_data.get("temporal_granularity", ""),
        "aging_or_degradation": methods_data.get("aging_or_degradation", ""),
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
