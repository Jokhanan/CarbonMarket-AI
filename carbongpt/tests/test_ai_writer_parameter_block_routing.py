"""
Tests for the SPEC-06 T5 integration in carbongpt.core.ai_writer:
generate_section_draft() routes parameter_blocks-format sections through
the sourced, validated pipeline (parameter_block_drafting.py) when a
parameter_id is given. No network — call_openai() and the database are
monkeypatched.
"""
import os

import pytest


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


def _rech_parameters_ready() -> bool:
    if not _db_available():
        return False
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute(
            """SELECT count(*) c FROM methodology_parameters mp
               JOIN methodology_version_history mvh ON mvh.id = mp.methodology_version_id
               WHERE mvh.methodology_code = '407' AND mvh.is_current = true"""
        )
        return cur.fetchone()["c"] > 0


requires_bootstrap = pytest.mark.skipif(
    not _vpa_dd_v3_analyzed() or not _rech_parameters_ready(),
    reason="VPA-DD v3.0 / RECH v5.0 parameters not bootstrapped (SPEC-05 T7 / SPEC-06 T3)",
)


@requires_bootstrap
class TestGenerateSectionDraftRoutesParameterBlocks:
    def test_routes_to_sourced_pipeline_when_parameter_id_given(self, monkeypatch):
        from carbongpt.core import ai_writer

        captured = {}

        def fake_generate(parameter_id, project_info):
            captured["parameter_id"] = parameter_id
            return "Data/parameter: WCCF\nUnit: Ratio (kg wood per kg charcoal)", "claude-sonnet-5", {}

        monkeypatch.setattr(ai_writer, "_draft_parameter_block", fake_generate)

        text = ai_writer.generate_section_draft(
            standard="GoldStandard", project_doc_type="vpa_dd", section_id="T37",
            project_info={"name": "Test", "country": "Ghana"}, parameter_id="ICS 17",
        )
        assert captured["parameter_id"] == "ICS 17"
        assert "WCCF" in text

    def test_does_not_route_without_a_parameter_id(self, monkeypatch):
        # Without parameter_id, must fall through to the generic path —
        # confirmed by checking _draft_parameter_block is never called and
        # the call reaches _call_openai instead (mocked to avoid network).
        from carbongpt.core import ai_writer

        def fail_if_called(*args, **kwargs):
            raise AssertionError("_draft_parameter_block should not be called without parameter_id")

        monkeypatch.setattr(ai_writer, "_draft_parameter_block", fail_if_called)
        monkeypatch.setattr(ai_writer, "_call_openai", lambda *a, **k: "generic drafted text")

        text = ai_writer.generate_section_draft(
            standard="GoldStandard", project_doc_type="vpa_dd", section_id="T37",
            project_info={"name": "Test", "country": "Ghana"},
        )
        assert text == "generic drafted text"

    def test_non_parameter_block_section_ignores_parameter_id(self, monkeypatch):
        # A prose section (e.g. a Heading field) must never reach
        # _draft_parameter_block even if a parameter_id is (incorrectly)
        # passed — the parameter_blocks routing condition checks
        # content_format, not just parameter_id presence. It still routes
        # through _draft_prose_section (a separate, correct routing for
        # prose sections on the DB-backed guide, v1.0) — parameter_id is
        # simply irrelevant there, not a signal to fall through further to
        # the generic path.
        from carbongpt.core import ai_writer

        def fail_if_called(*args, **kwargs):
            raise AssertionError("_draft_parameter_block should not be called for a prose section")

        def fake_prose(field_key, project_info):
            return "sourced prose text", "claude-sonnet-5", {}

        monkeypatch.setattr(ai_writer, "_draft_parameter_block", fail_if_called)
        monkeypatch.setattr(ai_writer, "_draft_prose_section", fake_prose)
        monkeypatch.setattr(ai_writer, "_call_openai", lambda *a, **k: "generic prose text")

        guide = ai_writer.load_guide("GoldStandard", "VPA-DD")
        prose_section_id = next(
            k for k, v in guide.SUBSECTIONS.items() if v.get("content_format") == "prose"
        )

        text = ai_writer.generate_section_draft(
            standard="GoldStandard", project_doc_type="vpa_dd", section_id=prose_section_id,
            project_info={"id": 12, "name": "Test", "country": "Ghana"}, parameter_id="ICS 17",
        )
        assert text == "sourced prose text"


@requires_bootstrap
class TestGenerateSectionDraftRoutesProseSections:
    def test_routes_prose_sections_to_the_sourced_pipeline(self, monkeypatch):
        from carbongpt.core import ai_writer

        captured = {}

        def fake_generate(field_key, project_info):
            captured["field_key"] = field_key
            return "This section applies RECH v5.0.", "claude-sonnet-5", {}

        monkeypatch.setattr(ai_writer, "_draft_prose_section", fake_generate)
        monkeypatch.setattr(ai_writer, "_call_openai", lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("generic path should not be reached for a prose DB-backed section")
        ))

        guide = ai_writer.load_guide("GoldStandard", "VPA-DD")
        prose_section_id = next(
            k for k, v in guide.SUBSECTIONS.items() if v.get("content_format") == "prose"
        )

        text = ai_writer.generate_section_draft(
            standard="GoldStandard", project_doc_type="vpa_dd", section_id=prose_section_id,
            project_info={"id": 12, "name": "Gh", "country": "Ghana"},
        )
        assert captured["field_key"] == prose_section_id
        assert "RECH v5.0" in text

    def test_non_db_backed_guide_uses_generic_path_for_prose(self, monkeypatch):
        # gs_vpa_dd_v2_3.py is unaffected — _draft_prose_section must never
        # be called for a section coming from a hand-written Python guide.
        from carbongpt.core import ai_writer

        def fail_if_called(*args, **kwargs):
            raise AssertionError("_draft_prose_section should not be called for a non-DB-backed guide")

        monkeypatch.setattr(ai_writer, "_draft_prose_section", fail_if_called)
        monkeypatch.setattr(ai_writer, "_call_openai", lambda *a, **k: "generic prose text")

        text = ai_writer.generate_section_draft(
            standard="GoldStandard", project_doc_type="poa_dd", section_id="A.1",
            project_info={"id": 12, "name": "Test", "country": "Ghana"},
        )
        assert text == "generic prose text"


@requires_bootstrap
class TestDraftFullParameterBlockSection:
    def test_concatenates_one_block_per_instance_with_separators(self, monkeypatch):
        from carbongpt.core import ai_writer

        calls = []

        def fake_draft(parameter_id, project_info):
            calls.append(parameter_id)
            return f"Data/parameter: {parameter_id}", "claude-sonnet-5", {}

        monkeypatch.setattr(ai_writer, "_draft_parameter_block", fake_draft)

        text = ai_writer._draft_full_parameter_block_section("T37", {"id": 12, "document_language": "en"})

        assert len(calls) == 18  # ex ante block, SPEC-06 T5 result (17 ICS + fNRB)
        assert "=== PARAMETER BLOCK:" in text
        for parameter_id in calls:
            assert parameter_id in text

    def test_a_failing_instance_is_recorded_inline_not_silently_dropped(self, monkeypatch):
        from carbongpt.core import ai_writer

        def fake_draft(parameter_id, project_info):
            if parameter_id == "ICS 1":
                raise ValueError("simulated validator rejection")
            return f"Data/parameter: {parameter_id}", "claude-sonnet-5", {}

        monkeypatch.setattr(ai_writer, "_draft_parameter_block", fake_draft)

        text = ai_writer._draft_full_parameter_block_section("T37", {"id": 12, "document_language": "en"})
        assert "[ERROR:" in text
        assert "simulated validator rejection" in text

    def test_unmapped_patron_returns_a_clear_not_available_marker_not_generated_text(self):
        from carbongpt.core import ai_writer

        text = ai_writer._draft_full_parameter_block_section("T55", {"id": 12, "document_language": "en"})
        assert text.startswith("[NOT AVAILABLE:")
