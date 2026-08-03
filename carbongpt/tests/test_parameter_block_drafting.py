"""
Tests for carbongpt.repository.parameter_block_drafting (docs/SPEC-06.md
T5). No network calls — call_openai() is monkeypatched at its source
module (same pattern as test_defendability.py, SPEC-04).
"""
import pytest

from carbongpt.repository.parameter_block_drafting import (
    ParameterBlockValidationError,
    build_parameter_fact_set,
    generate_parameter_block_content,
    validate_parameter_block_content,
)

_PARAMETER = {
    "parameter_id": "ICS 17",
    "key": "WCCF",
    "description": "Wood-to-Charcoal Conversion Factor (WCCF); The factor expressing the "
                    "amount of wood required to produce a standard quantity of charcoal.",
    "unit": "Ratio (kg wood per kg charcoal)",
    "purpose": "Baseline emissions",
    "timing_classification": "ex_ante",
    "measurement_frequency_note": None,
    "measurement_method": "Determined using the applicable regional default or a project-specific "
                           "assessment following ISO 17225 sampling guidance.",
    "source_of_data": "Methodology default or project-specific field assessment.",
    "responsible_entity": None,
    "qa_qc_procedures": None,
    "section_ref": "14.2",
    "page_ref": "63",
}


def _fact_set(**overrides):
    kwargs = {
        "methodology_code": "407", "methodology_version": "5.0",
        "document_name": "Reduced Emissions from Cooking and Heating (RECH)",
    }
    kwargs.update(overrides)
    return build_parameter_fact_set(_PARAMETER, **kwargs)


class TestBuildParameterFactSet:
    def test_contains_only_the_sourced_parameter(self):
        fact_set = _fact_set()
        assert fact_set["parameter_id"] == "ICS 17"
        assert fact_set["key"] == "WCCF"
        assert fact_set["section_ref"] == "14.2"
        assert fact_set["page_ref"] == "63"
        assert fact_set["methodology"]["code"] == "407"

    def test_defaults_document_language_to_english(self):
        fact_set = _fact_set()
        assert fact_set["document_language"] == "en"

    def test_respects_explicit_document_language(self):
        fact_set = _fact_set(document_language="fr")
        assert fact_set["document_language"] == "fr"


class TestValidateParameterBlockContent:
    def test_accepts_text_using_only_fact_set_values(self):
        fact_set = _fact_set()
        text = (
            "Data/parameter: WCCF\n"
            "Description: Wood-to-Charcoal Conversion Factor (WCCF).\n"
            "Unit: Ratio (kg wood per kg charcoal)\n"
            "Source of data: Methodology default or project-specific field assessment.\n"
            "Measurement methods and procedures: Determined using the applicable regional "
            "default or a project-specific assessment following ISO 17225 sampling guidance.\n"
            "Value applied: [To be confirmed at Design Certification / during monitoring]"
        )
        validate_parameter_block_content(text, fact_set)  # must not raise

    def test_rejects_number_absent_from_fact_set(self):
        fact_set = _fact_set()
        text = "Value applied: 6.2"
        with pytest.raises(ParameterBlockValidationError):
            validate_parameter_block_content(text, fact_set)

    def test_rejects_section_reference_absent_from_fact_set(self):
        fact_set = _fact_set()
        text = "As specified in section 9.9 of the methodology."
        with pytest.raises(ParameterBlockValidationError):
            validate_parameter_block_content(text, fact_set)

    def test_rejects_invented_methodology_or_tool_reference(self):
        # The exact failure mode found testing this session (docs/STATUS.md):
        # the model inventing "TPDDTEC Version 4.0" / "TOOL33 Version 03.0".
        fact_set = _fact_set()
        text = "Deemed valid by GS TPDDTEC Methodology, per TOOL33 guidance."
        with pytest.raises(ParameterBlockValidationError, match="tokens"):
            validate_parameter_block_content(text, fact_set)

    def test_a_true_former_name_is_allowed_but_an_invented_version_is_not(self):
        # Precision check on the real DB content (03.08.2026): RECH v5.0's
        # own document_name literally is "...(RECH) (formerly TPDDTEC)" —
        # so "TPDDTEC" alone is a true, sourced fact when the real
        # document_name is used, not something to block. What actually
        # got hallucinated in the original failure was the invented
        # version numbers and an unrelated tool (CDM TOOL33) — those are
        # what must be rejected, not the accurate former name.
        fact_set = _fact_set(
            document_name="Reduced emissions from cooking and heating (RECH) (formerly TPDDTEC)"
        )
        honest_text = "This methodology, formerly known as TPDDTEC, defines this parameter."
        validate_parameter_block_content(honest_text, fact_set)  # must not raise

        fabricated_text = (
            "Deemed valid by GS TPDDTEC Methodology, Version 4.0, per CDM Standardized "
            "Baseline Tool TOOL33, Version 03.0 (EB 125, June 2025)."
        )
        with pytest.raises(ParameterBlockValidationError) as exc_info:
            validate_parameter_block_content(fabricated_text, fact_set)
        # The invented numbers and the unrelated "CDM" tool are caught —
        # "TPDDTEC" itself is correctly not flagged, it's the true former name.
        assert "CDM" in str(exc_info.value)
        assert "4.0" in str(exc_info.value)

    def test_accepts_allcaps_token_that_is_genuinely_in_the_fact_set(self):
        # "ISO" is legitimately in measurement_method here — must not be
        # flagged just because it's an ALLCAPS token.
        fact_set = _fact_set()
        text = "Measurement methods and procedures: per ISO sampling guidance."
        validate_parameter_block_content(text, fact_set)  # must not raise

    def test_page_ref_registered_as_page_n_phrase(self):
        fact_set = _fact_set()
        text = "As described on page 63 of the methodology."
        validate_parameter_block_content(text, fact_set)  # must not raise


class TestGenerateParameterBlockContent:
    def test_delegates_to_call_openai_and_returns_model_used(self, monkeypatch):
        fact_set = _fact_set()
        captured = {}

        def fake_call_openai(system_prompt, user_prompt, **kwargs):
            captured["system_prompt"] = system_prompt
            captured["user_prompt"] = user_prompt
            return "Data/parameter: WCCF\nUnit: Ratio (kg wood per kg charcoal)"

        monkeypatch.setattr("carbongpt.core.openai_client.call_openai", fake_call_openai)
        monkeypatch.setattr("carbongpt.core.openai_client._resolve_model", lambda override: "claude-sonnet-5")

        text, model = generate_parameter_block_content(fact_set)

        assert "WCCF" in text
        assert model == "claude-sonnet-5"
        assert "ICS 17" in captured["user_prompt"]

    def test_propagates_validation_error_when_model_hallucinates(self, monkeypatch):
        fact_set = _fact_set()

        def fake_call_openai(system_prompt, user_prompt, **kwargs):
            return "Per TOOL33 v03.0, the default value is 6.2."

        monkeypatch.setattr("carbongpt.core.openai_client.call_openai", fake_call_openai)

        with pytest.raises(ParameterBlockValidationError):
            generate_parameter_block_content(fact_set)

    def test_propagates_missing_api_key_error(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        fact_set = _fact_set()
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            generate_parameter_block_content(fact_set)
