import logging
import re
from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

STANDARD_NAME_ALIASES = {
    "gold standard": "goldstandard",
    "gs4gg": "goldstandard",
    "gs": "goldstandard",
    "verra vcs": "verra",
    "verra": "verra",
    "vcs": "verra",
    "verified carbon standard": "verra",
    "cdm": "cdm",
    "clean development mechanism": "cdm",
    "plan vivo": "planvivo",
}


def match_standard_version(detected_standard: str, detected_version: str = None) -> int | None:
    if not detected_standard:
        return None

    slug = None
    normalized = detected_standard.strip().lower()
    for alias, s in STANDARD_NAME_ALIASES.items():
        if alias in normalized:
            slug = s
            break

    if not slug:
        return None

    with get_cursor() as cur:
        cur.execute(
            "SELECT sv.id, sv.version FROM standard_versions sv "
            "JOIN standards s ON sv.standard_id = s.id "
            "WHERE s.slug = %s ORDER BY sv.version DESC",
            (slug,)
        )
        versions = cur.fetchall()

    if not versions:
        return None

    if detected_version:
        clean_ver = re.sub(r'^v', '', str(detected_version).strip(), flags=re.IGNORECASE)
        for v in versions:
            db_ver = re.sub(r'^v', '', v["version"].strip(), flags=re.IGNORECASE)
            if db_ver == clean_ver:
                return v["id"]
        for v in versions:
            db_ver = re.sub(r'^v', '', v["version"].strip(), flags=re.IGNORECASE)
            if clean_ver.startswith(db_ver) or db_ver.startswith(clean_ver):
                return v["id"]

    return versions[0]["id"]


def list_standards():
    with get_cursor() as cur:
        cur.execute("SELECT id, name, slug, description FROM standards ORDER BY name")
        return cur.fetchall()


def list_standard_versions(standard_id=None):
    with get_cursor() as cur:
        if standard_id:
            cur.execute(
                "SELECT sv.id, sv.standard_id, s.name as standard_name, sv.version, "
                "sv.effective_date, sv.status, sv.notes "
                "FROM standard_versions sv JOIN standards s ON sv.standard_id = s.id "
                "WHERE sv.standard_id = %s ORDER BY sv.version DESC",
                (standard_id,)
            )
        else:
            cur.execute(
                "SELECT sv.id, sv.standard_id, s.name as standard_name, sv.version, "
                "sv.effective_date, sv.status, sv.notes "
                "FROM standard_versions sv JOIN standards s ON sv.standard_id = s.id "
                "ORDER BY s.name, sv.version DESC"
            )
        return cur.fetchall()


def create_standard(name, slug, description=""):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO standards (name, slug, description) VALUES (%s, %s, %s) RETURNING id",
            (name, slug, description)
        )
        return cur.fetchone()["id"]


def create_standard_version(standard_id, version, effective_date=None, status="active", notes=""):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO standard_versions (standard_id, version, effective_date, status, notes) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (standard_id, version, effective_date, status, notes)
        )
        return cur.fetchone()["id"]


def create_document(standard_version_id, category, title, file_path, file_type,
                    reference_id=None, doc_version=None, file_size_bytes=None):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO documents (standard_version_id, category, title, file_path, file_type, "
            "reference_id, doc_version, file_size_bytes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (standard_version_id, category, title, file_path, file_type,
             reference_id, doc_version, file_size_bytes)
        )
        return cur.fetchone()["id"]


def update_document_detection(doc_id, auto_standard=None, auto_version=None,
                               auto_category=None, auto_applicability=None):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE documents SET auto_detected_standard = %s, auto_detected_version = %s, "
            "auto_detected_category = %s, auto_detected_applicability = %s, "
            "updated_at = NOW() WHERE id = %s",
            (auto_standard, auto_version, auto_category, auto_applicability, doc_id)
        )


def update_document_ingestion(doc_id, status, error=None, page_count=None, word_count=None):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE documents SET ingestion_status = %s, ingestion_error = %s, "
            "page_count = %s, word_count = %s, updated_at = NOW() WHERE id = %s",
            (status, error, page_count, word_count, doc_id)
        )


def update_document_metadata(doc_id, standard_version_id=None, category=None,
                              title=None, reference_id=None, doc_version=None, status=None):
    updates = []
    params = []
    if standard_version_id is not None:
        updates.append("standard_version_id = %s")
        params.append(standard_version_id)
    if category is not None:
        updates.append("category = %s")
        params.append(category)
    if title is not None:
        updates.append("title = %s")
        params.append(title)
    if reference_id is not None:
        updates.append("reference_id = %s")
        params.append(reference_id)
    if doc_version is not None:
        updates.append("doc_version = %s")
        params.append(doc_version)
    if status is not None:
        updates.append("status = %s")
        params.append(status)
    if not updates:
        return
    updates.append("updated_at = NOW()")
    params.append(doc_id)
    with get_cursor() as cur:
        cur.execute(f"UPDATE documents SET {', '.join(updates)} WHERE id = %s", params)


def list_documents(standard_version_id=None, category=None, ingestion_status=None):
    with get_cursor() as cur:
        query = (
            "SELECT d.id, d.title, d.category, d.reference_id, d.doc_version, "
            "d.file_path, d.file_type, d.file_size_bytes, d.status, "
            "d.ingestion_status, d.page_count, d.word_count, "
            "d.auto_detected_standard, d.auto_detected_version, "
            "d.auto_detected_category, d.auto_detected_applicability, "
            "d.created_at, sv.version as standard_version, s.name as standard_name "
            "FROM documents d "
            "LEFT JOIN standard_versions sv ON d.standard_version_id = sv.id "
            "LEFT JOIN standards s ON sv.standard_id = s.id "
        )
        conditions = []
        params = []
        if standard_version_id:
            conditions.append("d.standard_version_id = %s")
            params.append(standard_version_id)
        if category:
            conditions.append("d.category = %s")
            params.append(category)
        if ingestion_status:
            conditions.append("d.ingestion_status = %s")
            params.append(ingestion_status)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY d.created_at DESC"
        cur.execute(query, params)
        return cur.fetchall()


def get_document(doc_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT d.*, sv.version as standard_version, s.name as standard_name "
            "FROM documents d "
            "LEFT JOIN standard_versions sv ON d.standard_version_id = sv.id "
            "LEFT JOIN standards s ON sv.standard_id = s.id "
            "WHERE d.id = %s",
            (doc_id,)
        )
        return cur.fetchone()


def find_document_by_reference(reference_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT d.*, sv.version as standard_version, s.name as standard_name "
            "FROM documents d "
            "LEFT JOIN standard_versions sv ON d.standard_version_id = sv.id "
            "LEFT JOIN standards s ON sv.standard_id = s.id "
            "WHERE d.reference_id = %s LIMIT 1",
            (reference_id,)
        )
        return cur.fetchone()


def delete_document(doc_id):
    with get_cursor() as cur:
        cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))


def save_sections(doc_id, sections):
    with get_cursor() as cur:
        cur.execute("DELETE FROM document_sections WHERE document_id = %s", (doc_id,))
        for i, sec in enumerate(sections):
            cur.execute(
                "INSERT INTO document_sections (document_id, section_number, title, content, "
                "section_order, word_count) VALUES (%s, %s, %s, %s, %s, %s)",
                (doc_id, sec.get("number"), sec.get("title"), sec["content"],
                 i, len(sec["content"].split()))
            )


def save_chunks(doc_id, chunks):
    with get_cursor() as cur:
        cur.execute("DELETE FROM document_chunks WHERE document_id = %s", (doc_id,))
        for chunk in chunks:
            embedding = chunk.get("embedding")
            cur.execute(
                "INSERT INTO document_chunks (document_id, section_id, chunk_index, content, "
                "token_count, embedding, metadata) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (doc_id, chunk.get("section_id"), chunk["chunk_index"], chunk["content"],
                 chunk.get("token_count"), embedding, '{}')
            )


def search_chunks(query_embedding, limit=10, standard_version_id=None, category=None):
    with get_cursor() as cur:
        filter_conditions = []
        filter_params = []
        if standard_version_id:
            filter_conditions.append("d.standard_version_id = %s")
            filter_params.append(standard_version_id)
        if category:
            filter_conditions.append("d.category = %s")
            filter_params.append(category)
        where_extra = ""
        if filter_conditions:
            where_extra = "AND " + " AND ".join(filter_conditions)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        query_params = filter_params + [embedding_str, embedding_str, limit]
        cur.execute(
            f"SELECT dc.id, dc.content, dc.metadata, dc.token_count, "
            f"d.title as document_title, d.category as document_category, "
            f"s.name as standard_name, sv.version as standard_version, "
            f"dc.embedding <=> %s::vector AS distance "
            f"FROM document_chunks dc "
            f"JOIN documents d ON dc.document_id = d.id "
            f"LEFT JOIN standard_versions sv ON d.standard_version_id = sv.id "
            f"LEFT JOIN standards s ON sv.standard_id = s.id "
            f"WHERE dc.embedding IS NOT NULL {where_extra} "
            f"ORDER BY dc.embedding <=> %s::vector "
            f"LIMIT %s",
            query_params
        )
        return cur.fetchall()


def get_document_stats():
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) as total_documents,
                COUNT(*) FILTER (WHERE ingestion_status = 'completed') as ingested,
                COUNT(*) FILTER (WHERE ingestion_status = 'pending') as pending,
                COUNT(*) FILTER (WHERE ingestion_status = 'processing') as processing,
                COUNT(*) FILTER (WHERE ingestion_status = 'failed') as failed,
                COALESCE(SUM(word_count), 0) as total_words,
                COALESCE(SUM(page_count), 0) as total_pages
            FROM documents
        """)
        return cur.fetchone()

    
def get_chunk_count():
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as count FROM document_chunks WHERE embedding IS NOT NULL")
        return cur.fetchone()["count"]


def create_compliance_rule(
    rule_type, severity, title, description, conditions=None,
    standard_id=None, effective_date=None, expiry_date=None,
    source_url=None, source_description=None, status="active",
    discovered_by="manual", review_notes=None
):
    import json
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO compliance_rules (standard_id, rule_type, severity, title, "
            "description, conditions, effective_date, expiry_date, source_url, "
            "source_description, status, discovered_by, review_notes) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (standard_id, rule_type, severity, title, description,
             json.dumps(conditions or {}), effective_date, expiry_date,
             source_url, source_description, status, discovered_by, review_notes)
        )
        return cur.fetchone()["id"]


def list_compliance_rules(standard_id=None, rule_type=None, status=None, include_expired=False):
    with get_cursor() as cur:
        conditions = []
        params = []
        if standard_id:
            conditions.append("cr.standard_id = %s")
            params.append(standard_id)
        if rule_type:
            conditions.append("cr.rule_type = %s")
            params.append(rule_type)
        if status:
            conditions.append("cr.status = %s")
            params.append(status)
        if not include_expired:
            conditions.append("(cr.expiry_date IS NULL OR cr.expiry_date >= CURRENT_DATE)")
        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)
        cur.execute(
            f"SELECT cr.*, s.name as standard_name FROM compliance_rules cr "
            f"LEFT JOIN standards s ON cr.standard_id = s.id "
            f"{where} ORDER BY cr.created_at DESC",
            params
        )
        return cur.fetchall()


def get_compliance_rule(rule_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT cr.*, s.name as standard_name FROM compliance_rules cr "
            "LEFT JOIN standards s ON cr.standard_id = s.id "
            "WHERE cr.id = %s", (rule_id,)
        )
        return cur.fetchone()


def update_compliance_rule(rule_id, **kwargs):
    import json
    allowed = {
        "rule_type", "severity", "title", "description", "conditions",
        "standard_id", "effective_date", "expiry_date", "source_url",
        "source_description", "status", "review_notes"
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return
    if "conditions" in updates:
        updates["conditions"] = json.dumps(updates["conditions"])
    updates["updated_at"] = "NOW()"
    set_parts = []
    params = []
    for k, v in updates.items():
        if v == "NOW()":
            set_parts.append(f"{k} = NOW()")
        else:
            set_parts.append(f"{k} = %s")
            params.append(v)
    params.append(rule_id)
    with get_cursor() as cur:
        cur.execute(
            f"UPDATE compliance_rules SET {', '.join(set_parts)} WHERE id = %s",
            params
        )


def delete_compliance_rule(rule_id):
    with get_cursor() as cur:
        cur.execute("DELETE FROM compliance_rules WHERE id = %s", (rule_id,))


def get_active_rules_for_standard(standard_slug):
    with get_cursor() as cur:
        cur.execute(
            "SELECT cr.* FROM compliance_rules cr "
            "JOIN standards s ON cr.standard_id = s.id "
            "WHERE s.slug = %s AND cr.status = 'active' "
            "AND (cr.expiry_date IS NULL OR cr.expiry_date >= CURRENT_DATE) "
            "ORDER BY cr.severity DESC, cr.rule_type",
            (standard_slug,)
        )
        return cur.fetchall()


def check_methodology_rules(methodology_name, standard_slug):
    import json
    with get_cursor() as cur:
        cur.execute(
            "SELECT cr.* FROM compliance_rules cr "
            "JOIN standards s ON cr.standard_id = s.id "
            "WHERE s.slug = %s AND cr.status = 'active' "
            "AND cr.rule_type IN ('methodology_status', 'methodology_transition') "
            "AND (cr.expiry_date IS NULL OR cr.expiry_date >= CURRENT_DATE) "
            "ORDER BY cr.severity DESC",
            (standard_slug,)
        )
        rules = cur.fetchall()

    matches = []
    meth_lower = methodology_name.lower().strip()
    for rule in rules:
        cond = rule["conditions"] if isinstance(rule["conditions"], dict) else json.loads(rule["conditions"])
        affected = [m.lower().strip() for m in cond.get("affected_methodologies", [])]
        keywords = [k.lower().strip() for k in cond.get("keywords", [])]
        if any(a in meth_lower or meth_lower in a for a in affected):
            matches.append(rule)
        elif any(k in meth_lower for k in keywords):
            matches.append(rule)
    return matches
