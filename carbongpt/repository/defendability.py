"""
defendability.py — AI-generated defendability arguments (docs/SPEC-04.md).

The model sees only a closed "fact set" already sourced in the database
(regulatory_values, regulatory_value_preferences, project context, the
open-question answer that drove the choice) and writes 3-5 sentences of
prose explaining why the retained value applies to this specific project.

It can never introduce a number or section reference that isn't already in
the fact set — validate_generated_argument() checks this mechanically after
generation and rejects the text if it fails. This is the only place in the
system where a language model contributes anything beyond formatting already
-decided facts (see CLAUDE.md R1-R3) — everything upstream of it is data and
rules.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
_SECTION_RE = re.compile(r"§\s*\d+(?:\.\d+)*|\bpage\s+\d+\b", re.I)

# Tokens resembling an external methodology/tool/standard name — 3+
# consecutive uppercase letters (TPDDTEC, TOOL, CDM, ISO, WBT, KPT...).
# Legitimate only if the same token already appears in the fact set (it is
# then genuinely sourced). Shared by every closed-fact-set drafting module
# (defendability.py, parameter_block_drafting.py, prose_section_drafting.py)
# — found once here (SPEC-06, parameter_block_drafting.py) rather than
# reimplemented per module.
_ALLCAPS_TOKEN_RE = re.compile(r"\b[A-Z]{3,}\b")

# A candidate value's "applicability.region" field (sourced from the
# methodology) describes which category of country a RULE applies to, e.g.
# "Sub-Saharan Africa or Least Developed Countries" — it is NOT a sourced
# fact about this project's own country. docs/SPEC-02.md (country
# classification ingestion) isn't implemented yet, so no fact set ever
# contains a genuine classification for the project's country. Any of
# these terms in generated text is therefore an invented fact about the
# country, not a citation of the rule's scope — reject unconditionally
# unless a future SPEC-02-sourced project_context.country_classification
# field explicitly authorizes it.
_CLASSIFICATION_CLAIM_RE = re.compile(
    r"least[\s-]developed\s+countr\w*|\bLDCs?\b|"
    r"pays\s+les\s+moins\s+avanc\w*|\bPMA\b|"
    r"sub-?saharan\s+africa\w*|afrique\s+subsaharienne\w*|"
    r"industriali[sz]ed\s+countr\w*|developing\s+countr\w*",
    re.I,
)

_LANGUAGE_INSTRUCTIONS = {
    "en": "Write the argument in English.",
    "fr": "Redige l'argument en francais.",
}


class ArgumentValidationError(Exception):
    """Raised by validate_generated_argument() when the generated text
    contains a number, section reference, or country-classification claim
    absent from the fact set."""


def build_fact_set(*, param_key: str, chosen: dict, alternatives: list[dict],
                    project_context: dict, question_answer: str, question_text: str) -> dict:
    """Assembles the closed fact set passed to the model. Nothing else is
    available to it — no raw PDF, no web search, no other regulatory_values
    rows than what the resolver already selected."""
    return {
        "param_key": param_key,
        "chosen": {
            "value": chosen["value"], "unit": chosen.get("unit"),
            "section_ref": chosen["section_ref"], "page_ref": chosen.get("page_ref"),
            "obligation": chosen.get("obligation"), "applicability": chosen.get("applicability"),
        },
        "project_context": project_context,
        "question_answer": question_answer,
        "question_text": question_text,
        "rejected_alternatives": [
            {"value": a["value"], "unit": a.get("unit"), "section_ref": a.get("section_ref"),
             "reason": a.get("rejection_reason")}
            for a in alternatives
        ],
    }


def _system_prompt(document_language: str) -> str:
    language_instruction = _LANGUAGE_INSTRUCTIONS.get(
        document_language, f"Write the argument in the language identified by ISO code '{document_language}'."
    )
    return (
        "You write short defendability arguments for a carbon credit regulatory "
        "reasoning system. You will be given a JSON fact set: a chosen regulatory "
        "value, its source, the project context that led to choosing it, and the "
        "alternatives that were not chosen and why.\n\n"
        "STRICT RULES:\n"
        "1. You must use NO number, NO section reference, and NO unit that does not "
        "appear verbatim in the fact set provided. Do not compute, round, or "
        "introduce any new figure.\n"
        "2. Do not use the words or phrases 'Least Developed Country', 'LDC', "
        "'Sub-Saharan Africa', 'industrialized', or 'developing country' anywhere "
        "in your answer, under any framing — not to describe the project's "
        "country, and not even when paraphrasing or quoting a candidate value's "
        "'region' field, which describes which category of country the cited "
        "rule applies to in the methodology, not a confirmed fact about this "
        "project's own country. Refer to the country only by the name given in "
        "project_context, with no classification qualifier. If the rule's scope "
        "needs mentioning, describe it structurally (e.g. 'the regional default "
        "provision') without naming the classification.\n"
        "3. If you cannot build a solid argument without introducing information "
        "absent from the fact set, say so explicitly instead of improvising.\n"
        "4. Write 3-5 sentences, addressed to a VVB (validation/verification body), "
        "explaining why the chosen value applies to THIS project specifically — use "
        "the project context and the question answer, not just the source citation.\n"
        "5. You may mention a rejected alternative and why, using only the reason "
        "already given in the fact set.\n"
        "6. Translate internal field values into plain regulatory language — never "
        "print a raw database code such as 'default_permitted' verbatim; say what it "
        "means (e.g. a default value the methodology permits to apply).\n"
        "7. State the basis for the argument, don't dictate the VVB's conclusion — "
        "never write instructions to the VVB such as 'the VVB should validate/"
        "confirm/accept'. Present the reasoning and let the auditor draw their own "
        "conclusion.\n"
        f"8. {language_instruction}\n"
        "Respond with the argument text only, no preamble, no markdown."
    )


def generate_defendability_argument(fact_set: dict, *, model_override: str | None = None) -> tuple[str, str]:
    """Returns (argument_text, model_used). Raises whatever call_openai() or
    validate_generated_argument() raise — callers (resolve_parameter) are
    responsible for catching and falling back to the template (SPEC-03).

    document_language comes from fact_set["project_context"]["document_language"]
    — the language the DELIVERABLE must be written in (set per-project, defaults
    to 'en' for Gold Standard/Verra), not the chat interface language."""
    from carbongpt.core.openai_client import call_openai, _resolve_model

    document_language = (fact_set.get("project_context") or {}).get("document_language") or "en"
    user_prompt = "Fact set:\n" + json.dumps(fact_set, indent=2, ensure_ascii=False)
    text = call_openai(_system_prompt(document_language), user_prompt, temperature=0.3, max_tokens=700,
                        model_override=model_override).strip()
    validate_generated_argument(text, fact_set)
    return text, _resolve_model(model_override)


def validate_generated_argument(text: str, fact_set: dict) -> None:
    """Raises ArgumentValidationError if `text` contains a number, section
    reference, or country-classification claim not licensed by `fact_set`.
    Does not — cannot — verify that the text correctly interprets the facts
    it cites, only that it doesn't invent ones absent from the input."""
    fact_text = json.dumps(fact_set, ensure_ascii=False)
    allowed_numbers = set(_NUMBER_RE.findall(fact_text))
    allowed_sections = {s.lower().replace(" ", "") for s in _SECTION_RE.findall(fact_text)}

    # page_ref is stored as a bare number under its own JSON key (e.g. "page_ref": "12"),
    # never as the literal phrase "page 12" — the JSON text never contains that phrasing,
    # so register it explicitly. Without this, any natural-language "page N" mention in
    # the generated text is flagged as hallucinated even when N is exactly the sourced
    # page, silently defeating AI generation on every real call.
    page_ref = fact_set.get("chosen", {}).get("page_ref")
    if page_ref:
        allowed_sections.add(f"page{str(page_ref).strip()}")

    found_numbers = set(_NUMBER_RE.findall(text))
    found_sections = {s.lower().replace(" ", "") for s in _SECTION_RE.findall(text)}

    unknown_numbers = found_numbers - allowed_numbers
    unknown_sections = found_sections - allowed_sections

    if unknown_numbers or unknown_sections:
        raise ArgumentValidationError(
            f"Generated argument contains values absent from the fact set — "
            f"unknown numbers: {sorted(unknown_numbers)}, unknown sections: {sorted(unknown_sections)}"
        )

    # A candidate value's applicability.region text legitimately contains phrases
    # like "Least Developed Countries" (it describes the RULE's scope, sourced from
    # the methodology) — so a plain "does this substring appear in fact_text" check
    # would wrongly let the model launder that into a claim about the project's own
    # country. Country classification isn't sourced anywhere yet (SPEC-02 not
    # implemented), so any such claim is unconditionally rejected unless a future
    # project_context.country_classification field explicitly authorizes it.
    classification_hits = _CLASSIFICATION_CLAIM_RE.findall(text)
    if classification_hits:
        authorized = (fact_set.get("project_context") or {}).get("country_classification") or ""
        unauthorized = [h for h in classification_hits if h.lower() not in authorized.lower()]
        if unauthorized:
            raise ArgumentValidationError(
                f"Generated argument asserts a country classification not sourced in the fact set "
                f"(docs/SPEC-02.md not implemented yet) — found: {sorted(set(unauthorized))}"
            )
