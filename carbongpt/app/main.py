"""
main.py — FastAPI application entry point for CarbonGPT.
"""

import logging
import os
import shutil
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from carbongpt.app.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    HOST,
    PORT,
    UPLOAD_DIR,
)
from carbongpt.core.models import (
    AIReviewRequest,
    AIReviewResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzeSelectedRequest,
    AnalyzeSelectedResponse,
    AnalyzeWithTemplateRequest,
    AnalyzeWithTemplateResponse,
    UploadResponse,
)
from carbongpt.core.orchestrator import (
    run_analysis,
    run_selected_analysis,
    run_template_analysis,
)
from carbongpt.core.task_store import create_task, get_task
from carbongpt.tools.parse_docx import debug_sections
from carbongpt.app.admin_routes import router as admin_router
from carbongpt.app.project_routes import router as project_router
from carbongpt.app.pack_routes import router as pack_router
from carbongpt.app.profile_routes import router as profile_router
from carbongpt.app.calculate_routes import router as calculate_router
from carbongpt.app.methodology_routes import router as methodology_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — specify exact origins; wildcard + credentials is invalid per CORS spec
_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CARBONGPT_ALLOWED_ORIGINS",
        "http://localhost:5000,http://0.0.0.0:5000,"
        "http://localhost:5173,http://localhost:5174,"
        "http://localhost:5175,http://localhost:5176,"
        "http://localhost:5177,http://localhost:5178,"
        "http://localhost:5179,http://localhost:5180",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional API key authentication — activated when CARBONGPT_API_KEY env var is set
_API_KEY = os.getenv("CARBONGPT_API_KEY", "")
_PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not _API_KEY:
            return await call_next(request)
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)
        key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").removeprefix("Bearer ")
        if key != _API_KEY:
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
        return await call_next(request)


app.add_middleware(APIKeyMiddleware)

app.include_router(admin_router)
app.include_router(project_router)
app.include_router(pack_router)
app.include_router(profile_router)
app.include_router(calculate_router)
app.include_router(methodology_router)


@app.on_event("startup")
def startup_init_db():
    try:
        from carbongpt.repository.schema import ensure_schema
        ensure_schema()
    except Exception as exc:
        logger.warning("Database schema init skipped: %s", exc)

    try:
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM methodologies")
            count = cur.fetchone()["count"]
        if count == 0:
            from carbongpt.repository.methodology_db import populate_methodologies_from_projects
            n = populate_methodologies_from_projects()
            logger.info("Auto-populated %d methodologies on first startup", n)
    except Exception as exc:
        logger.warning("Methodology auto-population skipped: %s", exc)

    if os.getenv("CARBONGPT_AUTO_SYNC", "").lower() in ("1", "true", "yes"):
        try:
            from carbongpt.repository.methodology_sync import start_weekly_sync
            start_weekly_sync()
        except Exception as exc:
            logger.warning("Methodology sync scheduler skipped: %s", exc)

    if os.getenv("CARBONGPT_AUTO_SYNC_PROJECTS", "").lower() in ("1", "true", "yes"):
        try:
            from carbongpt.repository.project_sync import start_registry_sync_schedule
            start_registry_sync_schedule()
        except Exception as exc:
            logger.warning("Registry project sync scheduler skipped: %s", exc)

    try:
        from carbongpt.repository.registry_normalizer import seed_ref_registries, run_registry_normalization_pass
        n = seed_ref_registries()
        logger.info("ref_registries seeded: %d rows", n)
        run_registry_normalization_pass()
    except Exception as exc:
        logger.warning("Registry seed/normalization skipped: %s", exc)

    try:
        from carbongpt.repository.country_normalizer import (
            seed_countries_table,
            seed_countries_aliases,
            run_country_normalization_pass,
            run_user_project_country_normalization_pass,
        )
        n = seed_countries_table()
        logger.info("countries table seeded: %d rows", n)
        seed_countries_aliases()
        result = run_country_normalization_pass()
        logger.info("carbon_projects country normalization: %s", result)
        run_user_project_country_normalization_pass()
    except Exception as exc:
        logger.warning("Country seed/normalization skipped: %s", exc)

    try:
        from carbongpt.repository.methodology_normalizer import (
            seed_methodology_library_from_db,
            seed_ref_methodologies,
        )
        seed_methodology_library_from_db()
        n = seed_ref_methodologies()
        logger.info("ref_methodologies seeded: %d rows", n)
    except Exception as exc:
        logger.warning("Methodology seed skipped: %s", exc)


@app.get("/health", tags=["system"])
def health_check() -> dict:
    return {"status": "ok", "app": APP_TITLE, "version": APP_VERSION}


@app.post(
    "/upload-document",
    response_model=UploadResponse,
    tags=["documents"],
    summary="Upload a .docx compliance report",
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are accepted.")

    _max_bytes = int(os.getenv("CARBONGPT_MAX_UPLOAD_MB", "50")) * 1024 * 1024
    _docx_magic = b"PK\x03\x04"  # DOCX/ZIP magic bytes

    content = await file.read()
    if len(content) > _max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds maximum size of {_max_bytes // (1024*1024)} MB.")
    if not content.startswith(_docx_magic):
        raise HTTPException(status_code=400, detail="File content does not match .docx format.")

    unique_stem = f"{uuid.uuid4().hex}_{Path(file.filename).stem}"
    dest_path: Path = UPLOAD_DIR / f"{unique_stem}.docx"

    try:
        dest_path.write_bytes(content)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not save file: {exc}") from exc
    finally:
        await file.close()

    return UploadResponse(file_path=str(dest_path), filename=file.filename)


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    tags=["analysis"],
    summary="Run compliance analysis on an uploaded document",
)
def analyze_document(request: AnalyzeRequest) -> AnalyzeResponse:
    if not Path(request.file_path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    try:
        result = run_analysis(file_path=request.file_path, rule_file_name=request.rule_file)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    return result


@app.post(
    "/analyze-with-template",
    response_model=AnalyzeWithTemplateResponse,
    tags=["analysis"],
    summary="Compare a document against a template",
)
def analyze_with_template(request: AnalyzeWithTemplateRequest) -> AnalyzeWithTemplateResponse:
    for label, path in [
        ("User document", request.user_doc_path),
        ("Template document", request.template_doc_path),
    ]:
        if not Path(path).exists():
            raise HTTPException(status_code=404, detail=f"{label} not found: {path}")

    try:
        result = run_template_analysis(
            user_doc_path=request.user_doc_path,
            template_doc_path=request.template_doc_path,
            threshold=request.threshold,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Template analysis failed: {exc}") from exc

    return result


@app.post(
    "/analyze-selected",
    response_model=AnalyzeSelectedResponse,
    tags=["analysis"],
    summary="Analyse document using an internally registered template and rules",
    description=(
        "Select a standard, document type, and version to use the "
        "internally stored template and rules.  Upload the user doc "
        "first via /upload-document."
    ),
)
def analyze_selected(request: AnalyzeSelectedRequest) -> AnalyzeSelectedResponse:
    if not Path(request.user_doc_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"User document not found: {request.user_doc_path}",
        )

    try:
        result = run_selected_analysis(
            standard=request.standard,
            doc_type=request.doc_type,
            version=request.version,
            user_doc_path=request.user_doc_path,
            threshold=request.threshold,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    return result


@app.post(
    "/ai-review",
    tags=["analysis"],
    summary="Start AI-powered section-by-section review (beta)",
    description=(
        "Starts an async AI review task in a separate process. Returns a task_id. "
        "Poll GET /ai-review/{task_id} for results."
    ),
)
def ai_review(request: AIReviewRequest) -> dict:
    from carbongpt.guides import is_ai_review_supported
    if not is_ai_review_supported(request.standard, request.doc_type):
        raise HTTPException(
            status_code=422,
            detail=f"AI review is not supported for standard='{request.standard}', doc_type='{request.doc_type}'. "
                   f"Supported combinations: GoldStandard with MR, PDD, PoA-DD, or VPA-DD.",
        )

    if not Path(request.doc_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {request.doc_path}",
        )

    task_id = create_task(
        doc_path=request.doc_path,
        standard=request.standard,
        doc_type=request.doc_type,
    )
    logger.info("AI review task %s created for %s (standard=%s, doc_type=%s)",
                task_id, request.doc_path, request.standard, request.doc_type)
    return {"task_id": task_id, "status": "pending"}


@app.get(
    "/ai-review/{task_id}",
    tags=["analysis"],
    summary="Poll AI review task status and results",
)
def get_ai_review_result(task_id: str) -> dict:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if task["status"] == "complete":
        return {"status": "complete", "result": task["result"]}
    elif task["status"] == "failed":
        return {"status": "failed", "error": task["error"]}
    else:
        return {"status": task["status"]}


@app.get(
    "/debug/sections",
    tags=["debug"],
    summary="Diagnose section detection for a document",
)
def debug_doc_sections(path: str = Query(..., description="Path to the .docx file")) -> dict:
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    try:
        return debug_sections(path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    uvicorn.run("carbongpt.app.main:app", host=HOST, port=PORT, reload=True)
