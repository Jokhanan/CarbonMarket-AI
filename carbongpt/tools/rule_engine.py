"""
rule_engine.py — Load YAML compliance rules and evaluate them against
parsed document sections.

Supported rule types
--------------------
required_section
    Uses fuzzy matching (via section_mapper) to check whether a heading
    sufficiently close to the rule's ``section`` value exists in the
    document.  Returns an ERROR/WARNING/INFO finding when it is missing.

required_field
    Checks that specific content (detected via regex patterns) exists
    inside a matched section.  If the parent section itself is missing,
    a single "section missing" finding is emitted instead (no duplicate
    field-level noise).

Extending the engine
--------------------
Add new rule types by:
1. Adding a handler function  ``_check_<type>(rule, sections, section_map) -> Finding | None``
2. Registering it in ``_RULE_HANDLERS``.
"""

from pathlib import Path
from typing import Any
import yaml

from carbongpt.core.models import Finding
from carbongpt.tools.section_mapper import map_sections
from carbongpt.tools.regex_utils import any_pattern_matches


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_yaml(rule_file: str | Path) -> dict:
    """Read and parse a YAML rule file."""
    path = Path(rule_file)
    if not path.exists():
        raise FileNotFoundError(f"Rule file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in '{path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Rule file '{path}' must be a YAML mapping at the top level.")

    return data


# ---------------------------------------------------------------------------
# Compliance score
# ---------------------------------------------------------------------------

_SEVERITY_PENALTY = {
    "ERROR": 10,
    "WARNING": 3,
    "INFO": 0,
}


def compute_compliance_score(findings: list[Finding]) -> int:
    """
    Start at 100, subtract per finding based on severity.  Floor at 0.
    """
    score = 100
    for f in findings:
        score -= _SEVERITY_PENALTY.get(f.severity, 0)
    return max(score, 0)


# ---------------------------------------------------------------------------
# Rule-type handlers
# ---------------------------------------------------------------------------

def _check_required_section(
    rule: dict[str, Any],
    sections: dict[str, str],
    section_map: dict[str, str | None],
) -> Finding | None:
    """Return a Finding if the required section is absent, else None."""
    required: str = rule.get("section", "")
    if not required:
        return None

    if section_map.get(required) is not None:
        return None

    return Finding(
        rule_id=rule["id"],
        severity=rule.get("severity", "ERROR"),
        message=f"Missing required section: {required}",
    )


def _check_required_field(
    rule: dict[str, Any],
    sections: dict[str, str],
    section_map: dict[str, str | None],
) -> Finding | None:
    """
    Return a Finding if a required field is missing from a section.

    If the parent section itself is not matched in the document, emit a
    single finding about the missing section rather than a field-level
    finding, to avoid duplicate noise.
    """
    section_name: str = rule.get("section", "")
    field_name: str = rule.get("field_name", "")
    patterns: list[str] = rule.get("patterns", [])

    if not section_name or not field_name:
        return None

    matched_heading = section_map.get(section_name)

    if matched_heading is None:
        return Finding(
            rule_id=rule["id"],
            severity=rule.get("severity", "ERROR"),
            message=f"Missing required field: {field_name} (section '{section_name}' not found)",
        )

    section_text = sections.get(matched_heading, "")

    if any_pattern_matches(section_text, patterns):
        return None

    return Finding(
        rule_id=rule["id"],
        severity=rule.get("severity", "ERROR"),
        message=f"Missing required field: {field_name} in section: {section_name}",
    )


# ---------------------------------------------------------------------------
# Handler dispatch table
# ---------------------------------------------------------------------------

_RULE_HANDLERS = {
    "required_section": _check_required_section,
    "required_field": _check_required_field,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _collect_expected_sections(rules: list[dict]) -> list[str]:
    """Gather all unique section names referenced across rule types."""
    seen: set[str] = set()
    ordered: list[str] = []
    for r in rules:
        sec = r.get("section", "")
        if sec and sec not in seen:
            seen.add(sec)
            ordered.append(sec)
    return ordered


def run_rules(
    rule_file: str | Path,
    sections: dict[str, str],
    threshold: int = 85,
) -> tuple[list[Finding], dict]:
    """
    Load a YAML rule file and evaluate every rule against *sections*.

    Returns
    -------
    findings:
        List of Finding objects.  Empty when fully compliant.
    metadata:
        Dict with ``standard``, ``doc_type``, and ``compliance_score``.
    """
    data = _load_yaml(rule_file)

    metadata = {
        "standard": data.get("standard", ""),
        "doc_type": data.get("doc_type", ""),
    }

    rules: list[dict] = data.get("rules", [])

    expected_sections = _collect_expected_sections(rules)
    found_headings = list(sections.keys())
    section_map = map_sections(expected_sections, found_headings, threshold)

    findings: list[Finding] = []

    for rule in rules:
        rule_type: str = rule.get("type", "")
        handler = _RULE_HANDLERS.get(rule_type)

        if handler is None:
            findings.append(
                Finding(
                    rule_id=rule.get("id", "UNKNOWN"),
                    severity="INFO",
                    message=f"Unsupported rule type '{rule_type}' — skipped.",
                )
            )
            continue

        finding = handler(rule, sections, section_map)
        if finding is not None:
            findings.append(finding)

    metadata["compliance_score"] = compute_compliance_score(findings)
    return findings, metadata


def run_template_rules(
    expected_sections: list[str],
    sections: dict[str, str],
    threshold: int = 85,
) -> tuple[list[Finding], dict[str, str | None]]:
    """
    Check *sections* against a list of expected headings (from a template).

    Returns
    -------
    findings:
        One finding per missing section.
    section_map:
        The full mapping so callers can see which headings matched.
    """
    found_headings = list(sections.keys())
    section_map = map_sections(expected_sections, found_headings, threshold)

    findings: list[Finding] = []
    for idx, expected in enumerate(expected_sections, start=1):
        if section_map.get(expected) is None:
            findings.append(
                Finding(
                    rule_id=f"TPL_{idx:03d}",
                    severity="ERROR",
                    message=f"Missing required section: {expected}",
                )
            )

    return findings, section_map
