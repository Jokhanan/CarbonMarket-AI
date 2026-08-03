"""
Tests for carbongpt.repository.non_deducible_facts (docs/SPEC-06.md, T6).
"""
import os

import pytest

from carbongpt.repository.non_deducible_facts import (
    NON_DEDUCIBLE_FACT_CATEGORIES,
    list_non_deducible_facts,
)


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


class TestListNonDeducibleFacts:
    def test_returns_five_categories(self):
        assert len(list_non_deducible_facts()) == 5

    def test_every_category_has_a_reason_and_affected_sections(self):
        for cat in NON_DEDUCIBLE_FACT_CATEGORIES:
            assert cat["why_not_deducible"]
            assert cat["affected_sections"]

    def test_contact_information_matches_the_t4_structural_gap(self):
        # H300 ("Contact information of CME") is one of the two sections
        # find_unlinked_sections() (T4) reports as having zero governing
        # source at all — this category documents WHY, consistently.
        contact = next(c for c in NON_DEDUCIBLE_FACT_CATEGORIES if c["key"] == "contact_information_cme")
        assert "H300" in contact["affected_sections"]
        assert contact["governing_source"] is None


@requires_db
class TestEnsureOpenQuestionsForProject:
    @pytest.fixture(autouse=True)
    def _project(self):
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO user_projects (name, standard, methodology, country, country_iso)
                   VALUES ('TEST-non-deducible-facts', 'GoldStandard', 'TPDDTEC', 'Ghana', 'GHA')
                   RETURNING id"""
            )
            self.project_id = cur.fetchone()["id"]
        yield
        with get_cursor() as cur:
            cur.execute("DELETE FROM project_open_questions WHERE project_id = %s", (self.project_id,))
            cur.execute("DELETE FROM user_projects WHERE id = %s", (self.project_id,))

    def test_creates_one_open_question_per_category(self):
        from carbongpt.repository.non_deducible_facts import ensure_open_questions_for_project

        results = ensure_open_questions_for_project(self.project_id)
        assert len(results) == 5
        assert all(r["status"] == "open" for r in results)

    def test_idempotent_does_not_duplicate_or_reopen_answered(self):
        from carbongpt.repository.db import get_cursor
        from carbongpt.repository.non_deducible_facts import ensure_open_questions_for_project

        ensure_open_questions_for_project(self.project_id)

        with get_cursor() as cur:
            cur.execute(
                "UPDATE project_open_questions SET status='answered', answer_value='responsive' "
                "WHERE project_id=%s AND question_key='gender_track_choice'",
                (self.project_id,),
            )

        results = ensure_open_questions_for_project(self.project_id)
        gender = next(r for r in results if r["key"] == "gender_track_choice")
        assert gender["status"] == "answered"
        assert gender["answer_value"] == "responsive"

        with get_cursor() as cur:
            cur.execute(
                "SELECT count(*) c FROM project_open_questions WHERE project_id=%s",
                (self.project_id,),
            )
            assert cur.fetchone()["c"] == 5
