import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from carbongpt.app.config import BASE_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

PROJECT_FILES_DIR = BASE_DIR / "project_files"
PROJECT_FILES_DIR.mkdir(parents=True, exist_ok=True)


class ProjectCreate(BaseModel):
    name: str
    standard: str
    doc_type: str | None = None
    methodology: str | None = None
    country: str | None = None
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    standard: str | None = None
    doc_type: str | None = None
    methodology: str | None = None
    country: str | None = None
    description: str | None = None
    status: str | None = None


class WriteSectionRequest(BaseModel):
    section_id: str
    user_instructions: str | None = None


class ExplainSectionRequest(BaseModel):
    section_id: str


class ReviewDocumentRequest(BaseModel):
    document_id: int


@router.get("")
def list_projects(status: str = None):
    from carbongpt.repository.store import list_user_projects
    return list_user_projects(status=status)


@router.post("")
def create_project(data: ProjectCreate):
    from carbongpt.repository.store import create_user_project
    project_id = create_user_project(
        name=data.name,
        standard=data.standard,
        doc_type=data.doc_type,
        methodology=data.methodology,
        country=data.country,
        description=data.description,
    )
    project_dir = PROJECT_FILES_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    return {"id": project_id, "message": "Project created."}


@router.get("/{project_id}")
def get_project(project_id: int):
    from carbongpt.repository.store import get_user_project
    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.patch("/{project_id}")
def update_project(project_id: int, data: ProjectUpdate):
    from carbongpt.repository.store import get_user_project, update_user_project
    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    update_user_project(project_id, **data.dict(exclude_none=True))
    return {"message": "Project updated."}


@router.delete("/{project_id}")
def delete_project(project_id: int):
    from carbongpt.repository.store import delete_user_project
    delete_user_project(project_id)
    return {"message": "Project deleted."}


@router.post("/{project_id}/documents")
def upload_project_document(
    project_id: int,
    file: UploadFile = File(...),
    doc_type: str = Form("other"),
    notes: str = Form(None),
):
    from carbongpt.repository.store import get_user_project, add_project_document, update_project_document

    VALID_DOC_TYPES = {"pdd", "mr", "valver", "poa_dd", "vpa_dd", "reference", "research", "field_data", "template", "other"}
    if doc_type not in VALID_DOC_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid doc_type '{doc_type}'. Must be one of: {', '.join(sorted(VALID_DOC_TYPES))}")

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "other"
    file_type_map = {"pdf": "pdf", "docx": "docx", "xlsx": "xlsx", "csv": "csv"}
    file_type = file_type_map.get(ext, "other")

    project_dir = PROJECT_FILES_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = project_dir / safe_name
    content = file.file.read()
    file_path.write_bytes(content)

    doc_id = add_project_document(
        project_id=project_id,
        doc_type=doc_type,
        file_name=file.filename,
        file_path=str(file_path),
        file_type=file_type,
        file_size_bytes=len(content),
        notes=notes,
    )

    parsed_text = None
    parsed_sections = []
    try:
        if file_type == "docx":
            from carbongpt.tools.parse_docx import parse_docx
            result = parse_docx(str(file_path))
            parsed_text = result.get("full_text", "")
            parsed_sections = [
                {"heading": s.get("heading", ""), "text": s.get("text", "")[:500]}
                for s in result.get("sections", [])
            ]
        elif file_type == "pdf":
            try:
                import pdfplumber
                text_parts = []
                with pdfplumber.open(str(file_path)) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            text_parts.append(t)
                parsed_text = "\n".join(text_parts)
            except Exception as e:
                logger.warning("PDF parsing failed: %s", e)
    except Exception as e:
        logger.warning("Document parsing failed: %s", e)

    if parsed_text:
        import json
        update_project_document(
            doc_id,
            parsed_text=parsed_text,
            parsed_sections=json.dumps(parsed_sections),
            status="parsed",
        )

    return {
        "id": doc_id,
        "file_name": file.filename,
        "doc_type": doc_type,
        "parsed": parsed_text is not None,
        "message": "Document uploaded successfully.",
    }


@router.delete("/{project_id}/documents/{doc_id}")
def delete_document(project_id: int, doc_id: int):
    from carbongpt.repository.store import get_project_document, delete_project_document
    doc = get_project_document(doc_id)
    if not doc or doc["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        os.remove(doc["file_path"])
    except OSError:
        pass
    delete_project_document(doc_id)
    return {"message": "Document deleted."}


@router.get("/{project_id}/sections")
def get_document_sections(project_id: int, doc_type: str = "pdd"):
    from carbongpt.repository.store import get_user_project
    from carbongpt.core.ai_writer import get_sections_for_doc_type

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    sections = get_sections_for_doc_type(project["standard"], doc_type)
    if sections is None:
        raise HTTPException(status_code=400, detail=f"No guide available for {project['standard']}/{doc_type}")
    return sections


@router.post("/{project_id}/write")
def write_section(project_id: int, data: WriteSectionRequest, doc_type: str = "pdd"):
    from carbongpt.repository.store import (
        get_user_project, get_project_documents_by_type,
        save_write_session
    )
    from carbongpt.core.ai_writer import generate_section_draft

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    project_info = {
        "name": project["name"],
        "methodology": project.get("methodology"),
        "country": project.get("country"),
        "description": project.get("description"),
    }

    pdd_text = None
    if doc_type == "mr":
        pdd_docs = get_project_documents_by_type(project_id, "pdd")
        if pdd_docs:
            pdd_text = pdd_docs[0].get("parsed_text", "")

    ref_texts = []
    for ref_type in ["reference", "research", "field_data"]:
        ref_docs = get_project_documents_by_type(project_id, ref_type)
        for rd in ref_docs:
            if rd.get("parsed_text"):
                ref_texts.append(rd["parsed_text"][:2000])
    reference_text = "\n---\n".join(ref_texts) if ref_texts else None

    try:
        generated = generate_section_draft(
            standard=project["standard"],
            project_doc_type=doc_type,
            section_id=data.section_id,
            project_info=project_info,
            existing_pdd_text=pdd_text,
            reference_docs_text=reference_text,
            user_instructions=data.user_instructions,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("AI writing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"AI writing failed: {e}")

    from carbongpt.core.ai_writer import get_sections_for_doc_type
    sections = get_sections_for_doc_type(project["standard"], doc_type) or []
    section_title = ""
    for s in sections:
        if s["id"] == data.section_id:
            section_title = s["title"]
            break

    session_id = save_write_session(
        project_id=project_id,
        doc_type=doc_type,
        section_id=data.section_id,
        section_title=section_title,
        generated_text=generated,
    )

    return {
        "session_id": session_id,
        "section_id": data.section_id,
        "section_title": section_title,
        "generated_text": generated,
    }


@router.post("/{project_id}/explain")
def explain_section_endpoint(project_id: int, data: ExplainSectionRequest, doc_type: str = "pdd"):
    from carbongpt.repository.store import get_user_project
    from carbongpt.core.ai_writer import explain_section

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        explanation = explain_section(
            standard=project["standard"],
            project_doc_type=doc_type,
            section_id=data.section_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Explain section failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Explain failed: {e}")

    return {"section_id": data.section_id, "explanation": explanation}


@router.post("/{project_id}/review/{doc_id}")
def review_document(project_id: int, doc_id: int):
    from carbongpt.repository.store import (
        get_user_project, get_project_document,
        get_project_documents_by_type, update_project_document
    )
    from carbongpt.core.ai_writer import review_with_context

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    doc = get_project_document(doc_id)
    if not doc or doc["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not doc.get("parsed_text"):
        raise HTTPException(status_code=400, detail="Document has not been parsed. Please upload a DOCX or PDF file.")

    project_info = {
        "name": project["name"],
        "methodology": project.get("methodology"),
        "country": project.get("country"),
        "description": project.get("description"),
    }

    pdd_text = None
    if doc["doc_type"] == "mr":
        pdd_docs = get_project_documents_by_type(project_id, "pdd")
        if pdd_docs:
            pdd_text = pdd_docs[0].get("parsed_text", "")

    ref_texts = []
    for ref_type in ["reference", "research", "field_data"]:
        ref_docs = get_project_documents_by_type(project_id, ref_type)
        for rd in ref_docs:
            if rd.get("parsed_text"):
                ref_texts.append(rd["parsed_text"][:2000])
    reference_text = "\n---\n".join(ref_texts) if ref_texts else None

    try:
        review_result = review_with_context(
            standard=project["standard"],
            project_doc_type=doc["doc_type"],
            document_text=doc["parsed_text"],
            project_info=project_info,
            pdd_text=pdd_text,
            reference_texts=reference_text,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Review failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Review failed: {e}")

    from psycopg2.extras import Json
    update_project_document(
        doc_id,
        review_result=Json(review_result),
        status="reviewed",
    )

    return review_result


@router.get("/{project_id}/write-sessions")
def get_write_sessions_endpoint(project_id: int, doc_type: str = None):
    from carbongpt.repository.store import get_write_sessions
    return get_write_sessions(project_id, doc_type=doc_type)
