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


@router.post("/documents/batch-reingest")
def batch_reingest_documents():
    from carbongpt.repository.store import list_documents

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY not set.")

    all_docs = list_documents()
    needs_ingestion = []
    for doc in all_docs:
        if doc["file_type"] not in ("pdf", "docx"):
            continue
        if not doc.get("file_path") or not Path(doc["file_path"]).exists():
            continue
        has_sections = doc.get("section_count", 0) or 0
        has_chunks = doc.get("chunk_count", 0) or 0
        status = doc.get("ingestion_status", "")
        if has_sections == 0 or has_chunks == 0 or status in ("failed", "processing", None, ""):
            needs_ingestion.append(doc)

    if not needs_ingestion:
        return {"status": "ok", "message": "All documents are fully ingested.", "count": 0}

    import time as _time

    def _run_batch():
        succeeded = 0
        failed = 0
        for doc in needs_ingestion:
            try:
                from carbongpt.repository.ingestion import ingest_document
                logger.info("Batch re-ingesting doc %s: %s", doc["id"], doc["title"])
                ingest_document(doc["id"], doc["file_path"], api_key)
                succeeded += 1
                _time.sleep(0.5)
            except Exception as e:
                logger.error("Batch re-ingest failed for doc %s: %s", doc["id"], e)
                failed += 1
        logger.info("Batch re-ingest complete: %d succeeded, %d failed out of %d",
                     succeeded, failed, len(needs_ingestion))

    thread = threading.Thread(target=_run_batch, daemon=True)
    thread.start()

    return {
        "status": "started",
        "message": f"Batch re-ingestion started for {len(needs_ingestion)} documents.",
        "count": len(needs_ingestion),
        "doc_ids": [d["id"] for d in needs_ingestion],
    }


@router.post("/documents/reclassify")
def reclassify_documents():
    from carbongpt.repository.store import list_documents, update_document_metadata
    from carbongpt.repository.ingestion import classify_by_filename, classify_by_content, VALID_CATEGORIES

    all_docs = list_documents()
    reclassified = []

    for doc in all_docs:
        current_cat = doc.get("category", "")
        if current_cat not in ("other", "standard_text", None, ""):
            continue

        title = doc.get("title", "")
        filename_cat = classify_by_filename(title)

        content_cat = None
        if not filename_cat:
            from carbongpt.repository.store import get_document_sections
            sections = get_document_sections(doc["id"])
            if sections:
                preview = "\n".join(s.get("content", "")[:500] for s in sections[:5])
                from carbongpt.repository.ingestion import classify_by_content
                content_cat = classify_by_content(preview)

        new_cat = filename_cat or content_cat
        if new_cat and new_cat in VALID_CATEGORIES:
            update_document_metadata(doc["id"], category=new_cat)
            reclassified.append({
                "id": doc["id"],
                "title": title,
                "old": current_cat,
                "new": new_cat,
                "method": "filename" if filename_cat else "content",
            })

    return {
        "status": "ok",
        "reclassified": len(reclassified),
        "details": reclassified,
    }


@router.post("/documents/deduplicate")
def deduplicate_documents():
    from carbongpt.repository.store import list_documents, delete_document

    all_docs = list_documents()
    by_title: dict[str, list] = {}
    for doc in all_docs:
        title = doc.get("title", "")
        by_title.setdefault(title, []).append(doc)

    removed = []
    for title, docs in by_title.items():
        if len(docs) <= 1:
            continue
        docs_sorted = sorted(docs, key=lambda d: (
            -(d.get("chunk_count", 0) or 0),
            -(d.get("section_count", 0) or 0),
            -d.get("id", 0),
        ))
        keep = docs_sorted[0]
        for dup in docs_sorted[1:]:
            logger.info("Removing duplicate doc %s (keeping %s): %s", dup["id"], keep["id"], title)
            fp = dup.get("file_path")
            if fp and Path(fp).exists():
                Path(fp).unlink(missing_ok=True)
            delete_document(dup["id"])
            removed.append({"id": dup["id"], "title": title, "kept_id": keep["id"]})

    return {
        "status": "ok",
        "removed": len(removed),
        "details": removed,
    }


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


PRIORITY_METHODOLOGY_CODES = ["GS-TPDDTEC", "VM0050", "ACM0002", "AMS-I.D."]

METHODOLOGY_KB_CODE_MAP = {
    "GS-TPDDTEC": "TPDDTEC",
}


@router.get("/methodology-pipeline/status")
def get_methodology_pipeline_status():
    from carbongpt.repository.db import get_cursor
    results = []
    with get_cursor() as cur:
        for code in PRIORITY_METHODOLOGY_CODES:
            cur.execute("SELECT code, name, standard, sector FROM methodologies WHERE code = %s", (code,))
            meth = cur.fetchone()

            kb_code = METHODOLOGY_KB_CODE_MAP.get(code, code)

            cur.execute("SELECT count(*) as cnt FROM methodology_knowledge WHERE methodology_code = %s", (kb_code,))
            kb_count = cur.fetchone()["cnt"]

            cur.execute("""
                SELECT chunk_type, count(*) as cnt 
                FROM methodology_knowledge 
                WHERE methodology_code = %s 
                GROUP BY chunk_type ORDER BY chunk_type
            """, (kb_code,))
            chunk_breakdown = {r["chunk_type"]: r["cnt"] for r in cur.fetchall()}

            cur.execute("SELECT parse_status, model_used, parsed_at FROM methodology_parsed WHERE methodology_code = %s", (kb_code,))
            parsed = cur.fetchone()

            results.append({
                "code": code,
                "name": meth["name"] if meth else None,
                "standard": meth["standard"] if meth else None,
                "kb_chunks": kb_count,
                "chunk_breakdown": chunk_breakdown,
                "parsed": parsed["parse_status"] if parsed else "not_parsed",
                "model": parsed["model_used"] if parsed else None,
                "parsed_at": str(parsed["parsed_at"]) if parsed and parsed["parsed_at"] else None,
            })

    return {
        "priority_methodologies": results,
        "total_kb_chunks": sum(r["kb_chunks"] for r in results),
    }


@router.post("/methodology-enrich")
def run_methodology_enrich():
    from carbongpt.repository.methodology_db import enrich_from_verra_api, populate_methodologies_from_projects
    repopulated = populate_methodologies_from_projects()
    enriched = enrich_from_verra_api()
    return {"repopulated": repopulated, "enriched_from_verra_api": enriched}


@router.post("/scrape-verra-docs/{methodology_code}")
def scrape_verra_docs_for_methodology(
    methodology_code: str,
    max_projects: int = 20,
    background: bool = True,
):
    from carbongpt.repository.methodology_sync import scrape_verra_methodology_docs

    if background:
        def _run():
            try:
                result = scrape_verra_methodology_docs(
                    methodology_code=methodology_code,
                    max_projects=max_projects,
                )
                logger.info(
                    "Verra doc scrape for %s complete: %d projects, %d new docs, %d errors",
                    methodology_code,
                    result["projects_checked"],
                    result["newly_downloaded"],
                    result["errors"],
                )
            except Exception as e:
                logger.error("Verra doc scrape failed for %s: %s", methodology_code, e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return {
            "status": "started",
            "methodology": methodology_code,
            "max_projects": max_projects,
            "message": f"Background scrape started for {methodology_code}. Check logs for progress.",
        }
    else:
        result = scrape_verra_methodology_docs(
            methodology_code=methodology_code,
            max_projects=max_projects,
        )
        return result


@router.post("/scrape-verra-docs-all")
def scrape_all_priority_docs(
    max_projects_per_meth: int = 20,
    background: bool = True,
):
    from carbongpt.repository.methodology_sync import scrape_all_priority_methodology_docs

    if background:
        def _run():
            try:
                result = scrape_all_priority_methodology_docs(
                    max_projects_per_meth=max_projects_per_meth,
                )
                logger.info(
                    "Full priority doc scrape complete: %d projects, %d new docs, %d errors",
                    result["total_projects_checked"],
                    result["total_newly_downloaded"],
                    result["total_errors"],
                )
            except Exception as e:
                logger.error("Full priority doc scrape failed: %s", e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return {
            "status": "started",
            "max_projects_per_meth": max_projects_per_meth,
            "message": "Background scrape started for all priority methodologies.",
        }
    else:
        return scrape_all_priority_methodology_docs(
            max_projects_per_meth=max_projects_per_meth,
        )


@router.get("/scrape-verra-docs/stats")
def get_scraped_doc_statistics():
    from carbongpt.repository.methodology_sync import get_scraped_doc_stats
    return get_scraped_doc_stats()


@router.post("/extract-findings")
def extract_findings_from_documents(max_documents: int = 20, background: bool = True):
    from carbongpt.core.findings_extractor import extract_findings_from_all_fvr_valver

    if background:
        def _run():
            try:
                result = extract_findings_from_all_fvr_valver(max_documents=max_documents)
                logger.info(
                    "Findings extraction complete: %d processed, %d findings, %d errors",
                    result["processed"], result["total_findings"], result["errors"],
                )
            except Exception as e:
                logger.error("Findings extraction failed: %s", e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return {
            "status": "started",
            "max_documents": max_documents,
            "message": "Background findings extraction started. Check logs for progress.",
        }
    else:
        return extract_findings_from_all_fvr_valver(max_documents=max_documents)


@router.post("/extract-findings/{document_id}")
def extract_findings_single(document_id: int):
    from carbongpt.repository.store import list_documents
    from carbongpt.core.findings_extractor import process_document_for_findings

    all_docs = list_documents() or []
    doc = next((d for d in all_docs if d["id"] == document_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.get("file_path"):
        raise HTTPException(status_code=400, detail="Document has no file path")

    return process_document_for_findings(document_id, doc["file_path"])


@router.get("/findings/stats")
def get_findings_statistics():
    from carbongpt.repository.store import get_findings_stats
    return get_findings_stats()


@router.get("/findings/{methodology_code}")
def get_findings_for_methodology(methodology_code: str, finding_type: str = None, limit: int = 50):
    from carbongpt.repository.store import get_findings_by_methodology
    return get_findings_by_methodology(methodology_code, finding_type=finding_type, limit=limit)


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


_project_sync_status = {"running": False, "last_result": None}

@router.get("/reference/registries")
def get_reference_registries():
    """Return all canonical registries from ref_registries."""
    from carbongpt.repository.store import get_ref_registries
    return get_ref_registries()


@router.get("/reference/countries")
def get_reference_countries():
    """Return all canonical countries with project counts."""
    from carbongpt.repository.store import get_ref_countries
    return get_ref_countries()


@router.get("/reference/methodologies")
def get_reference_methodologies(
    family: str | None = None,
    registry: str | None = None,
    sector: str | None = None,
):
    """
    Return canonical methodologies from ref_methodologies.
    Optional query params: family, registry (slug), sector.
    """
    from carbongpt.repository.store import get_ref_methodologies
    return get_ref_methodologies(family=family, registry=registry, sector=sector)


@router.get("/market-intelligence")
def get_market_intelligence(
    country_iso: str | None = None,
    methodology_family: str | None = None,
):
    """
    Return structured Carbon Intelligence market context for a country and/or
    methodology family.  Used by the AI prompt-building layer.

    At least one of country_iso or methodology_family must be provided.
    """
    if not country_iso and not methodology_family:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="At least one of country_iso or methodology_family is required.",
        )
    from carbongpt.repository.store import get_market_intelligence_context
    return get_market_intelligence_context(
        country_iso=country_iso,
        methodology_family=methodology_family,
    )


@router.get("/projects/timeline")
def get_projects_timeline(registry: str | None = None):
    """
    Return monthly project registration counts, optionally filtered by
    ref_registry_id slug (verra, cdm, goldstandard, etc.).
    Used for the registration timeline chart.
    """
    from carbongpt.repository.store import get_registration_timeline
    return get_registration_timeline(registry=registry)


@router.post("/normalization/countries/run")
def trigger_country_normalization():
    """Backfill country_iso on all carbon_projects rows."""
    from carbongpt.repository.country_normalizer import run_country_normalization_pass
    return run_country_normalization_pass()


@router.get("/normalization/countries/coverage")
def get_country_normalization_coverage():
    """Coverage stats: how many carbon_projects have a resolved country_iso."""
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM carbon_projects")
        total = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS n FROM carbon_projects WHERE country_iso IS NOT NULL")
        resolved = cur.fetchone()["n"]
    return {
        "total":    total,
        "resolved": resolved,
        "pct":      round(resolved / total * 100, 1) if total else 0,
    }


@router.post("/normalization/registries/run")
def trigger_registry_normalization():
    """Backfill ref_registry_id on all carbon_projects rows where it is NULL."""
    from carbongpt.repository.registry_normalizer import run_registry_normalization_pass
    return run_registry_normalization_pass()


@router.get("/normalization/registries/coverage")
def get_registry_normalization_coverage_endpoint():
    """Coverage stats: how many carbon_projects have a resolved ref_registry_id."""
    from carbongpt.repository.store import get_registry_normalization_coverage
    return get_registry_normalization_coverage()


@router.get("/normalization/coverage")
def get_normalization_coverage():
    """Normalization coverage stats for both country and methodology."""
    from carbongpt.repository.store import get_normalization_coverage_stats
    return get_normalization_coverage_stats()


@router.get("/normalization/methodology-log")
def get_methodology_log(status: str = "unknown", limit: int = 100):
    """Return unmatched methodology strings queued for human review."""
    from carbongpt.repository.store import get_methodology_normalization_log
    return get_methodology_normalization_log(status=status, limit=limit)


@router.post("/normalization/methodology-log/ignore")
def ignore_methodology_log_entry(raw_string: str):
    """Mark a normalization log entry as intentionally ignored."""
    from carbongpt.repository.store import mark_normalization_log_ignored
    mark_normalization_log_ignored(raw_string)
    return {"status": "ignored", "raw_string": raw_string}


@router.post("/normalization/run")
def trigger_normalization():
    """Manually trigger a normalization pass (country + methodology)."""
    from carbongpt.repository.country_normalizer import (
        seed_countries_table, run_country_normalization_pass,
    )
    from carbongpt.repository.methodology_normalizer import (
        seed_methodology_library_from_db, run_methodology_normalization_pass,
    )
    seed_countries_table()
    seed_methodology_library_from_db()
    country_result = run_country_normalization_pass()
    meth_result    = run_methodology_normalization_pass()
    return {"country": country_result, "methodology": meth_result}


@router.get("/normalization/methodology-families")
def get_methodology_families():
    """Return project counts grouped by normalized methodology family."""
    from carbongpt.repository.store import get_methodology_family_analytics
    return get_methodology_family_analytics()


@router.get("/sync-projects/schedule")
def get_registry_sync_schedule():
    """Return the state of the registry sync scheduler."""
    from carbongpt.repository.project_sync import get_registry_scheduler_state
    return get_registry_scheduler_state()


@router.post("/sync-projects")
def sync_projects(
    max_verra: int = None,
    max_gs: int = None,
    max_cdm: int = None,
    background: bool = True,
):
    """Trigger a full sync of Verra, Gold Standard, and CDM projects."""
    import threading
    from carbongpt.repository.project_sync import sync_all_projects

    if _project_sync_status["running"]:
        return {"status": "already_running", "message": "A project sync is already in progress."}

    if not background:
        result = sync_all_projects(max_verra=max_verra, max_gs=max_gs, max_cdm=max_cdm)
        _project_sync_status["last_result"] = result
        return result

    def _run_sync():
        _project_sync_status["running"] = True
        try:
            result = sync_all_projects(max_verra=max_verra, max_gs=max_gs, max_cdm=max_cdm)
            _project_sync_status["last_result"] = result
        except Exception as e:
            _project_sync_status["last_result"] = {"error": str(e)}
        finally:
            _project_sync_status["running"] = False

    threading.Thread(target=_run_sync, daemon=True).start()
    return {"status": "started", "message": "Project sync started in background. Check /admin/sync-projects/status for progress."}


@router.post("/sync-projects/cdm")
def sync_cdm_only(max_cdm: int = None, background: bool = True):
    """Trigger a CDM-only sync without touching Verra or Gold Standard."""
    import threading
    from carbongpt.repository.project_sync import sync_cdm_projects

    if _project_sync_status["running"]:
        return {"status": "already_running", "message": "A sync is already in progress."}

    if not background:
        result = sync_cdm_projects(max_projects=max_cdm)
        _project_sync_status["last_result"] = {"cdm": result}
        return result

    def _run():
        _project_sync_status["running"] = True
        try:
            result = sync_cdm_projects(max_projects=max_cdm)
            _project_sync_status["last_result"] = {"cdm": result}
        except Exception as e:
            _project_sync_status["last_result"] = {"cdm": {"error": str(e)}}
        finally:
            _project_sync_status["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "message": "CDM sync started in background."}


@router.get("/sync-projects/status")
def get_sync_status():
    from carbongpt.repository.store import get_project_count
    count = get_project_count()
    return {
        "running": _project_sync_status["running"],
        "total_projects_in_db": count,
        "last_result": _project_sync_status["last_result"],
    }


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


@router.get("/projects/methodologies/family")
def get_methodology_family_analytics():
    """
    Return project counts and estimated credits grouped by methodology family,
    using the normalized project_methodology_codes → methodology_library tables.
    """
    from carbongpt.repository.store import get_normalized_methodology_family_analytics
    return get_normalized_methodology_family_analytics()


@router.get("/projects/country/{country}")
def get_country_detail(country: str):
    from carbongpt.repository.store import get_country_details
    return get_country_details(country)


@router.get("/projects/search")
def search_projects(q: str, limit: int = 50):
    from carbongpt.repository.store import search_carbon_projects
    return search_carbon_projects(q, limit=limit)


@router.get("/methodology-parsed")
def list_parsed_methodologies_endpoint():
    from carbongpt.repository.store import list_parsed_methodologies
    rows = list_parsed_methodologies()
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "methodology_code": r["methodology_code"],
            "document_id": r.get("document_id"),
            "document_title": r.get("document_title"),
            "model_used": r.get("model_used"),
            "parse_status": r.get("parse_status"),
            "parse_error": r.get("parse_error"),
            "parsed_at": str(r.get("parsed_at", "")),
        })
    return result


@router.post("/methodology-parsed/parse")
def parse_single_methodology(methodology_code: str, force: bool = False):
    from carbongpt.core.methodology_parser import parse_methodology_and_save
    try:
        parsed = parse_methodology_and_save(methodology_code, force=force)
        methods_count = len(parsed.get("calculation_methods", []))
        params_count = len(parsed.get("parameters", []))
        return {
            "status": "success",
            "methodology_code": methodology_code,
            "methods": methods_count,
            "parameters": params_count,
        }
    except Exception as e:
        logger.error("Parse methodology failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/methodology-parsed/batch")
def batch_parse_methodologies_endpoint(force: bool = False, codes: list[str] = None):
    import threading
    from carbongpt.core.methodology_parser import batch_parse_methodologies

    def _run_batch():
        try:
            result = batch_parse_methodologies(codes=codes, force=force)
            logger.info("Batch methodology parse complete: %s", result)
        except Exception as e:
            logger.error("Batch methodology parse failed: %s", e)

    thread = threading.Thread(target=_run_batch, daemon=True)
    thread.start()
    return {"status": "started", "message": "Batch methodology parsing started in background."}


@router.post("/methodology-kb/build/{methodology_code}")
def build_methodology_kb(methodology_code: str, document_id: int = None, force: bool = False):
    from carbongpt.core.methodology_kb import build_methodology_knowledge
    from carbongpt.core.methodology_parser import get_methodology_sections

    if not document_id:
        sections_data = get_methodology_sections(methodology_code)
        if not sections_data:
            raise HTTPException(status_code=404, detail=f"No methodology document found for '{methodology_code}'")
        document_id = sections_data["doc_id"]

    try:
        result = build_methodology_knowledge(document_id, methodology_code, force=force)
        return result
    except Exception as e:
        logger.error("KB build failed for %s: %s", methodology_code, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/methodology-kb/{methodology_code}")
def get_methodology_kb(methodology_code: str, chunk_type: str = None):
    from carbongpt.core.methodology_kb import get_methodology_knowledge
    knowledge = get_methodology_knowledge(methodology_code, chunk_type)
    if not knowledge:
        raise HTTPException(status_code=404, detail=f"No knowledge base found for '{methodology_code}'")
    total_chunks = sum(len(v) for v in knowledge.values())
    return {
        "methodology_code": methodology_code,
        "total_chunks": total_chunks,
        "chunk_types": {k: len(v) for k, v in knowledge.items()},
        "chunks": knowledge,
    }


@router.get("/methodology-kb/{methodology_code}/structure")
def get_methodology_structure_endpoint(methodology_code: str):
    from carbongpt.repository.store import get_methodology_structure
    from carbongpt.core.methodology_parser import get_methodology_sections

    sections_data = get_methodology_sections(methodology_code)
    if not sections_data:
        raise HTTPException(status_code=404, detail=f"No methodology document found for '{methodology_code}'")

    structure = get_methodology_structure(sections_data["doc_id"])
    if not structure:
        from carbongpt.core.methodology_kb import detect_document_structure
        detected_format, section_map = detect_document_structure(sections_data["doc_id"], methodology_code)
        return {
            "methodology_code": methodology_code,
            "document_id": sections_data["doc_id"],
            "detected_format": detected_format,
            "section_map": section_map,
            "cached": False,
        }

    return {
        "methodology_code": methodology_code,
        "document_id": structure["document_id"],
        "detected_format": structure["detected_format"],
        "section_map": structure["section_map"],
        "cached": True,
    }


@router.post("/methodology-kb/batch")
def batch_build_kb(force: bool = False, limit: int = None):
    import threading
    from carbongpt.core.methodology_kb import batch_build_knowledge

    def _run_batch():
        try:
            result = batch_build_knowledge(force=force, limit=limit)
            logger.info("Batch KB build complete: %s", result)
        except Exception as e:
            logger.error("Batch KB build failed: %s", e)

    thread = threading.Thread(target=_run_batch, daemon=True)
    thread.start()
    return {"status": "started", "message": "Batch knowledge base build started in background."}
