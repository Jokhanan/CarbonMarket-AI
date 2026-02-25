"""
rule_engine.py — Load YAML compliance rules and evaluate them against
parsed document sections.

Supported rule types
--------------------
required_section
    Fuzzy-matches a heading against the document.

required_field
    Checks that regex patterns match inside a section's body text.
    Silently skipped when the parent section is missing (the
    required_section rule already covers that).

date_format_ddmmyyyy
    Finds date-like strings in a section and verifies they use
    DD/MM/YYYY format.  Raises a finding for wrong formats.

not_applicable_required_when_blank
    If a section exists but contains fewer than N characters, requires
    the text to contain "Not Applicable" or "N/A".
"""

from pathlib import Path
from typing import Any
import yaml

from carbongpt.core.models import Finding
from carbongpt.tools.section_mapper import map_sections
from carbongpt.tools.regex_utils import any_pattern_matches, find_all_matches, is_ddmmyyyy


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
    """Start at 100, subtract per finding based on severity.  Floor at 0."""
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
    If the parent section is missing, return None (no duplicate noise).
    Only emit a finding when the section exists but the field is absent.
    """
    section_name: str = rule.get("section", "")
    field_name: str = rule.get("field_name", "")
    patterns: list[str] = rule.get("patterns", [])

    if not section_name or not field_name:
        return None

    matched_heading = section_map.get(section_name)
    if matched_heading is None:
        return None

    section_text = sections.get(matched_heading, "")

    if any_pattern_matches(section_text, patterns):
        return None

    return Finding(
        rule_id=rule["id"],
        severity=rule.get("severity", "ERROR"),
        message=f"Missing required field: {field_name} in section: {section_name}",
    )


def _check_date_format_ddmmyyyy(
    rule: dict[str, Any],
    sections: dict[str, str],
    section_map: dict[str, str | None],
) -> Finding | None:
    """
    Find date-like strings in a section using *date_patterns*, then
    verify each one is DD/MM/YYYY.  If any date is found in a wrong
    format, emit a finding.  Silently skip if the section is missing.
    """
    section_name: str = rule.get("section", "")
    date_patterns: list[str] = rule.get("date_patterns", [])

    if not section_name or not date_patterns:
        return None

    matched_heading = section_map.get(section_name)
    if matched_heading is None:
        return None

    section_text = sections.get(matched_heading, "")
    found_dates = find_all_matches(section_text, date_patterns)

    if not found_dates:
        return None

    bad_dates = [d for d in found_dates if not is_ddmmyyyy(d)]

    if not bad_dates:
        return None

    examples = ", ".join(bad_dates[:3])
    return Finding(
        rule_id=rule["id"],
        severity=rule.get("severity", "WARNING"),
        message=(
            f"Date format violation in section: {section_name}. "
            f"Expected DD/MM/YYYY but found: {examples}"
        ),
    )


_NA_KEYWORDS = ("not applicable", "n/a")
_DEFAULT_MIN_CHARS = 40


def _check_not_applicable_required_when_blank(
    rule: dict[str, Any],
    sections: dict[str, str],
    section_map: dict[str, str | None],
) -> Finding | None:
    """
    If a section exists but has fewer than *min_chars* characters,
    require the presence of "Not Applicable" or "N/A".
    """
    section_name: str = rule.get("section", "")
    min_chars: int = rule.get("min_chars", _DEFAULT_MIN_CHARS)

    if not section_name:
        return None

    matched_heading = section_map.get(section_name)
    if matched_heading is None:
        return None

    section_text = sections.get(matched_heading, "")

    if len(section_text.strip()) >= min_chars:
        return None

    lower_text = section_text.lower()
    if any(kw in lower_text for kw in _NA_KEYWORDS):
        return None

    return Finding(
        rule_id=rule["id"],
        severity=rule.get("severity", "WARNING"),
        message=(
            f"Section '{section_name}' has fewer than {min_chars} characters "
            f"and does not contain 'Not Applicable' or 'N/A'"
        ),
    )


# ---------------------------------------------------------------------------
# Handler dispatch table
# ---------------------------------------------------------------------------

_RULE_HANDLERS = {
    "required_section": _check_required_section,
    "required_field": _check_required_field,
    "date_format_ddmmyyyy": _check_date_format_ddmmyyyy,
    "not_applicable_required_when_blank": _check_not_applicable_required_when_blank,
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
    Check *sections* against expected headings from a template.
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
