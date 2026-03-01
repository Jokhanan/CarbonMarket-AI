import logging
import os
import uuid
import threading
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from carbongpt.app.config import BASE_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

REPO_DIR = BASE_DIR / "document_repository"
REPO_DIR.mkdir(parents=True, exist_ok=True)

VALID_CATEGORIES = [
    "standard_text", "methodology", "guidance", "tool", "template",
    "example_pdd", "example_mr", "example_fvr", "example_valver",
    "example_other", "rule_update", "other"
]

CATEGORY_LABELS = {
    "standard_text": "Standard Document",
    "methodology": "Methodology",
    "guidance": "Guidance Document",
    "tool": "Calculation Tool",
    "template": "Template",
    "example_pdd": "Example PDD",
    "example_mr": "Example Monitoring Report",
    "example_fvr": "Example Final Verification Report",
    "example_valver": "Example Validation/Verification Report",
    "example_other": "Example (Other)",
    "rule_update": "Rule Update",
    "other": "Other",
}


class StandardCreate(BaseModel):
    name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    description: str = ""


class VersionCreate(BaseModel):
    standard_id: int
    version: str = Field(..., min_length=1)
    effective_date: str = None
    status: str = "active"
    notes: str = ""


class DocumentUpdate(BaseModel):
    standard_version_id: int = None
    category: str = None
    title: str = None
    reference_id: str = None
    doc_version: str = None
    status: str = None


class ComplianceRuleCreate(BaseModel):
    standard_id: int = None
    rule_type: str = Field(..., min_length=1)
    severity: str = "error"
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    conditions: dict = {}
    effective_date: str = None
    expiry_date: str = None
    source_url: str = None
    source_description: str = None
    status: str = "active"
    discovered_by: str = "manual"
    review_notes: str = None


class ComplianceRuleUpdate(BaseModel):
    standard_id: int = None
    rule_type: str = None
    severity: str = None
    title: str = None
    description: str = None
    conditions: dict = None
    effective_date: str = None
    expiry_date: str = None
    source_url: str = None
    source_description: str = None
    status: str = None
    review_notes: str = None


@router.get("/standards")
def get_standards():
    from carbongpt.repository.store import list_standards
    return list_standards()


@router.get("/standard-versions")
def get_standard_versions(standard_id: int = None):
    from carbongpt.repository.store import list_standard_versions
    return list_standard_versions(standard_id)


@router.post("/standards")
def add_standard(data: StandardCreate):
    from carbongpt.repository.store import create_standard
    try:
        sid = create_standard(data.name, data.slug, data.description)
        return {"id": sid, "message": f"Standard '{data.name}' created."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/standard-versions")
def add_standard_version(data: VersionCreate):
    from carbongpt.repository.store import create_standard_version
    try:
        vid = create_standard_version(
            data.standard_id, data.version, data.effective_date, data.status, data.notes
        )
        return {"id": vid, "message": f"Version '{data.version}' created."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/upload")
async def upload_repository_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    category: str = Form("other"),
    standard_version_id: int = Form(None),
    reference_id: str = Form(None),
    doc_version: str = Form(None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    file_type_map = {".pdf": "pdf", ".docx": "docx", ".xlsx": "xlsx", ".csv": "csv"}
    file_type = file_type_map.get(ext)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Accepted: .pdf, .docx, .xlsx, .csv"
        )

    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    unique_name = f"{uuid.uuid4().hex}_{Path(file.filename).stem}{ext}"
    dest_path = REPO_DIR / unique_name
    file_content = await file.read()
    file_size = len(file_content)

    try:
        with dest_path.open("wb") as f:
            f.write(file_content)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not save file: {exc}")
    finally:
        await file.close()

    from carbongpt.repository.store import create_document
    doc_title = title or Path(file.filename).stem
    sv_id = standard_version_id if standard_version_id and standard_version_id > 0 else None

    doc_id = create_document(
        standard_version_id=sv_id,
        category=category,
        title=doc_title,
        file_path=str(dest_path),
        file_type=file_type,
        reference_id=reference_id or None,
        doc_version=doc_version or None,
        file_size_bytes=file_size,
    )

    if file_type in ("pdf", "docx"):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            thread = threading.Thread(
                target=_run_ingestion_background,
                args=(doc_id, str(dest_path), api_key),
                daemon=True,
            )
            thread.start()
            msg = "Document uploaded. Ingestion started in background."
        else:
            msg = "Document uploaded. Set OPENAI_API_KEY for auto-ingestion."
    else:
        from carbongpt.repository.store import update_document_ingestion
        update_document_ingestion(doc_id, "unsupported")
        msg = f"Document uploaded. Text extraction not supported for {file_type.upper()} files — stored for reference."

    return {
        "id": doc_id,
        "title": doc_title,
        "file_path": str(dest_path),
        "message": msg,
    }


def _run_ingestion_background(doc_id, file_path, api_key):
    try:
        from carbongpt.repository.ingestion import ingest_document
        ingest_document(doc_id, file_path, api_key)
    except Exception as e:
        logger.error("Background ingestion failed for doc %s: %s", doc_id, e)


@router.get("/documents")
def get_documents(standard_version_id: int = None, category: str = None):
    from carbongpt.repository.store import list_documents
    return list_documents(standard_version_id, category)


@router.get("/documents/{doc_id}")
def get_document_detail(doc_id: int):
    from carbongpt.repository.store import get_document
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.patch("/documents/{doc_id}")
def update_document(doc_id: int, data: DocumentUpdate):
    from carbongpt.repository.store import get_document, update_document_metadata
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    update_document_metadata(
        doc_id,
        standard_version_id=data.standard_version_id,
        category=data.category,
        title=data.title,
        reference_id=data.reference_id,
        doc_version=data.doc_version,
        status=data.status,
    )
    return {"message": "Document updated."}


@router.delete("/documents/{doc_id}")
def remove_document(doc_id: int):
    from carbongpt.repository.store import get_document, delete_document
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    file_path = doc["file_path"]
    if file_path and Path(file_path).exists():
        Path(file_path).unlink(missing_ok=True)
    delete_document(doc_id)
    return {"message": "Document deleted."}


@router.post("/documents/{doc_id}/reingest")
def reingest_document(doc_id: int):
    from carbongpt.repository.store import get_document
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY not set.")
    if doc["file_type"] not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files can be ingested.")

    thread = threading.Thread(
        target=_run_ingestion_background,
        args=(doc_id, doc["file_path"], api_key),
        daemon=True,
    )
    thread.start()
    return {"message": "Re-ingestion started."}


@router.get("/stats")
def get_stats():
    from carbongpt.repository.store import get_document_stats, get_chunk_count
    stats = get_document_stats()
    stats["total_chunks"] = get_chunk_count()
    return stats


@router.get("/search")
def search_documents(q: str, limit: int = 10, standard_version_id: int = None,
                     mode: str = "hybrid",
                     semantic_weight: float = 0.7, keyword_weight: float = 0.3):
    if mode == "keyword":
        from carbongpt.repository.store import full_text_search
        results = full_text_search(q, limit=limit, standard_version_id=standard_version_id)
        return results

    api_key = os.getenv("OPENAI_API_KEY")

    if mode == "semantic" and not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY required for semantic search.")

    from carbongpt.repository.store import search_chunks, hybrid_search

    query_embedding = None
    if api_key:
        try:
            from carbongpt.repository.ingestion import create_embeddings
            query_embedding = create_embeddings([q], api_key)[0]
        except Exception:
            pass

    if mode == "hybrid":
        results = hybrid_search(
            q, query_embedding, limit=limit,
            standard_version_id=standard_version_id,
            semantic_weight=semantic_weight, keyword_weight=keyword_weight,
        )
    else:
        if query_embedding is None:
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY required for semantic search.")
        results = search_chunks(query_embedding, limit=limit, standard_version_id=standard_version_id)
    return results


@router.get("/search-documents")
def search_docs_fts(q: str, limit: int = 20, standard_version_id: int = None, category: str = None):
    from carbongpt.repository.store import search_documents_fts
    results = search_documents_fts(q, limit=limit, standard_version_id=standard_version_id, category=category)
    return results


@router.post("/backfill-metadata")
def backfill_chunk_metadata():
    import json
    from carbongpt.repository.db import get_cursor
    from carbongpt.repository.store import (
        get_document, get_section_ids_for_document, update_search_vector
    )

    updated_chunks = 0
    updated_docs = 0

    with get_cursor() as cur:
        cur.execute("SELECT DISTINCT document_id FROM document_chunks")
        doc_ids = [r["document_id"] for r in cur.fetchall()]

    for doc_id in doc_ids:
        doc = get_document(doc_id)
        if not doc:
            continue

        sections = get_section_ids_for_document(doc_id)
        section_map = {s["id"]: s for s in sections}

        doc_meta = {
            "document_title": doc.get("title", ""),
            "document_category": doc.get("category", ""),
            "standard_name": doc.get("standard_name") or doc.get("auto_detected_standard", ""),
            "reference_id": doc.get("reference_id", ""),
        }

        with get_cursor() as cur:
            cur.execute(
                "SELECT id, section_id, metadata FROM document_chunks WHERE document_id = %s",
                (doc_id,)
            )
            chunks = cur.fetchall()

        for chunk in chunks:
            existing_meta = chunk["metadata"]
            if isinstance(existing_meta, str):
                try:
                    existing_meta = json.loads(existing_meta)
                except Exception:
                    existing_meta = {}
            elif existing_meta is None:
                existing_meta = {}

            new_meta = {**existing_meta, **doc_meta}

            sec_id = chunk["section_id"]
            if sec_id and sec_id in section_map:
                sec = section_map[sec_id]
                new_meta["section_number"] = sec.get("section_number")
                new_meta["section_title"] = sec.get("title", "")

            with get_cursor() as cur:
                cur.execute(
                    "UPDATE document_chunks SET metadata = %s, "
                    "search_vector = to_tsvector('english', content) WHERE id = %s",
                    (json.dumps(new_meta), chunk["id"])
                )
            updated_chunks += 1

        update_search_vector(doc_id)
        updated_docs += 1

    return {
        "updated_documents": updated_docs,
        "updated_chunks": updated_chunks,
    }


@router.get("/compliance-rules")
def get_compliance_rules(standard_id: int = None, rule_type: str = None, status: str = None):
    from carbongpt.repository.store import list_compliance_rules
    return list_compliance_rules(standard_id=standard_id, rule_type=rule_type, status=status)


@router.get("/compliance-rules/{rule_id}")
def get_compliance_rule_detail(rule_id: int):
    from carbongpt.repository.store import get_compliance_rule
    rule = get_compliance_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Compliance rule not found.")
    return rule


@router.post("/compliance-rules")
def add_compliance_rule(data: ComplianceRuleCreate):
    from carbongpt.repository.store import create_compliance_rule
    try:
        rule_id = create_compliance_rule(
            rule_type=data.rule_type,
            severity=data.severity,
            title=data.title,
            description=data.description,
            conditions=data.conditions,
            standard_id=data.standard_id,
            effective_date=data.effective_date,
            expiry_date=data.expiry_date,
            source_url=data.source_url,
            source_description=data.source_description,
            status=data.status,
            discovered_by=data.discovered_by,
            review_notes=data.review_notes,
        )
        return {"id": rule_id, "message": "Compliance rule created."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/compliance-rules/{rule_id}")
def update_compliance_rule_endpoint(rule_id: int, data: ComplianceRuleUpdate):
    from carbongpt.repository.store import get_compliance_rule, update_compliance_rule
    rule = get_compliance_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Compliance rule not found.")
    update_compliance_rule(rule_id, **data.model_dump(exclude_none=True))
    return {"message": "Compliance rule updated."}


@router.delete("/compliance-rules/{rule_id}")
def remove_compliance_rule(rule_id: int):
    from carbongpt.repository.store import get_compliance_rule, delete_compliance_rule
    rule = get_compliance_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Compliance rule not found.")
    delete_compliance_rule(rule_id)
    return {"message": "Compliance rule deleted."}


@router.post("/compliance-rules/check")
def check_methodology(methodology: str = Form(...), standard_slug: str = Form("verra")):
    from carbongpt.repository.store import check_methodology_rules
    matches = check_methodology_rules(methodology, standard_slug)
    return {"methodology": methodology, "standard": standard_slug, "matching_rules": matches}


class WebVerifyRequest(BaseModel):
    methodology: str = Field(..., min_length=1)
    standard: str = "Verra VCS"
    standard_id: int = None


class KnowledgeRefreshRequest(BaseModel):
    standard: str = "Verra VCS"
    standard_id: int = None
    topics: list[str] = None
    auto_save: bool = False


@router.post("/web-intelligence/verify-methodology")
def verify_methodology_via_web(data: WebVerifyRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY required for web intelligence.")

    from carbongpt.core.web_intelligence import verify_methodology_status
    result = verify_methodology_status(data.methodology, data.standard)
    if not result:
        raise HTTPException(status_code=500, detail="Web verification failed.")
    return {"methodology": data.methodology, "standard": data.standard, "result": result}


@router.post("/web-intelligence/propose-rule")
def propose_rule_from_web(data: WebVerifyRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY required for web intelligence.")

    from carbongpt.core.web_intelligence import propose_compliance_rule_from_web
    proposed = propose_compliance_rule_from_web(data.methodology, data.standard, data.standard_id)
    if not proposed:
        return {"methodology": data.methodology, "message": "No compliance issues found or rule already exists.", "proposed_rule": None}
    return {"methodology": data.methodology, "proposed_rule": proposed}


@router.post("/web-intelligence/knowledge-refresh")
def run_knowledge_refresh(data: KnowledgeRefreshRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY required for web intelligence.")

    from carbongpt.core.web_intelligence import research_standard_updates
    proposed_rules = research_standard_updates(data.standard, data.standard_id, data.topics)

    saved_count = 0
    if data.auto_save and proposed_rules:
        from carbongpt.repository.store import create_compliance_rule
        for rule in proposed_rules:
            try:
                create_compliance_rule(
                    rule_type=rule["rule_type"],
                    severity=rule["severity"],
                    title=rule["title"],
                    description=rule["description"],
                    conditions=rule.get("conditions", {}),
                    standard_id=rule.get("standard_id"),
                    source_url=rule.get("source_url"),
                    source_description=rule.get("source_description"),
                    status="proposed",
                    discovered_by="web_search",
                )
                saved_count += 1
            except Exception as e:
                logger.warning("Could not save proposed rule '%s': %s", rule.get("title"), e)

    return {
        "standard": data.standard,
        "proposed_rules": proposed_rules,
        "total_found": len(proposed_rules),
        "saved_count": saved_count,
    }


class MethodologySyncRequest(BaseModel):
    sources: list[str] = ["verra", "cdm", "goldstandard"]
    max_per_source: int = 50
    dry_run: bool = False
    include_program_docs: bool = True
    include_registry_projects: bool = False
    max_registry_projects: int = 5
    discover_projects: bool = False


@router.post("/methodology-sync")
def run_methodology_sync(data: MethodologySyncRequest):
    valid_sources = {"verra", "cdm", "goldstandard"}
    for s in data.sources:
        if s not in valid_sources:
            raise HTTPException(status_code=400, detail=f"Invalid source: {s}. Valid: {', '.join(valid_sources)}")

    from carbongpt.repository.methodology_sync import sync_methodologies
    result = sync_methodologies(
        sources=data.sources,
        max_per_source=data.max_per_source,
        dry_run=data.dry_run,
        include_program_docs=data.include_program_docs,
        include_registry_projects=data.include_registry_projects,
        max_registry_projects=data.max_registry_projects,
        discover_projects=data.discover_projects,
    )
    return result


@router.get("/methodology-sync/status")
def get_sync_status():
    from carbongpt.repository.methodology_sync import _scheduler_started
    from carbongpt.repository.store import list_documents
    all_docs = list_documents() or []

    by_source = {}
    by_category = {}
    for doc in all_docs:
        ref = doc.get("reference_id", "") or ""
        cat = doc.get("category", "unknown")
        by_category.setdefault(cat, 0)
        by_category[cat] += 1

        if ref.startswith("verra_"):
            by_source.setdefault("verra", 0)
            by_source["verra"] += 1
        elif ref.startswith("cdm_"):
            by_source.setdefault("cdm", 0)
            by_source["cdm"] += 1
        elif ref.startswith("goldstandard_"):
            by_source.setdefault("goldstandard", 0)
            by_source["goldstandard"] += 1
        else:
            by_source.setdefault("manual", 0)
            by_source["manual"] += 1

    return {
        "scheduler_active": _scheduler_started,
        "total_documents": len(all_docs),
        "by_source": by_source,
        "by_category": by_category,
        "sync_interval_hours": int(os.getenv("CARBONGPT_SYNC_INTERVAL_HOURS", "168")),
    }


@router.post("/sync-projects")
def sync_projects(max_verra: int = None, max_gs: int = None):
    from carbongpt.repository.project_sync import sync_all_projects
    result = sync_all_projects(max_verra=max_verra, max_gs=max_gs)
    return result


@router.get("/projects")
def get_projects(registry: str = None, country: str = None, status: str = None,
                 project_type: str = None, methodology: str = None,
                 limit: int = 100, offset: int = 0):
    from carbongpt.repository.store import list_carbon_projects
    return list_carbon_projects(
        registry=registry, country=country, status=status,
        project_type=project_type, methodology=methodology,
        limit=limit, offset=offset
    )


@router.get("/projects/analytics")
def get_project_analytics_endpoint():
    from carbongpt.repository.store import get_project_analytics
    return get_project_analytics()


@router.get("/projects/countries")
def get_project_countries():
    from carbongpt.repository.store import get_project_analytics
    analytics = get_project_analytics()
    return analytics.get("by_country", [])


@router.get("/projects/methodologies")
def get_project_methodologies(limit: int = 30):
    from carbongpt.repository.store import get_top_methodologies
    return get_top_methodologies(limit=limit)


@router.get("/projects/country/{country}")
def get_country_detail(country: str):
    from carbongpt.repository.store import get_country_details
    return get_country_details(country)


@router.get("/projects/search")
def search_projects(q: str, limit: int = 50):
    from carbongpt.repository.store import search_carbon_projects
    return search_carbon_projects(q, limit=limit)
