import logging
from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)


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
