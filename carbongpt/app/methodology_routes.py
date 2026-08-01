"""
REST API routes for the versioned regulatory corpus (docs/SPEC-01.md, T7).

Reachable through the frontend proxy at /api/methodologies/... (Express
strips the /api prefix before forwarding to FastAPI — see server/index.ts).
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from carbongpt.repository.gs_ingest import (
    IngestError,
    check_for_updates,
    ingest_methodology,
    resolve_applicable_version,
)
from carbongpt.repository.db import get_cursor

router = APIRouter(prefix="/methodologies", tags=["methodologies"])


class IngestRequest(BaseModel):
    url: str
    methodology_code: str
    registry: str = "GoldStandard"
    short_name: Optional[str] = None
    former_name: Optional[str] = None


@router.get("")
def list_methodologies():
    """List methodologies that have at least one ingested version, with their current version."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT m.code, m.name, m.short_name, m.former_name, m.standard, m.last_checked_at,
                      v.version AS current_version, v.effective_from AS current_effective_from,
                      v.paris_aligned AS current_paris_aligned
               FROM methodologies m
               JOIN methodology_version_history v
                    ON v.methodology_code = m.code AND v.is_current = TRUE
               ORDER BY m.code"""
        )
        return cur.fetchall()


@router.get("/{code}/versions")
def get_versions(code: str, registry: str = "GoldStandard"):
    """Full version history for a methodology, most recent first."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT version, released_date, effective_from, effective_until, is_current,
                      paris_aligned, document_name, pdf_url, local_path, status
               FROM methodology_version_history
               WHERE methodology_code = %s AND registry = %s
               ORDER BY effective_from DESC""",
            (code, registry),
        )
        rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No ingested versions for {code} ({registry})")
    return rows


@router.post("/ingest")
def trigger_ingest(body: IngestRequest):
    """Fetch, parse, and ingest a methodology's page. Idempotent — safe to re-run."""
    try:
        return ingest_methodology(
            body.url, methodology_code=body.methodology_code, registry=body.registry,
            short_name=body.short_name, former_name=body.former_name,
        )
    except IngestError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/{code}/resolve")
def resolve_version(code: str, at_date: date, registry: str = "GoldStandard",
                     validated_under_version: Optional[str] = None):
    """Version of `code` applicable on `at_date` (query param, e.g. ?at_date=2026-07-01)."""
    try:
        return resolve_applicable_version(
            code, at_date, registry=registry, validated_under_version=validated_under_version,
        )
    except IngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{code}/check-updates")
def check_updates(code: str, url: str, registry: str = "GoldStandard"):
    """Re-parse `url` and report versions not yet in the database. Does not ingest anything."""
    try:
        return {"new_versions": check_for_updates(code, url, registry=registry)}
    except IngestError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
