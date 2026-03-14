"""
pack_routes.py — FastAPI router for the Methodology Pack Manager.
All endpoints are mounted under /admin/packs.
"""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from carbongpt.app.config import UPLOAD_DIR
from carbongpt.repository.pack_store import (
    activate_pack,
    add_document_link,
    add_finding,
    archive_pack,
    create_pack,
    delete_finding,
    evaluate_pack_readiness,
    get_indexed_pack_for_methodology,
    get_pack,
    get_pack_candidates,
    list_findings,
    list_pack_documents,
    list_packs,
    list_version_history,
    record_version,
    remove_document_link,
    update_pack,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/packs", tags=["methodology-packs"])


# ── Pydantic models ──────────────────────────────────────────────────────────

class PackCreate(BaseModel):
    methodology_code: str
    registry: str
    methodology_version: Optional[str] = None
    methodology_family: Optional[str] = None
    target_pdd_count: int = 30
    target_mr_count: int = 5
    target_validation_count: int = 3
    notes: Optional[str] = None
    created_by: str = "admin"


class PackUpdate(BaseModel):
    indexing_status: Optional[str] = None
    methodology_version: Optional[str] = None
    methodology_family: Optional[str] = None
    target_pdd_count: Optional[int] = None
    target_mr_count: Optional[int] = None
    target_validation_count: Optional[int] = None
    notes: Optional[str] = None


class DocumentLinkCreate(BaseModel):
    document_id: int
    document_role: str
    project_id: Optional[int] = None
    project_registry_id: Optional[str] = None
    methodology_version: Optional[str] = None
    vintage_year: Optional[int] = None
    validation_body: Optional[str] = None
    added_by: str = "admin"


class FindingCreate(BaseModel):
    finding_type: str
    finding_text: str
    source_link_id: Optional[int] = None
    finding_reference: Optional[str] = None
    section_reference: Optional[str] = None
    response_text: Optional[str] = None
    resolution_status: str = "closed"
    finding_vintage: Optional[int] = None
    validation_body: Optional[str] = None


class VersionRecordCreate(BaseModel):
    methodology_code: str
    registry: str
    version: str
    source_url: Optional[str] = None
    content_hash: Optional[str] = None
    pack_id: Optional[int] = None


# ── Pack CRUD ────────────────────────────────────────────────────────────────

@router.get("")
def list_all_packs(
    status: Optional[str] = Query(None),
    registry: Optional[str] = Query(None),
):
    return list_packs(status_filter=status, registry=registry)


@router.post("", status_code=201)
def create_new_pack(data: PackCreate):
    try:
        pack = create_pack(
            methodology_code=data.methodology_code,
            registry=data.registry,
            methodology_version=data.methodology_version,
            methodology_family=data.methodology_family,
            target_pdd_count=data.target_pdd_count,
            target_mr_count=data.target_mr_count,
            target_validation_count=data.target_validation_count,
            notes=data.notes,
            created_by=data.created_by,
        )
        return pack
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/for-methodology/{code}")
def get_pack_for_methodology(code: str):
    """Return the active indexed pack for a methodology code."""
    pack = get_indexed_pack_for_methodology(code.upper())
    if not pack:
        raise HTTPException(status_code=404, detail=f"No indexed pack for {code}")
    return pack


@router.get("/{pack_id}")
def get_pack_detail(pack_id: int):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return pack


@router.patch("/{pack_id}")
def update_pack_endpoint(pack_id: int, data: PackUpdate):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    updates = {k: v for k, v in data.dict().items() if v is not None}
    updated = update_pack(pack_id, **updates)
    return updated


@router.delete("/{pack_id}")
def archive_pack_endpoint(pack_id: int):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return archive_pack(pack_id)


@router.post("/{pack_id}/activate")
def activate_pack_endpoint(pack_id: int):
    """Mark pack as indexed (live for AI retrieval). Admin-triggered."""
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    readiness = evaluate_pack_readiness(pack_id)
    if not readiness["all_gates_pass"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot activate: hard gates not met",
                "gate_failures": readiness["gate_failures"],
                "score": readiness["score"],
            },
        )
    return activate_pack(pack_id)


# ── Readiness ────────────────────────────────────────────────────────────────

@router.get("/{pack_id}/readiness")
def get_readiness(pack_id: int):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return evaluate_pack_readiness(pack_id)


# ── Candidate projects (from Carbon Intelligence) ────────────────────────────

@router.get("/{pack_id}/candidates")
def get_candidates(
    pack_id: int,
    limit: int = Query(100, le=500),
    country: Optional[str] = Query(None),
    registered_only: bool = Query(True),
):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return get_pack_candidates(
        methodology_code=pack["methodology_code"],
        pack_id=pack_id,
        limit=limit,
        country_filter=country,
        registered_only=registered_only,
    )


# ── Document links ───────────────────────────────────────────────────────────

@router.get("/{pack_id}/documents")
def get_pack_documents(pack_id: int):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return list_pack_documents(pack_id)


@router.post("/{pack_id}/link-document")
def link_document(pack_id: int, data: DocumentLinkCreate):
    """Link an already-ingested document (by its existing document_id) to this pack."""
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    try:
        link = add_document_link(
            pack_id=pack_id,
            document_id=data.document_id,
            document_role=data.document_role,
            project_id=data.project_id,
            project_registry_id=data.project_registry_id,
            methodology_version=data.methodology_version,
            vintage_year=data.vintage_year,
            validation_body=data.validation_body,
            added_by=data.added_by,
        )
        return link
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{pack_id}/upload-document")
async def upload_and_link_document(
    pack_id: int,
    file: UploadFile = File(...),
    document_role: str = Form(...),
    project_registry_id: str = Form(""),
    methodology_version: str = Form(""),
    vintage_year: str = Form(""),
    validation_body: str = Form(""),
    added_by: str = Form("admin"),
):
    """
    Upload a new document file, ingest it into the existing documents system,
    then link it to this pack.  Uses the same ingestion pipeline as
    /admin/documents/upload — no separate file storage.
    """
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    if document_role not in {
        "METHODOLOGY_DOC", "TOOL_DOC", "GUIDANCE_DOC", "TEMPLATE",
        "PDD", "MR", "VALIDATION_REPORT", "VERIFICATION_REPORT",
        "DEVIATION_REPORT", "DOE_FINDING",
    }:
        raise HTTPException(status_code=400, detail=f"Invalid document_role: {document_role}")

    filename = file.filename or f"upload_{uuid.uuid4().hex}.pdf"
    safe_stem = f"{uuid.uuid4().hex}_{Path(filename).stem}"
    suffix = Path(filename).suffix.lower() or ".pdf"
    dest_path = UPLOAD_DIR / f"{safe_stem}{suffix}"

    try:
        with dest_path.open("wb") as out_file:
            shutil.copyfileobj(file.file, out_file)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not save file: {exc}") from exc
    finally:
        await file.close()

    # Map document_role → category for the existing documents table
    role_to_category = {
        "METHODOLOGY_DOC": "methodology",
        "TOOL_DOC":        "tool",
        "GUIDANCE_DOC":    "guidance",
        "TEMPLATE":        "template",
        "PDD":             "pdd",
        "MR":              "monitoring_report",
        "VALIDATION_REPORT":   "validation_report",
        "VERIFICATION_REPORT": "verification_report",
        "DEVIATION_REPORT":    "deviation",
        "DOE_FINDING":         "finding",
    }
    category = role_to_category.get(document_role, "other")

    from carbongpt.repository.store import create_document, update_document_ingestion
    from carbongpt.repository.ingestion import ingest_document
    import os

    api_key = os.getenv("OPENAI_API_KEY", "")
    file_type = suffix.lstrip(".") or "pdf"
    doc_id = create_document(
        standard_version_id=None,
        category=category,
        title=filename,
        file_path=str(dest_path),
        file_type=file_type,
    )

    import threading
    def _ingest():
        try:
            ingest_document(doc_id, str(dest_path), api_key)
        except Exception as exc:
            logger.error("Pack document ingestion failed doc=%s: %s", doc_id, exc)
            update_document_ingestion(doc_id, "failed")

    threading.Thread(target=_ingest, daemon=True).start()

    # Link to pack immediately; ingestion runs in background
    try:
        link = add_document_link(
            pack_id=pack_id,
            document_id=doc_id,
            document_role=document_role,
            project_registry_id=project_registry_id or None,
            methodology_version=methodology_version or None,
            vintage_year=int(vintage_year) if vintage_year.isdigit() else None,
            validation_body=validation_body or None,
            added_by=added_by,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "document_id":    doc_id,
        "link_id":        link["id"],
        "filename":       filename,
        "ingestion":      "started_in_background",
        "document_role":  document_role,
    }


@router.delete("/{pack_id}/links/{link_id}")
def remove_link(pack_id: int, link_id: int):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    removed = remove_document_link(pack_id, link_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"removed": True, "link_id": link_id}


# ── Findings ─────────────────────────────────────────────────────────────────

@router.get("/{pack_id}/findings")
def get_findings(
    pack_id: int,
    finding_type: Optional[str] = Query(None),
):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return list_findings(pack_id, finding_type=finding_type)


@router.post("/{pack_id}/findings", status_code=201)
def create_finding(pack_id: int, data: FindingCreate):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    try:
        finding = add_finding(
            pack_id=pack_id,
            finding_type=data.finding_type,
            finding_text=data.finding_text,
            source_link_id=data.source_link_id,
            finding_reference=data.finding_reference,
            section_reference=data.section_reference,
            response_text=data.response_text,
            resolution_status=data.resolution_status,
            finding_vintage=data.finding_vintage,
            validation_body=data.validation_body,
        )
        return finding
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{pack_id}/findings/{finding_id}")
def remove_finding(pack_id: int, finding_id: int):
    removed = delete_finding(finding_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Finding not found")
    return {"removed": True, "finding_id": finding_id}


# ── Version history ──────────────────────────────────────────────────────────

@router.get("/{pack_id}/versions")
def get_version_history(pack_id: int):
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return list_version_history(pack["methodology_code"])


@router.post("/version-history")
def record_version_endpoint(data: VersionRecordCreate):
    return record_version(
        methodology_code=data.methodology_code,
        registry=data.registry,
        version=data.version,
        source_url=data.source_url,
        content_hash=data.content_hash,
        pack_id=data.pack_id,
    )
