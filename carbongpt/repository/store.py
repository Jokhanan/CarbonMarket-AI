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
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO carbon_projects
            (registry, registry_id, name, status, country, region, proponent,
             methodology, project_type, project_subtype, estimated_annual_credits,
             crediting_period_start, crediting_period_end, registration_date,
             latitude, longitude, description, sdgs, extra_data, synced_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
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
             synced_at = NOW()
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
            SELECT registry, COUNT(*) as project_count,
                   COALESCE(SUM(estimated_annual_credits), 0) as total_credits
            FROM carbon_projects
            GROUP BY registry
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


def create_user_project(name, standard, doc_type=None, methodology=None, country=None, description=None):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO user_projects (name, standard, doc_type, methodology, country, description) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (name, standard, doc_type, methodology, country, description)
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
    allowed = {"name", "standard", "doc_type", "methodology", "country", "description", "status"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return
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
    allowed = {"parsed_text", "parsed_sections", "status", "review_result", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
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
