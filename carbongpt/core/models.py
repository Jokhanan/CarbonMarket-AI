"""
models.py — Pydantic request / response models for CarbonGPT.

All data flowing through the API is typed here.  The models are
intentionally kept flat and explicit; no inheritance tricks that
would obscure what each endpoint actually accepts or returns.
"""

from typing import Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    """Returned after a successful document upload."""

    file_path: str = Field(
        ...,
        description="Absolute path to the saved .docx file on disk.",
        examples=["/home/runner/uploads/report.docx"],
    )
    filename: str = Field(
        ...,
        description="Original filename as supplied by the client.",
    )
    message: str = Field(default="File uploaded successfully.")


# ---------------------------------------------------------------------------
# Analyze endpoint — request
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Caller supplies the path returned by /upload-document."""

    file_path: str = Field(
        ...,
        description="Path to the .docx file to analyse (as returned by /upload-document).",
    )
    rule_file: str = Field(
        default="goldstandard_mr_v1.yaml",
        description="YAML rule file to apply (relative to the rules/ directory).",
    )


# ---------------------------------------------------------------------------
# Analyze-with-template endpoint — request
# ---------------------------------------------------------------------------

class AnalyzeWithTemplateRequest(BaseModel):
    """Accept two document paths for template-based section checking."""

    user_doc_path: str = Field(
        ...,
        description="Path to the user's .docx file to analyse.",
    )
    template_doc_path: str = Field(
        ...,
        description="Path to the template .docx whose headings define expected sections.",
    )
    threshold: int = Field(
        default=85,
        ge=0,
        le=100,
        description="Fuzzy-match similarity threshold (0-100).  Defaults to 85.",
    )


# ---------------------------------------------------------------------------
# Analyze endpoint — response primitives
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    """A single compliance finding produced by the rule engine."""

    rule_id: str = Field(..., description="Unique identifier of the violated rule.")
    severity: Literal["ERROR", "WARNING", "INFO"] = Field(
        ..., description="Impact level of the finding."
    )
    message: str = Field(..., description="Human-readable description of the finding.")


class AnalyzeResponse(BaseModel):
    """Full analysis result returned to the caller."""

    file_path: str = Field(..., description="Path of the document that was analysed.")
    standard: str = Field(..., description="Compliance standard applied (from YAML).")
    doc_type: str = Field(..., description="Document type defined by the rule set.")
    sections_found: list[str] = Field(
        ..., description="Headings discovered in the document."
    )
    findings: list[Finding] = Field(
        ..., description="List of compliance findings.  Empty list means fully compliant."
    )
    compliant: bool = Field(
        ...,
        description="True only when no ERROR-level findings are present.",
    )


class SectionMatch(BaseModel):
    """One row in the matched-sections table."""

    expected: str = Field(..., description="Section name from the template.")
    matched: str | None = Field(
        None, description="Heading in the user doc that matched, or null."
    )


class AnalyzeWithTemplateResponse(BaseModel):
    """Result of template-based section analysis."""

    user_doc_path: str = Field(..., description="Path of the user document analysed.")
    template_doc_path: str = Field(..., description="Path of the template document.")
    template_sections: list[str] = Field(
        ..., description="Headings extracted from the template document."
    )
    user_sections_found: list[str] = Field(
        ..., description="Headings found in the user document."
    )
    section_matches: list[SectionMatch] = Field(
        ..., description="Per-section match results."
    )
    findings: list[Finding] = Field(
        ..., description="Findings for missing sections."
    )
    compliant: bool = Field(
        ..., description="True only when no ERROR-level findings are present."
    )
