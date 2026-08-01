"""
parameter_resolver.py — Parameter resolution engine (docs/SPEC-03.md).

Thin slice: limited to EF_CO2 / EF_nonCO2 (charcoal), the only two
parameters that already have a full regulatory_value_preferences hierarchy
(docs/SPEC-03.md T2). Demonstrates the whole chain — open question, answer,
proposed value, rejected alternatives with reasons, defendability argument,
traced override — before SPEC-02 or the rest of SPEC-03 is built out.

STUB, clearly scoped: region classification (Sub-Saharan Africa / LDC vs
industrialized) is docs/SPEC-02.md's job and is NOT implemented yet. A
minimal lookup below covers only the countries exercised by tests and the
demo (Ghana, Burkina Faso) — it is not a real ingested dataset and must not
be mistaken for one.
"""

import datetime
import json
import logging
from typing import Any

from carbongpt.repository.db import get_cursor
from carbongpt.repository.defendability import build_fact_set, generate_defendability_argument

logger = logging.getLogger(__name__)


class ResolutionError(Exception):
    """Raised whenever resolve_parameter/override_parameter cannot proceed
    safely — missing hierarchy, unanswered question, no candidate. Never
    swallowed; guessing would defeat the purpose of this engine."""


_SUPPORTED_KEYS = {"EF_CO2", "EF_nonCO2"}

_KILN_QUESTION_KEY = "kiln_type_wccf_ratio"

# STUB — see docs/SPEC-02.md, not yet implemented. Covers only the two
# countries used by tests/demo, not a real LDC/Sub-Saharan-Africa dataset.
_REGION_CLASSIFICATION_STUB = {
    "GHA": "sub_saharan_africa_or_ldc",  # Ghana: qualifies via Sub-Saharan Africa (not on the UN LDC list)
    "BFA": "sub_saharan_africa_or_ldc",  # Burkina Faso: qualifies via LDC and Sub-Saharan Africa
}

_ANSWER_TO_APPLICABILITY_HINT = {
    "combustion_only": {"basis": "combustion_only"},
    "wccf_6_1": {"wccf_ratio": "6:1"},
    "wccf_4_1": {"wccf_ratio": "4:1"},
}

_OPTION_LABELS = {
    "combustion_only": "la combustion seule (carbonisation exclue)",
    "wccf_6_1": "le ratio bois→charbon 6:1 (défaut régional)",
    "wccf_4_1": "le ratio bois→charbon 4:1 (option conservatrice)",
}


def _applicability_to_answer_kind(applicability: dict[str, Any]) -> str | None:
    if applicability.get("basis") == "combustion_only":
        return "combustion_only"
    if applicability.get("wccf_ratio") == "6:1":
        return "wccf_6_1"
    if applicability.get("wccf_ratio") == "4:1":
        return "wccf_4_1"
    return None


def _rejection_reason(chosen_answer: str, alt_applicability: dict[str, Any], alt_rationale: str) -> str:
    """A rejection reason must say why this candidate does NOT apply to THIS
    project — not describe the candidate's own merits (that was the original
    bug: 'always available, more conservative' reads as an argument FOR the
    option, not against it). The real reason it's rejected here is always the
    same: the project's own answer to the open question pointed elsewhere.
    The static rule text is kept as supporting context, not as the headline."""
    alt_kind = _applicability_to_answer_kind(alt_applicability)
    alt_label = _OPTION_LABELS.get(alt_kind, "cette option")
    chosen_label = _OPTION_LABELS.get(chosen_answer, "l'option retenue")
    return (
        f"Non retenu pour ce projet : le développeur a confirmé {chosen_label} "
        f"(réponse à la question sur le traitement de la carbonisation), pas {alt_label}. "
        f"{alt_rationale}"
    )

_KILN_QUESTION_TEXT = (
    "Pour calculer le facteur d'émission du charbon de ce projet, il faut savoir "
    "comment traiter les émissions de fabrication du charbon (carbonisation) :\n"
    "  1. combustion_only — émissions de carbonisation exclues (combustion seule)\n"
    "  2. wccf_6_1 — incluses, ratio bois→charbon 6:1 (défaut régional Afrique "
    "subsaharienne/PMA, ~17% rendement de meule)\n"
    "  3. wccf_4_1 — incluses, ratio bois→charbon 4:1 (choix plus conservateur, "
    "toujours disponible)\n"
    "Quelle option s'applique à ce projet ?"
)


def _region_classification(country_iso: str | None) -> str | None:
    if not country_iso:
        return None
    return _REGION_CLASSIFICATION_STUB.get(country_iso.strip().upper())


def _get_project_context(project_id: int, context_override: dict[str, Any] | None) -> dict[str, Any]:
    with get_cursor() as cur:
        cur.execute("SELECT country_iso, country FROM user_projects WHERE id = %s", (project_id,))
        row = cur.fetchone()
    if row is None:
        raise ResolutionError(f"Project {project_id} not found")
    context = {"country_iso": row["country_iso"], "country": row["country"]}
    if context_override:
        context.update(context_override)
    return context


def ask_or_get_kiln_question(project_id: int) -> dict[str, Any]:
    """Create the WCCF/kiln open question if it doesn't exist yet, or return
    its current state (open or answered)."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, status, answer_value FROM project_open_questions "
            "WHERE project_id = %s AND question_key = %s",
            (project_id, _KILN_QUESTION_KEY),
        )
        row = cur.fetchone()
    if row is not None:
        return dict(row)
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO project_open_questions
                   (project_id, question_key, question_text, blocks_param_keys, status)
               VALUES (%s, %s, %s, %s, 'open')
               RETURNING id, status, answer_value""",
            (project_id, _KILN_QUESTION_KEY, _KILN_QUESTION_TEXT, list(_SUPPORTED_KEYS)),
        )
        return dict(cur.fetchone())


def answer_question(project_id: int, question_key: str, answer_value: str, answered_by: str) -> dict[str, Any]:
    if question_key == _KILN_QUESTION_KEY:
        ask_or_get_kiln_question(project_id)  # create it if it doesn't exist yet
    with get_cursor() as cur:
        cur.execute(
            """UPDATE project_open_questions
               SET status = 'answered', answer_value = %s, answered_by = %s, answered_at = NOW()
               WHERE project_id = %s AND question_key = %s
               RETURNING id, status, answer_value""",
            (answer_value, answered_by, project_id, question_key),
        )
        row = cur.fetchone()
    if row is None:
        raise ResolutionError(f"No open question {question_key!r} for project {project_id}")
    return dict(row)


def resolve_parameter(project_id: int, param_key: str, methodology_version_id: int, *,
                       context_override: dict[str, Any] | None = None,
                       engine_version: str = "spec03-thin-0.1") -> dict[str, Any]:
    """
    Resolve one parameter for a project. Returns either:
      {"status": "blocked_on_question", "question_key": ..., "question_text": ...}
    or:
      {"status": "resolved", "value": ..., "defendability_argument": ...,
       "alternatives": [...]}
    Never invents a value silently — raises ResolutionError if the hierarchy
    (regulatory_value_preferences) needed to choose isn't sourced yet.
    """
    if param_key not in _SUPPORTED_KEYS:
        raise ResolutionError(
            f"resolve_parameter is a thin slice limited to {sorted(_SUPPORTED_KEYS)}, got {param_key!r}"
        )

    context = _get_project_context(project_id, context_override)
    region = _region_classification(context.get("country_iso"))
    if region is None:
        raise ResolutionError(
            f"Cannot classify region for country_iso={context.get('country_iso')!r} — "
            "docs/SPEC-02.md (LDC/Sub-Saharan-Africa ingestion) isn't implemented yet, "
            "only a stub covering Ghana and Burkina Faso exists (parameter_resolver.py)"
        )

    question = ask_or_get_kiln_question(project_id)
    if question["status"] != "answered":
        return {
            "status": "blocked_on_question",
            "question_key": _KILN_QUESTION_KEY,
            "question_text": _KILN_QUESTION_TEXT,
        }

    with get_cursor() as cur:
        cur.execute(
            """SELECT rvp.rank, rvp.obligation, rvp.rationale, rvp.section_ref, rvp.page_ref,
                      rvp.extraction_method, rv.id AS regulatory_value_id, rv.value, rv.unit, rv.applicability
               FROM regulatory_value_preferences rvp
               JOIN regulatory_values rv ON rv.id = rvp.regulatory_value_id
               WHERE rvp.version_id = %s AND rvp.key = %s AND rvp.context_condition = %s::jsonb
               ORDER BY rvp.rank""",
            (methodology_version_id, param_key, json.dumps({"region_classification": region})),
        )
        rules = cur.fetchall()

    usable = [r for r in rules if r["extraction_method"] != "llm_unverified"]
    if not usable:
        raise ResolutionError(
            f"No usable regulatory_value_preferences for key={param_key!r}, "
            f"region_classification={region!r} — hierarchy not sourced yet, refusing to guess"
        )

    hint = _ANSWER_TO_APPLICABILITY_HINT.get(question["answer_value"])
    if hint is None:
        raise ResolutionError(f"Unrecognised answer {question['answer_value']!r} for {_KILN_QUESTION_KEY!r}")

    chosen = next((r for r in usable if all(r["applicability"].get(k) == v for k, v in hint.items())), None)
    if chosen is None:
        raise ResolutionError(f"Answer {question['answer_value']!r} matches no candidate for {param_key!r}")

    alternatives = [r for r in usable if r["regulatory_value_id"] != chosen["regulatory_value_id"]]
    alt_reasons = [
        (alt, _rejection_reason(question["answer_value"], alt["applicability"], alt["rationale"]))
        for alt in alternatives
    ]

    template_argument = (
        f"{param_key} = {chosen['value']} {chosen['unit'] or ''}. "
        f"Source : {chosen['section_ref']}, page {chosen['page_ref']}. "
        f"Statut : {chosen['obligation']}. {chosen['rationale']}"
    ).strip()

    defendability_argument = template_argument
    argument_source = "template"
    argument_model = None
    argument_generated_at = None

    try:
        fact_set = build_fact_set(
            param_key=param_key,
            chosen=chosen,
            alternatives=[
                {"value": alt["value"], "unit": alt["unit"], "section_ref": alt["section_ref"],
                 "rejection_reason": reason}
                for alt, reason in alt_reasons
            ],
            project_context=context,
            question_answer=question["answer_value"],
            question_text=_KILN_QUESTION_TEXT,
        )
        ai_text, ai_model = generate_defendability_argument(fact_set)
        defendability_argument = ai_text
        argument_source = "ai_generated"
        argument_model = ai_model
        argument_generated_at = datetime.datetime.now(datetime.timezone.utc)
    except Exception as exc:
        logger.warning(
            "Génération IA de l'argument de défendabilité indisponible pour project=%s param=%s, "
            "repli sur le gabarit SPEC-03 : %s", project_id, param_key, exc,
        )

    with get_cursor() as cur:
        cur.execute(
            "SELECT id, source_type FROM project_parameters WHERE project_id = %s AND param_key = %s "
            "AND applicable_year IS NULL",
            (project_id, param_key),
        )
        existing = cur.fetchone()

    if existing and existing["source_type"] == "user_override":
        return {
            "status": "kept_user_override",
            "project_parameter_id": existing["id"],
            "message": (
                f"{param_key} a déjà une valeur modifiée par l'utilisateur (user_override) — "
                "le moteur ne l'écrase pas. Utiliser override_parameter() pour la changer "
                "explicitement, ou repasser par une confirmation dédiée pour ré-appliquer "
                "la proposition automatique."
            ),
        }

    with get_cursor() as cur:
        if existing:
            cur.execute(
                """UPDATE project_parameters SET
                       value = %s, unit = %s, source_type = 'methodology', source_reference = %s,
                       defendability_argument = %s, original_proposed_value = %s,
                       resolution_engine_version = %s, resolved_at = NOW(), updated_at = NOW(),
                       defendability_argument_source = %s, defendability_argument_model = %s,
                       defendability_argument_generated_at = %s
                   WHERE id = %s
                   RETURNING id""",
                (chosen["value"], chosen["unit"], chosen["section_ref"], defendability_argument,
                 chosen["value"], engine_version, argument_source, argument_model,
                 argument_generated_at, existing["id"]),
            )
        else:
            cur.execute(
                """INSERT INTO project_parameters
                       (project_id, param_key, param_name, category, value, unit, data_type,
                        source_type, source_reference, methodology_code, defendability_argument,
                        original_proposed_value, resolution_engine_version, resolved_at,
                        defendability_argument_source, defendability_argument_model,
                        defendability_argument_generated_at)
                   VALUES (%s, %s, %s, 'emission_factor', %s, %s, 'number',
                           'methodology', %s, '407', %s, %s, %s, NOW(), %s, %s, %s)
                   RETURNING id""",
                (project_id, param_key, param_key, chosen["value"], chosen["unit"], chosen["section_ref"],
                 defendability_argument, chosen["value"], engine_version,
                 argument_source, argument_model, argument_generated_at),
            )
        pp_id = cur.fetchone()["id"]

        cur.execute("DELETE FROM project_parameter_alternatives WHERE project_parameter_id = %s", (pp_id,))
        cur.execute(
            """INSERT INTO project_parameter_alternatives
                   (project_parameter_id, value, unit, regulatory_value_id, section_ref,
                    applicability, rank, is_selected, rejection_reason)
               VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, NULL)""",
            (pp_id, chosen["value"], chosen["unit"], chosen["regulatory_value_id"], chosen["section_ref"],
             json.dumps(chosen["applicability"]), chosen["rank"]),
        )
        for alt, reason in alt_reasons:
            cur.execute(
                """INSERT INTO project_parameter_alternatives
                       (project_parameter_id, value, unit, regulatory_value_id, section_ref,
                        applicability, rank, is_selected, rejection_reason)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE, %s)""",
                (pp_id, alt["value"], alt["unit"], alt["regulatory_value_id"], alt["section_ref"],
                 json.dumps(alt["applicability"]), alt["rank"], reason),
            )

    return {
        "status": "resolved",
        "project_parameter_id": pp_id,
        "param_key": param_key,
        "value": chosen["value"],
        "unit": chosen["unit"],
        "obligation": chosen["obligation"],
        "defendability_argument": defendability_argument,
        "defendability_argument_source": argument_source,
        "defendability_argument_model": argument_model,
        "defendability_argument_template": template_argument,
        "alternatives": [
            {"value": a["value"], "unit": a["unit"], "rank": a["rank"], "rejection_reason": reason}
            for a, reason in alt_reasons
        ],
    }


def override_parameter(project_id: int, param_key: str, new_value: str, reason: str, user: str) -> dict[str, Any]:
    """The only path to modify a resolved value. Requires a non-empty reason.
    Never overwrites `original_proposed_value` — the engine's first proposal
    stays visible next to the override."""
    if not reason or not reason.strip():
        raise ResolutionError("override_parameter requires a non-empty reason")

    with get_cursor() as cur:
        cur.execute(
            "SELECT id, value, original_proposed_value, notes FROM project_parameters "
            "WHERE project_id = %s AND param_key = %s AND applicable_year IS NULL",
            (project_id, param_key),
        )
        row = cur.fetchone()
    if row is None:
        raise ResolutionError(f"No resolved parameter {param_key!r} for project {project_id} to override")

    history_line = (
        f"[{datetime.date.today().isoformat()}] Override par {user} : {reason} "
        f"(valeur précédente : {row['value']})"
    )
    new_notes = f"{row['notes']}\n{history_line}" if row["notes"] else history_line

    with get_cursor() as cur:
        cur.execute(
            """UPDATE project_parameters SET
                   value = %s, source_type = 'user_override', notes = %s, updated_at = NOW()
               WHERE id = %s""",
            (new_value, new_notes, row["id"]),
        )

    return {
        "project_parameter_id": row["id"],
        "previous_value": row["value"],
        "original_proposed_value": row["original_proposed_value"],
        "new_value": new_value,
    }
