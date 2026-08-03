"""
Tests for carbongpt.repository.rech_parameter_extractor (docs/SPEC-06.md,
T3). Runs against the real RECH v5.0 PDF already in document_repository/
(content-addressed path, stable) — no network involved.
"""
from pathlib import Path

import pytest

from carbongpt.repository.rech_parameter_extractor import (
    RechParameterExtractionError,
    extract_rech_parameters,
)

REPO_DIR = Path(__file__).parent.parent.parent / "document_repository"
RECH_V5_PATH = REPO_DIR / (
    "46b28bf95d6c80b7_CURRENT_DOCUMENT-_Reduced_emissions_from_cooking_and_heating__RECH___formerly_TPDDTEC"
)

requires_fixture = pytest.mark.skipif(not RECH_V5_PATH.exists(), reason="RECH v5.0 PDF not ingested yet")


class TestExtractionErrors:
    def test_raises_on_missing_file(self):
        with pytest.raises(RechParameterExtractionError):
            extract_rech_parameters("/nonexistent/rech.pdf")


@requires_fixture
class TestRechV5Extraction:
    @pytest.fixture(scope="class")
    def params(self):
        return extract_rech_parameters(str(RECH_V5_PATH))

    def test_extracts_all_26_parameters(self, params):
        ids = {p["parameter_id"] for p in params}
        assert len(params) == 26
        assert ids == {f"ICS {n}" for n in range(1, 27)}

    def test_ics_1_to_17_are_ex_ante_under_section_14_2(self, params):
        # RECH v5.0's own §14.2.1 text: "shall be determined ex-ante ...
        # and shall remain fixed for the duration of the crediting period."
        for n in range(1, 18):
            p = next(x for x in params if x["parameter_id"] == f"ICS {n}")
            assert p["section_ref"] == "14.2"
            assert p["timing_classification"] == "ex_ante"

    def test_ics_18_to_26_are_under_section_14_3(self, params):
        # §14.3.1 : "shall be monitored during the crediting period" —
        # 'monitoring' by default, except ICS 20 (fNRB, see below).
        for n in range(18, 27):
            p = next(x for x in params if x["parameter_id"] == f"ICS {n}")
            assert p["section_ref"] == "14.3"
            assert p["timing_classification"] in ("monitoring", "both")

    def test_fnrb_ics_20_classified_both_not_decided_automatically(self, params):
        # The methodology's own text: "Determined ex-ante and fixed for the
        # crediting period OR updated ... biennially. The choice shall be
        # confirmed at Design Certification." — must not be silently
        # bucketed into just one of ex_ante/monitoring (explicit user
        # requirement).
        fnrb = next(p for p in params if p["parameter_id"] == "ICS 20")
        assert fnrb["timing_classification"] == "both"
        assert "ex-ante" in fnrb["measurement_frequency_note"].lower()
        assert "biennial" in fnrb["measurement_frequency_note"].lower()

    def test_every_parameter_has_a_section_and_page_reference(self, params):
        # Explicit requirement: every parameter traced to its section and page.
        for p in params:
            assert p["section_ref"] in ("14.2", "14.3")
            assert p["page_ref"] and p["page_ref"].isdigit()

    def test_monitored_parameters_have_a_frequency_note(self, params):
        # ICS 18-26 (monitoring/both) must all have a non-empty
        # measurement_frequency_note — this is the field the classification
        # itself is derived from, so it can't legitimately be absent for
        # any parameter classified monitoring/both.
        for p in params:
            if p["timing_classification"] in ("monitoring", "both"):
                assert p["measurement_frequency_note"], p["parameter_id"]

    def test_ics_1_key_fields_are_clean(self, params):
        ics1 = next(p for p in params if p["parameter_id"] == "ICS 1")
        assert ics1["key"] == "Activity technology description and thermal efficiency"
        assert ics1["unit"] == "%, kW"
        assert "cookstoves" in ics1["measurement_method"].lower()
        # No page-boundary contamination (ICS 15/19 span a page break —
        # regression check for the header/footer-stripping bug found while
        # building this extractor).
        assert "PAGE:" not in (ics1["key"] or "")
        assert "GS4GG PAA M400-08" not in (ics1["description"] or "")

    def test_ics_7_unit_is_not_contaminated_by_equations_referred_field(self, params):
        # ICS 7 is the only parameter with an "Equations referred:" field
        # between "Data unit:" and "Purpose of data:" — unrecognised in an
        # earlier version, its value ("N/A") bled into "unit" ("N/A
        # Equations N/A referred:"). Caught by the user reviewing the
        # delivered table.
        ics7 = next(p for p in params if p["parameter_id"] == "ICS 7")
        assert ics7["unit"] == "N/A"
        assert "equations" not in (ics7["unit"] or "").lower()

    def test_page_spanning_parameters_are_not_contaminated(self, params):
        # ICS 15 and ICS 19 span a page break in the source PDF — found
        # corrupted with header/footer boilerplate before the fix.
        for pid in ("ICS 15", "ICS 19"):
            p = next(x for x in params if x["parameter_id"] == pid)
            assert "PAGE:" not in (p["key"] or "")
            assert "Reduced Emissions from Cooking and Heating" not in (p["key"] or "")
