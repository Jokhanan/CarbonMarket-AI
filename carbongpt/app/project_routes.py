import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
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
    project_type: str | None = None
    parent_project_id: int | None = None
    monitoring_period_start: str | None = None
    monitoring_period_end: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    standard: str | None = None
    doc_type: str | None = None
    methodology: str | None = None
    country: str | None = None
    description: str | None = None
    status: str | None = None
    crediting_period_start: str | None = None
    crediting_period_years: int | None = None
    project_settings: dict | None = None
    project_intake: dict | None = None
    project_type: str | None = None
    parent_project_id: int | None = None
    monitoring_period_start: str | None = None
    monitoring_period_end: str | None = None


class WriteSectionRequest(BaseModel):
    section_id: str
    user_instructions: str | None = None


class WriteAllRequest(BaseModel):
    user_instructions: str | None = None


class UpdateSectionTextRequest(BaseModel):
    section_id: str
    doc_type: str = "pdd"
    text: str


class ExplainSectionRequest(BaseModel):
    section_id: str


class ParseMethodologyRequest(BaseModel):
    methodology_code: str


class RunCalculationRequest(BaseModel):
    method_id: str | None = None
    crediting_years: int = 7
    user_inputs: dict = Field(default_factory=dict)


class ExportCalculationRequest(BaseModel):
    calculation_result: dict
    format: str = "excel"


class GenerateTemplateRequest(BaseModel):
    doc_type: str = "pdd"
    sections_to_generate: list[str] | None = None
    include_calculations: bool = True
    calculation_result: dict | None = None
    user_instructions: str | None = None


class ReviewDocumentRequest(BaseModel):
    document_id: int


@router.get("/methodologies")
def get_methodologies(standard: str = None, category: str = None, search: str = None, limit: int = 200):
    from carbongpt.repository.store import list_methodologies
    return list_methodologies(standard=standard, category=category, search=search, limit=limit)


@router.get("/methodologies/categories")
def get_methodology_categories_endpoint():
    from carbongpt.repository.store import get_methodology_categories
    return get_methodology_categories()


@router.get("/methodologies/{code}")
def get_methodology_detail(code: str):
    from carbongpt.repository.store import get_methodology
    m = get_methodology(code)
    if not m:
        raise HTTPException(status_code=404, detail="Methodology not found.")
    return m


@router.post("/methodologies/populate")
def populate_methodologies():
    from carbongpt.repository.methodology_db import populate_methodologies_from_projects
    count = populate_methodologies_from_projects()
    return {"populated": count}


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
        project_type=data.project_type,
        parent_project_id=data.parent_project_id,
        monitoring_period_start=data.monitoring_period_start,
        monitoring_period_end=data.monitoring_period_end,
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


@router.get("/{project_id}/children")
def get_child_projects_endpoint(project_id: int):
    from carbongpt.repository.store import get_child_projects
    return get_child_projects(project_id)


@router.patch("/{project_id}/documents/{doc_id}/ai-context")
def toggle_document_ai_context(project_id: int, doc_id: int, use_as_ai_context: bool = True):
    from carbongpt.repository.store import get_project_document, update_document_ai_context
    doc = get_project_document(doc_id)
    if not doc or doc["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Document not found.")
    update_document_ai_context(doc_id, use_as_ai_context)
    return {"message": "AI context updated.", "use_as_ai_context": use_as_ai_context}


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

    ai_summary = None
    if parsed_text:
        import json
        update_project_document(
            doc_id,
            parsed_text=parsed_text,
            parsed_sections=json.dumps(parsed_sections),
            status="parsed",
        )

        try:
            from carbongpt.core.ai_writer import extract_document_intelligence
            ai_summary = extract_document_intelligence(parsed_text, file.filename, doc_type)
            if ai_summary:
                update_project_document(doc_id, ai_extracted_summary=ai_summary)
        except Exception as e:
            logger.warning("AI extraction failed for %s: %s", file.filename, e)

    return {
        "id": doc_id,
        "file_name": file.filename,
        "doc_type": doc_type,
        "parsed": parsed_text is not None,
        "ai_extracted": ai_summary is not None,
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


@router.post("/{project_id}/documents/{doc_id}/extract-intelligence")
def extract_document_intel(project_id: int, doc_id: int):
    from carbongpt.repository.store import get_project_document, update_project_document
    doc = get_project_document(doc_id)
    if not doc or doc["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not doc.get("parsed_text"):
        raise HTTPException(status_code=400, detail="Document has not been parsed yet.")
    try:
        from carbongpt.core.ai_writer import extract_document_intelligence
        summary = extract_document_intelligence(doc["parsed_text"], doc["file_name"], doc["doc_type"])
        if summary:
            update_project_document(doc_id, ai_extracted_summary=summary)
            return {"message": "Intelligence extracted.", "summary": summary}
        return {"message": "Extraction returned no results."}
    except Exception as e:
        logger.error("Intelligence extraction failed for doc %s: %s", doc_id, e)
        raise HTTPException(status_code=500, detail="Intelligence extraction failed. Please try again.")


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


def _gather_ai_context(project_id, project, doc_type):
    from carbongpt.repository.store import get_project_documents_for_ai, get_project_documents_by_type
    pdd_text = None
    if doc_type == "mr":
        pdd_docs = get_project_documents_by_type(project_id, "pdd")
        if pdd_docs:
            pdd_text = pdd_docs[0].get("parsed_text", "")
        if not pdd_text and project.get("parent_project_id"):
            parent_pdd_docs = get_project_documents_by_type(project["parent_project_id"], "pdd")
            if parent_pdd_docs:
                pdd_text = parent_pdd_docs[0].get("parsed_text", "")

    DOC_TYPE_LABELS = {
        "pdd": "PDD", "mr": "Monitoring Report", "poa_dd": "PoA-DD",
        "vpa_dd": "VPA-DD", "valver": "Validation/Verification Report",
        "reference": "Reference Document", "research": "Research",
        "field_data": "Field Data / Survey", "other": "Supporting Document",
    }

    MAX_RAW_FALLBACK = 12000
    MAX_TOTAL_REF = 50000

    MAX_SUMMARY = 8000

    def _doc_text(rd, prefix="Document"):
        label = DOC_TYPE_LABELS.get(rd.get("doc_type", "other"), rd.get("doc_type", "other"))
        fname = rd.get("file_name", "")
        header = f"[{prefix}: {fname} | Type: {label}]"
        summary = (rd.get("ai_extracted_summary") or "").strip()
        if summary:
            text = summary[:MAX_SUMMARY]
            return f"{header}\n{text}"
        raw = rd.get("parsed_text", "")
        if raw:
            text = raw[:MAX_RAW_FALLBACK]
            if len(raw) > MAX_RAW_FALLBACK:
                text += "\n[... document truncated, AI extraction not yet run ...]"
            return f"{header}\n{text}"
        return None

    ai_docs = get_project_documents_for_ai(project_id)
    ref_parts = []
    for rd in ai_docs:
        if not rd.get("parsed_text") and not rd.get("ai_extracted_summary"):
            continue
        rd_type = rd.get("doc_type", "other")
        if rd_type == "pdd" and doc_type == "mr" and not pdd_text:
            pdd_text = rd.get("parsed_text", "")
            continue
        part = _doc_text(rd)
        if part:
            ref_parts.append(part)

    if project.get("parent_project_id"):
        parent_ai_docs = get_project_documents_for_ai(project["parent_project_id"])
        for rd in parent_ai_docs:
            part = _doc_text(rd, prefix="Parent Project Document")
            if part:
                ref_parts.append(part)

    combined = "\n\n---\n\n".join(ref_parts) if ref_parts else None
    if combined and len(combined) > MAX_TOTAL_REF:
        combined = combined[:MAX_TOTAL_REF] + "\n[... remaining documents truncated ...]"
    reference_text = combined
    return pdd_text, reference_text


@router.post("/{project_id}/write")
def write_section(project_id: int, data: WriteSectionRequest, doc_type: str = "pdd"):
    from carbongpt.repository.store import (
        get_user_project, save_write_session
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
        "project_intake": project.get("project_intake") or {},
        "project_settings": project.get("project_settings") or {},
    }

    pdd_text, reference_text = _gather_ai_context(project_id, project, doc_type)

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


@router.post("/{project_id}/write-all")
def write_all_sections(project_id: int, data: WriteAllRequest, doc_type: str = "pdd"):
    from carbongpt.repository.store import (
        get_user_project, save_write_session
    )
    from carbongpt.core.ai_writer import generate_full_document

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    project_info = {
        "name": project["name"],
        "methodology": project.get("methodology"),
        "country": project.get("country"),
        "description": project.get("description"),
        "project_intake": project.get("project_intake") or {},
        "project_settings": project.get("project_settings") or {},
    }

    pdd_text, reference_text = _gather_ai_context(project_id, project, doc_type)

    try:
        results = generate_full_document(
            standard=project["standard"],
            project_doc_type=doc_type,
            project_info=project_info,
            existing_pdd_text=pdd_text,
            reference_docs_text=reference_text,
            user_instructions=data.user_instructions,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("AI full document generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"AI full document generation failed: {e}")

    for r in results:
        if r["status"] == "success" and r["generated_text"]:
            save_write_session(
                project_id=project_id,
                doc_type=doc_type,
                section_id=r["section_id"],
                section_title=r["section_title"],
                generated_text=r["generated_text"],
            )

    return {
        "sections": results,
        "total": len(results),
        "success_count": sum(1 for r in results if r["status"] == "success"),
    }


@router.patch("/{project_id}/section-text")
def update_section_text(project_id: int, data: UpdateSectionTextRequest):
    from carbongpt.repository.store import get_user_project, save_write_session
    from carbongpt.core.ai_writer import get_sections_for_doc_type

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    sections = get_sections_for_doc_type(project["standard"], data.doc_type) or []
    section_title = ""
    for s in sections:
        if s["id"] == data.section_id:
            section_title = s["title"]
            break

    session_id = save_write_session(
        project_id=project_id,
        doc_type=data.doc_type,
        section_id=data.section_id,
        section_title=section_title,
        generated_text=data.text,
        user_text=data.text,
    )

    return {"session_id": session_id, "section_id": data.section_id, "saved": True}


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
        "project_intake": project.get("project_intake") or {},
        "project_settings": project.get("project_settings") or {},
    }

    pdd_text, reference_text = _gather_ai_context(project_id, project, doc["doc_type"])

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


@router.post("/{project_id}/review-draft")
def review_draft(project_id: int, doc_type: str = "pdd"):
    from carbongpt.repository.store import get_user_project, get_write_sessions
    from carbongpt.core.ai_writer import review_with_context

    valid_doc_types = {"pdd", "mr", "poa_dd", "vpa_dd", "valver"}
    if doc_type not in valid_doc_types:
        raise HTTPException(status_code=400, detail=f"Invalid doc_type: {doc_type}. Must be one of: {', '.join(sorted(valid_doc_types))}")

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    sessions = get_write_sessions(project_id, doc_type=doc_type)
    if not sessions:
        raise HTTPException(status_code=400, detail="No drafted sections found for this document type.")

    draft_parts = []
    for sess in sessions:
        text = sess.get("user_text") or sess.get("generated_text") or ""
        if text.strip():
            section_id = sess.get("section_id", "")
            section_title = sess.get("section_title", "")
            draft_parts.append(f"## {section_id} {section_title}\n\n{text}")

    if not draft_parts:
        raise HTTPException(status_code=400, detail="All drafted sections are empty.")

    document_text = "\n\n---\n\n".join(draft_parts)

    project_info = {
        "name": project["name"],
        "methodology": project.get("methodology"),
        "country": project.get("country"),
        "description": project.get("description"),
        "project_intake": project.get("project_intake") or {},
        "project_settings": project.get("project_settings") or {},
    }

    pdd_text, reference_text = _gather_ai_context(project_id, project, doc_type)

    try:
        review_result = review_with_context(
            standard=project["standard"],
            project_doc_type=doc_type,
            document_text=document_text,
            project_info=project_info,
            pdd_text=pdd_text,
            reference_texts=reference_text,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Draft review failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Draft review failed: {e}")

    return review_result


@router.post("/{project_id}/respond-to-finding")
def respond_to_finding(project_id: int, data: dict):
    from carbongpt.repository.store import get_user_project, get_write_sessions
    from carbongpt.core.ai_writer import _call_openai

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    finding_text = data.get("finding_text", "")
    finding_type = data.get("finding_type", "CL")
    pdd_section = data.get("pdd_section", "")
    doc_type = data.get("doc_type", "pdd")

    if not finding_text:
        raise HTTPException(status_code=400, detail="finding_text is required")

    project_info = {
        "name": project["name"],
        "methodology": project.get("methodology"),
        "country": project.get("country"),
        "description": project.get("description"),
        "project_intake": project.get("project_intake") or {},
        "project_settings": project.get("project_settings") or {},
    }

    pdd_text, reference_text = _gather_ai_context(project_id, project, doc_type)

    relevant_section_text = ""
    if pdd_section:
        sessions = get_write_sessions(project_id, doc_type=doc_type)
        for sess in sessions:
            if pdd_section.lower() in (sess.get("section_id", "") or "").lower():
                relevant_section_text = sess.get("user_text") or sess.get("generated_text") or ""
                break

    from carbongpt.core.ai_writer import STANDARD_LABELS, DOC_TYPE_LABELS, get_guide_doc_type
    std_label = STANDARD_LABELS.get(project["standard"], project["standard"])

    system_prompt = (
        f"You are an expert carbon project developer responding to a {finding_type} "
        f"(finding) raised by a VVB or standard body ({std_label}) during validation/verification.\n\n"
        "RULES:\n"
        "- Draft a professional, detailed response that directly addresses the finding.\n"
        "- Reference specific project data, methodology clauses, and evidence.\n"
        "- If the PDD or document needs to be updated, clearly state what changes are needed.\n"
        "- Follow the standard response format: acknowledge the issue, explain the resolution, cite evidence.\n"
        "- Be thorough but concise. VVBs appreciate clear, well-structured responses.\n"
        "- Format your response as JSON with keys: 'response_text', 'pdd_updates_needed' (array of {section, change_description}), "
        "'evidence_to_provide' (array of strings), 'response_approach' (one of: pdd_update, clarification, evidence_provided, calculation_corrected, methodology_reference)"
    )

    user_prompt = f"## Finding to respond to:\n"
    user_prompt += f"**Type:** {finding_type}\n"
    user_prompt += f"**PDD Section:** {pdd_section or 'Not specified'}\n"
    user_prompt += f"**Finding:**\n{finding_text}\n\n"

    user_prompt += f"### Project Information:\n"
    user_prompt += f"- Project: {project_info.get('name', 'Unknown')}\n"
    user_prompt += f"- Standard: {std_label}\n"
    user_prompt += f"- Methodology: {project_info.get('methodology', 'Not specified')}\n"
    user_prompt += f"- Country: {project_info.get('country', 'Not specified')}\n\n"

    if relevant_section_text:
        user_prompt += (
            f"### Current content of section {pdd_section}:\n"
            f'"""\n{relevant_section_text[:4000]}\n"""\n\n'
        )

    if pdd_text:
        user_prompt += (
            "### PDD content for reference:\n"
            f'"""\n{pdd_text[:4000]}\n"""\n\n'
        )

    findings_context = ""
    try:
        methodology = project_info.get("methodology", "")
        if methodology:
            from carbongpt.repository.store import get_findings_by_methodology
            similar = get_findings_by_methodology(methodology, limit=20)
            relevant_similar = [
                f for f in similar
                if f.get("resolution") and (
                    (f.get("topic") or "").lower() in finding_text.lower()
                    or (f.get("pdd_section") or "").lower() == (pdd_section or "").lower()
                )
            ][:5]
            if relevant_similar:
                findings_context = "### How similar findings were resolved on other projects:\n"
                for sf in relevant_similar:
                    findings_context += f"- [{sf['finding_type']}] {sf.get('topic', '')}: {sf.get('description', '')[:200]}\n"
                    findings_context += f"  Resolution: {sf.get('resolution', '')[:200]}\n"
                    findings_context += f"  Approach: {sf.get('resolution_approach', '')}\n\n"
    except Exception as e:
        logger.warning("Failed to get similar findings: %s", e)

    if findings_context:
        user_prompt += findings_context + "\n"

    user_prompt += "Draft a professional response to this finding."

    try:
        import openai, json, os as _os
        api_key = _os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=3000,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        logger.error("Finding response generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"AI response generation failed: {e}")


@router.post("/{project_id}/parse-findings-document")
def parse_findings_document(
    project_id: int,
    file: UploadFile = File(...),
):
    from carbongpt.repository.store import get_user_project

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    MAX_FILE_SIZE = 20 * 1024 * 1024
    import tempfile
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    tmp.write(content)
    tmp.close()

    parsed_text = ""
    try:
        if ext == "pdf":
            import pdfplumber
            text_parts = []
            with pdfplumber.open(tmp.name) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
            parsed_text = "\n".join(text_parts)
        elif ext == "docx":
            from carbongpt.tools.parse_docx import parse_docx
            result = parse_docx(tmp.name)
            sections = result.get("sections", {})
            parsed_text = "\n\n".join(
                f"### {k}\n{v}" if k != "__PREAMBLE__" else v
                for k, v in sections.items() if v
            )
    except Exception as e:
        logger.error("Failed to parse findings document: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {e}")
    finally:
        os.unlink(tmp.name)

    if not parsed_text or len(parsed_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not extract meaningful text from the document.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable.")

    max_chunk_chars = 12000
    chunks = []
    words = parsed_text.split()
    current_chunk = []
    current_len = 0
    for word in words:
        current_chunk.append(word)
        current_len += len(word) + 1
        if current_len >= max_chunk_chars:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_len = 0
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    extraction_prompt = (
        "You are an expert carbon credit auditor. Extract ALL individual findings "
        "(CARs, CLs, FARs, observations, PRR comments) from the document text below.\n\n"
        "For each finding, provide:\n"
        "- finding_type: 'CAR' | 'CL' | 'FAR' | 'observation' | 'prr_comment'\n"
        "- finding_id: the original ID from the document (e.g., 'CAR #1', 'CL 05')\n"
        "- pdd_section: which PDD/MR section this relates to\n"
        "- description: the VVB's or reviewer's question/concern (the actual finding text)\n"
        "- topic: short categorization (e.g., 'baseline scenario', 'monitoring parameters')\n\n"
        "Return JSON: {\"findings\": [...]}. If no findings found, return {\"findings\": []}.\n"
        "Be thorough - extract EVERY finding including minor clarifications.\n\n"
        "Document text:\n"
    )

    all_findings = []
    failed_chunks = []
    import openai, json
    client = openai.OpenAI(api_key=api_key)

    for i, chunk in enumerate(chunks):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": extraction_prompt},
                    {"role": "user", "content": chunk},
                ],
                max_tokens=4000,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            chunk_findings = result.get("findings", [])
            all_findings.extend(chunk_findings)
            logger.info("Chunk %d/%d: extracted %d findings", i + 1, len(chunks), len(chunk_findings))
        except Exception as e:
            logger.warning("Findings extraction failed for chunk %d: %s", i + 1, e)
            failed_chunks.append({"chunk": i + 1, "error": str(e)})

    if failed_chunks and not all_findings:
        raise HTTPException(
            status_code=500,
            detail=f"AI extraction failed for all {len(chunks)} document sections. First error: {failed_chunks[0]['error']}"
        )

    seen = set()
    unique_findings = []
    for f in all_findings:
        key = (f.get("finding_id", ""), f.get("description", "")[:80])
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    return {
        "findings": unique_findings,
        "total": len(unique_findings),
        "document_name": file.filename,
        "text_length": len(parsed_text),
        "chunks_processed": len(chunks),
        "chunks_failed": len(failed_chunks),
        "warnings": [f"Chunk {fc['chunk']} failed: {fc['error'][:100]}" for fc in failed_chunks] if failed_chunks else [],
    }


@router.post("/{project_id}/batch-respond-to-findings")
def batch_respond_to_findings(project_id: int, data: dict):
    from carbongpt.repository.store import get_user_project, get_write_sessions

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    findings = data.get("findings", [])
    doc_type = data.get("doc_type", "pdd")

    if not findings:
        raise HTTPException(status_code=400, detail="No findings provided.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable.")

    project_info = {
        "name": project["name"],
        "methodology": project.get("methodology"),
        "country": project.get("country"),
        "description": project.get("description"),
        "project_intake": project.get("project_intake") or {},
    }

    pdd_text, reference_text = _gather_ai_context(project_id, project, doc_type)

    sessions = get_write_sessions(project_id, doc_type=doc_type)
    session_map = {}
    for sess in sessions:
        sid = (sess.get("section_id") or "").lower()
        session_map[sid] = sess.get("user_text") or sess.get("generated_text") or ""

    from carbongpt.core.ai_writer import STANDARD_LABELS
    std_label = STANDARD_LABELS.get(project["standard"], project["standard"])

    findings_context = ""
    try:
        methodology = project_info.get("methodology", "")
        if methodology:
            from carbongpt.repository.store import get_findings_by_methodology
            similar = get_findings_by_methodology(methodology, limit=30)
            if similar:
                findings_context = "### How similar findings were resolved on other projects:\n"
                for sf in similar[:10]:
                    if sf.get("resolution"):
                        findings_context += f"- [{sf['finding_type']}] {sf.get('topic', '')}: {sf.get('description', '')[:150]}\n"
                        findings_context += f"  Resolution: {sf.get('resolution', '')[:150]}\n\n"
    except Exception:
        pass

    responses = []
    import openai, json
    client = openai.OpenAI(api_key=api_key)

    for idx, finding in enumerate(findings):
        finding_text = finding.get("description", "")
        finding_type = finding.get("finding_type", "CL")
        finding_id = finding.get("finding_id", f"Finding {idx + 1}")
        pdd_section = finding.get("pdd_section", "")

        relevant_section_text = ""
        if pdd_section:
            for sid, text in session_map.items():
                if pdd_section.lower() in sid:
                    relevant_section_text = text
                    break

        system_prompt = (
            f"You are an expert carbon project developer responding to a {finding_type} "
            f"raised by a VVB or standard body ({std_label}).\n\n"
            "RULES:\n"
            "- Draft a professional, detailed response that directly addresses the finding.\n"
            "- Reference specific project data, methodology clauses, and evidence.\n"
            "- If the PDD/document needs updating, clearly state what changes are needed.\n"
            "- Be thorough but concise.\n"
            "- Format response as JSON with keys: 'response_text', 'pdd_updates_needed' (array of {section, change_description}), "
            "'evidence_to_provide' (array of strings), 'response_approach' (one of: pdd_update, clarification, evidence_provided, calculation_corrected, methodology_reference)"
        )

        user_prompt = f"## Finding: {finding_id}\n"
        user_prompt += f"**Type:** {finding_type}\n"
        user_prompt += f"**PDD Section:** {pdd_section or 'Not specified'}\n"
        user_prompt += f"**Finding:**\n{finding_text}\n\n"
        user_prompt += f"### Project Information:\n"
        user_prompt += f"- Project: {project_info.get('name', 'Unknown')}\n"
        user_prompt += f"- Standard: {std_label}\n"
        user_prompt += f"- Methodology: {project_info.get('methodology', 'Not specified')}\n"
        user_prompt += f"- Country: {project_info.get('country', 'Not specified')}\n\n"

        if relevant_section_text:
            user_prompt += f"### Current content of section {pdd_section}:\n\"\"\"\n{relevant_section_text[:3000]}\n\"\"\"\n\n"
        if pdd_text:
            user_prompt += f"### PDD content:\n\"\"\"\n{pdd_text[:3000]}\n\"\"\"\n\n"
        if findings_context:
            user_prompt += findings_context + "\n"

        user_prompt += "Draft a professional response."

        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=2500,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            ai_result = json.loads(resp.choices[0].message.content)
            responses.append({
                "finding_id": finding_id,
                "finding_type": finding_type,
                "finding_text": finding_text,
                "pdd_section": pdd_section,
                "topic": finding.get("topic", ""),
                "status": "success",
                **ai_result,
            })
            logger.info("Generated response for %s (%d/%d)", finding_id, idx + 1, len(findings))
        except Exception as e:
            logger.warning("Failed to generate response for %s: %s", finding_id, e)
            responses.append({
                "finding_id": finding_id,
                "finding_type": finding_type,
                "finding_text": finding_text,
                "pdd_section": pdd_section,
                "topic": finding.get("topic", ""),
                "status": "error",
                "error": str(e),
                "response_text": "",
                "pdd_updates_needed": [],
                "evidence_to_provide": [],
                "response_approach": "",
            })

    return {
        "responses": responses,
        "total": len(findings),
        "successful": sum(1 for r in responses if r["status"] == "success"),
        "failed": sum(1 for r in responses if r["status"] == "error"),
    }


@router.get("/{project_id}/write-sessions")
def get_write_sessions_endpoint(project_id: int, doc_type: str = None):
    from carbongpt.repository.store import get_write_sessions
    return get_write_sessions(project_id, doc_type=doc_type)


@router.get("/{project_id}/methodology-data")
def get_methodology_data_endpoint(project_id: int):
    from carbongpt.repository.store import get_user_project, get_parsed_methodology

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    methodology = project.get("methodology")
    if not methodology:
        return {"status": "no_methodology", "parsed": None}

    cached = get_parsed_methodology(methodology)
    if cached and cached.get("parsed_data"):
        data = cached["parsed_data"]
        if isinstance(data, str):
            import json as _json
            data = _json.loads(data)
        return {"status": "ready", "parsed": data, "parsed_at": str(cached.get("parsed_at", ""))}

    return {"status": "not_parsed", "parsed": None}


@router.post("/{project_id}/parse-methodology")
def parse_methodology_endpoint(project_id: int, data: ParseMethodologyRequest):
    from carbongpt.repository.store import get_user_project
    from carbongpt.core.methodology_parser import get_methodology_sections

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    force = data.force if hasattr(data, 'force') else False

    try:
        from carbongpt.core.methodology_kb import build_methodology_knowledge
        sections_data = get_methodology_sections(data.methodology_code)
        if not sections_data:
            raise ValueError(f"No methodology document found for '{data.methodology_code}'")
        result = build_methodology_knowledge(sections_data["doc_id"], data.methodology_code, force=force)
        from carbongpt.core.methodology_kb import get_knowledge_as_parsed_format
        parsed = get_knowledge_as_parsed_format(data.methodology_code)
        if parsed:
            return parsed
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Methodology KB build failed, falling back to legacy parser: %s", e)
        from carbongpt.core.methodology_parser import parse_methodology_and_save
        try:
            parsed = parse_methodology_and_save(data.methodology_code, force=force)
            return parsed
        except Exception as e2:
            logger.error("Legacy parse also failed: %s", e2)
            raise HTTPException(status_code=500, detail=f"Failed to parse methodology: {e2}")


@router.post("/{project_id}/calculate")
def run_calculation_endpoint(project_id: int, data: RunCalculationRequest):
    from carbongpt.repository.store import get_user_project
    from carbongpt.core.methodology_parser import get_or_parse_methodology
    from carbongpt.core.calculation_engine import run_calculation

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    methodology = project.get("methodology")
    if not methodology:
        raise HTTPException(status_code=400, detail="Project has no methodology assigned.")

    try:
        parsed = get_or_parse_methodology(methodology)
    except Exception as e:
        logger.error("Methodology parse failed for calc: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to parse methodology: {e}")

    project_info = {
        "name": project["name"],
        "standard": project.get("standard"),
        "country": project.get("country"),
        "description": project.get("description"),
    }

    try:
        calc_result = run_calculation(
            parsed_methodology=parsed,
            user_inputs=data.user_inputs,
            method_id=data.method_id,
            crediting_years=data.crediting_years,
            project_info=project_info,
        )
    except Exception as e:
        logger.error("Calculation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Calculation failed: {e}")

    return calc_result


@router.post("/{project_id}/export-calculation")
def export_calculation_endpoint(project_id: int, data: ExportCalculationRequest):
    from carbongpt.repository.store import get_user_project
    from carbongpt.core.doc_exporter import export_calculation_excel

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    project_info = {
        "name": project["name"],
        "standard": project.get("standard"),
        "country": project.get("country"),
    }

    try:
        buf = export_calculation_excel(data.calculation_result, project_info=project_info)
    except Exception as e:
        logger.error("Excel export failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

    safe_name = project["name"].replace(" ", "_")[:30]
    filename = f"{safe_name}_calculations.xlsx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{project_id}/generate-template")
def generate_template_endpoint(project_id: int, data: GenerateTemplateRequest):
    from carbongpt.repository.store import get_user_project, get_write_sessions
    from carbongpt.core.ai_writer import get_sections_for_doc_type
    from carbongpt.core.doc_exporter import generate_filled_template

    project = get_user_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    intake = {}
    if project.get("project_intake"):
        try:
            import json
            raw = project["project_intake"]
            intake = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except Exception:
            intake = {}

    project_info = {
        "name": project["name"],
        "standard": project.get("standard"),
        "methodology": project.get("methodology"),
        "country": project.get("country"),
        "description": project.get("description"),
        "doc_type": data.doc_type,
        "intake": intake,
    }

    sections = get_sections_for_doc_type(project["standard"], data.doc_type)
    if not sections:
        raise HTTPException(status_code=400,
                            detail=f"No template guide found for {project['standard']}/{data.doc_type}")

    write_sessions = get_write_sessions(project_id, doc_type=data.doc_type)
    session_map = {ws["section_id"]: ws for ws in write_sessions}

    generated_sections = []
    for sec in sections:
        sid = sec["id"]
        content = ""
        ws = session_map.get(sid)
        if ws:
            content = ws.get("user_text") or ws.get("generated_text") or ""
        generated_sections.append({
            "section_id": sid,
            "title": sec.get("title", ""),
            "content": content,
        })

    calc_result = None
    if data.include_calculations and data.calculation_result:
        calc_result = data.calculation_result

    try:
        buf = generate_filled_template(project_info, generated_sections, calc_result=calc_result)
    except Exception as e:
        logger.error("Template generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Template generation failed: {e}")

    safe_name = project["name"].replace(" ", "_")[:30]
    doc_type_label = data.doc_type.upper().replace("_", "-")
    filename = f"{safe_name}_{doc_type_label}.docx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
