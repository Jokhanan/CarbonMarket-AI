import json
import logging
import os
import re
import requests

from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

MODEL = os.getenv("CARBONGPT_AI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

FINDINGS_EXTRACTION_PROMPT = """You are an expert carbon credit auditor analyzing a Verification or Validation Report from a VVB (Validation/Verification Body).

Extract ALL audit findings from the text below. Findings include:
- CAR (Corrective Action Request): A material non-conformity that must be corrected
- CL (Clarification): A request for additional information or explanation
- FAR (Forward Action Request): An action required for future monitoring/verification periods
- OBS (Observation): A non-binding recommendation or minor observation

For each finding, return a JSON object with these fields:
{
  "finding_type": "CAR" | "CL" | "FAR" | "OBS",
  "finding_id": "the finding's ID/number as stated in the report (e.g., 'CAR 01', 'CL-03')",
  "severity": "major" | "minor" | "observation",
  "pdd_section": "the PDD/MR section this finding relates to (e.g., 'B.6.3', 'Section 3.1', 'Monitoring')",
  "topic": "short topic label (e.g., 'Baseline emission factor', 'Sampling methodology', 'Additionality')",
  "description": "the finding description as stated by the VVB",
  "resolution": "the project developer's response or resolution, if provided in the text",
  "methodology_code": "the methodology code if identifiable (e.g., 'ACM0002', 'VM0050', 'AMS-I.D.')"
}

RULES:
- Extract ONLY actual audit findings — formal CARs, CLs, FARs, and observations issued by the VVB.
- Do NOT fabricate findings. If the text contains no findings, return an empty array [].
- The "description" must closely follow the VVB's stated text, not be invented.
- If the finding ID is not stated, use "unknown".
- If pdd_section is not identifiable, use "general".
- If methodology_code is not identifiable from the text, use null.
- Set severity: "major" for CARs about material issues, "minor" for procedural CARs and CLs, "observation" for FARs and OBS.
- Return ONLY a valid JSON array, no other text."""

METADATA_PROMPT = """Based on this document text from a carbon project validation/verification report, identify:
1. methodology_code: The methodology used (e.g., "VM0050", "ACM0002", "AMS-I.D.", "AMS-II.G")
2. standard: "Verra" or "GoldStandard"
3. vvb_name: Name of the VVB/auditor organization
4. project_id: The VCS or GS project ID number
5. project_name: The project name
6. doc_type: "validation_report" or "verification_report"

Return as JSON object. Use null for any field you cannot determine.

Document text (first 3000 chars):
"""


def _call_llm(system_prompt, user_prompt, temperature=0):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = requests.post(
            OPENAI_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return None


def _parse_json_response(raw):
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            if "findings" in parsed:
                return parsed["findings"]
            return [parsed]
    except (json.JSONDecodeError, ValueError):
        return []
    return []


def _normalize_text(text):
    text = (text or "").lower().strip()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _word_set(text):
    return set(_normalize_text(text).split())


def _word_overlap(a, b):
    sa = _word_set(a)
    sb = _word_set(b)
    if not sa or not sb:
        return 0.0
    intersection = sa & sb
    smaller = min(len(sa), len(sb))
    return len(intersection) / smaller if smaller > 0 else 0.0


def _sections_nearby(sec_a, sec_b):
    a = _normalize_text(sec_a)
    b = _normalize_text(sec_b)
    if a == b:
        return True
    if a == "general" or b == "general":
        return False
    num_a = re.findall(r'[\d]+(?:\.[\d]+)*', a)
    num_b = re.findall(r'[\d]+(?:\.[\d]+)*', b)
    if num_a and num_b:
        return num_a[0].split('.')[0] == num_b[0].split('.')[0]
    return _word_overlap(a, b) > 0.6


def _merge_finding(existing, new_f):
    if len(new_f.get("description", "")) > len(existing.get("description", "")):
        existing["description"] = new_f["description"]
    if new_f.get("resolution") and not existing.get("resolution"):
        existing["resolution"] = new_f["resolution"]
    if new_f.get("finding_id", "unknown") != "unknown" and existing.get("finding_id", "unknown") == "unknown":
        existing["finding_id"] = new_f["finding_id"]
    if new_f.get("pdd_section", "general") != "general" and existing.get("pdd_section", "general") == "general":
        existing["pdd_section"] = new_f["pdd_section"]


def _deduplicate_findings(findings):
    seen = {}
    for f in findings:
        ftype = f.get("finding_type", "")
        fid = f.get("finding_id", "")
        desc = (f.get("description") or "")[:100].lower().strip()
        topic = (f.get("topic") or "").lower().strip()

        if fid and fid != "unknown":
            key = (ftype, fid)
        else:
            key = (ftype, topic, desc[:60])

        if key not in seen:
            seen[key] = f
        else:
            _merge_finding(seen[key], f)

    kept = list(seen.values())

    merged = True
    while merged:
        merged = False
        result = []
        used = set()
        for i, a in enumerate(kept):
            if i in used:
                continue
            for j in range(i + 1, len(kept)):
                if j in used:
                    continue
                b = kept[j]
                if a.get("finding_type") != b.get("finding_type"):
                    continue
                a_fid = a.get("finding_id", "unknown")
                b_fid = b.get("finding_id", "unknown")
                if (a_fid != "unknown" and b_fid != "unknown"
                        and a_fid != b_fid):
                    continue
                desc_sim = _word_overlap(
                    a.get("description", ""), b.get("description", "")
                )
                topic_sim = _word_overlap(
                    a.get("topic", ""), b.get("topic", "")
                )
                sec_a = a.get("pdd_section", "general")
                sec_b = b.get("pdd_section", "general")
                same_section = _sections_nearby(sec_a, sec_b)

                is_dup = False
                if desc_sim >= 0.85 and same_section:
                    is_dup = True
                elif desc_sim >= 0.80 and topic_sim >= 0.60 and same_section:
                    is_dup = True
                elif desc_sim >= 0.92 and topic_sim >= 0.75 and same_section:
                    is_dup = True

                if is_dup:
                    _merge_finding(a, b)
                    used.add(j)
                    merged = True
            result.append(a)
        kept = result

    return kept


def extract_findings_from_chunks(doc_id):
    with get_cursor() as cur:
        cur.execute("SELECT id, category, title FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            return {"error": "Document not found", "doc_id": doc_id}

        cur.execute(
            "SELECT content FROM document_chunks WHERE document_id = %s ORDER BY chunk_index",
            (doc_id,),
        )
        chunks = [r["content"] for r in cur.fetchall()]

    if not chunks:
        return {"error": "No chunks found", "doc_id": doc_id}

    header_text = "\n".join(chunks[:3])[:3000]
    meta_raw = _call_llm(
        "You extract metadata from carbon project documents. Return valid JSON only.",
        METADATA_PROMPT + header_text,
    )
    metadata = {}
    if meta_raw:
        try:
            metadata = json.loads(meta_raw.strip().lstrip("```json").rstrip("```").strip())
        except (json.JSONDecodeError, ValueError):
            pass
    llm_calls = 1

    GROUP_SIZE = 25000
    chunk_groups = []
    group = []
    group_len = 0
    for chunk in chunks:
        clen = len(chunk)
        if group_len + clen > GROUP_SIZE and group:
            chunk_groups.append(group)
            group = [chunk]
            group_len = clen
        else:
            group.append(chunk)
            group_len += clen
    if group:
        chunk_groups.append(group)

    all_findings = []
    for gi, grp in enumerate(chunk_groups):
        combined_text = "\n\n---\n\n".join(grp)
        user_prompt = (
            f"Document: {doc['title']}\n"
            f"Section group {gi + 1}/{len(chunk_groups)}\n\n"
            f"{combined_text}"
        )
        raw = _call_llm(FINDINGS_EXTRACTION_PROMPT, user_prompt)
        llm_calls += 1
        parsed = _parse_json_response(raw)
        all_findings.extend(parsed)

    deduped = _deduplicate_findings(all_findings)

    stored = 0
    with get_cursor() as cur:
        for f in deduped:
            finding_type = f.get("finding_type", "CL")
            if finding_type == "OBS":
                finding_type = "observation"
            if finding_type not in ("CAR", "CL", "FAR", "observation", "comment", "prr_comment"):
                finding_type = "observation"

            severity_map = {"major": "critical", "minor": "medium", "observation": "low"}
            severity_raw = f.get("severity", "medium")
            severity = severity_map.get(severity_raw, severity_raw)
            if severity not in ("critical", "high", "medium", "low", "info"):
                severity = "medium"

            try:
                cur.execute("""
                    INSERT INTO findings_knowledge
                    (source_document_id, finding_type, severity, pdd_section, topic,
                     description, resolution, methodology_code, extraction_method, confidence,
                     doc_type, vvb_name, source_project_id, source_project_name, structured_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    doc_id,
                    finding_type,
                    severity,
                    f.get("pdd_section", "general"),
                    f.get("topic", ""),
                    f.get("description", ""),
                    f.get("resolution"),
                    f.get("methodology_code") or metadata.get("methodology_code"),
                    "ai_assisted",
                    0.8,
                    metadata.get("doc_type", doc["category"]),
                    metadata.get("vvb_name"),
                    str(metadata.get("project_id", "")) or None,
                    metadata.get("project_name"),
                    json.dumps({"finding_id": f.get("finding_id", "unknown")}),
                ))
                stored += 1
            except Exception as e:
                logger.error("Failed to store finding: %s", e)

    return {
        "doc_id": doc_id,
        "doc_title": doc["title"],
        "doc_category": doc["category"],
        "chunk_count": len(chunks),
        "chunk_groups": len(chunk_groups),
        "llm_calls": llm_calls,
        "metadata_detected": metadata,
        "raw_findings": len(all_findings),
        "deduped_findings": len(deduped),
        "stored": stored,
        "findings": deduped,
    }


SECTION_TOPIC_MAP = {
    "project_description": ["project description", "project design", "project activity", "technology"],
    "baseline": ["baseline", "baseline scenario", "baseline emissions", "common practice"],
    "additionality": ["additionality", "barrier analysis", "investment analysis", "common practice"],
    "monitoring": ["monitoring", "monitoring plan", "monitoring parameters", "data quality", "QA/QC", "sampling"],
    "emission_reductions": ["emission reductions", "emission calculations", "quantification", "ERs", "calculation"],
    "stakeholder": ["stakeholder", "stakeholder engagement", "consultation", "grievance"],
    "safeguards": ["safeguards", "environmental impact", "social impact", "no net harm", "do no harm"],
    "eligibility": ["eligibility", "applicability", "project boundary", "scope"],
    "crediting_period": ["crediting period", "start date", "project start"],
    "methodology": ["methodology", "methodology deviation", "methodology application"],
    "leakage": ["leakage", "leakage emissions"],
    "sdg": ["sustainable development", "SDG", "co-benefits"],
    "double_counting": ["double counting", "double claim", "other programs", "registry"],
    "ownership": ["ownership", "right of use", "project proponent"],
    "sampling": ["sampling", "sample size", "confidence interval", "statistical"],
    "data_management": ["data management", "data quality", "calibration", "measurement"],
    "fnrb": ["fNRB", "non-renewable biomass", "fraction of non-renewable"],
    "wbt": ["WBT", "water boiling test", "thermal efficiency", "boiling test"],
    "stove_distribution": ["distribution", "stove distribution", "device distribution", "tracking"],
}


def _derive_section_keywords(section_title):
    title_lower = section_title.lower()
    keywords = set()
    for category, terms in SECTION_TOPIC_MAP.items():
        for term in terms:
            if term.lower() in title_lower:
                keywords.update(terms)
                break

    if not keywords:
        words = re.split(r'[\s/,\-]+', title_lower)
        keywords = {w for w in words if len(w) > 3}

    return list(keywords)[:5]


def get_findings_context_for_section(methodology_code, section_title):
    keywords = _derive_section_keywords(section_title)
    if not keywords:
        return ""

    with get_cursor() as cur:
        cur.execute("""
            SELECT finding_type, severity, pdd_section, topic, description, resolution
            FROM findings_knowledge
            WHERE methodology_code = %s
            AND (topic ILIKE ANY(%s) OR pdd_section ILIKE ANY(%s))
            ORDER BY finding_type, severity
            LIMIT 8
        """, (methodology_code,
              [f"%{k}%" for k in keywords],
              [f"%{k}%" for k in keywords]))
        findings = cur.fetchall()

    if not findings:
        return ""

    lines = [f"### Common VVB findings for this section (from {len(findings)} past audits):"]
    lines.append("The following issues have been raised by VVBs on similar projects. Address these proactively:\n")
    for f in findings:
        ftype = f.get("finding_type", "CL")
        topic = f.get("topic", "")
        desc = (f.get("description") or "")[:300]
        severity = f.get("severity", "minor")
        lines.append(f"- [{ftype}] ({severity}) {topic}: {desc}")
        resolution = f.get("resolution")
        if resolution:
            lines.append(f"  Resolution: {resolution[:200]}")
        lines.append("")
    return "\n".join(lines)


def get_findings_review_context(methodology_code):
    with get_cursor() as cur:
        cur.execute("""
            SELECT finding_type, severity, pdd_section, topic, description
            FROM findings_knowledge
            WHERE methodology_code = %s
            ORDER BY finding_type, topic
            LIMIT 30
        """, (methodology_code,))
        findings = cur.fetchall()

    if not findings:
        return ""

    by_topic = {}
    for f in findings:
        topic = f.get("topic", "general")
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(f)

    lines = ["### Known VVB findings patterns for this methodology:"]
    lines.append("Based on analysis of past validation/verification reports, VVBs commonly raise these issues:\n")
    for topic, topic_findings in sorted(by_topic.items(), key=lambda x: -len(x[1])):
        car_count = sum(1 for f in topic_findings if f["finding_type"] == "CAR")
        cl_count = sum(1 for f in topic_findings if f["finding_type"] == "CL")
        lines.append(f"**{topic}** ({len(topic_findings)} findings: {car_count} CARs, {cl_count} CLs)")
        for f in topic_findings[:2]:
            desc = (f.get("description") or "")[:200]
            lines.append(f"  - {f['finding_type']}: {desc}")
        lines.append("")
    return "\n".join(lines)[:4000]
