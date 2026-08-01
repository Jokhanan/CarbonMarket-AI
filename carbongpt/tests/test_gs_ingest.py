"""
Tests for carbongpt.repository.gs_ingest (docs/SPEC-01.md).

Parsing tests run against a saved HTML fixture — no network involved, since
Gold Standard's markup can change without notice and parsing must be
verifiable offline. Database tests need a reachable PostgreSQL with the
SPEC-01 schema and the RECH (407) bootstrap already ingested (docs/SPEC-01.md
T3); they skip automatically otherwise, so the suite stays runnable without
a database.
"""
import os
import tempfile
from pathlib import Path

import pytest

from carbongpt.repository.gs_ingest import (
    IngestError,
    _parse_gs_date,
    parse_related_documents,
    parse_revision_history,
)

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "rech_407_page.html").read_text(encoding="utf-8")


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


def _rech_ingested() -> bool:
    if not _db_available():
        return False
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute("SELECT count(*) AS c FROM methodology_version_history WHERE methodology_code = '407'")
        return cur.fetchone()["c"] > 0


requires_db = pytest.mark.skipif(not _db_available(), reason="DATABASE_URL not set or DB unreachable")
requires_rech = pytest.mark.skipif(not _rech_ingested(), reason="RECH (407) not ingested yet — run T3 bootstrap first")


class TestParseGsDate:
    def test_parses_single_digit_day(self):
        assert _parse_gs_date("5.05.2026").isoformat() == "2026-05-05"

    def test_parses_two_digit_day(self):
        assert _parse_gs_date("27.10.2020").isoformat() == "2020-10-27"

    def test_rejects_unrecognised_format(self):
        with pytest.raises(IngestError):
            _parse_gs_date("2026-05-05")


class TestParseRevisionHistory:
    def test_finds_six_versions_with_exact_dates(self):
        history = parse_revision_history(FIXTURE_HTML)
        versions = {e["version"]: e["released_date"].isoformat() for e in history if e["kind"] == "version"}
        assert versions == {
            "5.0": "2026-05-05",
            "4.0": "2021-10-07",
            "3.1": "2017-08-25",
            "3.0": "2017-07-10",
            "2.0": "2015-04-24",
            "1.0": "2011-04-11",
        }

    def test_current_version_has_pdf_url_from_download_block(self):
        history = parse_revision_history(FIXTURE_HTML)
        current = next(e for e in history if e["kind"] == "version" and e["is_current"])
        assert current["version"] == "5.0"
        assert current["pdf_url"] == (
            "https://globalgoals.goldstandard.org/standards/"
            "407_v5.0_PAA-M400-08_Reduced-Emission-from-Cooking-and-Heating.pdf"
        )

    def test_finds_two_rule_updates_and_one_rule_clarification(self):
        history = parse_revision_history(FIXTURE_HTML)
        assert len([e for e in history if e["kind"] == "rule_update"]) == 2
        assert len([e for e in history if e["kind"] == "rule_clarification"]) == 1

    def test_raises_on_missing_revision_history_block(self):
        with pytest.raises(IngestError):
            parse_revision_history("<html><body>nothing here</body></html>")


class TestParseRelatedDocuments:
    def test_finds_cookstove_usage_rate_guidelines(self):
        related = parse_related_documents(FIXTURE_HTML)
        assert len(related) == 1
        assert related[0]["title"] == "Cookstove Usage Rate Guidelines"
        assert related[0]["version"] == "2.0"

    def test_returns_empty_list_when_no_related_documents_section(self):
        assert parse_related_documents("<html><body>nothing here</body></html>") == []


@requires_db
class TestIngestionIdempotence:
    """Ingests a throwaway methodology code twice against the saved fixture
    (network and PDF downloads stubbed out) and checks the second run creates
    no duplicate rows."""

    TEST_CODE = "TEST-407-IDEMPOTENCE"

    @pytest.fixture(autouse=True)
    def cleanup(self):
        yield
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute("DELETE FROM documents WHERE sha256 LIKE 'TESTFAKE%%'")
            cur.execute("DELETE FROM methodology_version_history WHERE methodology_code = %s", (self.TEST_CODE,))
            cur.execute("DELETE FROM methodologies WHERE code = %s", (self.TEST_CODE,))

    def test_two_ingestions_do_not_duplicate(self, monkeypatch):
        import carbongpt.repository.gs_ingest as gs_ingest

        def fake_download(url: str, filename_hint: str):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(b"fake pdf content")
            tmp.close()
            return tmp.name, f"TESTFAKE{abs(hash(url))}"

        monkeypatch.setattr(gs_ingest, "fetch_methodology_page", lambda url: FIXTURE_HTML)
        monkeypatch.setattr(gs_ingest, "download_document", fake_download)
        monkeypatch.setattr(gs_ingest, "parse_related_documents", lambda html: [])

        gs_ingest.ingest_methodology("http://fake.invalid/methodology", methodology_code=self.TEST_CODE)
        gs_ingest.ingest_methodology("http://fake.invalid/methodology", methodology_code=self.TEST_CODE)

        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute(
                "SELECT count(*) AS c FROM methodology_version_history WHERE methodology_code = %s",
                (self.TEST_CODE,),
            )
            assert cur.fetchone()["c"] == 6
            cur.execute("SELECT count(*) AS c FROM documents WHERE sha256 LIKE 'TESTFAKE%%'")
            assert cur.fetchone()["c"] == 9  # 6 versions + 2 rule updates + 1 rule clarification


@requires_rech
class TestResolveApplicableVersion:
    """Exercises the real ingested RECH (407) data. See docs/RECH-V5-VALUE-AUDIT.md
    for why 2026-07-01 resolves to v4.0 rather than v5.0 as docs/SPEC-01.md's
    original example assumed: the PDF states entry into force is 90 days after
    publication (2026-05-05 + 90 days = 2026-08-03), and v5.0 had not taken
    effect yet on 2026-07-01. Trusting the primary source over the spec's
    example was a deliberate choice — flagged to the user, not silently made."""

    def test_before_v4_release(self):
        from carbongpt.repository.gs_ingest import resolve_applicable_version
        assert resolve_applicable_version("407", "2021-06-01")["version"] == "3.1"

    def test_before_v5_entry_into_force(self):
        from carbongpt.repository.gs_ingest import resolve_applicable_version
        assert resolve_applicable_version("407", "2026-07-01")["version"] == "4.0"

    def test_on_v5_entry_into_force_date(self):
        from carbongpt.repository.gs_ingest import resolve_applicable_version
        assert resolve_applicable_version("407", "2026-08-03")["version"] == "5.0"

    def test_transition_required_flag_for_pre_paris_validation(self):
        from carbongpt.repository.gs_ingest import resolve_applicable_version
        result = resolve_applicable_version("407", "2026-08-03", validated_under_version="4.0")
        assert result["transition_required"] is True
        assert "v4.0" in result["transition_reason"]
        assert "v5.0" in result["transition_reason"]


@requires_rech
class TestRegulatoryValues:
    def test_ef_co2_has_multiple_distinct_rows_for_charcoal(self):
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute(
                """SELECT applicability FROM regulatory_values
                   WHERE key = 'EF_CO2' AND version_id =
                       (SELECT id FROM methodology_version_history
                        WHERE methodology_code='407' AND version='5.0')"""
            )
            rows = cur.fetchall()
        charcoal_rows = [r for r in rows if r["applicability"].get("fuel") == "charcoal"]
        assert len(charcoal_rows) == 3, "combustion-only, WCCF 6:1, and WCCF 4:1 must all be present"
        assert len({str(r["applicability"]) for r in charcoal_rows}) == 3, "the three rows must be genuinely distinct"

    def test_llm_unverified_value_raises_on_read(self):
        from carbongpt.repository.db import get_cursor
        from carbongpt.repository.gs_ingest import get_regulatory_value
        with get_cursor() as cur:
            cur.execute(
                "SELECT id FROM methodology_version_history WHERE methodology_code='407' AND version='5.0'"
            )
            version_id = cur.fetchone()["id"]
        with pytest.raises(IngestError, match="llm_unverified"):
            get_regulatory_value(version_id, "fNRB_default")
