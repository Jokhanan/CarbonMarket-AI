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
def search_documents(q: str, limit: int = 10, standard_version_id: int = None):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY required for semantic search.")

    from carbongpt.repository.ingestion import create_embeddings
    from carbongpt.repository.store import search_chunks

    query_embedding = create_embeddings([q], api_key)[0]
    results = search_chunks(query_embedding, limit=limit, standard_version_id=standard_version_id)
    return results
