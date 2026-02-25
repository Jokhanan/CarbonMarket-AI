"""
orchestrator.py — Coordinates the analysis pipeline for CarbonGPT.
"""

from pathlib import Path

from carbongpt.app.config import RULES_DIR, BASE_DIR
from carbongpt.core.models import (
    AnalyzeResponse,
    AnalyzeSelectedResponse,
    AnalyzeWithTemplateResponse,
    Finding,
    SectionMatch,
)
from carbongpt.tools.parse_docx import parse_docx
from carbongpt.tools.rule_engine import run_rules, run_template_rules, compute_compliance_score
from carbongpt.templates.registry import lookup


def run_analysis(
    file_path: str,
    rule_file_name: str = "goldstandard_mr_v1.yaml",
) -> AnalyzeResponse:
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
        compliance_score=metadata.get("compliance_score", 100),
    )


def run_template_analysis(
    user_doc_path: str,
    template_doc_path: str,
    threshold: int = 85,
) -> AnalyzeWithTemplateResponse:
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
        compliance_score=compute_compliance_score(findings),
    )


def run_selected_analysis(
    standard: str,
    doc_type: str,
    version: str,
    user_doc_path: str,
    threshold: int = 85,
) -> AnalyzeSelectedResponse:
    """
    Combined analysis: looks up the internal template + rules from the
    registry, runs both template section comparison and YAML rule
    evaluation, and merges findings.
    """
    entry = lookup(standard, doc_type, version)
    if entry is None:
        raise ValueError(
            f"No template registered for standard={standard}, "
            f"doc_type={doc_type}, version={version}"
        )

    template_path = entry.get("template_path")
    rules_path = entry.get("rules_path")

    if not template_path or not rules_path:
        raise ValueError(
            f"Template or rules not yet available for {standard}/{doc_type}/{version}"
        )

    abs_template = BASE_DIR / template_path
    abs_rules = BASE_DIR / rules_path

    if not abs_template.exists():
        raise FileNotFoundError(f"Template file not found: {abs_template}")
    if not abs_rules.exists():
        raise FileNotFoundError(f"Rules file not found: {abs_rules}")

    user_parsed = parse_docx(user_doc_path)
    user_sections: dict[str, str] = user_parsed["sections"]

    template_parsed = parse_docx(str(abs_template))
    template_headings = list(template_parsed["sections"].keys())

    template_findings, section_map = run_template_rules(
        expected_sections=template_headings,
        sections=user_sections,
        threshold=threshold,
    )

    rule_findings, metadata = run_rules(abs_rules, user_sections, threshold)

    all_findings = rule_findings + template_findings

    matches = [
        SectionMatch(expected=exp, matched=section_map.get(exp))
        for exp in template_headings
    ]

    has_errors = any(f.severity == "ERROR" for f in all_findings)

    return AnalyzeSelectedResponse(
        user_doc_path=user_doc_path,
        standard=standard,
        doc_type=doc_type,
        version=version,
        sections_found=list(user_sections.keys()),
        template_sections=template_headings,
        section_matches=matches,
        rule_findings=rule_findings,
        template_findings=template_findings,
        findings=all_findings,
        compliant=not has_errors,
        compliance_score=compute_compliance_score(all_findings),
    )
