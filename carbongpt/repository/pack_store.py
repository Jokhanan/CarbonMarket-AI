"""
pack_store.py — Data access layer for the Methodology Pack Manager.

Reuses the existing documents + document_chunks tables for all chunk/embedding
storage.  This module only manages pack metadata, document links, findings,
and readiness evaluation.
"""

import hashlib
import logging
from datetime import datetime, timezone

from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

VALID_ROLES = {
    "METHODOLOGY_DOC", "TOOL_DOC", "GUIDANCE_DOC", "TEMPLATE",
    "PDD", "MR", "VALIDATION_REPORT", "VERIFICATION_REPORT",
    "DEVIATION_REPORT", "DOE_FINDING",
}

VALID_FINDING_TYPES = {"CAR", "CL", "FAR", "CR", "REVIEW_COMMENT"}

VALID_STATUSES = {
    "not_started", "collecting_documents", "ready_for_indexing",
    "indexed", "needs_update", "archived",
}

# ────────────────────────────────────────────────────────────────────────────
# PACK CRUD
# ────────────────────────────────────────────────────────────────────────────

def create_pack(
    methodology_code: str,
    registry: str,
    methodology_version: str | None = None,
    methodology_family: str | None = None,
    target_pdd_count: int = 30,
    target_mr_count: int = 5,
    target_validation_count: int = 3,
    notes: str | None = None,
    created_by: str = "admin",
) -> dict:
    """Create a new methodology pack. Returns the created pack dict."""
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO methodology_packs
                (methodology_code, registry, methodology_version, methodology_family,
                 target_pdd_count, target_mr_count, target_validation_count,
                 notes, created_by, indexing_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'not_started')
            RETURNING *
            """,
            (
                methodology_code.strip().upper(),
                registry.strip().lower(),
                methodology_version,
                methodology_family,
                target_pdd_count,
                target_mr_count,
                target_validation_count,
                notes,
                created_by,
            ),
        )
        return dict(cur.fetchone())


def get_pack(pack_id: int) -> dict | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM methodology_packs WHERE id = %s", (pack_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_packs(status_filter: str | None = None, registry: str | None = None) -> list[dict]:
    clauses, params = [], []
    if status_filter:
        clauses.append("indexing_status = %s")
        params.append(status_filter)
    if registry:
        clauses.append("registry = %s")
        params.append(registry.lower())
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_cursor() as cur:
        cur.execute(
            f"SELECT * FROM methodology_packs {where} ORDER BY last_updated DESC",
            params,
        )
        return [dict(r) for r in cur.fetchall()]


def update_pack(pack_id: int, **fields) -> dict | None:
    allowed = {
        "indexing_status", "methodology_version", "methodology_family",
        "version_valid_from", "version_valid_to", "target_pdd_count",
        "target_mr_count", "target_validation_count", "notes",
        "readiness_score", "readiness_gates_passed",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_pack(pack_id)
    updates["last_updated"] = datetime.now(timezone.utc)
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    with get_cursor() as cur:
        cur.execute(
            f"UPDATE methodology_packs SET {set_clause} WHERE id = %s RETURNING *",
            list(updates.values()) + [pack_id],
        )
        row = cur.fetchone()
        return dict(row) if row else None


def archive_pack(pack_id: int) -> dict | None:
    return update_pack(pack_id, indexing_status="archived")


def get_indexed_pack_for_methodology(methodology_code: str) -> dict | None:
    """Return the active indexed pack for a methodology code, or None."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM methodology_packs
            WHERE methodology_code = %s
              AND indexing_status = 'indexed'
            ORDER BY last_updated DESC
            LIMIT 1
            """,
            (methodology_code.strip().upper(),),
        )
        row = cur.fetchone()
        return dict(row) if row else None


# ────────────────────────────────────────────────────────────────────────────
# DOCUMENT LINKS
# ────────────────────────────────────────────────────────────────────────────

def add_document_link(
    pack_id: int,
    document_id: int,
    document_role: str,
    project_id: int | None = None,
    project_registry_id: str | None = None,
    methodology_version: str | None = None,
    vintage_year: int | None = None,
    validation_body: str | None = None,
    added_by: str = "admin",
    quality_flags: dict | None = None,
) -> dict:
    """Link an existing document to a pack. Raises on duplicate (pack_id, document_id)."""
    if document_role not in VALID_ROLES:
        raise ValueError(f"Invalid document_role: {document_role}. Must be one of {VALID_ROLES}")
    import json
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO methodology_pack_document_links
                (pack_id, document_id, document_role, project_id, project_registry_id,
                 methodology_version, vintage_year, validation_body, added_by, quality_flags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (pack_id, document_id) DO UPDATE
                SET document_role = EXCLUDED.document_role,
                    project_registry_id = EXCLUDED.project_registry_id,
                    vintage_year = EXCLUDED.vintage_year,
                    validation_body = EXCLUDED.validation_body,
                    added_at = NOW()
            RETURNING *
            """,
            (
                pack_id, document_id, document_role, project_id,
                project_registry_id, methodology_version, vintage_year,
                validation_body, added_by,
                json.dumps(quality_flags or {}),
            ),
        )
        link = dict(cur.fetchone())
    _refresh_pack_counts(pack_id)
    _auto_advance_status(pack_id)
    return link


def remove_document_link(pack_id: int, link_id: int) -> bool:
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM methodology_pack_document_links WHERE id = %s AND pack_id = %s",
            (link_id, pack_id),
        )
        deleted = cur.rowcount > 0
    if deleted:
        _refresh_pack_counts(pack_id)
    return deleted


def list_pack_documents(pack_id: int) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT
                mpdl.*,
                d.filename,
                d.source_url       AS doc_source_url,
                d.ingestion_status AS doc_ingestion_status,
                d.category         AS doc_category,
                d.file_path,
                cp.name            AS project_name,
                cp.country         AS project_country,
                cp.status          AS project_status
            FROM methodology_pack_document_links mpdl
            JOIN documents d ON d.id = mpdl.document_id
            LEFT JOIN carbon_projects cp ON cp.id = mpdl.project_id
            WHERE mpdl.pack_id = %s
            ORDER BY mpdl.document_role, mpdl.added_at
            """,
            (pack_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def _refresh_pack_counts(pack_id: int) -> None:
    """Recompute denormalized counts from actual links."""
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE methodology_packs mp
            SET
                pdd_count        = (SELECT COUNT(*) FROM methodology_pack_document_links
                                    WHERE pack_id = %s AND document_role = 'PDD'),
                mr_count         = (SELECT COUNT(*) FROM methodology_pack_document_links
                                    WHERE pack_id = %s AND document_role = 'MR'),
                validation_count = (SELECT COUNT(*) FROM methodology_pack_document_links
                                    WHERE pack_id = %s AND document_role IN
                                          ('VALIDATION_REPORT', 'VERIFICATION_REPORT')),
                tool_doc_count   = (SELECT COUNT(*) FROM methodology_pack_document_links
                                    WHERE pack_id = %s AND document_role IN
                                          ('METHODOLOGY_DOC', 'TOOL_DOC', 'GUIDANCE_DOC', 'TEMPLATE')),
                last_updated     = NOW()
            WHERE mp.id = %s
            """,
            (pack_id, pack_id, pack_id, pack_id, pack_id),
        )


# ────────────────────────────────────────────────────────────────────────────
# READINESS EVALUATION
# ────────────────────────────────────────────────────────────────────────────

def evaluate_pack_readiness(pack_id: int) -> dict:
    """
    Evaluate the two-tier readiness model:
      - Hard gates (all must pass for status to advance to ready_for_indexing)
      - Qualitative score (0–100)
    Returns a dict with gates, score, failures, and recommendation.
    Thresholds are derived from the pack's own target_* fields so smaller
    methodologies are never blocked by a fixed global minimum.
    """
    pack = get_pack(pack_id)
    if not pack:
        return {"error": "Pack not found"}

    with get_cursor() as cur:
        # All ingested links with doc metadata
        cur.execute(
            """
            SELECT
                mpdl.document_role,
                mpdl.project_id,
                mpdl.vintage_year,
                mpdl.validation_body,
                mpdl.project_registry_id,
                d.ingestion_status,
                d.word_count,
                cp.status  AS project_status,
                cp.country AS project_country,
                cp.registration_date
            FROM methodology_pack_document_links mpdl
            JOIN documents d ON d.id = mpdl.document_id
            LEFT JOIN carbon_projects cp ON cp.id = mpdl.project_id
            WHERE mpdl.pack_id = %s
            """,
            (pack_id,),
        )
        docs = [dict(r) for r in cur.fetchall()]

        # Findings count
        cur.execute(
            "SELECT finding_type, section_reference FROM pack_findings WHERE pack_id = %s",
            (pack_id,),
        )
        findings = [dict(r) for r in cur.fetchall()]

    # Categorise ingested docs
    def ingested(role):
        return [
            d for d in docs
            if d["document_role"] == role and d["ingestion_status"] == "ingested"
        ]

    pdds      = ingested("PDD")
    mrs       = ingested("MR")
    val_docs  = ingested("VALIDATION_REPORT") + ingested("VERIFICATION_REPORT")
    meth_docs = ingested("METHODOLOGY_DOC")

    # Targets (from pack config — smaller methodologies can have lower targets)
    tgt_pdd = max(pack["target_pdd_count"], 5)
    tgt_mr  = max(pack["target_mr_count"],  1)
    tgt_val = max(pack["target_validation_count"], 1)

    # Word-count helper (fallback to None if column absent)
    def wc(d):
        return d.get("word_count") or 0

    # ── Hard gates ──────────────────────────────────────────────────────────
    gates = {}

    # G1: methodology document ingested with meaningful content
    gates["G1_methodology_doc"] = (
        len(meth_docs) >= 1 and any(wc(d) >= 500 for d in meth_docs)
    )

    # G2: minimum PDD threshold (50% of target, floor 5)
    min_pdds = max(5, tgt_pdd // 2)
    gates["G2_pdd_count"] = len(pdds) >= min_pdds

    # G3: extraction quality — fewer than 30% of PDDs have < 200 words
    if pdds:
        poor = sum(1 for d in pdds if wc(d) < 200)
        gates["G3_extraction_quality"] = (poor / len(pdds)) <= 0.30
    else:
        gates["G3_extraction_quality"] = False

    # G4: registered projects — at least 60% of linked projects are registered
    linked_projects = [d for d in docs if d["project_id"] and d["project_status"]]
    if linked_projects:
        registered = sum(1 for d in linked_projects if d["project_status"] == "registered")
        gates["G4_registered_projects"] = (registered / len(linked_projects)) >= 0.60
    else:
        gates["G4_registered_projects"] = True  # no project links yet — not blocked

    # G5: monitoring coverage
    gates["G5_monitoring_report"] = len(mrs) >= 1 and any(wc(d) >= 200 for d in mrs)

    all_gates_pass = all(gates.values())

    # ── Qualitative score ────────────────────────────────────────────────────
    score = 0

    # Geography diversity (max 25)
    countries = set(d["project_country"] for d in pdds if d.get("project_country"))
    if len(countries) >= 4:
        score += 25
    elif len(countries) >= 2:
        score += 16
    elif len(countries) == 1:
        score += 8

    # Document quality (max 20) — avg word count of PDDs vs 2000-word benchmark
    if pdds:
        avg_wc = sum(wc(d) for d in pdds) / len(pdds)
        score += min(20, int(20 * min(avg_wc, 2000) / 2000))

    # PDD volume (max 15)
    if len(pdds) >= tgt_pdd:
        score += 15
    elif len(pdds) >= tgt_pdd // 2:
        score += 10
    elif len(pdds) >= 5:
        score += 5

    # Validation body diversity (max 5)
    val_bodies = set(
        d["validation_body"] for d in val_docs if d.get("validation_body")
    )
    if len(val_bodies) >= 2:
        score += 5
    elif len(val_bodies) == 1:
        score += 3

    # Findings coverage (max 20)
    f_types = {f["finding_type"] for f in findings}
    if len(findings) >= 3 and len(f_types) >= 2:
        score += 20
    elif len(findings) >= 1:
        score += 10

    # Temporal spread across registration years (max 10)
    years = set()
    for d in pdds:
        if d.get("registration_date"):
            try:
                yr = int(str(d["registration_date"])[:4])
                years.add(yr)
            except Exception:
                pass
    if len(years) >= 3:
        score += 10
    elif len(years) >= 2:
        score += 5

    # Validation/verification coverage (max 5)
    if len(val_docs) >= tgt_val:
        score += 5
    elif len(val_docs) >= 1:
        score += 2

    score = min(score, 100)

    # Status recommendation
    if all_gates_pass and score >= 60:
        recommendation = "ready_for_indexing"
    elif all_gates_pass:
        recommendation = "collecting_documents"
    else:
        recommendation = "collecting_documents"

    gate_failures = [g for g, passed in gates.items() if not passed]

    result = {
        "pack_id":        pack_id,
        "gates":          gates,
        "gate_failures":  gate_failures,
        "all_gates_pass": all_gates_pass,
        "score":          score,
        "recommendation": recommendation,
        "details": {
            "pdd_count":           len(pdds),
            "mr_count":            len(mrs),
            "validation_count":    len(val_docs),
            "methodology_docs":    len(meth_docs),
            "countries":           list(countries),
            "finding_count":       len(findings),
            "finding_types":       list(f_types),
            "validation_bodies":   list(val_bodies),
            "target_pdd_count":    tgt_pdd,
            "target_mr_count":     tgt_mr,
            "target_val_count":    tgt_val,
        },
    }

    import json
    update_pack(pack_id, readiness_score=score, readiness_gates_passed=json.dumps(gates))
    return result


def _auto_advance_status(pack_id: int) -> None:
    """After document changes, auto-advance status if readiness passes."""
    pack = get_pack(pack_id)
    if not pack:
        return
    if pack["indexing_status"] in ("indexed", "archived"):
        return
    readiness = evaluate_pack_readiness(pack_id)
    current = pack["indexing_status"]
    if current == "not_started":
        update_pack(pack_id, indexing_status="collecting_documents")
    elif current == "collecting_documents" and readiness["recommendation"] == "ready_for_indexing":
        update_pack(pack_id, indexing_status="ready_for_indexing")


def activate_pack(pack_id: int) -> dict | None:
    """Admin-triggered: mark pack as indexed (live for AI retrieval)."""
    return update_pack(pack_id, indexing_status="indexed")


# ────────────────────────────────────────────────────────────────────────────
# CANDIDATE PROJECTS (from Carbon Intelligence)
# ────────────────────────────────────────────────────────────────────────────

def get_pack_candidates(
    methodology_code: str,
    pack_id: int | None = None,
    limit: int = 100,
    country_filter: str | None = None,
    registered_only: bool = True,
) -> list[dict]:
    """
    Query carbon_projects via project_methodology_codes to find projects
    using this methodology.  Excludes projects already linked to the pack.
    """
    params: list = [methodology_code.strip().upper()]
    clauses = ["UPPER(pmc.methodology_code) = %s"]

    if registered_only:
        clauses.append("LOWER(cp.status) = 'registered'")

    if country_filter:
        clauses.append("cp.country ILIKE %s")
        params.append(f"%{country_filter}%")

    if pack_id is not None:
        clauses.append(
            """cp.id NOT IN (
                SELECT project_id FROM methodology_pack_document_links
                WHERE pack_id = %s AND project_id IS NOT NULL
            )"""
        )
        params.append(pack_id)

    where = "WHERE " + " AND ".join(clauses)
    params.append(limit)

    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT DISTINCT
                cp.id,
                cp.name,
                cp.country,
                cp.status,
                cp.registry,
                cp.estimated_annual_credits,
                cp.registration_date,
                cp.methodology           AS raw_methodology,
                pmc.methodology_code
            FROM carbon_projects cp
            JOIN project_methodology_codes pmc ON pmc.project_id = cp.id
            {where}
            ORDER BY cp.estimated_annual_credits DESC NULLS LAST
            LIMIT %s
            """,
            params,
        )
        return [dict(r) for r in cur.fetchall()]


# ────────────────────────────────────────────────────────────────────────────
# FINDINGS
# ────────────────────────────────────────────────────────────────────────────

def add_finding(
    pack_id: int,
    finding_type: str,
    finding_text: str,
    source_link_id: int | None = None,
    finding_reference: str | None = None,
    section_reference: str | None = None,
    response_text: str | None = None,
    resolution_status: str = "closed",
    finding_vintage: int | None = None,
    validation_body: str | None = None,
    extracted_automatically: bool = False,
) -> dict:
    if finding_type not in VALID_FINDING_TYPES:
        raise ValueError(f"Invalid finding_type: {finding_type}")
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO pack_findings
                (pack_id, source_link_id, finding_type, finding_reference,
                 section_reference, finding_text, response_text,
                 resolution_status, finding_vintage, validation_body,
                 extracted_automatically)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                pack_id, source_link_id, finding_type, finding_reference,
                section_reference, finding_text, response_text,
                resolution_status, finding_vintage, validation_body,
                extracted_automatically,
            ),
        )
        return dict(cur.fetchone())


def list_findings(pack_id: int, finding_type: str | None = None) -> list[dict]:
    params = [pack_id]
    clause = ""
    if finding_type:
        clause = "AND finding_type = %s"
        params.append(finding_type)
    with get_cursor() as cur:
        cur.execute(
            f"SELECT * FROM pack_findings WHERE pack_id = %s {clause} ORDER BY finding_type, created_at",
            params,
        )
        return [dict(r) for r in cur.fetchall()]


def delete_finding(finding_id: int) -> bool:
    with get_cursor() as cur:
        cur.execute("DELETE FROM pack_findings WHERE id = %s", (finding_id,))
        return cur.rowcount > 0


# ────────────────────────────────────────────────────────────────────────────
# AI RETRIEVAL  — pack-scoped vector search via existing document_chunks
# ────────────────────────────────────────────────────────────────────────────

def retrieve_pack_chunks(
    pack_id: int,
    query_embedding: list[float],
    role_filter: list[str] | None = None,
    max_chunks: int = 8,
) -> list[dict]:
    """
    Vector similarity search scoped to a pack's linked documents.
    Uses the existing document_chunks table — no duplicate storage.
    Requires pgvector extension.
    """
    import json
    role_clause = ""
    params: list = [pack_id]
    if role_filter:
        placeholders = ",".join(["%s"] * len(role_filter))
        role_clause = f"AND mpdl.document_role IN ({placeholders})"
        params.extend(role_filter)
    embedding_literal = json.dumps(query_embedding)
    params.extend([embedding_literal, max_chunks])
    with get_cursor() as cur:
        try:
            cur.execute(
                f"""
                SELECT
                    dc.content,
                    dc.chunk_index,
                    mpdl.document_role,
                    mpdl.project_registry_id,
                    mpdl.vintage_year,
                    d.filename,
                    dc.embedding <=> %s::vector AS distance
                FROM document_chunks dc
                JOIN methodology_pack_document_links mpdl ON mpdl.document_id = dc.document_id
                JOIN documents d ON d.id = dc.document_id
                WHERE mpdl.pack_id = %s
                  {role_clause}
                  AND dc.embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT %s
                """,
                # embedding placeholder (%s::vector) is in SELECT, comes before WHERE pack_id
                [embedding_literal, pack_id] + (role_filter or []) + [max_chunks],
            )
            return [dict(r) for r in cur.fetchall()]
        except Exception as exc:
            logger.warning("Pack chunk retrieval failed (pgvector?): %s", exc)
            return []


def retrieve_pack_chunks_by_text(
    pack_id: int,
    query_embedding: list[float],
    role_priority: list[str] | None = None,
    max_chunks: int = 8,
) -> list[dict]:
    """
    Retrieve pack chunks with role priority ordering.
    Returns methodology docs first, then examples.
    """
    priority = role_priority or ["METHODOLOGY_DOC", "TOOL_DOC", "PDD", "MR",
                                  "VALIDATION_REPORT", "VERIFICATION_REPORT"]
    return retrieve_pack_chunks(pack_id, query_embedding, role_filter=priority,
                                max_chunks=max_chunks)


# ────────────────────────────────────────────────────────────────────────────
# VERSION HISTORY
# ────────────────────────────────────────────────────────────────────────────

def record_version(
    methodology_code: str,
    registry: str,
    version: str,
    source_url: str | None = None,
    content_hash: str | None = None,
    pack_id: int | None = None,
) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO methodology_version_history
                (methodology_code, registry, version, source_url, content_hash, pack_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (methodology_code, registry, version) DO UPDATE
                SET content_hash = EXCLUDED.content_hash,
                    detected_at  = NOW()
            RETURNING *
            """,
            (methodology_code, registry, version, source_url, content_hash, pack_id),
        )
        return dict(cur.fetchone())


def list_version_history(methodology_code: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM methodology_version_history WHERE methodology_code = %s ORDER BY detected_at DESC",
            (methodology_code,),
        )
        return [dict(r) for r in cur.fetchall()]
