import json
import logging
import os
import requests
from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

MODEL = os.getenv("CARBONGPT_AI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

CRITICAL_PARAMS = [
    "fNRB",
    "num_devices",
    "num_households",
    "household_size",
    "baseline_fuel_consumption",
    "project_fuel_consumption",
    "usage_rate",
    "SFC_baseline",
    "SFC_project",
]


def add_evidence_link(project_id, target_type, target_id, source_type,
                      target_description=None, source_doc_id=None, source_chunk_id=None,
                      source_title=None, source_detail=None, page_number=None,
                      table_reference=None, quote=None, confidence=1.0):
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO evidence_links
            (project_id, target_type, target_id, target_description,
             source_type, source_doc_id, source_chunk_id, source_title,
             source_detail, page_number, table_reference, quote, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (project_id, target_type, target_id, target_description,
              source_type, source_doc_id, source_chunk_id, source_title,
              source_detail, page_number, table_reference, quote, confidence))
        return cur.fetchone()


def get_evidence_links(project_id, target_type=None, target_id=None):
    with get_cursor() as cur:
        query = "SELECT * FROM evidence_links WHERE project_id = %s"
        params = [project_id]
        if target_type:
            query += " AND target_type = %s"
            params.append(target_type)
        if target_id:
            query += " AND target_id = %s"
            params.append(target_id)
        query += " ORDER BY target_type, target_id, created_at"
        cur.execute(query, params)
        return cur.fetchall()


def delete_evidence_link(link_id):
    with get_cursor() as cur:
        cur.execute("DELETE FROM evidence_links WHERE id = %s RETURNING id", (link_id,))
        return cur.fetchone()


def verify_evidence_link(link_id, verified=True):
    with get_cursor() as cur:
        cur.execute("UPDATE evidence_links SET verified = %s WHERE id = %s RETURNING *", (verified, link_id))
        return cur.fetchone()


def get_evidence_completeness(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT pp.param_key, pp.param_name, pp.value, pp.source_type,
                   pp.validation_status,
                   COUNT(el.id) as evidence_count,
                   bool_or(el.verified) as has_verified_evidence
            FROM project_parameters pp
            LEFT JOIN evidence_links el ON el.project_id = pp.project_id
                AND el.target_type = 'parameter' AND el.target_id = pp.param_key
            WHERE pp.project_id = %s
            GROUP BY pp.id, pp.param_key, pp.param_name, pp.value,
                     pp.source_type, pp.validation_status
            ORDER BY pp.category, pp.param_key
        """, (project_id,))
        params = cur.fetchall()

        total = len(params)
        with_evidence = len([p for p in params if p["evidence_count"] > 0])
        with_verified = len([p for p in params if p["has_verified_evidence"]])
        needs_evidence = [p for p in params if p["evidence_count"] == 0 and p["value"] is not None]

        cur.execute("""
            SELECT pws.section_id, pws.section_title,
                   COUNT(el.id) as evidence_count
            FROM project_write_sessions pws
            LEFT JOIN evidence_links el ON el.project_id = pws.project_id
                AND el.target_type = 'section' AND el.target_id = pws.section_id
            WHERE pws.project_id = %s
            GROUP BY pws.id, pws.section_id, pws.section_title
            ORDER BY pws.section_id
        """, (project_id,))
        sections = cur.fetchall()

        sections_total = len(sections)
        sections_with_evidence = len([s for s in sections if s["evidence_count"] > 0])

        score = 0
        if total > 0:
            score = round(with_evidence / total * 100)

        return {
            "parameters": {
                "total": total,
                "with_evidence": with_evidence,
                "with_verified": with_verified,
                "needs_evidence": needs_evidence,
                "score": score,
            },
            "sections": {
                "total": sections_total,
                "with_evidence": sections_with_evidence,
                "details": sections,
            },
            "overall_score": score,
        }


def generate_citation_list(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT el.*, pd.file_name as doc_file_name
            FROM evidence_links el
            LEFT JOIN project_documents pd ON pd.id = el.source_doc_id
            WHERE el.project_id = %s
            ORDER BY el.target_type, el.target_id
        """, (project_id,))
        links = cur.fetchall()

        citations = []
        for i, link in enumerate(links):
            ref_num = i + 1
            title = link.get("source_title") or link.get("doc_file_name") or "Unknown source"
            detail = link.get("source_detail") or ""
            page = f", p. {link['page_number']}" if link.get("page_number") else ""
            table = f", {link['table_reference']}" if link.get("table_reference") else ""

            citation_text = f"[{ref_num}] {title}{page}{table}"
            if detail:
                citation_text += f". {detail}"

            citations.append({
                "ref_number": ref_num,
                "citation_text": citation_text,
                "target_type": link["target_type"],
                "target_id": link["target_id"],
                "target_description": link.get("target_description"),
                "quote": link.get("quote"),
                "verified": link.get("verified", False),
            })

        return citations


def auto_link_parameter_evidence(project_id, param_key, source_doc_id, source_detail=None):
    with get_cursor() as cur:
        cur.execute("""
            SELECT param_name FROM project_parameters
            WHERE project_id = %s AND param_key = %s
        """, (project_id, param_key))
        param = cur.fetchone()
        if not param:
            return None

        cur.execute("""
            SELECT file_name FROM project_documents WHERE id = %s
        """, (source_doc_id,))
        doc = cur.fetchone()

        return add_evidence_link(
            project_id=project_id,
            target_type="parameter",
            target_id=param_key,
            target_description=param["param_name"],
            source_type="project_document",
            source_doc_id=source_doc_id,
            source_title=doc["file_name"] if doc else None,
            source_detail=source_detail,
        )


def extract_parameter_evidence(project_id, doc_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM project_documents WHERE id = %s AND project_id = %s", (doc_id, project_id))
        doc = cur.fetchone()
        if not doc:
            return {"error": "Document not found", "extracted": 0}

        parsed_text = doc.get("parsed_text") or ""
        if not parsed_text.strip():
            return {"error": "Document has no parsed text", "extracted": 0}

        cur.execute("""
            SELECT param_key, param_name, value, unit
            FROM project_parameters
            WHERE project_id = %s AND param_key = ANY(%s) AND applicable_year IS NULL
        """, (project_id, CRITICAL_PARAMS))
        params = cur.fetchall()

    if not params:
        return {"error": "No critical parameters found for this project", "extracted": 0}

    param_lines = []
    for p in params:
        current = p["value"] if p["value"] is not None else "not set"
        unit = p.get("unit") or ""
        param_lines.append(f"- {p['param_key']} ({p['param_name']}): current value = {current} {unit}")

    with get_cursor() as cur:
        cur.execute("SELECT standard, methodology_code FROM user_projects WHERE id = %s", (project_id,))
        proj = cur.fetchone()
    methodology = ""
    if proj:
        methodology = f"{proj.get('standard', '')} {proj.get('methodology_code', '')}".strip()

    doc_text = parsed_text[:15000]

    system_prompt = f"""You are analyzing a document for a carbon project using methodology {methodology}.

Search ONLY for specific numeric values related to these parameters:
{chr(10).join(param_lines)}

For each value you find, return JSON array:
[
  {{
    "param_key": "fNRB",
    "extracted_value": "0.35",
    "extracted_unit": "fraction",
    "quote": "The fraction of non-renewable biomass was determined to be 0.35",
    "page_or_section": "Page 12, Section 4.2",
    "confidence": 0.9
  }}
]

Rules:
- Only extract concrete numeric values, not descriptions or ranges
- Include the exact quote from the document
- Set confidence: 0.9+ if value is clearly stated, 0.7-0.9 if inferred, <0.7 if uncertain
- Return empty array [] if no relevant values found
- Return ONLY valid JSON array, no other text"""

    user_prompt = f"Document: {doc['file_name']}\n\n{doc_text}"

    try:
        raw = _call_openai(system_prompt, user_prompt)
    except Exception as e:
        logger.error("Evidence extraction LLM call failed: %s", e)
        return {"error": f"AI extraction failed: {str(e)}", "extracted": 0}

    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        extractions = json.loads(cleaned)
        if not isinstance(extractions, list):
            extractions = []
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse extraction response: %s", raw[:200])
        return {"error": "AI returned unparseable response", "extracted": 0}

    param_map = {p["param_key"]: p for p in params}
    created = 0

    with get_cursor() as cur:
        for item in extractions:
            pk = item.get("param_key", "")
            if pk not in param_map:
                continue

            ext_value = str(item.get("extracted_value", "")).strip()
            ext_unit = str(item.get("extracted_unit", "")).strip()
            quote = str(item.get("quote", "")).strip()
            page_section = str(item.get("page_or_section", "")).strip()
            confidence = float(item.get("confidence", 0.5))

            if not ext_value:
                continue

            cur.execute("""
                INSERT INTO evidence_links
                (project_id, target_type, target_id, target_description,
                 source_type, source_doc_id, source_title, source_detail,
                 quote, confidence, extracted_value, extracted_unit,
                 param_key, evidence_type, evidence_decision)
                VALUES (%s, 'parameter', %s, %s,
                        'project_document', %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, 'parameter_value', 'pending')
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (
                project_id, pk, param_map[pk]["param_name"],
                doc_id, doc.get("file_name", ""), page_section,
                quote, confidence, ext_value, ext_unit,
                pk,
            ))
            if cur.fetchone():
                created += 1

    return {"extracted": created, "doc_id": doc_id, "doc_name": doc.get("file_name", "")}


def get_pending_evidence(project_id, doc_id=None):
    with get_cursor() as cur:
        query = """
            SELECT el.*, pd.file_name as doc_file_name,
                   pp.value as current_param_value, pp.unit as param_unit,
                   pp.param_name, pp.param_status, pp.source_type as param_source_type
            FROM evidence_links el
            LEFT JOIN project_documents pd ON pd.id = el.source_doc_id
            LEFT JOIN project_parameters pp ON pp.project_id = el.project_id
                AND pp.param_key = el.param_key AND pp.applicable_year IS NULL
            WHERE el.project_id = %s AND el.evidence_decision = 'pending'
              AND el.evidence_type = 'parameter_value'
        """
        params = [project_id]
        if doc_id:
            query += " AND el.source_doc_id = %s"
            params.append(doc_id)
        query += " ORDER BY el.param_key, el.created_at"
        cur.execute(query, params)
        return cur.fetchall()


def get_evidence_counts_by_param(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT param_key,
                   COUNT(*) FILTER (WHERE evidence_decision = 'pending') as pending,
                   COUNT(*) FILTER (WHERE evidence_decision = 'accepted') as accepted,
                   COUNT(*) FILTER (WHERE evidence_decision = 'accepted_as_reference') as reference,
                   COUNT(*) FILTER (WHERE evidence_decision = 'rejected') as rejected,
                   COUNT(*) as total
            FROM evidence_links
            WHERE project_id = %s AND evidence_type = 'parameter_value' AND param_key IS NOT NULL
            GROUP BY param_key
        """, (project_id,))
        rows = cur.fetchall()
        return {r["param_key"]: dict(r) for r in rows}


def decide_evidence(project_id, link_id, decision):
    valid_decisions = ("accepted", "accepted_as_reference", "rejected")
    if decision not in valid_decisions:
        return {"error": f"Invalid decision. Must be one of: {valid_decisions}"}

    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM evidence_links
            WHERE id = %s AND project_id = %s
            FOR UPDATE
        """, (link_id, project_id))
        link = cur.fetchone()

        if not link:
            return {"error": "Evidence link not found"}

        if link.get("evidence_decision") != "pending":
            return {"error": f"Evidence already decided: {link['evidence_decision']}"}

        pk = link.get("param_key")

        if decision == "accepted" and pk:
            cur.execute("""
                SELECT param_status, value, source_type FROM project_parameters
                WHERE project_id = %s AND param_key = %s AND applicable_year IS NULL
            """, (project_id, pk))
            param_row = cur.fetchone()

            if param_row and param_row.get("param_status") == "confirmed":
                current_val = param_row.get("value", "")
                extracted_val = link.get("extracted_value", "")
                if str(current_val).strip() != str(extracted_val).strip():
                    return {
                        "requires_confirmation": True,
                        "link_id": link_id,
                        "param_key": pk,
                        "current_value": current_val,
                        "extracted_value": extracted_val,
                        "message": f"Parameter '{pk}' is already confirmed with value '{current_val}'. Accepting will overwrite with '{extracted_val}'.",
                    }

            _apply_accepted_evidence(cur, project_id, pk, link_id, link)

        cur.execute("""
            UPDATE evidence_links SET evidence_decision = %s
            WHERE id = %s AND project_id = %s AND evidence_decision = 'pending'
            RETURNING *
        """, (decision, link_id, project_id))
        updated = cur.fetchone()

        if not updated:
            return {"error": "Evidence was already decided by another action"}

    return {"success": True, "evidence": updated, "decision": decision}


def decide_evidence_force(project_id, link_id, decision):
    valid_decisions = ("accepted", "accepted_as_reference", "rejected")
    if decision not in valid_decisions:
        return {"error": f"Invalid decision. Must be one of: {valid_decisions}"}

    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM evidence_links
            WHERE id = %s AND project_id = %s
            FOR UPDATE
        """, (link_id, project_id))
        link = cur.fetchone()

        if not link:
            return {"error": "Evidence link not found"}

        if link.get("evidence_decision") not in ("pending",):
            return {"error": f"Evidence already decided: {link['evidence_decision']}"}

        pk = link.get("param_key")

        if decision == "accepted" and pk:
            _apply_accepted_evidence(cur, project_id, pk, link_id, link)

        cur.execute("""
            UPDATE evidence_links SET evidence_decision = %s
            WHERE id = %s AND project_id = %s AND evidence_decision = 'pending'
            RETURNING *
        """, (decision, link_id, project_id))
        updated = cur.fetchone()

        if not updated:
            return {"error": "Evidence was already decided by another action"}

    return {"success": True, "evidence": updated, "decision": decision}


def _apply_accepted_evidence(cur, project_id, param_key, link_id, link):
    cur.execute("""
        UPDATE evidence_links SET evidence_decision = 'superseded'
        WHERE project_id = %s AND param_key = %s AND evidence_decision = 'accepted'
          AND id != %s
    """, (project_id, param_key, link_id))

    cur.execute("""
        UPDATE project_parameters
        SET value = %s, source_type = 'document_extracted',
            source_reference = %s, param_status = 'confirmed', updated_at = NOW()
        WHERE project_id = %s AND param_key = %s AND applicable_year IS NULL
    """, (
        link.get("extracted_value"),
        f"Document: {link.get('source_title', '')} - {link.get('source_detail', '')}",
        project_id, param_key,
    ))


def get_evidence_decision_summary(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE evidence_decision = 'pending') as pending,
                COUNT(*) FILTER (WHERE evidence_decision = 'accepted') as accepted,
                COUNT(*) FILTER (WHERE evidence_decision = 'accepted_as_reference') as reference,
                COUNT(*) FILTER (WHERE evidence_decision = 'rejected') as rejected,
                COUNT(*) FILTER (WHERE evidence_decision = 'superseded') as superseded,
                COUNT(*) as total
            FROM evidence_links
            WHERE project_id = %s AND evidence_type = 'parameter_value'
        """, (project_id,))
        row = cur.fetchone()
        if not row:
            return {"pending": 0, "accepted": 0, "reference": 0, "rejected": 0, "superseded": 0, "total": 0}
        return dict(row)


def _call_openai(system_prompt, user_prompt):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 4000,
        "temperature": 0.1,
    }
    resp = requests.post(
        OPENAI_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
