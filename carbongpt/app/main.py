"""
main.py — FastAPI application entry point for CarbonGPT.

Endpoints
---------
POST /upload-document
    Accept a .docx file, persist it locally, return the saved path.

POST /analyze
    Accept a file path + optional rule-file name, run the compliance
    pipeline, return structured JSON findings.
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
from carbongpt.core.models import AnalyzeRequest, AnalyzeResponse, UploadResponse
from carbongpt.core.orchestrator import run_analysis

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins for development; tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok", "app": APP_TITLE, "version": APP_VERSION}


# ---------------------------------------------------------------------------
# POST /upload-document
# ---------------------------------------------------------------------------

@app.post(
    "/upload-document",
    response_model=UploadResponse,
    tags=["documents"],
    summary="Upload a .docx compliance report",
    description=(
        "Accepts a Word document (.docx), saves it to the server's upload "
        "directory under a unique filename, and returns the absolute path "
        "for use with the /analyze endpoint."
    ),
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    # Validate MIME type / extension
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail="Only .docx files are accepted.",
        )

    # Build a unique destination path to avoid collisions
    unique_stem = f"{uuid.uuid4().hex}_{Path(file.filename).stem}"
    dest_path: Path = UPLOAD_DIR / f"{unique_stem}.docx"

    try:
        with dest_path.open("wb") as out_file:
            shutil.copyfileobj(file.file, out_file)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save file: {exc}",
        ) from exc
    finally:
        await file.close()

    return UploadResponse(
        file_path=str(dest_path),
        filename=file.filename,
    )


# ---------------------------------------------------------------------------
# POST /analyze
# ---------------------------------------------------------------------------

@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    tags=["analysis"],
    summary="Run compliance analysis on an uploaded document",
    description=(
        "Accepts the file path returned by /upload-document plus an optional "
        "YAML rule-file name, parses the document, evaluates all rules, and "
        "returns structured compliance findings."
    ),
)
def analyze_document(request: AnalyzeRequest) -> AnalyzeResponse:
    # Confirm the file exists before handing off to the orchestrator
    if not Path(request.file_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.file_path}",
        )

    try:
        result = run_analysis(
            file_path=request.file_path,
            rule_file_name=request.rule_file,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}",
        ) from exc

    return result


# ---------------------------------------------------------------------------
# Direct execution entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "carbongpt.app.main:app",
        host=HOST,
        port=PORT,
        reload=True,
    )
