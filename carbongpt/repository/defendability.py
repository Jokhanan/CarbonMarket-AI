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


class ArgumentValidationError(Exception):
    """Raised by validate_generated_argument() when the generated text
    contains a number or section reference absent from the fact set."""


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


def _system_prompt() -> str:
    return (
        "You write short defendability arguments for a carbon credit regulatory "
        "reasoning system. You will be given a JSON fact set: a chosen regulatory "
        "value, its source, the project context that led to choosing it, and the "
        "alternatives that were not chosen and why.\n\n"
        "STRICT RULES:\n"
        "1. You must use NO number, NO section reference, and NO unit that does not "
        "appear verbatim in the fact set provided. Do not compute, round, or "
        "introduce any new figure.\n"
        "2. If you cannot build a solid argument without introducing information "
        "absent from the fact set, say so explicitly instead of improvising.\n"
        "3. Write 3-5 sentences, addressed to a VVB (validation/verification body), "
        "explaining why the chosen value applies to THIS project specifically — use "
        "the project context and the question answer, not just the source citation.\n"
        "4. You may mention a rejected alternative and why, using only the reason "
        "already given in the fact set.\n"
        "Respond with the argument text only, no preamble, no markdown."
    )


def generate_defendability_argument(fact_set: dict, *, model_override: str | None = None) -> tuple[str, str]:
    """Returns (argument_text, model_used). Raises whatever call_openai() or
    validate_generated_argument() raise — callers (resolve_parameter) are
    responsible for catching and falling back to the template (SPEC-03)."""
    from carbongpt.core.openai_client import call_openai, _resolve_model

    user_prompt = "Fact set:\n" + json.dumps(fact_set, indent=2, ensure_ascii=False)
    text = call_openai(_system_prompt(), user_prompt, temperature=0.3, max_tokens=400,
                        model_override=model_override).strip()
    validate_generated_argument(text, fact_set)
    return text, _resolve_model(model_override)


def validate_generated_argument(text: str, fact_set: dict) -> None:
    """Raises ArgumentValidationError if `text` contains a number or section
    reference not present anywhere in `fact_set`. Does not — cannot — verify
    that the text correctly interprets the facts it cites, only that it
    doesn't invent ones absent from the input."""
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
