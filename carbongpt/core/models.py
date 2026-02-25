"""
models.py — Pydantic request / response models for CarbonGPT.
"""

from typing import Literal
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
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


class AnalyzeRequest(BaseModel):
    file_path: str = Field(
        ...,
        description="Path to the .docx file to analyse (as returned by /upload-document).",
    )
    rule_file: str = Field(
        default="goldstandard_mr_v1.yaml",
        description="YAML rule file to apply (relative to the rules/ directory).",
    )


class AnalyzeWithTemplateRequest(BaseModel):
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


class AnalyzeSelectedRequest(BaseModel):
    standard: str = Field(..., description="Compliance standard (e.g. 'GoldStandard').")
    doc_type: str = Field(..., description="Document type (e.g. 'MR').")
    version: str = Field(..., description="Template version (e.g. 'MR_v1_1').")
    user_doc_path: str = Field(
        ...,
        description="Path to the user's .docx file (from /upload-document).",
    )
    threshold: int = Field(
        default=85,
        ge=0,
        le=100,
        description="Fuzzy-match similarity threshold (0-100).",
    )


class Finding(BaseModel):
    rule_id: str = Field(..., description="Unique identifier of the violated rule.")
    severity: Literal["ERROR", "WARNING", "INFO"] = Field(
        ..., description="Impact level of the finding."
    )
    message: str = Field(..., description="Human-readable description of the finding.")


class AnalyzeResponse(BaseModel):
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
    compliance_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Score starting at 100, reduced by -10 per ERROR and -3 per WARNING.  Floor 0.",
    )


class SectionMatch(BaseModel):
    expected: str = Field(..., description="Section name from the template.")
    matched: str | None = Field(
        None, description="Heading in the user doc that matched, or null."
    )


class AnalyzeWithTemplateResponse(BaseModel):
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
    compliance_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Score starting at 100, reduced by -10 per ERROR and -3 per WARNING.  Floor 0.",
    )


class AnalyzeSelectedResponse(BaseModel):
    user_doc_path: str = Field(..., description="Path of the user document analysed.")
    standard: str = Field(..., description="Compliance standard applied.")
    doc_type: str = Field(..., description="Document type.")
    version: str = Field(..., description="Template version used.")
    sections_found: list[str] = Field(
        ..., description="Headings discovered in the user document."
    )
    template_sections: list[str] = Field(
        ..., description="Headings from the internal template."
    )
    section_matches: list[SectionMatch] = Field(
        ..., description="Per-section match results from template comparison."
    )
    rule_findings: list[Finding] = Field(
        ..., description="Findings from YAML rule evaluation."
    )
    template_findings: list[Finding] = Field(
        ..., description="Findings from template section comparison."
    )
    findings: list[Finding] = Field(
        ..., description="All findings combined (rules + template)."
    )
    compliant: bool = Field(
        ..., description="True only when no ERROR-level findings are present."
    )
    compliance_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Combined compliance score.  Floor 0.",
    )
