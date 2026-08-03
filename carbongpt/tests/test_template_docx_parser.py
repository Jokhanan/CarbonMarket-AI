"""
Tests for carbongpt.repository.template_docx_parser (docs/SPEC-05.md, T3).

Runs against the real VPA-DD v2.3/v3.0 .docx files already tracked in
document_repository/ (content-addressed by sha256 filename prefix, so the
path is stable) — no network involved, no database needed.
"""
from pathlib import Path

import pytest

from carbongpt.repository.template_docx_parser import (
    TemplateParseError,
    parse_template_structure,
)

REPO_DIR = Path(__file__).parent.parent.parent / "document_repository"
V2_3_PATH = REPO_DIR / "5629069d7319be57_T-PreReview_v2.3-VPA-Design-Document.docx"
V3_0_PATH = REPO_DIR / "85924c132bed502d_T-PAA_PreReview_V3.0_VPA-Design-Document.docx"

requires_v2_3_fixture = pytest.mark.skipif(not V2_3_PATH.exists(), reason="VPA-DD v2.3 not ingested yet")
requires_v3_0_fixture = pytest.mark.skipif(not V3_0_PATH.exists(), reason="VPA-DD v3.0 not ingested yet")


class TestParseTemplateStructureErrors:
    def test_raises_on_missing_file(self):
        with pytest.raises(TemplateParseError):
            parse_template_structure("/nonexistent/path/does-not-exist.docx")

    def test_raises_on_non_docx_file(self, tmp_path):
        bogus = tmp_path / "not_a_docx.docx"
        bogus.write_text("this is plain text, not a zip/docx package")
        with pytest.raises(TemplateParseError):
            parse_template_structure(str(bogus))


@requires_v2_3_fixture
class TestVpaDd23Structure:
    """VPA-DD v2.3 (29.06.2023) — used throughout this session as the
    reference the guide gs_vpa_dd_v2_3.py already models by hand."""

    def test_extracts_expected_field_type_counts(self):
        fields = parse_template_structure(str(V2_3_PATH))
        counts = {}
        for f in fields:
            counts[f["field_type"]] = counts.get(f["field_type"], 0) + 1
        # 18 tables total across table/single_value/checkbox/parameter_block,
        # matching the manual count from the reconnaissance session.
        assert counts["table"] + counts["single_value"] + counts["checkbox"] + counts["parameter_block"] == 18
        assert counts["parameter_block"] == 2

    def test_finds_both_parameter_blocks(self):
        fields = parse_template_structure(str(V2_3_PATH))
        param_blocks = [f for f in fields if f["field_type"] == "parameter_block"]
        assert len(param_blocks) == 2
        for f in param_blocks:
            assert f["position"]["table_index"] is not None

    def test_positions_are_structural_not_text_based(self):
        fields = parse_template_structure(str(V2_3_PATH))
        for f in fields:
            if f["field_type"] == "prose":
                assert "paragraph_index" in f["position"]
            else:
                assert "table_index" in f["position"]


@requires_v3_0_fixture
class TestVpaDd30Structure:
    """VPA-DD v3.0 (15.05.2026) — current official version, ingested and
    analysed for the first time this session."""

    def test_extracts_more_fields_than_v2_3(self):
        fields = parse_template_structure(str(V3_0_PATH))
        # v3.0 is a substantially larger, reorganised document (161 fields
        # extracted vs 29 for v2.3) — not a tuning knob, a structural fact
        # confirmed 03.08.2026.
        assert len(fields) > 100

    def test_finds_three_parameter_blocks(self):
        fields = parse_template_structure(str(V3_0_PATH))
        param_blocks = [f for f in fields if f["field_type"] == "parameter_block"]
        assert len(param_blocks) == 3

    def test_detects_modern_content_control_checkboxes(self):
        # v3.0 uses w:sdt/w14:checkbox content controls (479 raw instances),
        # not the legacy w:ffData/w:checkBox form fields v2.3 used — the
        # classifier must catch both mechanisms.
        fields = parse_template_structure(str(V3_0_PATH))
        checkboxes = [f for f in fields if f["field_type"] == "checkbox"]
        assert len(checkboxes) > 0

    def test_top_level_sections_no_longer_use_letter_codes(self):
        # v2.3 organised content under A/B/C/D/E/F letter-coded subsections
        # (mostly inline in table cells, not real Word headings). v3.0
        # replaced this with plain Word Heading 1/2/3 styles and descriptive
        # titles — confirmed structural change, not a parsing artifact.
        fields = parse_template_structure(str(V3_0_PATH))
        level_1 = [f["title"] for f in fields if f["field_type"] == "prose"
                   and f["position"].get("heading_level") == 1]
        assert "Gender equality assessment" in level_1
        assert not any(title.strip().lower().startswith(("a.", "b.", "c.")) for title in level_1)
