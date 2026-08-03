"""
Guide registry for CarbonGPT AI review and drafting.

Maps (standard, doc_type) pairs to the appropriate guide for
section-by-section review (ai_review.py) and drafting
(ai_writer.py::generate_full_document/generate_section_draft).

docs/SPEC-05.md T6 (03.08.2026): load_guide() now checks first whether an
analyzed template version exists in the database (SPEC-05 T1-T3/T7 —
document_template_versions + template_fields) for the requested
(standard, doc_type). If one does, a lightweight object built on the fly
from template_fields is returned, exposing the exact same interface as
the hand-written Python guide modules below (.SUBSECTIONS,
.get_subsections(), .get_subsection(), .get_parent_sections(),
.get_subsections_for_parent()) — callers (ai_writer.py, ai_review.py)
don't need to change, and don't know which source they got. If no
analyzed version exists yet for that pair, or the database is
unreachable, GUIDE_REGISTRY is used exactly as before — this is what
keeps every (standard, doc_type) pair not yet migrated working unchanged.

Only ("GoldStandard", "VPA-DD") is DB-backed today (VPA-DD v3.0, ingested
and analyzed in SPEC-05 T7). The other seven entries in GUIDE_REGISTRY
still resolve to their Python module exactly as before — verified by the
test suite (test_guides_db_adapter.py) importing each one unchanged.
"""

import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

GUIDE_REGISTRY: dict[tuple[str, str], str] = {
    ("GoldStandard", "MR"): "carbongpt.guides.gs_mr_perfcert_v1_2",
    ("GoldStandard", "PDD"): "carbongpt.guides.gs_pdd_v1_5",
    ("GoldStandard", "PoA-DD"): "carbongpt.guides.gs_poa_dd_v2_2",
    ("GoldStandard", "VPA-DD"): "carbongpt.guides.gs_vpa_dd_v2_3",
    # Generic Verra VCS guides (solar, REDD+, other non-cookstove methodologies)
    ("Verra", "VCS-PD"): "carbongpt.guides.vcs_pd_v4_4",
    ("Verra", "VCS-MR"): "carbongpt.guides.vcs_mr_v4_4",
    ("Verra", "VCS-ValVer"): "carbongpt.guides.vcs_valver_v4_4",
    # VM0050-specific guides (cookstoves / thermal energy, VCS VM0050 v1.0)
    ("Verra", "VM0050-PD"): "carbongpt.guides.vcs_vm0050_v1_0",
    ("Verra", "VM0050-MR"): "carbongpt.guides.vcs_vm0050_v1_0",
}

DOC_TYPE_LABELS: dict[str, str] = {
    "MR": "Monitoring Report",
    "PDD": "Project Design Document",
    "PoA-DD": "Programme of Activity Design Document",
    "VPA-DD": "VPA Design Document",
    "VCS-PD": "VCS Project Description",
    "VCS-MR": "VCS Monitoring Report",
    "VCS-ValVer": "VCS Joint Validation & Verification Report",
    "VM0050-PD": "VM0050 Project Description (Cookstoves)",
    "VM0050-MR": "VM0050 Monitoring Report (Cookstoves)",
}

# template_fields.field_type (SPEC-05) -> content_format, matching the
# vocabulary the hand-written guides already use (ai_writer.py's
# FORMAT_SYSTEM_GUIDANCE/FORMAT_CLOSING_INSTRUCTIONS dicts key on this;
# an unrecognised value degrades gracefully to no extra guidance, never
# an error — verified, see docs/STATUS.md).
_FIELD_TYPE_TO_CONTENT_FORMAT = {
    "prose": "prose",
    "table": "table",
    "single_value": "single_value",
    "checkbox": "checkbox",
    "parameter_block": "parameter_blocks",
    "checklist_item": "checklist",
    "attachment": "prose",
}


class _DbBackedGuide:
    """Same interface as the hand-written guide modules
    (carbongpt/guides/gs_*.py, vcs_*.py) — built from template_fields
    instead of a Python dict literal. See module docstring."""

    def __init__(self, guide_id: str, subsections: dict[str, dict]):
        self.GUIDE_ID = guide_id
        self.SUBSECTIONS = subsections

    def get_subsections(self) -> dict[str, dict]:
        return self.SUBSECTIONS

    def get_subsection(self, subsection_id: str) -> dict | None:
        return self.SUBSECTIONS.get(subsection_id)

    def get_parent_sections(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for sub in self.SUBSECTIONS.values():
            ps = sub.get("parent_section")
            if ps not in seen:
                seen.add(ps)
                result.append(ps)
        return result

    def get_subsections_for_parent(self, parent_section: str) -> dict[str, dict]:
        return {k: v for k, v in self.SUBSECTIONS.items() if v.get("parent_section") == parent_section}


def _build_parameter_block_scaffold(local_path: str, table_index: int) -> str:
    """Reads the actual row labels of a parameter_block table in the
    .docx (same file already used by SPEC-06 T5's block-pattern
    classifier) and produces a markdown scaffold in the same shape the
    hand-written guides used (see gs_vpa_dd_v2_3.py's B.6.2 entry) — real
    field labels from the official v3.0 template, not the v2.3 guide's
    hand-copied ones."""
    try:
        import docx
        doc = docx.Document(local_path)
        table = doc.tables[table_index]
        labels = [row.cells[0].text.strip() for row in table.rows if row.cells[0].text.strip()]
    except Exception as exc:
        logger.warning("Could not build a scaffold for table_index=%s in %r: %s", table_index, local_path, exc)
        return ""
    lines = ["| Field | Value |", "| --- | --- |"]
    lines += [f"| {label} | [...] |" for label in labels]
    return "\n".join(lines)


def _load_db_backed_guide(standard: str, doc_type: str) -> Any | None:
    """Returns a _DbBackedGuide for (standard, doc_type) if an analyzed,
    current template_version exists in the database — None otherwise
    (caller falls back to GUIDE_REGISTRY). Never raises: any DB error is
    logged and treated the same as "not found", so a database outage
    degrades to the Python guides rather than breaking drafting/review."""
    try:
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute(
                """SELECT dtv.id, dtv.local_path FROM document_template_versions dtv
                   JOIN document_templates dt ON dt.id = dtv.template_id
                   WHERE dt.standard = %s AND dt.doc_type = %s
                         AND dtv.is_current = true AND dtv.parsed_at IS NOT NULL""",
                (standard, doc_type),
            )
            version_row = cur.fetchone()
            if version_row is None:
                return None
            template_version_id, local_path = version_row["id"], version_row["local_path"]

            cur.execute(
                """SELECT field_key, parent_section, title, field_type, position,
                          must_include, format_instructions
                   FROM template_fields WHERE template_version_id = %s
                   ORDER BY field_key""",
                (template_version_id,),
            )
            fields = cur.fetchall()
    except Exception as exc:
        logger.warning("DB-backed guide lookup failed for standard=%r, doc_type=%r — "
                        "falling back to GUIDE_REGISTRY: %s", standard, doc_type, exc)
        return None

    if not fields:
        return None

    subsections: dict[str, dict] = {}
    for f in fields:
        content_format = _FIELD_TYPE_TO_CONTENT_FORMAT.get(f["field_type"], "prose")
        template_scaffold = ""
        if f["field_type"] == "parameter_block" and local_path:
            template_scaffold = _build_parameter_block_scaffold(local_path, f["position"]["table_index"])
        subsections[f["field_key"]] = {
            "title": f["title"] or "",
            "parent_section": f["parent_section"],
            "must_include": [f["must_include"]] if f["must_include"] else [],
            "examples": [],
            "failure_modes": [],
            "content_format": content_format,
            "format_instructions": f["format_instructions"] or "",
            "template_scaffold": template_scaffold,
        }

    return _DbBackedGuide(guide_id=f"{standard}_{doc_type}_db", subsections=subsections)


def load_guide(standard: str, doc_type: str) -> Any:
    db_guide = _load_db_backed_guide(standard, doc_type)
    if db_guide is not None:
        return db_guide

    key = (standard, doc_type)
    module_path = GUIDE_REGISTRY.get(key)
    if module_path is None:
        raise ValueError(
            f"No AI review guide registered for standard={standard!r}, "
            f"doc_type={doc_type!r}. Available: {list(GUIDE_REGISTRY.keys())}"
        )
    return importlib.import_module(module_path)


def list_supported_doc_types(standard: str) -> list[str]:
    return sorted(dt for (std, dt) in GUIDE_REGISTRY if std == standard)


def is_ai_review_supported(standard: str, doc_type: str) -> bool:
    return (standard, doc_type) in GUIDE_REGISTRY
