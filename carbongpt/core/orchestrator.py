"""
orchestrator.py — Coordinates the analysis pipeline for CarbonGPT.

The orchestrator is the single integration point between the API layer
and the tool layer.  Routes call ``run_analysis``; the orchestrator
calls parse_docx → rule_engine → assembles the response model.

Keeping this logic here (rather than inline in the route) means:
- Routes stay thin and testable.
- The pipeline can be extended (e.g. LLM post-processing) in one place.
- Individual tools remain unaware of each other.
"""

from pathlib import Path

from carbongpt.app.config import RULES_DIR
from carbongpt.core.models import AnalyzeResponse, Finding
from carbongpt.tools.parse_docx import parse_docx
from carbongpt.tools.rule_engine import run_rules


def run_analysis(file_path: str, rule_file_name: str = "goldstandard_mr_v1.yaml") -> AnalyzeResponse:
    """
    Execute the full compliance analysis pipeline.

    Steps
    -----
    1. Parse the .docx document into a sections mapping.
    2. Locate the requested YAML rule file.
    3. Run all rules against the sections.
    4. Assemble and return an :class:`~carbongpt.core.models.AnalyzeResponse`.

    Parameters
    ----------
    file_path:
        Absolute path to the .docx file to analyse.
    rule_file_name:
        Filename (not full path) of the YAML rule set to apply.
        Must exist inside the ``rules/`` directory.

    Returns
    -------
    AnalyzeResponse
        Structured compliance result ready for JSON serialisation.

    Raises
    ------
    FileNotFoundError — propagated from parse_docx or rule_engine.
    ValueError        — propagated when a file cannot be opened/parsed.
    """
    # ------------------------------------------------------------------
    # Step 1: Parse document
    # ------------------------------------------------------------------
    parsed = parse_docx(file_path)
    sections: dict[str, str] = parsed["sections"]

    # ------------------------------------------------------------------
    # Step 2: Resolve rule file path
    # ------------------------------------------------------------------
    rule_file_path: Path = RULES_DIR / rule_file_name
    if not rule_file_path.exists():
        raise FileNotFoundError(
            f"Rule file '{rule_file_name}' not found in rules directory: {RULES_DIR}"
        )

    # ------------------------------------------------------------------
    # Step 3: Run rules
    # ------------------------------------------------------------------
    findings: list[Finding]
    metadata: dict
    findings, metadata = run_rules(rule_file_path, sections)

    # ------------------------------------------------------------------
    # Step 4: Assemble response
    # ------------------------------------------------------------------
    has_errors = any(f.severity == "ERROR" for f in findings)

    return AnalyzeResponse(
        file_path=file_path,
        standard=metadata.get("standard", ""),
        doc_type=metadata.get("doc_type", ""),
        sections_found=list(sections.keys()),
        findings=findings,
        compliant=not has_errors,
    )
