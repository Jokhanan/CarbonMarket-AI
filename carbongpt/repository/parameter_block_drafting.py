"""
parameter_block_drafting.py — Rédaction sourcée d'un bloc de paramètre de
template (docs/SPEC-06.md T5, même discipline anti-hallucination que
docs/SPEC-04.md).

Trouvé en testant `generate_section_draft()` de bout en bout sur un vrai
bloc de paramètres (03.08.2026, `docs/STATUS.md`) : sans données sourcées
à citer, le modèle invente des références de méthodologie
(« TPDDTEC Version 4.0 », « TOOL33 Version 03.0 ») — le même mécanisme
qui a produit le charbon à 165.22 tCO2/TJ sans source (`docs/DECISIONS.md`,
avant SPEC-01). Ce module applique la même discipline que
`defendability.py` (SPEC-04) : le modèle ne voit qu'un jeu de faits
fermé — UN paramètre déjà extrait de la méthodologie
(`methodology_parameters`, SPEC-06 T3), avec sa référence de section et
page — et `validate_parameter_block_content()` rejette mécaniquement
toute référence de méthodologie, d'outil, de norme, de section ou de
nombre absente de ce jeu de faits. Pas seulement découragé par la
consigne système : bloqué par un contrôle après génération, comme SPEC-04.
"""

import json
import logging
import re
from typing import Any

from carbongpt.repository.defendability import _NUMBER_RE, _SECTION_RE

logger = logging.getLogger(__name__)

# Jetons ressemblant à un nom de méthodologie/outil/norme externe — 3+
# lettres majuscules consécutives (TPDDTEC, TOOL, CDM, ISO, WBT, KPT...).
# Légitime seulement si le même jeton apparaît déjà dans le jeu de faits
# (parce qu'il est réellement sourcé dans measurement_method/
# source_of_data extraits de RECH v5.0) — jamais supposé. Les nombres
# adjacents (ex. "33" dans "TOOL33", "4.0" dans "Version 4.0") sont déjà
# couverts par le contrôle numérique hérité de SPEC-04 — les deux
# contrôles ensemble couvrent le cas réel rencontré sans qu'un détecteur
# d'équations dédié soit nécessaire (une équation inventée fabrique
# presque toujours des constantes numériques absentes du jeu de faits).
_ALLCAPS_TOKEN_RE = re.compile(r"\b[A-Z]{3,}\b")

_LANGUAGE_INSTRUCTIONS = {
    "en": "Write the block in English.",
    "fr": "Redige le bloc en francais.",
}


class ParameterBlockValidationError(Exception):
    """Raised by validate_parameter_block_content() when the generated
    text references a number, section, or ALLCAPS methodology/tool/
    standard token absent from the fact set."""


def build_parameter_fact_set(parameter: dict[str, Any], *, methodology_code: str,
                              methodology_version: str, document_name: str,
                              document_language: str | None = None) -> dict[str, Any]:
    """Assembles the closed fact set for ONE parameter instance.
    `parameter` is a methodology_parameters row (SPEC-06 T3) — nothing
    else is available to the model: no other parameter, no raw PDF, no
    web search, no general knowledge about the methodology beyond what
    this one row says."""
    return {
        "methodology": {
            "code": methodology_code, "version": methodology_version, "document_name": document_name,
        },
        "parameter_id": parameter["parameter_id"],
        "key": parameter.get("key"),
        "description": parameter.get("description"),
        "unit": parameter.get("unit"),
        "purpose": parameter.get("purpose"),
        "timing_classification": parameter["timing_classification"],
        "measurement_frequency_note": parameter.get("measurement_frequency_note"),
        "measurement_method": parameter.get("measurement_method"),
        "source_of_data": parameter.get("source_of_data"),
        "responsible_entity": parameter.get("responsible_entity"),
        "qa_qc_procedures": parameter.get("qa_qc_procedures"),
        "section_ref": parameter["section_ref"],
        "page_ref": parameter["page_ref"],
        "document_language": document_language or "en",
    }


def _system_prompt(document_language: str) -> str:
    language_instruction = _LANGUAGE_INSTRUCTIONS.get(
        document_language, f"Write the block in the language identified by ISO code '{document_language}'."
    )
    return (
        "You fill in ONE data/parameter block of a Gold Standard VPA Design Document "
        "template, for a single methodology parameter. You will be given a JSON fact "
        "set: exactly one parameter already extracted from the methodology's own text, "
        "with its section and page reference.\n\n"
        "STRICT RULES:\n"
        "1. You must use NO number, unit, section reference, methodology name, tool "
        "name, standard name, or equation that does not appear verbatim in the fact "
        "set provided. Do not compute, round, or introduce anything new — including "
        "well-known tools, standards, or methodology versions you may recognise from "
        "general knowledge. If the fact set does not name a tool or standard, do not "
        "name one yourself, even if you believe you know which one is typically used.\n"
        "2. Fill in these fields, using only the fact set: Data/parameter, "
        "Description, Unit, Source of data, Measurement methods and procedures, "
        "Purpose of data. Include the measurement frequency, responsible entity, and "
        "QA/QC procedure if the fact set provides them.\n"
        "3. The actual VALUE applied for this project is NOT in the fact set (it is "
        "project-specific field data, sourced separately) — write "
        "'[To be confirmed at Design Certification / during monitoring]' for that "
        "field, never invent a number.\n"
        "4. If a field cannot be filled from the fact set, write 'Not specified in "
        "the methodology' rather than improvising.\n"
        f"5. {language_instruction}\n"
        "Respond with the filled block only, as plain 'Field: Value' lines — no "
        "preamble, no markdown table syntax."
    )


def generate_parameter_block_content(fact_set: dict[str, Any], *, model_override: str | None = None) -> tuple[str, str]:
    """Returns (block_text, model_used). Raises whatever call_openai() or
    validate_parameter_block_content() raise — callers decide what to do
    with a validation failure (no automatic template fallback exists for
    this content, unlike SPEC-04's defendability arguments: an unfillable
    parameter block should be surfaced for review, not silently
    replaced by guessed text)."""
    from carbongpt.core.openai_client import call_openai, _resolve_model

    document_language = fact_set.get("document_language") or "en"
    user_prompt = "Fact set:\n" + json.dumps(fact_set, indent=2, ensure_ascii=False)
    text = call_openai(_system_prompt(document_language), user_prompt, temperature=0.2, max_tokens=1600,
                        model_override=model_override).strip()
    validate_parameter_block_content(text, fact_set)
    return text, _resolve_model(model_override)


def validate_parameter_block_content(text: str, fact_set: dict[str, Any]) -> None:
    """Raises ParameterBlockValidationError if `text` contains a number,
    section reference, or ALLCAPS methodology/tool/standard token not
    present anywhere in `fact_set`. Same mechanism as
    defendability.validate_generated_argument() (SPEC-04) — the number/
    section regexes are imported and reused directly, not reimplemented."""
    fact_text = json.dumps(fact_set, ensure_ascii=False)
    allowed_numbers = set(_NUMBER_RE.findall(fact_text))
    allowed_sections = {s.lower().replace(" ", "") for s in _SECTION_RE.findall(fact_text)}
    allowed_tokens = set(_ALLCAPS_TOKEN_RE.findall(fact_text))

    # page_ref is a bare number under its own JSON key, never the literal
    # phrase "page N" — same fix as defendability.py (SPEC-04).
    page_ref = fact_set.get("page_ref")
    if page_ref:
        allowed_sections.add(f"page{str(page_ref).strip()}")

    found_numbers = set(_NUMBER_RE.findall(text))
    found_sections = {s.lower().replace(" ", "") for s in _SECTION_RE.findall(text)}
    found_tokens = set(_ALLCAPS_TOKEN_RE.findall(text))

    unknown_numbers = found_numbers - allowed_numbers
    unknown_sections = found_sections - allowed_sections
    unknown_tokens = found_tokens - allowed_tokens

    if unknown_numbers or unknown_sections or unknown_tokens:
        raise ParameterBlockValidationError(
            "Generated block references values absent from the fact set — "
            f"unknown numbers: {sorted(unknown_numbers)}, "
            f"unknown sections: {sorted(unknown_sections)}, "
            f"unknown methodology/tool/standard tokens: {sorted(unknown_tokens)}"
        )
