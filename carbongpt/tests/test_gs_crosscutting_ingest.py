"""
Tests for carbongpt.repository.gs_crosscutting_ingest (docs/SPEC-06.md, T2).

Parsing tests run against saved HTML fixtures — no network involved.
Database tests need a reachable PostgreSQL with the SPEC-06 schema; they
skip automatically otherwise.
"""
import os
from pathlib import Path

import pytest

from carbongpt.repository.gs_crosscutting_ingest import (
    CROSSCUTTING_DOCUMENTS,
    _parse_single_version,
)
from carbongpt.repository.gs_template_ingest import (
    TemplateIngestError,
    parse_template_revision_history,
)

FIXTURE_103 = (Path(__file__).parent / "fixtures" / "gs_103_safeguarding_page.html").read_text(encoding="utf-8")
FIXTURE_118 = (Path(__file__).parent / "fixtures" / "gs_118_sdg_indicators_page.html").read_text(encoding="utf-8")


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


class TestDocumentList:
    def test_lists_exactly_the_seven_documents(self):
        codes = {d["code"] for d in CROSSCUTTING_DOCUMENTS}
        assert codes == {"101", "102", "103", "104", "118", "119", "201"}


class TestCrosscuttingPageWithRevisionHistory:
    """103 uses the same REVISION HISTORY table pattern as the VPA-DD
    template pages (SPEC-05) — same parser, reused unchanged."""

    def test_current_version_is_2_1_released_29_06_2023(self):
        entries = {e["version"]: e for e in parse_template_revision_history(FIXTURE_103)}
        current = entries["2.1"]
        assert current["is_current"] is True
        assert current["released_date"].isoformat() == "2023-06-29"

    def test_current_version_download_url_is_a_pdf(self):
        # Regression check: an earlier version of _find_current_document_url
        # only recognised .docx/.doc — every current-version link on these
        # PDF-published cross-cutting pages came back None until fixed.
        entries = {e["version"]: e for e in parse_template_revision_history(FIXTURE_103)}
        current = entries["2.1"]
        assert current["download_url"] is not None
        assert current["download_url"].lower().endswith(".pdf")


class TestCrosscuttingPageWithoutRevisionHistory:
    """118 has no REVISION HISTORY block at all (single version published
    so far, confirmed 03.08.2026) — exercises the fallback parser."""

    def test_raises_via_the_normal_parser(self):
        with pytest.raises(TemplateIngestError):
            parse_template_revision_history(FIXTURE_118)

    def test_fallback_parser_finds_the_single_version(self):
        entries = _parse_single_version(FIXTURE_118)
        assert len(entries) == 1
        assert entries[0]["version"] == "1.0"
        assert entries[0]["is_current"] is True
        assert entries[0]["download_url"] is not None
        assert entries[0]["download_url"].lower().endswith(".pdf")

    def test_fallback_parser_finds_the_release_date(self):
        entries = _parse_single_version(FIXTURE_118)
        assert entries[0]["released_date"].isoformat() == "2025-10-18"


@requires_db
class TestIngestCrosscuttingDocumentIdempotence:
    @pytest.fixture(autouse=True)
    def _cleanup(self):
        from carbongpt.repository.db import get_cursor
        yield
        with get_cursor() as cur:
            cur.execute("DELETE FROM crosscutting_requirements WHERE code = 'TEST103'")

    def test_reingesting_the_same_fixture_does_not_duplicate_versions(self, monkeypatch):
        from carbongpt.repository.db import get_cursor
        import carbongpt.repository.gs_crosscutting_ingest as mod

        monkeypatch.setattr(mod, "fetch_template_page", lambda url: FIXTURE_103)
        monkeypatch.setattr(mod, "download_document", lambda url, hint: ("/dev/null", "fakehash", 0))

        mod.ingest_crosscutting_document("TEST103", "Test Safeguarding", "https://example.test/103")
        mod.ingest_crosscutting_document("TEST103", "Test Safeguarding", "https://example.test/103")

        with get_cursor() as cur:
            cur.execute("SELECT count(*) c FROM crosscutting_requirements WHERE code = 'TEST103'")
            assert cur.fetchone()["c"] == 5  # v1.0, 1.1, 1.2, 2.0, 2.1
