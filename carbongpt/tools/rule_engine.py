"""
rule_engine.py — Load YAML compliance rules and evaluate them against
parsed document sections.

Supported rule types
--------------------
required_section
    Uses fuzzy matching (via section_mapper) to check whether a heading
    sufficiently close to the rule's ``section`` value exists in the
    document.  Returns an ERROR/WARNING/INFO finding when it is missing.

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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_yaml(rule_file: str | Path) -> dict:
    """
    Read and parse a YAML rule file.

    Parameters
    ----------
    rule_file:
        Absolute path to the YAML file.

    Raises
    ------
    FileNotFoundError — if the file does not exist.
    ValueError        — if the file cannot be parsed.
    """
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
# Rule-type handlers
# ---------------------------------------------------------------------------

def _check_required_section(
    rule: dict[str, Any],
    sections: dict[str, str],
    section_map: dict[str, str | None],
) -> Finding | None:
    """
    Return a Finding if the required section is absent, else None.

    Uses the pre-computed *section_map* produced by the fuzzy mapper
    so that minor heading variations still match.
    """
    required: str = rule.get("section", "")
    if not required:
        return None

    matched = section_map.get(required)

    if matched is not None:
        return None

    return Finding(
        rule_id=rule["id"],
        severity=rule.get("severity", "ERROR"),
        message=f"Missing required section: {required}",
    )


# ---------------------------------------------------------------------------
# Handler dispatch table — extend here for new rule types
# ---------------------------------------------------------------------------

_RULE_HANDLERS = {
    "required_section": _check_required_section,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_rules(
    rule_file: str | Path,
    sections: dict[str, str],
    threshold: int = 85,
) -> tuple[list[Finding], dict]:
    """
    Load a YAML rule file and evaluate every rule against *sections*.

    Parameters
    ----------
    rule_file:
        Absolute path to the YAML rule file.
    sections:
        Mapping of heading -> body text as returned by ``parse_docx``.
    threshold:
        Fuzzy-match similarity threshold (0-100) forwarded to the mapper.

    Returns
    -------
    findings:
        List of :class:`~carbongpt.core.models.Finding` objects.  Empty
        when the document is fully compliant.
    metadata:
        Dict with ``standard`` and ``doc_type`` extracted from the YAML
        header (defaults to empty strings when absent).
    """
    data = _load_yaml(rule_file)

    metadata = {
        "standard": data.get("standard", ""),
        "doc_type": data.get("doc_type", ""),
    }

    rules: list[dict] = data.get("rules", [])

    expected_sections = [
        r["section"] for r in rules
        if r.get("type") == "required_section" and r.get("section")
    ]
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

    return findings, metadata


def run_template_rules(
    expected_sections: list[str],
    sections: dict[str, str],
    threshold: int = 85,
) -> tuple[list[Finding], dict[str, str | None]]:
    """
    Check *sections* against a list of expected headings (from a template).

    Unlike ``run_rules`` this does not load a YAML file — the expected
    sections come directly from a parsed template document.

    Parameters
    ----------
    expected_sections:
        Heading names the document must contain.
    sections:
        Heading -> body text mapping from the user document.
    threshold:
        Fuzzy-match similarity threshold (0-100).

    Returns
    -------
    findings:
        One finding per missing section.
    section_map:
        The full mapping from ``map_sections`` so callers can see which
        headings matched which.
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
