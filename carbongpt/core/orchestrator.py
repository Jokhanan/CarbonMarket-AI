"""
orchestrator.py — Coordinates the analysis pipeline for CarbonGPT.

The orchestrator is the single integration point between the API layer
and the tool layer.  Routes call ``run_analysis`` or ``run_template_analysis``;
the orchestrator calls parse_docx -> rule_engine -> assembles the response.
"""

from pathlib import Path

from carbongpt.app.config import RULES_DIR
from carbongpt.core.models import (
    AnalyzeResponse,
    AnalyzeWithTemplateResponse,
    Finding,
    SectionMatch,
)
from carbongpt.tools.parse_docx import parse_docx
from carbongpt.tools.rule_engine import run_rules, run_template_rules


def run_analysis(
    file_path: str,
    rule_file_name: str = "goldstandard_mr_v1.yaml",
) -> AnalyzeResponse:
    """
    Execute the YAML-based compliance analysis pipeline.

    Steps: parse docx -> locate YAML rules -> run rules -> assemble response.
    """
    parsed = parse_docx(file_path)
    sections: dict[str, str] = parsed["sections"]

    rule_file_path: Path = RULES_DIR / rule_file_name
    if not rule_file_path.exists():
        raise FileNotFoundError(
            f"Rule file '{rule_file_name}' not found in rules directory: {RULES_DIR}"
        )

    findings: list[Finding]
    metadata: dict
    findings, metadata = run_rules(rule_file_path, sections)

    has_errors = any(f.severity == "ERROR" for f in findings)

    return AnalyzeResponse(
        file_path=file_path,
        standard=metadata.get("standard", ""),
        doc_type=metadata.get("doc_type", ""),
        sections_found=list(sections.keys()),
        findings=findings,
        compliant=not has_errors,
    )


def run_template_analysis(
    user_doc_path: str,
    template_doc_path: str,
    threshold: int = 85,
) -> AnalyzeWithTemplateResponse:
    """
    Compare a user document against a template document.

    Steps:
    1. Parse both documents.
    2. Extract headings from the template as the expected sections.
    3. Fuzzy-match user doc headings against template headings.
    4. Report missing sections as findings.
    """
    user_parsed = parse_docx(user_doc_path)
    user_sections: dict[str, str] = user_parsed["sections"]

    template_parsed = parse_docx(template_doc_path)
    template_sections: dict[str, str] = template_parsed["sections"]

    expected = list(template_sections.keys())

    findings, section_map = run_template_rules(
        expected_sections=expected,
        sections=user_sections,
        threshold=threshold,
    )

    matches = [
        SectionMatch(expected=exp, matched=section_map.get(exp))
        for exp in expected
    ]

    has_errors = any(f.severity == "ERROR" for f in findings)

    return AnalyzeWithTemplateResponse(
        user_doc_path=user_doc_path,
        template_doc_path=template_doc_path,
        template_sections=expected,
        user_sections_found=list(user_sections.keys()),
        section_matches=matches,
        findings=findings,
        compliant=not has_errors,
    )
