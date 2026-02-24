"""
rule_engine.py — Load YAML compliance rules and evaluate them against
parsed document sections.

Supported rule types
--------------------
required_section
    Checks that a section whose heading *contains* the rule's ``section``
    value (case-insensitive) is present in the document.  Returns an
    ERROR/WARNING/INFO finding when it is missing.

Extending the engine
--------------------
Add new rule types by:
1. Adding a handler function  ``_check_<type>(rule, sections) -> Finding | None``
2. Registering it in ``_RULE_HANDLERS``.
"""

from pathlib import Path
from typing import Any
import yaml

from carbongpt.core.models import Finding


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


def _normalise(text: str) -> str:
    """Lowercase and strip whitespace for case-insensitive comparisons."""
    return text.strip().lower()


# ---------------------------------------------------------------------------
# Rule-type handlers
# ---------------------------------------------------------------------------

def _check_required_section(
    rule: dict[str, Any],
    sections: dict[str, str],
) -> Finding | None:
    """
    Return a Finding if the required section is absent, else None.

    Matching is performed case-insensitively on substring containment so
    that minor heading variations ("Monitoring Period Summary" still
    matches the rule for "Monitoring Period").
    """
    required: str = rule.get("section", "")
    if not required:
        return None  # Misconfigured rule — skip silently

    normalised_required = _normalise(required)
    found = any(
        normalised_required in _normalise(heading)
        for heading in sections
    )

    if found:
        return None  # Compliant — no finding

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
) -> tuple[list[Finding], dict]:
    """
    Load a YAML rule file and evaluate every rule against *sections*.

    Parameters
    ----------
    rule_file:
        Absolute path to the YAML rule file.
    sections:
        Mapping of heading → body text as returned by ``parse_docx``.

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
    findings: list[Finding] = []

    for rule in rules:
        rule_type: str = rule.get("type", "")
        handler = _RULE_HANDLERS.get(rule_type)

        if handler is None:
            # Unknown rule type — emit an informational finding so the
            # caller knows something was skipped rather than silently
            # ignoring misconfiguration.
            findings.append(
                Finding(
                    rule_id=rule.get("id", "UNKNOWN"),
                    severity="INFO",
                    message=f"Unsupported rule type '{rule_type}' — skipped.",
                )
            )
            continue

        finding = handler(rule, sections)
        if finding is not None:
            findings.append(finding)

    return findings, metadata
