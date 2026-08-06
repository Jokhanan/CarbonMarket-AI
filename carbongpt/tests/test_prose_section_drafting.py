"""
Tests for carbongpt.repository.prose_section_drafting (v1.0: sourced
narrative sections, same anti-hallucination discipline as SPEC-04's
defendability.py and SPEC-06's parameter_block_drafting.py).

Validator tests need no database. build_prose_section_fact_set() needs a
reachable database with VPA-DD v3.0 analyzed, RECH v5.0 parameters
extracted, and SPEC-06 T4 links written — it works against a throwaway
user_projects row, created and torn down per test, never the real
portfolio (project id=12).
"""
import os

import pytest

from carbongpt.repository.prose_section_drafting import (
    ProseSectionValidationError,
    _collect_explicit_citation_forms,
    generate_prose_section_content,
    validate_prose_section_content,
)


def _fact_set(**overrides):
    base = {
        "section": {"field_key": "H96", "title": "Application of methodology (ies)", "parent_section": None},
        "governing_sources": [
            {"type": "methodology", "code": "407", "version": "5.0",
             "document_name": "Reduced emissions from cooking and heating (RECH) (formerly TPDDTEC)",
             "note": "Reference RECH v5.0 itself."},
        ],
        "rech_parameters": [
            {"parameter_id": "ICS 17", "key": "WCCF", "description": "Wood-to-Charcoal Conversion Factor",
             "unit": "Ratio (kg wood per kg charcoal)", "timing_classification": "ex_ante",
             "section_ref": "14.2", "page_ref": "63"},
        ],
        "project": {"name": "Gh", "country": "Ghana", "methodology": "TPDDTEC"},
        "project_parameters": [
            {"param_key": "EF_CO2", "value": "355.36", "unit": "tCO2/TJ", "param_status": "default"},
        ],
        "open_questions": [],
        "document_language": "en",
    }
    base.update(overrides)
    return base


class TestCollectExplicitCitationForms:
    def test_registers_section_ref_with_section_symbol(self):
        forms = _collect_explicit_citation_forms(_fact_set())
        assert "§14.2" in forms

    def test_registers_page_ref_as_page_n_phrase(self):
        forms = _collect_explicit_citation_forms(_fact_set())
        assert "page63" in forms

    def test_ignores_empty_values(self):
        fact_set = _fact_set(rech_parameters=[{"parameter_id": "ICS 1", "section_ref": None, "page_ref": ""}])
        forms = _collect_explicit_citation_forms(fact_set)
        assert forms == set()


class TestValidateProseSectionContent:
    def test_accepts_text_using_only_fact_set_values(self):
        fact_set = _fact_set()
        text = (
            "This section describes the application of RECH v5.0 (formerly TPDDTEC) "
            "to this project in Ghana. Per §14.2, ICS 17 (WCCF) is a Wood-to-Charcoal "
            "Conversion Factor expressed as a Ratio (kg wood per kg charcoal), see "
            "page 63. The emission factor of 355.36 tCO2/TJ is a provisional, "
            "not-yet-confirmed project value."
        )
        validate_prose_section_content(text, fact_set)  # must not raise

    def test_rejects_number_absent_from_fact_set(self):
        fact_set = _fact_set()
        text = "The applicable emission factor for this project is 6.2 tCO2/TJ."
        with pytest.raises(ProseSectionValidationError):
            validate_prose_section_content(text, fact_set)

    def test_rejects_section_reference_absent_from_fact_set(self):
        fact_set = _fact_set()
        text = "As required under §9.9 of the methodology."
        with pytest.raises(ProseSectionValidationError):
            validate_prose_section_content(text, fact_set)

    def test_rejects_invented_methodology_or_tool_reference(self):
        fact_set = _fact_set()
        text = "This project applies CDM Standardized Baseline Tool TOOL33 for this calculation."
        with pytest.raises(ProseSectionValidationError, match="tokens"):
            validate_prose_section_content(text, fact_set)

    def test_accepts_governing_crosscutting_document_reference(self):
        fact_set = _fact_set(governing_sources=[
            {"type": "crosscutting", "code": "104", "name": "Gender Equality Requirements & Guidelines",
             "version": "2.0", "document_name": "CURRENT DOCUMENT- Gender Equality Requirements & Guidelines",
             "released_date": "2023-05-16", "note": "Gender track."},
        ])
        text = "This assessment follows document 104, Gender Equality Requirements & Guidelines, version 2.0."
        validate_prose_section_content(text, fact_set)  # must not raise

    def test_rejects_country_number_not_in_fact_set_even_if_plausible(self):
        # Guards against the model quietly inventing a plausible-looking
        # figure (e.g. a crediting period length) never actually provided.
        fact_set = _fact_set()
        text = "The crediting period for this VPA is 7 years."
        with pytest.raises(ProseSectionValidationError):
            validate_prose_section_content(text, fact_set)

    def test_allows_the_instructed_insert_placeholder_syntax(self):
        # Regression: found running this for real on project 12 (v1.0,
        # 04.08.2026) — the system prompt instructs the model to write
        # "[INSERT: ...]" placeholders, but the ALLCAPS check was
        # rejecting the literal word "INSERT" itself, since it never
        # appears in the fact set — a self-inflicted bug, not a caught
        # hallucination.
        fact_set = _fact_set()
        text = "The project's contact details are [INSERT: proponent contact information]."
        validate_prose_section_content(text, fact_set)  # must not raise

    def test_allows_generic_structural_vocabulary_not_in_fact_set(self):
        # VPA/VVB/GHG/SDG/etc name a document type, role, or concept
        # inherent to any VPA-DD — not a citable external fact that could
        # be wrong, unlike a specific tool/standard name.
        fact_set = _fact_set()
        text = "This VPA will be assessed by a VVB against GHG and SDG requirements."
        validate_prose_section_content(text, fact_set)  # must not raise

    def test_still_rejects_a_specific_uncited_external_standard(self):
        # The structural-vocabulary allowlist must stay narrow — a specific
        # citable standard like ISO 3166 is still blocked unless sourced.
        fact_set = _fact_set()
        text = "Country codes follow ISO 3166."
        with pytest.raises(ProseSectionValidationError):
            validate_prose_section_content(text, fact_set)

    def test_open_question_answer_number_is_allowed(self):
        fact_set = _fact_set(open_questions=[
            {"fact": "Scale of the VPA", "why_not_deducible": "Project-specific.",
             "status": "answered", "answer": "Micro-scale, 500 devices"},
        ])
        text = "Per the project developer's confirmation, this is a Micro-scale VPA covering 500 devices."
        validate_prose_section_content(text, fact_set)  # must not raise


class TestGenerateProseSectionContent:
    def test_delegates_to_call_openai_and_returns_model_used(self, monkeypatch):
        fact_set = _fact_set()
        captured = {}

        def fake_call_openai(system_prompt, user_prompt, **kwargs):
            captured["user_prompt"] = user_prompt
            return "This section applies RECH v5.0 per §14.2, referencing ICS 17 (WCCF)."

        monkeypatch.setattr("carbongpt.core.openai_client.call_openai", fake_call_openai)
        monkeypatch.setattr("carbongpt.core.openai_client._resolve_model", lambda override: "claude-sonnet-5")

        text, model = generate_prose_section_content(fact_set)

        assert "ICS 17" in text
        assert model == "claude-sonnet-5"
        assert "H96" in captured["user_prompt"]

    def test_propagates_validation_error_when_model_hallucinates(self, monkeypatch):
        fact_set = _fact_set()

        def fake_call_openai(system_prompt, user_prompt, **kwargs):
            return "Per TOOL33 v03.0, this project uses the default emission factor of 6.2 tCO2/TJ."

        monkeypatch.setattr("carbongpt.core.openai_client.call_openai", fake_call_openai)

        with pytest.raises(ProseSectionValidationError):
            generate_prose_section_content(fact_set)

    def test_propagates_missing_api_key_error(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        fact_set = _fact_set()
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            generate_prose_section_content(fact_set)


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


def _vpa_dd_v3_linked() -> bool:
    if not _db_available():
        return False
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute(
            """SELECT count(*) c FROM template_field_requirements tfr
               JOIN template_fields tf ON tf.id = tfr.template_field_id
               JOIN document_template_versions dtv ON dtv.id = tf.template_version_id
               JOIN document_templates dt ON dt.id = dtv.template_id
               WHERE dt.doc_type = 'VPA-DD' AND dtv.version = '3.0' AND dtv.is_current = true"""
        )
        return cur.fetchone()["c"] > 0


requires_bootstrap = pytest.mark.skipif(
    not _vpa_dd_v3_linked(), reason="VPA-DD v3.0 not ingested/linked (SPEC-05 T7 / SPEC-06 T3/T4 bootstrap)"
)


@requires_bootstrap
class TestBuildProseSectionFactSet:
    @pytest.fixture(autouse=True)
    def project(self):
        from carbongpt.repository.db import get_cursor
        from carbongpt.repository.non_deducible_facts import ensure_open_questions_for_project

        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO user_projects (name, standard, methodology, country, country_iso)
                   VALUES ('TEST-prose-drafting-ghana', 'GoldStandard', 'TPDDTEC', 'Ghana', 'GHA')
                   RETURNING id"""
            )
            self.project_id = cur.fetchone()["id"]
        ensure_open_questions_for_project(self.project_id)
        yield
        with get_cursor() as cur:
            cur.execute("DELETE FROM project_open_questions WHERE project_id = %s", (self.project_id,))
            cur.execute("DELETE FROM project_parameters WHERE project_id = %s", (self.project_id,))
            cur.execute("DELETE FROM user_projects WHERE id = %s", (self.project_id,))

    def _project_info(self):
        return {"id": self.project_id, "document_language": "en"}

    def test_methodology_governed_section_includes_rech_parameters(self):
        from carbongpt.repository.prose_section_drafting import build_prose_section_fact_set

        fact_set = build_prose_section_fact_set("H96", self._project_info())
        assert fact_set["section"]["field_key"] == "H96"
        assert any(s["type"] == "methodology" and s["code"] == "407" for s in fact_set["governing_sources"])
        assert len(fact_set["rech_parameters"]) == 26

    def test_crosscutting_governed_section_has_no_rech_parameters(self):
        from carbongpt.repository.prose_section_drafting import build_prose_section_fact_set

        fact_set = build_prose_section_fact_set("H285", self._project_info())
        assert all(s["type"] == "crosscutting" for s in fact_set["governing_sources"])
        assert any(s["code"] == "102" for s in fact_set["governing_sources"])
        assert fact_set["rech_parameters"] == []

    def test_non_root_field_inherits_ancestor_governing_sources(self):
        from carbongpt.repository.prose_section_drafting import build_prose_section_fact_set

        fact_set = build_prose_section_fact_set("H101", self._project_info())
        assert fact_set["section"]["parent_section"] == "Application of methodology (ies)"
        assert any(s["type"] == "methodology" and s["code"] == "407" for s in fact_set["governing_sources"])

    def test_unlinked_section_has_no_governing_sources_but_has_open_question(self):
        from carbongpt.repository.prose_section_drafting import build_prose_section_fact_set

        fact_set = build_prose_section_fact_set("H300", self._project_info())
        assert fact_set["governing_sources"] == []
        assert any(q["fact"].startswith("Coordonnées") for q in fact_set["open_questions"])
        assert fact_set["open_questions"][0]["status"] == "open"

    def test_gender_section_pulls_both_crosscutting_docs_and_open_question(self):
        from carbongpt.repository.prose_section_drafting import build_prose_section_fact_set

        fact_set = build_prose_section_fact_set("H196", self._project_info())
        codes = {s["code"] for s in fact_set["governing_sources"]}
        assert {"103", "104"} <= codes
        assert any(q["status"] == "open" for q in fact_set["open_questions"])

    def test_result_is_json_serializable(self):
        import json

        from carbongpt.repository.prose_section_drafting import build_prose_section_fact_set

        fact_set = build_prose_section_fact_set("H96", self._project_info())
        json.dumps(fact_set)  # must not raise (date/Decimal already stringified)
