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
            "d.created_at, sv.version as standard_version, s.name as standard_name, "
            "(SELECT COUNT(*) FROM document_sections ds WHERE ds.document_id = d.id) as section_count, "
            "(SELECT COUNT(*) FROM document_chunks dc WHERE dc.document_id = d.id) as chunk_count "
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
        section_ids = []
        for i, sec in enumerate(sections):
            number = sec.get("number")
            title = sec.get("title", "")
            section_path = f"{number} {title}".strip() if number else title
            cur.execute(
                "INSERT INTO document_sections (document_id, section_number, title, content, "
                "section_order, word_count, section_path) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (doc_id, number, title, sec["content"],
                 i, len(sec["content"].split()), section_path)
            )
            row = cur.fetchone()
            section_ids.append(row["id"] if row else None)
        return section_ids


def get_document_sections(doc_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, document_id, section_number, title, content, section_order, word_count "
            "FROM document_sections WHERE document_id = %s ORDER BY section_order",
            (doc_id,)
        )
        return cur.fetchall()


def save_chunks(doc_id, chunks):
    import json
    with get_cursor() as cur:
        cur.execute("DELETE FROM document_chunks WHERE document_id = %s", (doc_id,))
        for chunk in chunks:
            embedding = chunk.get("embedding")
            metadata = chunk.get("metadata", {})
            metadata_json = json.dumps(metadata) if isinstance(metadata, dict) else metadata
            cur.execute(
                "INSERT INTO document_chunks (document_id, section_id, chunk_index, content, "
                "token_count, embedding, metadata, search_vector) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, to_tsvector('english', %s))",
                (doc_id, chunk.get("section_id"), chunk["chunk_index"], chunk["content"],
                 chunk.get("token_count"), embedding, metadata_json, chunk["content"])
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


def full_text_search(query_text, limit=10, standard_version_id=None, category=None):
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
        ts_query = " & ".join(w for w in query_text.split() if len(w) > 1)
        if not ts_query:
            return []
        filter_params.extend([ts_query, ts_query, limit])
        cur.execute(
            f"SELECT dc.id, dc.content, dc.metadata, dc.token_count, "
            f"d.title as document_title, d.category as document_category, "
            f"s.name as standard_name, sv.version as standard_version, "
            f"ts_rank(COALESCE(dc.search_vector, to_tsvector('english', dc.content)), to_tsquery('english', %s)) AS rank "
            f"FROM document_chunks dc "
            f"JOIN documents d ON dc.document_id = d.id "
            f"LEFT JOIN standard_versions sv ON d.standard_version_id = sv.id "
            f"LEFT JOIN standards s ON sv.standard_id = s.id "
            f"WHERE COALESCE(dc.search_vector, to_tsvector('english', dc.content)) @@ to_tsquery('english', %s) {where_extra} "
            f"ORDER BY rank DESC "
            f"LIMIT %s",
            filter_params
        )
        return cur.fetchall()


def hybrid_search(query_text, query_embedding=None, limit=10,
                  standard_version_id=None, category=None,
                  semantic_weight=0.7, keyword_weight=0.3):
    if query_embedding is not None:
        semantic_results = search_chunks(
            query_embedding, limit=limit * 2,
            standard_version_id=standard_version_id, category=category,
        )
    else:
        semantic_results = []
        semantic_weight = 0.0
        keyword_weight = 1.0

    keyword_results = full_text_search(
        query_text, limit=limit * 2,
        standard_version_id=standard_version_id, category=category,
    )

    scored = {}
    if semantic_results:
        max_dist = max(r.get("distance", 1.0) for r in semantic_results) or 1.0
        for r in semantic_results:
            dist = r.get("distance", 1.0)
            sem_score = max(0, 1 - dist / max_dist) if max_dist > 0 else 0
            scored[r["id"]] = {
                **r,
                "semantic_score": sem_score,
                "keyword_score": 0,
            }

    if keyword_results:
        max_rank = max(r.get("rank", 0) for r in keyword_results) or 1.0
        for r in keyword_results:
            rank = r.get("rank", 0)
            kw_score = rank / max_rank if max_rank > 0 else 0
            if r["id"] in scored:
                scored[r["id"]]["keyword_score"] = kw_score
            else:
                scored[r["id"]] = {
                    **r,
                    "semantic_score": 0,
                    "keyword_score": kw_score,
                }

    for item in scored.values():
        item["combined_score"] = (
            semantic_weight * item["semantic_score"]
            + keyword_weight * item["keyword_score"]
        )

    ranked = sorted(scored.values(), key=lambda x: x["combined_score"], reverse=True)
    return ranked[:limit]


def update_document_summary(doc_id, summary):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE documents SET summary = %s, updated_at = NOW() WHERE id = %s",
            (summary, doc_id)
        )


def update_search_vector(doc_id):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE documents SET search_vector = ("
            "  setweight(to_tsvector('english', COALESCE(title, '')), 'A') || "
            "  setweight(to_tsvector('english', COALESCE(summary, '')), 'B') || "
            "  setweight(to_tsvector('english', COALESCE(reference_id, '')), 'A') || "
            "  setweight(to_tsvector('english', COALESCE(auto_detected_applicability, '')), 'C')"
            ") WHERE id = %s",
            (doc_id,)
        )


def search_documents_fts(query_text, limit=20, standard_version_id=None, category=None):
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
        ts_query = " & ".join(w for w in query_text.split() if len(w) > 1)
        if not ts_query:
            return []
        filter_params.extend([ts_query, ts_query, limit])
        cur.execute(
            f"SELECT d.id, d.title, d.category, d.reference_id, d.summary, "
            f"d.word_count, d.page_count, d.ingestion_status, "
            f"s.name as standard_name, sv.version as standard_version, "
            f"ts_rank(d.search_vector, to_tsquery('english', %s)) AS rank "
            f"FROM documents d "
            f"LEFT JOIN standard_versions sv ON d.standard_version_id = sv.id "
            f"LEFT JOIN standards s ON sv.standard_id = s.id "
            f"WHERE d.search_vector @@ to_tsquery('english', %s) {where_extra} "
            f"ORDER BY rank DESC "
            f"LIMIT %s",
            filter_params
        )
        return cur.fetchall()


def get_section_ids_for_document(doc_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, section_number, title, section_order, section_path "
            "FROM document_sections WHERE document_id = %s ORDER BY section_order",
            (doc_id,)
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


def upsert_carbon_project(data):
    import json
    from carbongpt.repository.registry_normalizer import resolve_registry_id
    ref_registry_id = resolve_registry_id(data.get("registry"))
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO carbon_projects
            (registry, registry_id, name, status, country, region, proponent,
             methodology, project_type, project_subtype, estimated_annual_credits,
             crediting_period_start, crediting_period_end, registration_date,
             latitude, longitude, description, sdgs, extra_data, synced_at,
             ref_registry_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)
            ON CONFLICT (registry, registry_id) DO UPDATE SET
             name = EXCLUDED.name,
             status = EXCLUDED.status,
             country = EXCLUDED.country,
             region = EXCLUDED.region,
             proponent = EXCLUDED.proponent,
             methodology = EXCLUDED.methodology,
             project_type = EXCLUDED.project_type,
             project_subtype = EXCLUDED.project_subtype,
             estimated_annual_credits = EXCLUDED.estimated_annual_credits,
             crediting_period_start = EXCLUDED.crediting_period_start,
             crediting_period_end = EXCLUDED.crediting_period_end,
             registration_date = EXCLUDED.registration_date,
             latitude = EXCLUDED.latitude,
             longitude = EXCLUDED.longitude,
             description = EXCLUDED.description,
             sdgs = EXCLUDED.sdgs,
             extra_data = EXCLUDED.extra_data,
             synced_at = NOW(),
             ref_registry_id = EXCLUDED.ref_registry_id
            RETURNING id""",
            (
                data["registry"], data["registry_id"], data["name"],
                data.get("status"), data.get("country"), data.get("region"),
                data.get("proponent"), data.get("methodology"),
                data.get("project_type"), data.get("project_subtype"),
                data.get("estimated_annual_credits"),
                data.get("crediting_period_start"), data.get("crediting_period_end"),
                data.get("registration_date"),
                data.get("latitude"), data.get("longitude"),
                data.get("description"), data.get("sdgs"),
                json.dumps(data.get("extra_data") or {}),
                ref_registry_id,
            )
        )
        return cur.fetchone()["id"]


def list_carbon_projects(registry=None, country=None, status=None,
                         project_type=None, methodology=None,
                         limit=100, offset=0):
    with get_cursor() as cur:
        conditions = []
        params = []
        if registry:
            conditions.append("registry = %s")
            params.append(registry)
        if country:
            conditions.append("country = %s")
            params.append(country)
        if status:
            conditions.append("status = %s")
            params.append(status)
        if project_type:
            conditions.append("project_type = %s")
            params.append(project_type)
        if methodology:
            conditions.append("methodology ILIKE %s")
            params.append(f"%{methodology}%")
        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)
        params.extend([limit, offset])
        cur.execute(
            f"SELECT * FROM carbon_projects {where} "
            f"ORDER BY estimated_annual_credits DESC NULLS LAST, name "
            f"LIMIT %s OFFSET %s",
            params
        )
        return cur.fetchall()


def get_project_count(registry=None):
    with get_cursor() as cur:
        if registry:
            cur.execute("SELECT COUNT(*) as count FROM carbon_projects WHERE registry = %s", (registry,))
        else:
            cur.execute("SELECT COUNT(*) as count FROM carbon_projects")
        return cur.fetchone()["count"]


def get_project_analytics():
    with get_cursor() as cur:
        result = {}

        cur.execute("""
            SELECT country, COUNT(*) as project_count,
                   COALESCE(SUM(estimated_annual_credits), 0) as total_credits
            FROM carbon_projects
            WHERE country IS NOT NULL AND country != ''
            GROUP BY country
            ORDER BY project_count DESC
        """)
        result["by_country"] = cur.fetchall()

        cur.execute("""
            SELECT region, COUNT(*) as project_count,
                   COALESCE(SUM(estimated_annual_credits), 0) as total_credits
            FROM carbon_projects
            WHERE region IS NOT NULL AND region != ''
            GROUP BY region
            ORDER BY project_count DESC
        """)
        result["by_region"] = cur.fetchall()

        cur.execute("""
            SELECT status, COUNT(*) as project_count
            FROM carbon_projects
            WHERE status IS NOT NULL
            GROUP BY status
            ORDER BY project_count DESC
        """)
        result["by_status"] = cur.fetchall()

        cur.execute("""
            SELECT project_type, COUNT(*) as project_count,
                   COALESCE(SUM(estimated_annual_credits), 0) as total_credits
            FROM carbon_projects
            WHERE project_type IS NOT NULL AND project_type != ''
            GROUP BY project_type
            ORDER BY project_count DESC
        """)
        result["by_project_type"] = cur.fetchall()

        cur.execute("""
            SELECT
                cp.registry                                         AS registry,
                cp.ref_registry_id                                  AS ref_registry_id,
                COALESCE(rr.registry_short, cp.registry)            AS registry_display,
                COALESCE(rr.registry_name,  cp.registry)            AS registry_name,
                COUNT(*)                                            AS project_count,
                COALESCE(SUM(cp.estimated_annual_credits), 0)       AS total_credits
            FROM carbon_projects cp
            LEFT JOIN ref_registries rr ON cp.ref_registry_id = rr.registry_id
            GROUP BY cp.registry, cp.ref_registry_id, rr.registry_short, rr.registry_name
            ORDER BY project_count DESC
        """)
        result["by_registry"] = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) as total_projects,
                   COUNT(DISTINCT country) as total_countries,
                   COALESCE(SUM(estimated_annual_credits), 0) as total_estimated_credits,
                   COUNT(DISTINCT registry) as total_registries,
                   MAX(synced_at) as last_sync
            FROM carbon_projects
        """)
        result["summary"] = cur.fetchone()

        return result


def get_top_methodologies(limit=20):
    with get_cursor() as cur:
        cur.execute("""
            SELECT methodology, COUNT(*) as project_count,
                   COALESCE(SUM(estimated_annual_credits), 0) as total_credits
            FROM carbon_projects
            WHERE methodology IS NOT NULL AND methodology != ''
            GROUP BY methodology
            ORDER BY project_count DESC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()


def get_country_details(country):
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM carbon_projects
            WHERE country = %s
            ORDER BY estimated_annual_credits DESC NULLS LAST
        """, (country,))
        projects = cur.fetchall()

        cur.execute("""
            SELECT methodology, COUNT(*) as count,
                   COALESCE(SUM(estimated_annual_credits), 0) as credits
            FROM carbon_projects
            WHERE country = %s AND methodology IS NOT NULL
            GROUP BY methodology ORDER BY count DESC
        """, (country,))
        methodologies = cur.fetchall()

        cur.execute("""
            SELECT proponent, COUNT(*) as count
            FROM carbon_projects
            WHERE country = %s AND proponent IS NOT NULL
            GROUP BY proponent ORDER BY count DESC LIMIT 20
        """, (country,))
        developers = cur.fetchall()

        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM carbon_projects
            WHERE country = %s
            GROUP BY status ORDER BY count DESC
        """, (country,))
        statuses = cur.fetchall()

        return {
            "projects": projects,
            "methodologies": methodologies,
            "developers": developers,
            "statuses": statuses,
            "total": len(projects),
        }


def search_carbon_projects(query_text, limit=50):
    with get_cursor() as cur:
        like_pattern = f"%{query_text}%"
        cur.execute(
            "SELECT * FROM carbon_projects "
            "WHERE name ILIKE %s OR proponent ILIKE %s OR methodology ILIKE %s OR country ILIKE %s "
            "ORDER BY estimated_annual_credits DESC NULLS LAST "
            "LIMIT %s",
            (like_pattern, like_pattern, like_pattern, like_pattern, limit)
        )
        return cur.fetchall()


def upsert_methodology(code, name=None, standard=None, category=None, sector=None,
                       status="active", applicability=None, description=None,
                       source_url=None, superseded_by=None, project_count=0):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO methodologies (code, name, standard, category, sector, status,
               applicability, description, source_url, superseded_by, project_count)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (code) DO UPDATE SET
               name = COALESCE(EXCLUDED.name, methodologies.name),
               standard = COALESCE(EXCLUDED.standard, methodologies.standard),
               category = COALESCE(EXCLUDED.category, methodologies.category),
               sector = COALESCE(EXCLUDED.sector, methodologies.sector),
               status = COALESCE(EXCLUDED.status, methodologies.status),
               applicability = COALESCE(EXCLUDED.applicability, methodologies.applicability),
               description = COALESCE(EXCLUDED.description, methodologies.description),
               source_url = COALESCE(EXCLUDED.source_url, methodologies.source_url),
               superseded_by = COALESCE(EXCLUDED.superseded_by, methodologies.superseded_by),
               project_count = GREATEST(EXCLUDED.project_count, methodologies.project_count),
               updated_at = NOW()
               RETURNING id""",
            (code, name, standard, category, sector, status, applicability,
             description, source_url, superseded_by, project_count)
        )
        return cur.fetchone()["id"]


def list_methodologies(standard=None, category=None, status=None, search=None, limit=200):
    with get_cursor() as cur:
        conditions = []
        params = []
        if standard:
            conditions.append("standard = %s")
            params.append(standard)
        if category:
            conditions.append("category = %s")
            params.append(category)
        if status:
            conditions.append("status = %s")
            params.append(status)
        if search:
            conditions.append("(code ILIKE %s OR name ILIKE %s OR description ILIKE %s OR applicability ILIKE %s OR sector ILIKE %s)")
            like = f"%{search}%"
            params.extend([like, like, like, like, like])
        where = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)
        cur.execute(
            f"SELECT * FROM methodologies WHERE {where} ORDER BY code LIMIT %s",
            params
        )
        return cur.fetchall()


def get_methodology(code):
    import re as _re
    with get_cursor() as cur:
        cur.execute("SELECT * FROM methodologies WHERE code = %s", (code,))
        row = cur.fetchone()
        if row:
            return row
        normalized = code.strip()
        normalized = _re.sub(r'\s+[Vv]?\d+(\.\d+)?$', '', normalized)
        cur.execute("SELECT * FROM methodologies WHERE code = %s", (normalized,))
        row = cur.fetchone()
        if row:
            return row
        cur.execute("SELECT * FROM methodologies WHERE code ILIKE %s LIMIT 1", (f"%{normalized}%",))
        return cur.fetchone()


def save_parsed_methodology(methodology_code, parsed_data, document_id=None, model_used=None, status="completed", error=None):
    import json as _json
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO methodology_parsed
                (methodology_code, document_id, parsed_data, model_used, parse_status, parse_error, parsed_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (methodology_code) DO UPDATE SET
                document_id = EXCLUDED.document_id,
                parsed_data = EXCLUDED.parsed_data,
                model_used = EXCLUDED.model_used,
                parse_status = EXCLUDED.parse_status,
                parse_error = EXCLUDED.parse_error,
                parsed_at = NOW()
            RETURNING id
        """, (methodology_code, document_id, _json.dumps(parsed_data), model_used, status, error))
        return cur.fetchone()["id"]


def get_parsed_methodology(methodology_code):
    import re
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM methodology_parsed WHERE methodology_code = %s AND parse_status = 'completed' ORDER BY parsed_at DESC LIMIT 1",
            (methodology_code,)
        )
        row = cur.fetchone()
        if row:
            return row

        normalized = methodology_code.strip()
        normalized = re.sub(r'\s+[Vv]?\d+(\.\d+)?$', '', normalized)
        normalized = normalized.replace("GS-", "").replace("gs-", "")
        cur.execute(
            "SELECT * FROM methodology_parsed WHERE methodology_code ILIKE %s AND parse_status = 'completed' ORDER BY parsed_at DESC LIMIT 1",
            (f"%{normalized}%",)
        )
        return cur.fetchone()


def list_parsed_methodologies():
    with get_cursor() as cur:
        cur.execute("""
            SELECT mp.id, mp.methodology_code, mp.document_id, mp.model_used,
                   mp.parse_status, mp.parse_error, mp.parsed_at,
                   d.title as document_title
            FROM methodology_parsed mp
            LEFT JOIN documents d ON d.id = mp.document_id
            ORDER BY mp.methodology_code
        """)
        return cur.fetchall()


def get_methodology_categories():
    with get_cursor() as cur:
        cur.execute(
            "SELECT category, COUNT(*) as count FROM methodologies "
            "WHERE category IS NOT NULL GROUP BY category ORDER BY count DESC"
        )
        return cur.fetchall()


def create_user_project(name, standard, doc_type=None, methodology=None, country=None, description=None,
                        project_type=None, parent_project_id=None,
                        monitoring_period_start=None, monitoring_period_end=None,
                        methodology_settings=None,
                        location_name=None, region=None, district=None,
                        latitude=None, longitude=None, boundary_geojson=None,
                        project_intake=None):
    import json as _json
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO user_projects (name, standard, doc_type, methodology, country, description, "
            "project_type, parent_project_id, monitoring_period_start, monitoring_period_end, "
            "methodology_settings, location_name, region, district, latitude, longitude, boundary_geojson, "
            "project_intake) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (name, standard, doc_type, methodology, country, description,
             project_type or "standalone_pdd", parent_project_id,
             monitoring_period_start, monitoring_period_end,
             _json.dumps(methodology_settings) if methodology_settings else None,
             location_name, region, district, latitude, longitude, boundary_geojson,
             _json.dumps(project_intake) if project_intake else None)
        )
        row = cur.fetchone()
        return row["id"]


def get_user_project(project_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM user_projects WHERE id = %s", (project_id,))
        proj = cur.fetchone()
        if not proj:
            return None
        cur.execute(
            "SELECT * FROM project_documents WHERE project_id = %s ORDER BY created_at DESC",
            (project_id,)
        )
        docs = cur.fetchall()
        result = dict(proj)
        result["documents"] = [dict(d) for d in docs]
        return result


def list_user_projects(status=None):
    with get_cursor() as cur:
        if status:
            cur.execute(
                "SELECT p.*, "
                "(SELECT COUNT(*) FROM project_documents pd WHERE pd.project_id = p.id) AS doc_count "
                "FROM user_projects p WHERE p.status = %s ORDER BY p.updated_at DESC",
                (status,)
            )
        else:
            cur.execute(
                "SELECT p.*, "
                "(SELECT COUNT(*) FROM project_documents pd WHERE pd.project_id = p.id) AS doc_count "
                "FROM user_projects p ORDER BY p.updated_at DESC"
            )
        return cur.fetchall()


def update_user_project(project_id, **kwargs):
    import psycopg2.extras as _pg_extras
    allowed = {"name", "standard", "doc_type", "methodology", "country", "description", "status",
               "crediting_period_start", "crediting_period_years", "project_settings", "project_intake",
               "methodology_settings",
               "location_name", "region", "district", "latitude", "longitude", "boundary_geojson",
               "project_type", "parent_project_id", "monitoring_period_start", "monitoring_period_end"}
    nullable_fields = {"crediting_period_start", "country", "description",
                       "parent_project_id", "monitoring_period_start", "monitoring_period_end",
                       "location_name", "region", "district", "latitude", "longitude", "boundary_geojson"}
    updates = {}
    for k, v in kwargs.items():
        if k not in allowed:
            continue
        if v is None and k not in nullable_fields:
            continue
        updates[k] = v
    if not updates:
        return
    if "project_settings" in updates and isinstance(updates["project_settings"], dict):
        updates["project_settings"] = _pg_extras.Json(updates["project_settings"])
    if "project_intake" in updates and isinstance(updates["project_intake"], dict):
        updates["project_intake"] = _pg_extras.Json(updates["project_intake"])
    if "methodology_settings" in updates and isinstance(updates["methodology_settings"], dict):
        updates["methodology_settings"] = _pg_extras.Json(updates["methodology_settings"])
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [project_id]
    with get_cursor() as cur:
        cur.execute(
            f"UPDATE user_projects SET {set_clause}, updated_at = NOW() WHERE id = %s",
            values
        )


def delete_user_project(project_id):
    with get_cursor() as cur:
        cur.execute("DELETE FROM user_projects WHERE id = %s", (project_id,))


def create_monitoring_period(project_id, period_number=1, period_start=None,
                             period_end=None, status="planned", notes=None):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO monitoring_periods "
            "(project_id, period_number, period_start, period_end, status, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (project_id, period_number, period_start, period_end, status, notes),
        )
        return cur.fetchone()["id"]


def list_monitoring_periods(project_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM monitoring_periods WHERE project_id = %s ORDER BY period_number ASC",
            (project_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def update_monitoring_period(period_id, **kwargs):
    allowed = {"period_number", "period_start", "period_end", "status", "notes", "mr_project_id"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    with get_cursor() as cur:
        cur.execute(
            f"UPDATE monitoring_periods SET {set_clause}, updated_at = NOW() WHERE id = %s",
            list(updates.values()) + [period_id],
        )


def delete_monitoring_period(period_id):
    with get_cursor() as cur:
        cur.execute("DELETE FROM monitoring_periods WHERE id = %s", (period_id,))


def add_project_document(project_id, doc_type, file_name, file_path, file_type, file_size_bytes=None, notes=None):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO project_documents (project_id, doc_type, file_name, file_path, file_type, file_size_bytes, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (project_id, doc_type, file_name, file_path, file_type, file_size_bytes, notes)
        )
        row = cur.fetchone()
        cur.execute(
            "UPDATE user_projects SET updated_at = NOW() WHERE id = %s",
            (project_id,)
        )
        return row["id"]


def get_project_document(doc_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM project_documents WHERE id = %s", (doc_id,))
        return cur.fetchone()


def update_project_document(doc_id, **kwargs):
    import psycopg2.extras as _pg_extras
    allowed = {"parsed_text", "parsed_sections", "status", "review_result", "notes", "ai_extracted_summary", "ai_extracted_data"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    if "ai_extracted_data" in updates and isinstance(updates["ai_extracted_data"], (dict, list)):
        updates["ai_extracted_data"] = _pg_extras.Json(updates["ai_extracted_data"])
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [doc_id]
    with get_cursor() as cur:
        cur.execute(
            f"UPDATE project_documents SET {set_clause}, updated_at = NOW() WHERE id = %s",
            values
        )


def delete_project_document(doc_id):
    with get_cursor() as cur:
        cur.execute("DELETE FROM project_documents WHERE id = %s", (doc_id,))


def get_project_documents_by_type(project_id, doc_type):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM project_documents WHERE project_id = %s AND doc_type = %s ORDER BY created_at DESC",
            (project_id, doc_type)
        )
        return cur.fetchall()


def save_write_session(project_id, doc_type, section_id, section_title, generated_text, user_text=None, ai_context=None):
    import json as _json
    with get_cursor() as cur:
        cur.execute(
            "SELECT id FROM project_write_sessions WHERE project_id = %s AND doc_type = %s AND section_id = %s",
            (project_id, doc_type, section_id)
        )
        existing = cur.fetchone()
        ctx = _json.dumps(ai_context) if ai_context else '{}'
        if existing:
            cur.execute(
                "UPDATE project_write_sessions SET generated_text = %s, user_text = %s, "
                "section_title = %s, ai_context = %s, updated_at = NOW() WHERE id = %s RETURNING id",
                (generated_text, user_text, section_title, ctx, existing["id"])
            )
        else:
            cur.execute(
                "INSERT INTO project_write_sessions (project_id, doc_type, section_id, section_title, "
                "generated_text, user_text, ai_context) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (project_id, doc_type, section_id, section_title, generated_text, user_text, ctx)
            )
        return cur.fetchone()["id"]


def get_write_sessions(project_id, doc_type=None):
    with get_cursor() as cur:
        if doc_type:
            cur.execute(
                "SELECT * FROM project_write_sessions WHERE project_id = %s AND doc_type = %s ORDER BY section_id",
                (project_id, doc_type)
            )
        else:
            cur.execute(
                "SELECT * FROM project_write_sessions WHERE project_id = %s ORDER BY doc_type, section_id",
                (project_id,)
            )
        return cur.fetchall()


def get_write_session(session_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM project_write_sessions WHERE id = %s", (session_id,))
        return cur.fetchone()


def get_child_projects(parent_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT p.*, "
            "(SELECT COUNT(*) FROM project_documents pd WHERE pd.project_id = p.id) AS doc_count "
            "FROM user_projects p WHERE p.parent_project_id = %s ORDER BY p.created_at ASC",
            (parent_id,)
        )
        return cur.fetchall()


def update_document_ai_context(doc_id, use_as_ai_context):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE project_documents SET use_as_ai_context = %s, updated_at = NOW() WHERE id = %s",
            (use_as_ai_context, doc_id)
        )


def get_project_documents_for_ai(project_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM project_documents WHERE project_id = %s AND use_as_ai_context = true "
            "AND (parsed_text IS NOT NULL OR ai_extracted_summary IS NOT NULL) ORDER BY created_at DESC",
            (project_id,)
        )
        return cur.fetchall()


def save_knowledge_chunk(methodology_code, document_id, chunk_type, chunk_key, title,
                         content, structured_data=None, source_section_ids=None,
                         extraction_method="programmatic", confidence=1.0):
    import json as _json
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO methodology_knowledge
                (methodology_code, document_id, chunk_type, chunk_key, title,
                 content, structured_data, source_section_ids, extraction_method, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (methodology_code, chunk_type, chunk_key) DO UPDATE SET
                document_id = EXCLUDED.document_id,
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                structured_data = EXCLUDED.structured_data,
                source_section_ids = EXCLUDED.source_section_ids,
                extraction_method = EXCLUDED.extraction_method,
                confidence = EXCLUDED.confidence,
                version = methodology_knowledge.version + 1,
                updated_at = NOW()
            RETURNING id
        """, (
            methodology_code, document_id, chunk_type, chunk_key, title,
            content, _json.dumps(structured_data or {}),
            source_section_ids, extraction_method, confidence
        ))
        return cur.fetchone()["id"]


def get_knowledge_chunks(methodology_code, chunk_type=None):
    with get_cursor() as cur:
        if chunk_type:
            cur.execute("""
                SELECT * FROM methodology_knowledge
                WHERE methodology_code = %s AND chunk_type = %s
                ORDER BY chunk_type, chunk_key
            """, (methodology_code, chunk_type))
        else:
            cur.execute("""
                SELECT * FROM methodology_knowledge
                WHERE methodology_code = %s
                ORDER BY chunk_type, chunk_key
            """, (methodology_code,))
        return [dict(r) for r in cur.fetchall()]


def delete_methodology_knowledge(methodology_code):
    with get_cursor() as cur:
        cur.execute("DELETE FROM methodology_knowledge WHERE methodology_code = %s", (methodology_code,))
        cur.execute("DELETE FROM methodology_structure WHERE methodology_code = %s", (methodology_code,))


def save_finding(source_document_id, methodology_code, finding_type, description,
                  resolution=None, pdd_section=None, topic=None, severity="medium",
                  resolution_approach=None, standard=None, doc_type=None,
                  vvb_name=None, source_project_id=None, source_project_name=None,
                  structured_data=None, extraction_method="ai_assisted", confidence=0.8):
    import json as _json
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO findings_knowledge
                (source_document_id, methodology_code, finding_type, description,
                 resolution, pdd_section, topic, severity, resolution_approach,
                 standard, doc_type, vvb_name, source_project_id, source_project_name,
                 structured_data, extraction_method, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            source_document_id, methodology_code, finding_type, description,
            resolution, pdd_section, topic, severity, resolution_approach,
            standard, doc_type, vvb_name, source_project_id, source_project_name,
            _json.dumps(structured_data or {}), extraction_method, confidence
        ))
        return cur.fetchone()["id"]


def get_findings_by_methodology(methodology_code, finding_type=None, pdd_section=None, limit=50):
    with get_cursor() as cur:
        query = "SELECT * FROM findings_knowledge WHERE methodology_code = %s"
        params = [methodology_code]
        if finding_type:
            query += " AND finding_type = %s"
            params.append(finding_type)
        if pdd_section:
            query += " AND pdd_section ILIKE %s"
            params.append(f"%{pdd_section}%")
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def get_findings_for_section(methodology_code, section_keywords, limit=10):
    with get_cursor() as cur:
        conditions = " OR ".join(["topic ILIKE %s" for _ in section_keywords])
        query = f"""
            SELECT * FROM findings_knowledge
            WHERE methodology_code = %s AND ({conditions})
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                created_at DESC
            LIMIT %s
        """
        params = [methodology_code] + [f"%{kw}%" for kw in section_keywords] + [limit]
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def get_findings_stats():
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                methodology_code,
                finding_type,
                COUNT(*) as cnt
            FROM findings_knowledge
            GROUP BY methodology_code, finding_type
            ORDER BY methodology_code, finding_type
        """)
        rows = cur.fetchall()
        stats = {}
        for r in rows:
            mc = r["methodology_code"] or "unknown"
            if mc not in stats:
                stats[mc] = {}
            stats[mc][r["finding_type"]] = r["cnt"]

        cur.execute("SELECT COUNT(*) as total FROM findings_knowledge")
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT topic, COUNT(*) as cnt
            FROM findings_knowledge
            WHERE topic IS NOT NULL
            GROUP BY topic
            ORDER BY cnt DESC
            LIMIT 20
        """)
        top_topics = [{"topic": r["topic"], "count": r["cnt"]} for r in cur.fetchall()]

        return {"by_methodology": stats, "total": total, "top_topics": top_topics}


def get_findings_by_document(source_document_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM findings_knowledge WHERE source_document_id = %s ORDER BY id",
            (source_document_id,)
        )
        return [dict(r) for r in cur.fetchall()]


def save_methodology_structure(document_id, methodology_code, detected_format, section_map):
    import json as _json
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO methodology_structure (document_id, methodology_code, detected_format, section_map)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (document_id) DO UPDATE SET
                methodology_code = EXCLUDED.methodology_code,
                detected_format = EXCLUDED.detected_format,
                section_map = EXCLUDED.section_map
            RETURNING id
        """, (document_id, methodology_code,
              _json.dumps(detected_format), _json.dumps(section_map)))
        return cur.fetchone()["id"]


def get_methodology_structure(document_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM methodology_structure WHERE document_id = %s", (document_id,))
        row = cur.fetchone()
        return dict(row) if row else None


# ── Carbon Intelligence — Normalization Queries ──────────────────────────────

def get_ref_registries() -> list[dict]:
    """Return all canonical registries from the ref_registries table."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM ref_registries ORDER BY registry_name")
        return [dict(r) for r in cur.fetchall()]


def get_registry_normalization_coverage() -> dict:
    """Summary of how many carbon_projects have been resolved to ref_registry_id."""
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM carbon_projects")
        total = cur.fetchone()["total"]
        cur.execute(
            "SELECT COUNT(*) AS n FROM carbon_projects WHERE ref_registry_id IS NOT NULL"
        )
        resolved = cur.fetchone()["n"]
        return {
            "total_projects": total,
            "registry_resolved": resolved,
            "registry_pct": round(resolved / total * 100, 1) if total else 0,
        }


def get_methodology_normalization_log(status: str = "unknown", limit: int = 100) -> list:
    """Return unresolved (or all) methodology normalization log entries."""
    with get_cursor() as cur:
        if status == "all":
            cur.execute(
                "SELECT * FROM methodology_normalization_log ORDER BY occurrence_count DESC LIMIT %s",
                (limit,),
            )
        else:
            cur.execute(
                """SELECT * FROM methodology_normalization_log
                   WHERE status = %s
                   ORDER BY occurrence_count DESC
                   LIMIT %s""",
                (status, limit),
            )
        return [dict(r) for r in cur.fetchall()]


def mark_normalization_log_ignored(raw_string: str) -> bool:
    """Mark a normalization log entry as ignored."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE methodology_normalization_log SET status = 'ignored' WHERE raw_string = %s",
            (raw_string,),
        )
        return True


def get_methodology_family_analytics() -> list:
    """
    Return project counts grouped by methodology_family from the library.
    Uses the normalized junction table — more accurate than raw string GROUP BY.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT
                COALESCE(ml.methodology_family, 'Unknown') AS methodology_family,
                ml.sector,
                ml.registry,
                COUNT(DISTINCT pmc.project_id)             AS project_count,
                COALESCE(SUM(cp.estimated_annual_credits), 0) AS total_credits
            FROM project_methodology_codes pmc
            JOIN methodology_library ml
                ON pmc.methodology_code = ml.methodology_code
            JOIN carbon_projects cp
                ON pmc.project_id = cp.id
            GROUP BY ml.methodology_family, ml.sector, ml.registry
            ORDER BY project_count DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]


def get_country_iso_analytics() -> list:
    """
    Return project counts grouped by normalized country_iso + canonical name.
    Falls back gracefully to raw country name where iso is NULL.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT
                COALESCE(cp.country_iso, 'UNK')       AS country_iso,
                COALESCE(c.country_name, cp.country)  AS country_name,
                COALESCE(c.region, 'Unknown')          AS region,
                COUNT(*)                               AS project_count,
                COALESCE(SUM(cp.estimated_annual_credits), 0) AS total_credits
            FROM carbon_projects cp
            LEFT JOIN countries c ON cp.country_iso = c.country_iso
            WHERE cp.country IS NOT NULL
            GROUP BY cp.country_iso, c.country_name, cp.country, c.region
            ORDER BY project_count DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]


def get_normalization_coverage_stats() -> dict:
    """Return a summary of normalization coverage for the admin panel."""
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM carbon_projects")
        total = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS n FROM carbon_projects WHERE country_iso IS NOT NULL")
        country_resolved = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(DISTINCT project_id) AS n FROM project_methodology_codes")
        meth_resolved = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM methodology_normalization_log WHERE status = 'unknown'")
        unresolved_log = cur.fetchone()["n"]

        return {
            "total_projects":       total,
            "country_resolved":     country_resolved,
            "country_pct":          round(country_resolved / total * 100, 1) if total else 0,
            "meth_resolved":        meth_resolved,
            "meth_pct":             round(meth_resolved / total * 100, 1) if total else 0,
            "unresolved_meth_log":  unresolved_log,
        }


def get_registration_timeline(registry: str | None = None) -> list[dict]:
    """
    Return monthly project registration counts for the timeline chart.
    Optionally filtered by ref_registry_id slug (e.g. 'verra', 'cdm').
    Only rows with a valid registration_date are included.
    """
    params: list = []
    where_clauses = ["registration_date IS NOT NULL"]
    if registry:
        where_clauses.append("ref_registry_id = %s")
        params.append(registry)
    where = "WHERE " + " AND ".join(where_clauses)

    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                TO_CHAR(DATE_TRUNC('month', registration_date), 'YYYY-MM') AS month,
                COALESCE(rr.registry_short, ref_registry_id, cp.registry) AS registry_label,
                COUNT(*) AS project_count
            FROM carbon_projects cp
            LEFT JOIN ref_registries rr ON cp.ref_registry_id = rr.registry_id
            {where}
            GROUP BY DATE_TRUNC('month', registration_date),
                     rr.registry_short, cp.ref_registry_id, cp.registry
            ORDER BY DATE_TRUNC('month', registration_date)
            """,
            params,
        )
        return [dict(r) for r in cur.fetchall()]


def get_market_intelligence_context(
    country_iso: str | None = None,
    methodology_family: str | None = None,
    limit_projects: int = 10,
) -> dict:
    """
    Return structured market intelligence data for a country and/or
    methodology family.  Used to build AI prompt context.

    Returns a dict with:
        country_summary     — project counts, top methodologies, registries, developers
        methodology_summary — family breakdown, typical credits, registries
        raw_for_prompt      — pre-formatted text block for injection into AI prompt
    """
    result: dict = {}

    with get_cursor() as cur:
        if country_iso:
            # Country-level intelligence
            cur.execute(
                """
                SELECT
                    COALESCE(c.country_name, cp.country) AS country_name,
                    c.region,
                    c.subregion,
                    COUNT(*)                             AS total_projects,
                    COUNT(DISTINCT cp.ref_registry_id)   AS registry_count,
                    COALESCE(SUM(cp.estimated_annual_credits), 0) AS total_est_credits,
                    COALESCE(AVG(cp.estimated_annual_credits), 0) AS avg_est_credits,
                    COUNT(CASE WHEN cp.status ILIKE '%%registered%%'
                               OR cp.status ILIKE '%%active%%' THEN 1 END) AS active_count
                FROM carbon_projects cp
                LEFT JOIN countries c ON cp.country_iso = c.country_iso
                WHERE cp.country_iso = %s
                GROUP BY c.country_name, cp.country, c.region, c.subregion
                """,
                (country_iso,),
            )
            country_row = cur.fetchone()

            # Top methodologies in country
            cur.execute(
                """
                SELECT
                    cp.methodology,
                    COUNT(*)    AS project_count,
                    COALESCE(SUM(cp.estimated_annual_credits), 0) AS total_credits
                FROM carbon_projects cp
                WHERE cp.country_iso = %s
                  AND cp.methodology IS NOT NULL
                GROUP BY cp.methodology
                ORDER BY project_count DESC
                LIMIT 8
                """,
                (country_iso,),
            )
            country_methodologies = [dict(r) for r in cur.fetchall()]

            # Top registries in country
            cur.execute(
                """
                SELECT
                    COALESCE(rr.registry_short, cp.registry) AS registry,
                    COUNT(*) AS project_count
                FROM carbon_projects cp
                LEFT JOIN ref_registries rr ON cp.ref_registry_id = rr.registry_id
                WHERE cp.country_iso = %s
                GROUP BY rr.registry_short, cp.registry
                ORDER BY project_count DESC
                """,
                (country_iso,),
            )
            country_registries = [dict(r) for r in cur.fetchall()]

            # Top developers in country
            cur.execute(
                """
                SELECT proponent, COUNT(*) AS project_count
                FROM carbon_projects
                WHERE country_iso = %s AND proponent IS NOT NULL
                GROUP BY proponent
                ORDER BY project_count DESC
                LIMIT 5
                """,
                (country_iso,),
            )
            country_developers = [dict(r) for r in cur.fetchall()]

            result["country_summary"] = {
                "country_iso":       country_iso,
                "data":              dict(country_row) if country_row else {},
                "top_methodologies": country_methodologies,
                "registries":        country_registries,
                "top_developers":    country_developers,
            }

        if methodology_family:
            # Methodology family intelligence
            cur.execute(
                """
                SELECT
                    rm.methodology_family,
                    COUNT(rm.methodology_code)     AS code_count,
                    COALESCE(rr.registry_name, rm.ref_registry_id) AS registry_name,
                    rm.sector,
                    rm.technology
                FROM ref_methodologies rm
                LEFT JOIN ref_registries rr ON rm.ref_registry_id = rr.registry_id
                WHERE LOWER(rm.methodology_family) LIKE LOWER(%s)
                GROUP BY rm.methodology_family, rr.registry_name,
                         rm.ref_registry_id, rm.sector, rm.technology
                ORDER BY code_count DESC
                LIMIT 10
                """,
                (f"{methodology_family}%",),
            )
            family_rows = [dict(r) for r in cur.fetchall()]

            # Projects using this methodology family
            cur.execute(
                """
                SELECT
                    COALESCE(c.country_name, cp.country) AS country,
                    COUNT(*)     AS project_count,
                    COALESCE(AVG(cp.estimated_annual_credits), 0) AS avg_credits
                FROM carbon_projects cp
                INNER JOIN project_methodology_codes pmc
                        ON pmc.project_id = cp.id
                INNER JOIN ref_methodologies rm
                        ON UPPER(pmc.methodology_code) = rm.methodology_code
                LEFT JOIN countries c ON cp.country_iso = c.country_iso
                WHERE LOWER(rm.methodology_family) LIKE LOWER(%s)
                GROUP BY c.country_name, cp.country
                ORDER BY project_count DESC
                LIMIT 10
                """,
                (f"{methodology_family}%",),
            )
            family_countries = [dict(r) for r in cur.fetchall()]

            result["methodology_summary"] = {
                "family":          methodology_family,
                "codes":           family_rows,
                "top_countries":   family_countries,
            }

    # ── Build pre-formatted text block ────────────────────────────────────
    parts: list[str] = []

    if "country_summary" in result:
        cs  = result["country_summary"]
        dat = cs.get("data", {})
        if dat:
            name = dat.get("country_name", country_iso)
            total = dat.get("total_projects", 0)
            credits = dat.get("total_est_credits", 0)
            active  = dat.get("active_count", 0)
            region  = dat.get("region", "")
            parts.append(
                f"=== Market Intelligence: {name} ({country_iso}) ===\n"
                f"Region: {region}\n"
                f"Total carbon projects: {total:,}\n"
                f"Active/Registered projects: {active:,}\n"
                f"Total estimated annual credits (registry-declared, not issued): "
                f"{int(credits):,} tCO2e/year\n"
                f"Average per project: {int(dat.get('avg_est_credits', 0)):,} tCO2e/year\n"
            )
            if cs.get("top_methodologies"):
                parts.append("Top methodologies used:")
                for m in cs["top_methodologies"][:5]:
                    parts.append(f"  - {m['methodology']} ({m['project_count']} projects)")
            if cs.get("registries"):
                reg_str = ", ".join(
                    f"{r['registry']} ({r['project_count']})"
                    for r in cs["registries"]
                )
                parts.append(f"Registries: {reg_str}")
            if cs.get("top_developers"):
                dev_str = ", ".join(
                    f"{d['proponent']} ({d['project_count']})"
                    for d in cs["top_developers"][:3]
                )
                parts.append(f"Top developers: {dev_str}")

    if "methodology_summary" in result:
        ms = result["methodology_summary"]
        family = ms.get("family", methodology_family)
        codes  = ms.get("codes", [])
        countries_list = ms.get("top_countries", [])
        parts.append(f"\n=== Market Intelligence: {family} Methodology Family ===")
        if codes:
            code_str = ", ".join(
                c["methodology_family"] for c in codes[:3]
                if c.get("methodology_family")
            )
            parts.append(f"Methodology family variant(s): {code_str or family}")
        if countries_list:
            parts.append("Top countries using this family:")
            for c in countries_list[:5]:
                parts.append(
                    f"  - {c['country']} ({c['project_count']} projects, "
                    f"avg {int(c['avg_credits'] or 0):,} tCO2e/year)"
                )

    result["raw_for_prompt"] = "\n".join(parts) if parts else ""
    return result


def get_ref_countries() -> list[dict]:
    """Return all rows from the countries table, ordered by country name."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT
                c.country_iso,
                c.country_name,
                c.region,
                c.subregion,
                c.aliases,
                COUNT(cp.id) AS project_count
            FROM countries c
            LEFT JOIN carbon_projects cp ON cp.country_iso = c.country_iso
            GROUP BY c.country_iso, c.country_name, c.region, c.subregion, c.aliases
            ORDER BY c.country_name
            """
        )
        return [dict(r) for r in cur.fetchall()]


def get_ref_methodologies(
    family: str | None = None,
    registry: str | None = None,
    sector: str | None = None,
) -> list[dict]:
    """
    Return rows from ref_methodologies with optional filters.

    Parameters
    ----------
    family:   filter by methodology_family (case-insensitive prefix match)
    registry: filter by ref_registry_id slug (exact match)
    sector:   filter by sector (case-insensitive substring match)
    """
    clauses: list[str] = []
    params: list = []

    if family:
        clauses.append("LOWER(rm.methodology_family) LIKE LOWER(%s)")
        params.append(f"{family}%")
    if registry:
        clauses.append("rm.ref_registry_id = %s")
        params.append(registry.lower())
    if sector:
        clauses.append("LOWER(rm.sector) LIKE LOWER(%s)")
        params.append(f"%{sector}%")

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                rm.methodology_code,
                rm.methodology_name,
                rm.methodology_family,
                rm.ref_registry_id,
                rr.registry_name  AS registry_display_name,
                rm.sector,
                rm.technology,
                rm.status,
                rm.aliases,
                rm.version,
                rm.notes,
                COUNT(pmc.project_id) AS project_count
            FROM ref_methodologies rm
            LEFT JOIN ref_registries rr ON rr.registry_id = rm.ref_registry_id
            LEFT JOIN project_methodology_codes pmc
                   ON pmc.methodology_code = rm.methodology_code
            {where}
            GROUP BY rm.methodology_code, rm.methodology_name, rm.methodology_family,
                     rm.ref_registry_id, rr.registry_name,
                     rm.sector, rm.technology, rm.status, rm.aliases, rm.version, rm.notes
            ORDER BY rm.methodology_code
            """,
            params,
        )
        return [dict(r) for r in cur.fetchall()]
