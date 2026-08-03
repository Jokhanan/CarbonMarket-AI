"""
Tests for carbongpt.repository.gs_template_ingest (docs/SPEC-05.md, T2).

Parsing tests run against a saved HTML fixture — no network involved.
Database tests need a reachable PostgreSQL with the SPEC-05 schema
(document_templates/document_template_versions/template_fields); they skip
automatically otherwise.
"""
import os
from pathlib import Path

import pytest

from carbongpt.repository.gs_template_ingest import (
    TemplateIngestError,
    _parse_gs_date,
    parse_template_revision_history,
)

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "gs_vpa_dd_template_page.html").read_text(encoding="utf-8")


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


requires_db = pytest.mark.skipif(not _db_available(), reason="DATABASE_URL not set or DB unreachable")


class TestParseGsDate:
    def test_parses_single_digit_day(self):
        assert _parse_gs_date("4.05.2022").isoformat() == "2022-05-04"

    def test_parses_two_digit_day(self):
        assert _parse_gs_date("15.05.2026").isoformat() == "2026-05-15"

    def test_rejects_unrecognised_format(self):
        with pytest.raises(TemplateIngestError):
            _parse_gs_date("May 2026")


class TestParseTemplateRevisionHistory:
    def test_finds_all_seven_versions(self):
        entries = parse_template_revision_history(FIXTURE_HTML)
        versions = {e["version"] for e in entries}
        assert versions == {"1.0", "1.1", "2.0", "2.1", "2.2", "2.3", "3.0"}

    def test_current_version_is_3_0_released_15_05_2026(self):
        entries = {e["version"]: e for e in parse_template_revision_history(FIXTURE_HTML)}
        current = entries["3.0"]
        assert current["is_current"] is True
        assert current["released_date"].isoformat() == "2026-05-15"
        assert current["download_url"] is not None
        assert current["download_url"].lower().endswith((".docx", ".doc"))

    def test_older_versions_are_not_current_and_have_download_urls(self):
        entries = {e["version"]: e for e in parse_template_revision_history(FIXTURE_HTML)}
        v23 = entries["2.3"]
        assert v23["is_current"] is False
        assert v23["released_date"].isoformat() == "2023-06-29"
        assert v23["download_url"] == (
            "https://globalgoals.goldstandard.org/standards/T-PreReview_v2.3-VPA-Design-Document.docx"
        )

    def test_track_changes_and_guide_rows_are_not_treated_as_versions(self):
        # "TRACK CHANGES" and "v.2.3 Guide" share the table with real version
        # rows but are companions of a version, not versions of the template
        # itself (SPEC-05 scope).
        entries = parse_template_revision_history(FIXTURE_HTML)
        labels = {e["version"] for e in entries}
        assert "TRACK CHANGES" not in labels
        assert not any("guide" in str(e.get("document_name", "")).lower() and e["version"] not in
                        {"1.0", "1.1", "2.0", "2.1", "2.2", "2.3", "3.0"} for e in entries)

    def test_raises_on_missing_revision_history_block(self):
        with pytest.raises(TemplateIngestError):
            parse_template_revision_history("<html><body>nothing here</body></html>")


@requires_db
class TestIngestTemplateIdempotence:
    URL = "https://globalgoals.goldstandard.org/t-prereview-vpa-design-document/"

    @pytest.fixture(autouse=True)
    def _cleanup(self):
        from carbongpt.repository.db import get_cursor
        yield
        with get_cursor() as cur:
            cur.execute("DELETE FROM document_templates WHERE standard = 'TEST' AND doc_type = 'TEST-VPA-DD'")

    def test_reingesting_the_same_fixture_does_not_duplicate_versions(self, monkeypatch):
        from carbongpt.repository.db import get_cursor
        import carbongpt.repository.gs_template_ingest as mod

        monkeypatch.setattr(mod, "fetch_template_page", lambda url: FIXTURE_HTML)
        monkeypatch.setattr(mod, "download_document", lambda url, hint: ("/dev/null", "fakehash", 0))

        mod.ingest_template(self.URL, standard="TEST", doc_type="TEST-VPA-DD")
        mod.ingest_template(self.URL, standard="TEST", doc_type="TEST-VPA-DD")

        with get_cursor() as cur:
            cur.execute(
                """SELECT count(*) c FROM document_template_versions dtv
                   JOIN document_templates dt ON dt.id = dtv.template_id
                   WHERE dt.standard = 'TEST' AND dt.doc_type = 'TEST-VPA-DD'"""
            )
            assert cur.fetchone()["c"] == 7
