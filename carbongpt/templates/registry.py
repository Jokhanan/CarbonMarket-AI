"""
registry.py — Template registry loader for CarbonGPT.

Maps (standard, doc_type, version) tuples to their template and rule
file paths.  The registry is defined in registry.yaml alongside this
module.
"""

from pathlib import Path
from typing import Any

import yaml

_REGISTRY_PATH = Path(__file__).resolve().parent / "registry.yaml"


def _load_registry() -> list[dict[str, Any]]:
    with _REGISTRY_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data.get("templates", [])


def list_standards() -> list[str]:
    return sorted({e["standard"] for e in _load_registry()})


def list_doc_types(standard: str) -> list[str]:
    return sorted({
        e["doc_type"]
        for e in _load_registry()
        if e["standard"] == standard
    })


def list_versions(standard: str, doc_type: str) -> list[str]:
    return sorted({
        e["version"]
        for e in _load_registry()
        if e["standard"] == standard and e["doc_type"] == doc_type
    })


def lookup(
    standard: str,
    doc_type: str,
    version: str,
) -> dict[str, str | None] | None:
    """
    Return ``{"template_path": ..., "rules_path": ...}`` for the given
    combination, or None if not found.
    """
    for entry in _load_registry():
        if (
            entry["standard"] == standard
            and entry["doc_type"] == doc_type
            and entry["version"] == version
        ):
            return {
                "template_path": entry.get("template_path"),
                "rules_path": entry.get("rules_path"),
            }
    return None
