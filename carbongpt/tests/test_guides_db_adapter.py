"""
Tests for carbongpt.guides's DB-backed adapter (docs/SPEC-05.md, T6).

Needs a reachable PostgreSQL with VPA-DD v3.0 ingested and analyzed
(SPEC-05 T7); the fallback tests need no database at all — DB
unavailability IS what they exercise.
"""
import os

import pytest

from carbongpt.guides import GUIDE_REGISTRY, load_guide


def _db_available() -> bool:
    if not os.getenv("DATABASE_URL"):
        return False
    try:
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def _vpa_dd_v3_analyzed() -> bool:
    if not _db_available():
        return False
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute(
            """SELECT count(*) c FROM document_template_versions dtv
               JOIN document_templates dt ON dt.id = dtv.template_id
               WHERE dt.doc_type = 'VPA-DD' AND dtv.version = '3.0'
                     AND dtv.is_current = true AND dtv.parsed_at IS NOT NULL"""
        )
        return cur.fetchone()["c"] == 1


requires_vpa_dd_v3 = pytest.mark.skipif(
    not _vpa_dd_v3_analyzed(), reason="VPA-DD v3.0 not ingested/analyzed (SPEC-05 T7 bootstrap)"
)


class TestFallbackWithoutDatabase:
    """These must pass even when the database is unreachable — the whole
    point of the adapter is that a database outage degrades to the Python
    guides, never breaks drafting/review. carbongpt.repository.db reads
    DATABASE_URL once at import time (module-level constant), so
    monkeypatching the env var mid-suite has no effect on an
    already-imported module — get_cursor itself is monkeypatched instead,
    to simulate the outage directly rather than relying on import timing."""

    def _break_get_cursor(self, monkeypatch):
        import carbongpt.repository.db as db_module

        def _raise(*args, **kwargs):
            raise RuntimeError("simulated database outage")

        monkeypatch.setattr(db_module, "get_cursor", _raise)

    def test_every_registered_pair_still_loads(self, monkeypatch):
        self._break_get_cursor(monkeypatch)
        for standard, doc_type in GUIDE_REGISTRY:
            guide = load_guide(standard, doc_type)
            assert hasattr(guide, "SUBSECTIONS")
            assert len(guide.SUBSECTIONS) > 0

    def test_vpa_dd_falls_back_to_the_v2_3_python_module(self, monkeypatch):
        self._break_get_cursor(monkeypatch)
        guide = load_guide("GoldStandard", "VPA-DD")
        assert guide.__name__ == "carbongpt.guides.gs_vpa_dd_v2_3"
        assert len(guide.SUBSECTIONS) == 27


@requires_vpa_dd_v3
class TestDbBackedVpaDd:
    def test_vpa_dd_resolves_to_the_db_backed_guide(self):
        guide = load_guide("GoldStandard", "VPA-DD")
        assert type(guide).__name__ == "_DbBackedGuide"
        assert len(guide.SUBSECTIONS) == 161

    def test_other_seven_pairs_are_unaffected_still_python_modules(self):
        # The adapter must be selective — only the migrated pair changes.
        for standard, doc_type in GUIDE_REGISTRY:
            if (standard, doc_type) == ("GoldStandard", "VPA-DD"):
                continue
            guide = load_guide(standard, doc_type)
            assert type(guide).__name__ != "_DbBackedGuide", f"{standard}/{doc_type} unexpectedly DB-backed"

    def test_subsections_expose_the_full_guide_interface(self):
        guide = load_guide("GoldStandard", "VPA-DD")
        assert callable(guide.get_subsections)
        assert callable(guide.get_subsection)
        assert callable(guide.get_parent_sections)
        assert callable(guide.get_subsections_for_parent)
        assert guide.get_subsections() is guide.SUBSECTIONS

    def test_every_subsection_has_the_keys_ai_writer_and_ai_review_require(self):
        # ai_writer.py and ai_review.py index subsection['title'] and
        # subsection['parent_section'] directly (not .get) in places —
        # missing either would raise KeyError mid-draft/mid-review.
        guide = load_guide("GoldStandard", "VPA-DD")
        for key, sub in guide.SUBSECTIONS.items():
            assert "title" in sub, key
            assert "parent_section" in sub, key
            assert "must_include" in sub
            assert "content_format" in sub

    def test_parameter_block_fields_get_a_scaffold_from_the_real_docx(self):
        guide = load_guide("GoldStandard", "VPA-DD")
        param_blocks = {k: v for k, v in guide.SUBSECTIONS.items() if v["content_format"] == "parameter_blocks"}
        assert len(param_blocks) == 3  # T37, T40, T55 — SPEC-05 T7
        for key, sub in param_blocks.items():
            assert sub["template_scaffold"], f"{key} has no scaffold"
            assert "Data/parameter" in sub["template_scaffold"]

    def test_get_parent_sections_returns_the_nine_level_one_sections(self):
        guide = load_guide("GoldStandard", "VPA-DD")
        parents = guide.get_parent_sections()
        assert "Application of methodology (ies)" in parents
        assert "Sustainable development contribution" in parents
