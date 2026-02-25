"""
Tests for all rule types and compliance_score computation.

Covers:
- required_field: found, missing, silently skipped when section missing
- date_format_ddmmyyyy: correct format, wrong format, no dates, section missing
- not_applicable_required_when_blank: short with N/A, short without, long text, section missing
- compliance_score calculation
- end-to-end with real docx files
"""

import tempfile

import pytest
from docx import Document

from carbongpt.core.models import Finding
from carbongpt.tools.rule_engine import (
    compute_compliance_score,
    _check_required_field,
    _check_date_format_ddmmyyyy,
    _check_not_applicable_required_when_blank,
)
from carbongpt.tools.section_mapper import map_sections
from carbongpt.tools.regex_utils import any_pattern_matches, find_all_matches, is_ddmmyyyy
from carbongpt.tools.parse_docx import parse_docx
from carbongpt.core.orchestrator import run_analysis


# ---------------------------------------------------------------------------
# regex_utils
# ---------------------------------------------------------------------------

class TestRegexUtils:
    def test_any_pattern_matches_date(self):
        assert any_pattern_matches("Started on 2024-01-15", [r"\d{4}-\d{2}-\d{2}"])

    def test_any_pattern_matches_none(self):
        assert not any_pattern_matches("No dates here", [r"\d{4}-\d{2}-\d{2}"])

    def test_find_all_matches(self):
        text = "Dates: 2024-01-01 and 15/06/2024"
        matches = find_all_matches(text, [r"\d{4}-\d{2}-\d{2}", r"\d{2}/\d{2}/\d{4}"])
        assert "2024-01-01" in matches
        assert "15/06/2024" in matches

    def test_is_ddmmyyyy_valid(self):
        assert is_ddmmyyyy("15/06/2024")
        assert is_ddmmyyyy("01/01/2023")

    def test_is_ddmmyyyy_invalid(self):
        assert not is_ddmmyyyy("2024-01-15")
        assert not is_ddmmyyyy("15-06-2024")
        assert not is_ddmmyyyy("June 15, 2024")


# ---------------------------------------------------------------------------
# _check_required_field — field found
# ---------------------------------------------------------------------------

class TestRequiredFieldFound:
    def test_date_present(self):
        rule = {
            "id": "F001", "type": "required_field",
            "section": "Monitoring Period", "field_name": "start",
            "severity": "ERROR", "patterns": [r"\d{4}-\d{2}-\d{2}"],
        }
        sections = {"Monitoring Period": "Started 2024-01-01."}
        section_map = {"Monitoring Period": "Monitoring Period"}
        assert _check_required_field(rule, sections, section_map) is None

    def test_keyword_present(self):
        rule = {
            "id": "F004", "type": "required_field",
            "section": "Project Description", "field_name": "crediting_period",
            "severity": "ERROR", "patterns": [r"(?i)crediting\s+period"],
        }
        sections = {"Project Description": "The crediting period spans 10 years."}
        section_map = {"Project Description": "Project Description"}
        assert _check_required_field(rule, sections, section_map) is None

    def test_fuzzy_matched_heading(self):
        sections = {"B.1 Monitoring Period": "Data from 2024-06-01."}
        section_map = map_sections(["Monitoring Period"], list(sections.keys()), threshold=70)
        rule = {
            "id": "F002", "type": "required_field",
            "section": "Monitoring Period", "field_name": "start",
            "severity": "ERROR", "patterns": [r"\d{4}-\d{2}-\d{2}"],
        }
        assert _check_required_field(rule, sections, section_map) is None


# ---------------------------------------------------------------------------
# _check_required_field — field missing
# ---------------------------------------------------------------------------

class TestRequiredFieldMissing:
    def test_no_pattern_matches(self):
        rule = {
            "id": "F001", "type": "required_field",
            "section": "Monitoring Period", "field_name": "start",
            "severity": "ERROR", "patterns": [r"\d{4}-\d{2}-\d{2}"],
        }
        sections = {"Monitoring Period": "Monitoring was done throughout the year."}
        section_map = {"Monitoring Period": "Monitoring Period"}
        finding = _check_required_field(rule, sections, section_map)
        assert finding is not None
        assert "start" in finding.message
        assert finding.severity == "ERROR"


# ---------------------------------------------------------------------------
# _check_required_field — section missing => silently skipped
# ---------------------------------------------------------------------------

class TestRequiredFieldSectionMissing:
    def test_returns_none_when_section_missing(self):
        rule = {
            "id": "F001", "type": "required_field",
            "section": "Monitoring Period", "field_name": "start",
            "severity": "ERROR", "patterns": [r"\d{4}-\d{2}-\d{2}"],
        }
        sections = {"Project Description": "Some text."}
        section_map = {"Monitoring Period": None}
        assert _check_required_field(rule, sections, section_map) is None

    def test_returns_none_when_no_sections_at_all(self):
        rule = {
            "id": "F003", "type": "required_field",
            "section": "Data Quality", "field_name": "qa",
            "severity": "WARNING", "patterns": [r"(?i)quality"],
        }
        assert _check_required_field(rule, {}, {"Data Quality": None}) is None


# ---------------------------------------------------------------------------
# _check_date_format_ddmmyyyy
# ---------------------------------------------------------------------------

class TestDateFormatDDMMYYYY:
    def _rule(self, section="KEY PROJECT INFORMATION"):
        return {
            "id": "D001", "type": "date_format_ddmmyyyy",
            "section": section, "severity": "WARNING",
            "date_patterns": [r"\d{4}-\d{2}-\d{2}", r"\d{2}-\d{2}-\d{4}", r"\d{2}/\d{2}/\d{4}"],
        }

    def test_correct_format_no_finding(self):
        sections = {"KEY PROJECT INFORMATION": "Completion date: 15/06/2024"}
        section_map = {"KEY PROJECT INFORMATION": "KEY PROJECT INFORMATION"}
        assert _check_date_format_ddmmyyyy(self._rule(), sections, section_map) is None

    def test_wrong_format_yyyy_mm_dd(self):
        sections = {"KEY PROJECT INFORMATION": "Completion date: 2024-06-15"}
        section_map = {"KEY PROJECT INFORMATION": "KEY PROJECT INFORMATION"}
        finding = _check_date_format_ddmmyyyy(self._rule(), sections, section_map)
        assert finding is not None
        assert "2024-06-15" in finding.message
        assert finding.severity == "WARNING"

    def test_wrong_format_dd_dash_mm_yyyy(self):
        sections = {"KEY PROJECT INFORMATION": "Date: 15-06-2024"}
        section_map = {"KEY PROJECT INFORMATION": "KEY PROJECT INFORMATION"}
        finding = _check_date_format_ddmmyyyy(self._rule(), sections, section_map)
        assert finding is not None
        assert "15-06-2024" in finding.message

    def test_mixed_formats_reports_bad_only(self):
        sections = {"KEY PROJECT INFORMATION": "From 01/01/2024 to 2024-12-31"}
        section_map = {"KEY PROJECT INFORMATION": "KEY PROJECT INFORMATION"}
        finding = _check_date_format_ddmmyyyy(self._rule(), sections, section_map)
        assert finding is not None
        assert "2024-12-31" in finding.message
        assert "01/01/2024" not in finding.message

    def test_no_dates_no_finding(self):
        sections = {"KEY PROJECT INFORMATION": "No date information here."}
        section_map = {"KEY PROJECT INFORMATION": "KEY PROJECT INFORMATION"}
        assert _check_date_format_ddmmyyyy(self._rule(), sections, section_map) is None

    def test_section_missing_no_finding(self):
        sections = {}
        section_map = {"KEY PROJECT INFORMATION": None}
        assert _check_date_format_ddmmyyyy(self._rule(), sections, section_map) is None


# ---------------------------------------------------------------------------
# _check_not_applicable_required_when_blank
# ---------------------------------------------------------------------------

class TestNotApplicableRequiredWhenBlank:
    def _rule(self, section="Data Quality", min_chars=40):
        return {
            "id": "NA001", "type": "not_applicable_required_when_blank",
            "section": section, "severity": "WARNING", "min_chars": min_chars,
        }

    def test_long_text_no_finding(self):
        text = "This section provides comprehensive data quality procedures and controls for the monitoring."
        sections = {"Data Quality": text}
        section_map = {"Data Quality": "Data Quality"}
        assert _check_not_applicable_required_when_blank(self._rule(), sections, section_map) is None

    def test_short_text_with_na(self):
        sections = {"Data Quality": "N/A"}
        section_map = {"Data Quality": "Data Quality"}
        assert _check_not_applicable_required_when_blank(self._rule(), sections, section_map) is None

    def test_short_text_with_not_applicable(self):
        sections = {"Data Quality": "Not Applicable"}
        section_map = {"Data Quality": "Data Quality"}
        assert _check_not_applicable_required_when_blank(self._rule(), sections, section_map) is None

    def test_short_text_no_na_raises_finding(self):
        sections = {"Data Quality": "TBD"}
        section_map = {"Data Quality": "Data Quality"}
        finding = _check_not_applicable_required_when_blank(self._rule(), sections, section_map)
        assert finding is not None
        assert "fewer than 40 characters" in finding.message
        assert finding.severity == "WARNING"

    def test_empty_text_no_na_raises_finding(self):
        sections = {"Data Quality": ""}
        section_map = {"Data Quality": "Data Quality"}
        finding = _check_not_applicable_required_when_blank(self._rule(), sections, section_map)
        assert finding is not None

    def test_section_missing_no_finding(self):
        sections = {}
        section_map = {"Data Quality": None}
        assert _check_not_applicable_required_when_blank(self._rule(), sections, section_map) is None


# ---------------------------------------------------------------------------
# compliance_score
# ---------------------------------------------------------------------------

class TestComplianceScore:
    def test_no_findings(self):
        assert compute_compliance_score([]) == 100

    def test_one_error(self):
        assert compute_compliance_score([Finding(rule_id="X", severity="ERROR", message="m")]) == 90

    def test_one_warning(self):
        assert compute_compliance_score([Finding(rule_id="X", severity="WARNING", message="m")]) == 97

    def test_mixed(self):
        findings = [
            Finding(rule_id="A", severity="ERROR", message="m"),
            Finding(rule_id="B", severity="ERROR", message="m"),
            Finding(rule_id="C", severity="WARNING", message="m"),
        ]
        assert compute_compliance_score(findings) == 77

    def test_floor_at_zero(self):
        findings = [Finding(rule_id=f"E{i}", severity="ERROR", message="m") for i in range(15)]
        assert compute_compliance_score(findings) == 0

    def test_info_no_penalty(self):
        assert compute_compliance_score([Finding(rule_id="I", severity="INFO", message="m")]) == 100


# ---------------------------------------------------------------------------
# End-to-end with real docx
# ---------------------------------------------------------------------------

class TestEndToEnd:
    @staticmethod
    def _make_docx(sections: dict[str, str]) -> str:
        doc = Document()
        for heading, body in sections.items():
            doc.add_heading(heading, level=1)
            doc.add_paragraph(body)
        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        doc.save(tmp.name)
        return tmp.name

    def test_full_pipeline_with_fields_and_dates(self):
        path = self._make_docx({
            "KEY PROJECT INFORMATION": (
                "GS ID: GS-1234 Title of the project: Solar Cookstoves Kenya "
                "Version number: v2.0 Completion date: 15/06/2024 "
                "Monitoring period number: MP #3 "
                "Duration of this monitoring period: from 01/01/2024 to 31/12/2024 "
                "Host Country: Kenya "
                "Methodology applied: AMS-II.G version 09"
            ),
            "Project Description": "Solar cookstove distribution in rural Kenya. Crediting period 2020-2030.",
            "Monitoring Period": "From 01/01/2024 to 31/12/2024.",
            "Baseline Emissions": "15,000 tCO2e from firewood usage.",
            "Project Emissions": "500 tCO2e from transport.",
            "Emission Reductions": "14,500 tCO2e net reductions.",
            "Data Quality": "Comprehensive QA/QC procedures were applied throughout the monitoring period.",
            "Safeguards": "Environmental and social safeguards assessment completed for the project area.",
        })

        result = run_analysis(path)
        assert result.compliant is True
        assert result.compliance_score == 100
        assert len(result.findings) == 0

    def test_missing_fields_and_bad_dates(self):
        path = self._make_docx({
            "KEY PROJECT INFORMATION": (
                "Some basic info. Completion date: 2024-06-15."
            ),
            "Project Description": "A project.",
            "Monitoring Period": "Period covered: 2024-01-01 to 2024-12-31.",
            "Baseline Emissions": "TBD.",
            "Project Emissions": "TBD.",
            "Emission Reductions": "TBD.",
            "Data Quality": "TBD",
            "Safeguards": "N/A",
        })

        result = run_analysis(path)
        assert result.compliant is False
        assert result.compliance_score < 100

        messages = [f.message for f in result.findings]
        assert any("gs_id" in m for m in messages)
        assert any("title_of_project" in m for m in messages)
        assert any("Date format violation" in m for m in messages)
        assert any("fewer than 40 characters" in m for m in messages)
