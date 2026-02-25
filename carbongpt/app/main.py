"""
main.py — FastAPI application entry point for CarbonGPT.
"""

import shutil
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from carbongpt.app.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    HOST,
    PORT,
    UPLOAD_DIR,
)
from carbongpt.core.models import (
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

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    unique_stem = f"{uuid.uuid4().hex}_{Path(file.filename).stem}"
    dest_path: Path = UPLOAD_DIR / f"{unique_stem}.docx"

    try:
        with dest_path.open("wb") as out_file:
            shutil.copyfileobj(file.file, out_file)
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


if __name__ == "__main__":
    uvicorn.run("carbongpt.app.main:app", host=HOST, port=PORT, reload=True)
