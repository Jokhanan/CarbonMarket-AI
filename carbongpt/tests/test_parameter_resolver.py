"""
Tests for carbongpt.repository.parameter_resolver (docs/SPEC-03.md thin slice).

All tests need a reachable database with RECH (407) and its
regulatory_value_preferences already ingested; they skip automatically
otherwise. Each test works against a throwaway user_projects row (Ghana),
created and torn down per test, so they never touch the real portfolio.
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


def _preferences_ready() -> bool:
    if not _db_available():
        return False
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute("SELECT count(*) AS c FROM regulatory_value_preferences")
        return cur.fetchone()["c"] > 0


requires_engine = pytest.mark.skipif(
    not _preferences_ready(), reason="DATABASE_URL not set, DB unreachable, or regulatory_value_preferences empty"
)


@requires_engine
class TestParameterResolver:
    VERSION_ID = None

    @pytest.fixture(autouse=True)
    def project(self):
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO user_projects (name, standard, methodology, country, country_iso)
                   VALUES ('TEST-resolver-ghana', 'GoldStandard', 'TPDDTEC', 'Ghana', 'GHA')
                   RETURNING id"""
            )
            self.project_id = cur.fetchone()["id"]
            cur.execute(
                "SELECT id FROM methodology_version_history WHERE methodology_code='407' AND version='5.0'"
            )
            self.version_id = cur.fetchone()["id"]
        yield
        with get_cursor() as cur:
            cur.execute("DELETE FROM project_parameter_alternatives WHERE project_parameter_id IN "
                        "(SELECT id FROM project_parameters WHERE project_id = %s)", (self.project_id,))
            cur.execute("DELETE FROM project_parameters WHERE project_id = %s", (self.project_id,))
            cur.execute("DELETE FROM project_open_questions WHERE project_id = %s", (self.project_id,))
            cur.execute("DELETE FROM user_projects WHERE id = %s", (self.project_id,))

    def test_blocked_on_question_before_any_answer(self):
        from carbongpt.repository.parameter_resolver import resolve_parameter
        result = resolve_parameter(self.project_id, "EF_CO2", self.version_id)
        assert result["status"] == "blocked_on_question"
        assert result["question_key"] == "kiln_type_wccf_ratio"

    def test_resolved_with_two_alternatives_after_answer(self):
        from carbongpt.repository.parameter_resolver import answer_question, resolve_parameter
        answer_question(self.project_id, "kiln_type_wccf_ratio", "wccf_6_1", answered_by="test")
        result = resolve_parameter(self.project_id, "EF_CO2", self.version_id)
        assert result["status"] == "resolved"
        assert result["value"] == "355.36"
        assert len(result["alternatives"]) == 2
        assert all(a["rejection_reason"] for a in result["alternatives"])

    def test_defendability_argument_contains_section_reference(self):
        from carbongpt.repository.parameter_resolver import answer_question, resolve_parameter
        answer_question(self.project_id, "kiln_type_wccf_ratio", "wccf_6_1", answered_by="test")
        result = resolve_parameter(self.project_id, "EF_nonCO2", self.version_id)
        assert "§2 Definitions" in result["defendability_argument"]
        assert "page 7" in result["defendability_argument"]

    def test_different_answer_yields_different_value(self):
        from carbongpt.repository.parameter_resolver import answer_question, resolve_parameter
        answer_question(self.project_id, "kiln_type_wccf_ratio", "combustion_only", answered_by="test")
        result = resolve_parameter(self.project_id, "EF_CO2", self.version_id)
        assert result["value"] == "112"

    def test_override_preserves_original_proposed_value(self):
        from carbongpt.repository.parameter_resolver import (
            answer_question, override_parameter, resolve_parameter,
        )
        answer_question(self.project_id, "kiln_type_wccf_ratio", "wccf_6_1", answered_by="test")
        resolve_parameter(self.project_id, "EF_CO2", self.version_id)
        result = override_parameter(self.project_id, "EF_CO2", "340.0", reason="Field measurement", user="test")
        assert result["previous_value"] == "355.36"
        assert result["original_proposed_value"] == "355.36"
        assert result["new_value"] == "340.0"

    def test_override_requires_non_empty_reason(self):
        from carbongpt.repository.parameter_resolver import (
            ResolutionError, answer_question, override_parameter, resolve_parameter,
        )
        answer_question(self.project_id, "kiln_type_wccf_ratio", "wccf_6_1", answered_by="test")
        resolve_parameter(self.project_id, "EF_CO2", self.version_id)
        with pytest.raises(ResolutionError):
            override_parameter(self.project_id, "EF_CO2", "340.0", reason="", user="test")

    def test_resolve_never_overwrites_user_override(self):
        from carbongpt.repository.parameter_resolver import (
            answer_question, override_parameter, resolve_parameter,
        )
        answer_question(self.project_id, "kiln_type_wccf_ratio", "wccf_6_1", answered_by="test")
        resolve_parameter(self.project_id, "EF_CO2", self.version_id)
        override_parameter(self.project_id, "EF_CO2", "340.0", reason="Field measurement", user="test")
        result = resolve_parameter(self.project_id, "EF_CO2", self.version_id)
        assert result["status"] == "kept_user_override"

        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute(
                "SELECT value, source_type FROM project_parameters WHERE project_id=%s AND param_key='EF_CO2'",
                (self.project_id,),
            )
            row = cur.fetchone()
        assert row["value"] == "340.0"
        assert row["source_type"] == "user_override"

    def test_unsupported_param_key_raises(self):
        from carbongpt.repository.parameter_resolver import ResolutionError, resolve_parameter
        with pytest.raises(ResolutionError):
            resolve_parameter(self.project_id, "fNRB_default", self.version_id)

    def test_missing_region_classification_raises(self):
        from carbongpt.repository.db import get_cursor
        from carbongpt.repository.parameter_resolver import ResolutionError, resolve_parameter
        with get_cursor() as cur:
            cur.execute("UPDATE user_projects SET country_iso='FRA' WHERE id=%s", (self.project_id,))
        with pytest.raises(ResolutionError):
            resolve_parameter(self.project_id, "EF_CO2", self.version_id)
