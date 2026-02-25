"""
Tests for the required_field rule type and compliance_score computation.

Covers:
- required_field found (pattern matches in section text)
- required_field missing (no pattern matches)
- field rule in missing section (single finding about section, no duplicate noise)
- compliance_score calculation
"""

import pytest

from carbongpt.core.models import Finding
from carbongpt.tools.rule_engine import (
    compute_compliance_score,
    _check_required_field,
)
from carbongpt.tools.section_mapper import map_sections
from carbongpt.tools.regex_utils import any_pattern_matches


# ---------------------------------------------------------------------------
# regex_utils
# ---------------------------------------------------------------------------

class TestAnyPatternMatches:
    def test_date_yyyy_mm_dd(self):
        assert any_pattern_matches("Started on 2024-01-15", [r"\d{4}-\d{2}-\d{2}"])

    def test_date_dd_mm_yyyy(self):
        assert any_pattern_matches("Date: 15/01/2024", [r"\d{2}/\d{2}/\d{4}"])

    def test_keyword_match(self):
        assert any_pattern_matches("The project start date is listed.", [r"(?i)start\s+date"])

    def test_no_match(self):
        assert not any_pattern_matches("Nothing relevant here.", [r"\d{4}-\d{2}-\d{2}", r"(?i)start\s+date"])

    def test_empty_patterns(self):
        assert not any_pattern_matches("Some text", [])

    def test_empty_text(self):
        assert not any_pattern_matches("", [r"\d{4}-\d{2}-\d{2}"])


# ---------------------------------------------------------------------------
# _check_required_field — field found
# ---------------------------------------------------------------------------

class TestRequiredFieldFound:
    def test_date_present_in_section(self):
        rule = {
            "id": "F001",
            "type": "required_field",
            "section": "Monitoring Period",
            "field_name": "monitoring_period_start",
            "severity": "ERROR",
            "patterns": [r"\d{4}-\d{2}-\d{2}", r"(?i)start\s+date"],
        }
        sections = {
            "Monitoring Period": "The monitoring began on 2024-01-01 and ended on 2024-12-31."
        }
        section_map = {"Monitoring Period": "Monitoring Period"}

        finding = _check_required_field(rule, sections, section_map)
        assert finding is None

    def test_keyword_present_in_section(self):
        rule = {
            "id": "F004",
            "type": "required_field",
            "section": "Project Description",
            "field_name": "crediting_period",
            "severity": "ERROR",
            "patterns": [r"(?i)crediting\s+period"],
        }
        sections = {
            "Project Description": "The crediting period spans 10 years."
        }
        section_map = {"Project Description": "Project Description"}

        finding = _check_required_field(rule, sections, section_map)
        assert finding is None

    def test_fuzzy_matched_heading_still_resolves_text(self):
        sections = {
            "B.1 Monitoring Period": "Data from 2024-06-01 to 2024-12-31."
        }
        section_map = map_sections(
            ["Monitoring Period"], list(sections.keys()), threshold=70
        )
        rule = {
            "id": "F002",
            "type": "required_field",
            "section": "Monitoring Period",
            "field_name": "monitoring_period_start",
            "severity": "ERROR",
            "patterns": [r"\d{4}-\d{2}-\d{2}"],
        }

        finding = _check_required_field(rule, sections, section_map)
        assert finding is None


# ---------------------------------------------------------------------------
# _check_required_field — field missing
# ---------------------------------------------------------------------------

class TestRequiredFieldMissing:
    def test_no_pattern_matches(self):
        rule = {
            "id": "F001",
            "type": "required_field",
            "section": "Monitoring Period",
            "field_name": "monitoring_period_start",
            "severity": "ERROR",
            "patterns": [r"\d{4}-\d{2}-\d{2}", r"(?i)start\s+date"],
        }
        sections = {
            "Monitoring Period": "Monitoring was conducted throughout the year."
        }
        section_map = {"Monitoring Period": "Monitoring Period"}

        finding = _check_required_field(rule, sections, section_map)
        assert finding is not None
        assert finding.rule_id == "F001"
        assert finding.severity == "ERROR"
        assert "monitoring_period_start" in finding.message
        assert "Monitoring Period" in finding.message

    def test_country_field_missing(self):
        rule = {
            "id": "F005",
            "type": "required_field",
            "section": "Project Description",
            "field_name": "location_country",
            "severity": "ERROR",
            "patterns": [r"(?i)(?:located|country)", r"(?i)\bKenya\b"],
        }
        sections = {
            "Project Description": "This project reduces emissions."
        }
        section_map = {"Project Description": "Project Description"}

        finding = _check_required_field(rule, sections, section_map)
        assert finding is not None
        assert "location_country" in finding.message


# ---------------------------------------------------------------------------
# _check_required_field — section missing (no duplicate noise)
# ---------------------------------------------------------------------------

class TestRequiredFieldSectionMissing:
    def test_section_not_found_produces_single_finding(self):
        rule = {
            "id": "F001",
            "type": "required_field",
            "section": "Monitoring Period",
            "field_name": "monitoring_period_start",
            "severity": "ERROR",
            "patterns": [r"\d{4}-\d{2}-\d{2}"],
        }
        sections = {"Project Description": "Some text."}
        section_map = {"Monitoring Period": None}

        finding = _check_required_field(rule, sections, section_map)
        assert finding is not None
        assert "section" in finding.message.lower()
        assert "not found" in finding.message.lower()
        assert finding.rule_id == "F001"

    def test_empty_sections_still_reports_section_missing(self):
        rule = {
            "id": "F003",
            "type": "required_field",
            "section": "Data Quality",
            "field_name": "qa_procedure",
            "severity": "WARNING",
            "patterns": [r"(?i)quality\s+assurance"],
        }
        sections = {}
        section_map = {"Data Quality": None}

        finding = _check_required_field(rule, sections, section_map)
        assert finding is not None
        assert finding.severity == "WARNING"
        assert "not found" in finding.message.lower()


# ---------------------------------------------------------------------------
# compliance_score
# ---------------------------------------------------------------------------

class TestComplianceScore:
    def test_no_findings(self):
        assert compute_compliance_score([]) == 100

    def test_one_error(self):
        findings = [Finding(rule_id="X", severity="ERROR", message="m")]
        assert compute_compliance_score(findings) == 90

    def test_one_warning(self):
        findings = [Finding(rule_id="X", severity="WARNING", message="m")]
        assert compute_compliance_score(findings) == 97

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

    def test_info_has_no_penalty(self):
        findings = [Finding(rule_id="I", severity="INFO", message="m")]
        assert compute_compliance_score(findings) == 100
