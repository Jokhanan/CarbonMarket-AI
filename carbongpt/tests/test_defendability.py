"""
Tests for carbongpt.repository.defendability (docs/SPEC-04.md). No network
calls — call_openai() is monkeypatched at its source module.
"""
import pytest

from carbongpt.repository.defendability import (
    ArgumentValidationError,
    build_fact_set,
    generate_defendability_argument,
    validate_generated_argument,
)

_CHOSEN = {
    "value": "0.081", "unit": "tCO2/GJ", "section_ref": "§ 4.2", "page_ref": "12",
    "obligation": "mandatory",
    "applicability": {
        "kiln_type": "wccf_6_1",
        "region": "Sub-Saharan Africa or Least Developed Countries",
    },
    "rationale": "Ratio bois-charbon 6:1, defaut regional PMA/Afrique subsaharienne.",
}
_ALTERNATIVES = [
    {"value": "0.095", "unit": "tCO2/GJ", "section_ref": "§ 4.3",
     "rejection_reason": "La reponse du projet pointe vers wccf_6_1, pas vers wccf_4_1."},
]
_CONTEXT = {"country_iso": "GHA", "country": "Ghana", "document_language": "en"}


def _fact_set():
    return build_fact_set(
        param_key="EF_CO2", chosen=_CHOSEN, alternatives=_ALTERNATIVES,
        project_context=_CONTEXT, question_answer="wccf_6_1",
        question_text="Quel ratio bois-charbon ?",
    )


class TestBuildFactSet:
    def test_contains_only_sourced_fields(self):
        fact_set = _fact_set()
        assert fact_set["chosen"]["value"] == "0.081"
        assert fact_set["chosen"]["section_ref"] == "§ 4.2"
        assert fact_set["rejected_alternatives"][0]["reason"] == _ALTERNATIVES[0]["rejection_reason"]
        assert fact_set["project_context"] == _CONTEXT


class TestValidateGeneratedArgument:
    def test_accepts_text_using_only_fact_set_values(self):
        fact_set = _fact_set()
        text = (
            "La valeur de 0.081 tCO2/GJ retenue au § 4.2, page 12, s'applique a ce "
            "projet ghaneen car la reponse fournie correspond au ratio wccf_6_1."
        )
        validate_generated_argument(text, fact_set)  # must not raise

    def test_rejects_number_absent_from_fact_set(self):
        fact_set = _fact_set()
        text = "La valeur retenue est en realite de 0.500 tCO2/GJ, comme indique au § 4.2."
        with pytest.raises(ArgumentValidationError):
            validate_generated_argument(text, fact_set)

    def test_rejects_section_reference_absent_from_fact_set(self):
        fact_set = _fact_set()
        text = "La valeur de 0.081 s'applique conformement au § 9.9 de la methodologie."
        with pytest.raises(ArgumentValidationError):
            validate_generated_argument(text, fact_set)

    def test_rejects_country_classification_claim_not_sourced(self):
        # Reproduces the real bug: applicability.region legitimately contains
        # "Least Developed Countries" (it describes the RULE's scope, sourced
        # from the methodology) — the model must not launder that into a claim
        # that Ghana itself is an LDC. Ghana is NOT on the UN LDC list (Burkina
        # Faso is); docs/SPEC-02.md (country classification) isn't implemented,
        # so no fact set can ever license this claim today.
        fact_set = _fact_set()
        text = (
            "Since Ghana is a Least Developed Country, the value of 0.081 tCO2/GJ "
            "sourced at § 4.2 applies to this project."
        )
        with pytest.raises(ArgumentValidationError, match="classification"):
            validate_generated_argument(text, fact_set)

    def test_accepts_plain_country_name_with_no_classification_qualifier(self):
        fact_set = _fact_set()
        text = "For this project in Ghana, the value of 0.081 tCO2/GJ sourced at § 4.2 applies."
        validate_generated_argument(text, fact_set)  # must not raise


class TestGenerateDefendabilityArgument:
    def test_delegates_to_call_openai_and_returns_model_used(self, monkeypatch):
        fact_set = _fact_set()
        captured = {}

        def fake_call_openai(system_prompt, user_prompt, **kwargs):
            captured["system_prompt"] = system_prompt
            captured["user_prompt"] = user_prompt
            return "La valeur de 0.081 tCO2/GJ, sourcee au § 4.2, s'applique a ce projet."

        monkeypatch.setattr("carbongpt.core.openai_client.call_openai", fake_call_openai)
        monkeypatch.setattr("carbongpt.core.openai_client._resolve_model", lambda override: "claude-sonnet-5")

        text, model = generate_defendability_argument(fact_set)

        assert "0.081" in text
        assert model == "claude-sonnet-5"
        assert "0.081" in captured["user_prompt"]

    def test_propagates_validation_error_when_model_hallucinates(self, monkeypatch):
        fact_set = _fact_set()

        def fake_call_openai(system_prompt, user_prompt, **kwargs):
            return "La valeur retenue est de 99.99 tCO2/GJ."

        monkeypatch.setattr("carbongpt.core.openai_client.call_openai", fake_call_openai)

        with pytest.raises(ArgumentValidationError):
            generate_defendability_argument(fact_set)

    def test_propagates_missing_api_key_error(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        fact_set = _fact_set()
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            generate_defendability_argument(fact_set)

    def test_document_language_drives_system_prompt_instruction(self, monkeypatch):
        # document_language is the DELIVERABLE's language (per-project, defaults to
        # 'en' for Gold Standard/Verra) -- distinct from the chat interface language.
        captured = {}

        def fake_call_openai(system_prompt, user_prompt, **kwargs):
            captured["system_prompt"] = system_prompt
            return "0.081 tCO2/GJ, § 4.2."

        monkeypatch.setattr("carbongpt.core.openai_client.call_openai", fake_call_openai)
        monkeypatch.setattr("carbongpt.core.openai_client._resolve_model", lambda override: "claude-sonnet-5")

        fact_set = build_fact_set(
            param_key="EF_CO2", chosen=_CHOSEN, alternatives=_ALTERNATIVES,
            project_context={**_CONTEXT, "document_language": "fr"},
            question_answer="wccf_6_1", question_text="Quel ratio bois-charbon ?",
        )
        generate_defendability_argument(fact_set)
        assert "francais" in captured["system_prompt"].lower()

    def test_defaults_to_english_when_document_language_absent(self, monkeypatch):
        captured = {}

        def fake_call_openai(system_prompt, user_prompt, **kwargs):
            captured["system_prompt"] = system_prompt
            return "0.081 tCO2/GJ, § 4.2."

        monkeypatch.setattr("carbongpt.core.openai_client.call_openai", fake_call_openai)
        monkeypatch.setattr("carbongpt.core.openai_client._resolve_model", lambda override: "claude-sonnet-5")

        fact_set = build_fact_set(
            param_key="EF_CO2", chosen=_CHOSEN, alternatives=_ALTERNATIVES,
            project_context={"country_iso": "GHA", "country": "Ghana"},  # no document_language key
            question_answer="wccf_6_1", question_text="Quel ratio bois-charbon ?",
        )
        generate_defendability_argument(fact_set)
        assert "Write the argument in English" in captured["system_prompt"]
