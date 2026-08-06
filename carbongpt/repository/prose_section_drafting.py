"""
prose_section_drafting.py — Rédaction sourcée d'une section narrative de
template (v1.0, objectif produit : VPA-DD complet sous RECH v5.0 / VPA-DD
v3.0). Même discipline anti-hallucination que parameter_block_drafting.py
(SPEC-06 T5) et defendability.py (SPEC-04) : le modèle ne voit qu'un jeu de
faits fermé assemblé depuis ce qui est déjà en base, et
validate_prose_section_content() rejette mécaniquement toute référence
(nombre, section, méthodologie/outil/norme) absente de ce jeu de faits.

Le jeu de faits d'une section narrative est plus riche que celui d'un seul
bloc de paramètre — une section entière (ex. « Application of methodology
(ies) ») peut couvrir plusieurs des 26 paramètres RECH et plusieurs
documents transverses à la fois — mais le principe est identique : rien
n'entre dans le prompt qui ne soit déjà sourcé et tracé en base.

Sources composant le jeu de faits, toutes déjà construites par les sessions
précédentes (rien de nouveau n'est inventé ici, seulement assemblé) :
  - field_requirement_linking.py (SPEC-06 T4) : quelle section est
    gouvernée par RECH v5.0 et/ou quel(s) document(s) transverses. Un champ
    non racine (heading_level 2/3) hérite des liens de son ancêtre de
    niveau 1 — SECTION_LINKS ne couvre que les 9 sections racines, la
    résolution par ancêtre est faite ici.
  - methodology_parameters (SPEC-06 T3) : les 26 paramètres RECH, inclus
    seulement quand la section est gouvernée par la méthodologie.
  - crosscutting_requirements (SPEC-06 T2) : métadonnées des documents
    transverses gouvernant la section (code, nom, version, date).
  - project_parameters (SPEC-03) : valeurs déjà résolues pour ce projet
    (ex. EF_CO2), avec leur statut (confirmed/default) — jamais présentées
    comme confirmées si elles ne le sont pas.
  - project_open_questions via non_deducible_facts.py (SPEC-06 T6) : les
    faits que même toutes les sources ingérées ne peuvent fournir — inclus
    avec leur statut (répondu ou non), jamais devinés.
  - user_projects (identité et paramètres du projet saisis par le porteur
    de projet — données réelles, pas une invention du modèle).
"""

import json
import logging
from typing import Any

from carbongpt.repository.defendability import _ALLCAPS_TOKEN_RE, _NUMBER_RE, _SECTION_RE

logger = logging.getLogger(__name__)

_LANGUAGE_INSTRUCTIONS = {
    "en": "Write the section in English.",
    "fr": "Redige la section en francais.",
}

# Found running this pipeline for real on all 161 VPA-DD v3.0 sections
# (v1.0, 04.08.2026): the ALLCAPS-token check, reused verbatim from
# parameter_block_drafting.py, correctly catches an invented EXTERNAL
# citation (a specific tool/standard/methodology name/version not in the
# fact set — see defendability.py's TPDDTEC/TOOL33/CDM precedent) but was
# also rejecting two categories of legitimate text that are NOT citations:
#   1. "INSERT" — the literal placeholder syntax this module's own system
#      prompt instructs the model to write ("[INSERT: <data needed>]").
#      Rejecting our own instructed control word is a self-inflicted bug,
#      not a caught hallucination.
#   2. Generic Gold Standard / carbon-market STRUCTURAL vocabulary — names
#      for a document type, role, or concept inherent to writing ANY
#      VPA-DD (VPA, VVB, CME, GHG, SDG, NDC, GWP, GPS, VER) — never a
#      citable external fact that could be wrong, unlike "ISO 3166" (a
#      specific external standard, still correctly blocked unless sourced)
#      or "TOOL33"/"CDM" (specific external tools, still correctly
#      blocked). Distinguishing the two is a judgment call, kept narrow and
#      explicit here rather than loosened generally.
_STRUCTURAL_VOCABULARY = {
    "INSERT", "VPA", "VVB", "CME", "GHG", "SDG", "SDGS", "NDC", "GWP", "GPS", "VER",
}


class ProseSectionValidationError(Exception):
    """Raised by validate_prose_section_content() when the generated text
    references a number, section, or ALLCAPS methodology/tool/standard
    token absent from the fact set."""


def _stringify(value: Any) -> Any:
    """Recursively converts non-JSON-native values (date, Decimal) coming
    straight from DB rows into strings, so json.dumps() never raises and
    every value that could be cited is actually visible in the serialized
    fact text the validator scans."""
    if isinstance(value, dict):
        return {k: _stringify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_stringify(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _resolve_field(cur, template_version_id: int, field_key: str) -> dict[str, Any] | None:
    cur.execute(
        "SELECT id, field_key, parent_section, title, position FROM template_fields "
        "WHERE template_version_id = %s AND field_key = %s",
        (template_version_id, field_key),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _resolve_governing_field_id(cur, template_version_id: int, field: dict[str, Any]) -> int | None:
    """A field's own requirement links (template_field_requirements) exist
    only for the 9 level-1 sections and the 3 parameter-block patrons
    (field_requirement_linking.py, SPEC-06 T4) — every other field
    (heading_level 2/3) is governed by whichever requirement its level-1
    ancestor carries. The ancestor is identified by title, because that is
    literally what template_docx_parser.py stores in parent_section (SPEC-05
    T3) — there is no field_key back-reference. Returns the ancestor's
    template_fields.id, or the field's own id if it IS the level-1 heading."""
    if field["position"].get("heading_level") == 1 or field["parent_section"] is None:
        return field["id"]
    cur.execute(
        "SELECT id FROM template_fields WHERE template_version_id = %s AND title = %s "
        "AND (position->>'heading_level')::int = 1",
        (template_version_id, field["parent_section"]),
    )
    row = cur.fetchone()
    return row["id"] if row else None


def _fetch_governing_sources(cur, governing_field_id: int) -> list[dict[str, Any]]:
    cur.execute(
        "SELECT requirement_type, methodology_version_id, crosscutting_requirement_id, notes "
        "FROM template_field_requirements WHERE template_field_id = %s",
        (governing_field_id,),
    )
    sources = []
    for row in cur.fetchall():
        if row["requirement_type"] == "methodology" and row["methodology_version_id"]:
            cur.execute(
                "SELECT methodology_code, version, document_name FROM methodology_version_history "
                "WHERE id = %s",
                (row["methodology_version_id"],),
            )
            m = cur.fetchone()
            if m:
                sources.append({
                    "type": "methodology", "code": m["methodology_code"], "version": m["version"],
                    "document_name": m["document_name"], "note": row["notes"],
                })
        elif row["requirement_type"] == "crosscutting" and row["crosscutting_requirement_id"]:
            cur.execute(
                "SELECT code, name, version, document_name, released_date FROM crosscutting_requirements "
                "WHERE id = %s",
                (row["crosscutting_requirement_id"],),
            )
            c = cur.fetchone()
            if c:
                sources.append({
                    "type": "crosscutting", "code": c["code"], "name": c["name"], "version": c["version"],
                    "document_name": c["document_name"], "released_date": str(c["released_date"]),
                    "note": row["notes"],
                })
    return sources


def _fetch_rech_parameters(cur, methodology_version_id: int) -> list[dict[str, Any]]:
    cur.execute(
        "SELECT parameter_id, key, description, unit, timing_classification, section_ref, page_ref "
        "FROM methodology_parameters WHERE methodology_version_id = %s ORDER BY parameter_id",
        (methodology_version_id,),
    )
    return [dict(r) for r in cur.fetchall()]


def _fetch_project_identity(cur, project_id: int) -> dict[str, Any]:
    cur.execute(
        "SELECT name, country, country_iso, methodology, description, standard, "
        "crediting_period_start, crediting_period_years, methodology_settings, "
        "location_name, region, district, latitude, longitude "
        "FROM user_projects WHERE id = %s",
        (project_id,),
    )
    row = cur.fetchone()
    return _stringify(dict(row)) if row else {}


def _fetch_project_parameters(cur, project_id: int) -> list[dict[str, Any]]:
    cur.execute(
        "SELECT param_key, value, unit, source_type, source_reference, param_status, "
        "defendability_argument FROM project_parameters WHERE project_id = %s",
        (project_id,),
    )
    return [dict(r) for r in cur.fetchall()]


def _fetch_open_questions(cur, project_id: int, field_key: str) -> list[dict[str, Any]]:
    from carbongpt.repository.non_deducible_facts import NON_DEDUCIBLE_FACT_CATEGORIES

    relevant = [c for c in NON_DEDUCIBLE_FACT_CATEGORIES if field_key in c["affected_sections"]]
    if not relevant:
        return []
    keys = [c["key"] for c in relevant]
    cur.execute(
        "SELECT question_key, status, answer_value FROM project_open_questions "
        "WHERE project_id = %s AND question_key = ANY(%s)",
        (project_id, keys),
    )
    answers = {r["question_key"]: dict(r) for r in cur.fetchall()}
    result = []
    for cat in relevant:
        answer = answers.get(cat["key"])
        result.append({
            "fact": cat["label"],
            "why_not_deducible": cat["why_not_deducible"],
            "status": answer["status"] if answer else "open",
            "answer": answer["answer_value"] if answer else None,
        })
    return result


def build_prose_section_fact_set(field_key: str, project_info: dict[str, Any]) -> dict[str, Any]:
    """Assembles the closed fact set for ONE prose field of the VPA-DD v3.0
    template. Scoped to (GoldStandard, VPA-DD v3.0) governed by RECH v5.0
    only, matching parameter_block_drafting.py's own scope limit — this
    codebase still has no generic project -> methodology_version_id
    resolver (docs/STATUS.md)."""
    from carbongpt.repository.db import get_cursor

    project_id = project_info.get("id")
    if not project_id:
        raise ValueError("project_info['id'] is required to build a prose section fact set")

    with get_cursor() as cur:
        cur.execute(
            """SELECT dtv.id AS template_version_id FROM document_template_versions dtv
               JOIN document_templates dt ON dt.id = dtv.template_id
               WHERE dt.standard = 'GoldStandard' AND dt.doc_type = 'VPA-DD'
                     AND dtv.is_current = true AND dtv.parsed_at IS NOT NULL"""
        )
        tv_row = cur.fetchone()
        if tv_row is None:
            raise ValueError("VPA-DD v3.0 has no analyzed template version in the database")
        template_version_id = tv_row["template_version_id"]

        field = _resolve_field(cur, template_version_id, field_key)
        if field is None:
            raise ValueError(f"Field {field_key!r} not found in template_fields for VPA-DD v3.0")

        governing_field_id = _resolve_governing_field_id(cur, template_version_id, field)
        governing_sources = _fetch_governing_sources(cur, governing_field_id) if governing_field_id else []

        rech_parameters: list[dict[str, Any]] = []
        methodology_sources = [s for s in governing_sources if s["type"] == "methodology"]
        if methodology_sources:
            cur.execute(
                "SELECT id FROM methodology_version_history WHERE methodology_code = %s AND is_current = true",
                ("407",),
            )
            meth_row = cur.fetchone()
            if meth_row:
                rech_parameters = _fetch_rech_parameters(cur, meth_row["id"])

        project_identity = _fetch_project_identity(cur, project_id)
        project_parameters = _fetch_project_parameters(cur, project_id)
        # affected_sections in NON_DEDUCIBLE_FACT_CATEGORIES lists level-1
        # field_keys (H27, H196, H212, H300) — matched against this field's
        # own key, not the ancestor's, since non-root fields simply won't
        # match any category (only their level-1 heading will, when drafted).
        open_questions = _fetch_open_questions(cur, project_id, field_key)

    return {
        "section": {
            "field_key": field["field_key"],
            "title": field["title"],
            "parent_section": field["parent_section"],
        },
        "governing_sources": governing_sources,
        "rech_parameters": rech_parameters,
        "project": project_identity,
        "project_parameters": project_parameters,
        "open_questions": open_questions,
        "document_language": project_info.get("document_language") or "en",
    }


def _system_prompt(document_language: str) -> str:
    language_instruction = _LANGUAGE_INSTRUCTIONS.get(
        document_language, f"Write the section in the language identified by ISO code '{document_language}'."
    )
    return (
        "You draft ONE narrative section of a Gold Standard VPA Design Document (VPA-DD) "
        "template, for a specific cookstove project under methodology RECH v5.0 (Gold "
        "Standard 407). You will be given a JSON fact set: the section itself, the "
        "regulatory source(s) that govern it (the methodology and/or specific Gold "
        "Standard cross-cutting requirement documents), any RECH v5.0 parameters "
        "relevant to it, the project's own identity and settings, any project "
        "calculation parameters already resolved, and any fact this system could not "
        "deduce from any source and has asked the project developer directly.\n\n"
        "STRICT RULES:\n"
        "1. You must use NO number, unit, section reference, methodology name, tool "
        "name, standard name, document version, or equation that does not appear "
        "verbatim in the fact set provided. Do not compute, round, or introduce "
        "anything new — including well-known tools, standards, or methodology "
        "versions you may recognise from general knowledge. If the fact set does not "
        "name a document or tool, do not name one yourself.\n"
        "2. Ground every substantive claim in the governing_sources given — cite them "
        "by document code/name and version when relevant, never a document not listed.\n"
        "3. If rech_parameters is non-empty and relevant to this section, reference "
        "them by their Parameter ID (e.g. 'ICS 17') and description — do not invent "
        "parameter IDs not present in the list.\n"
        "4. project_parameters may have param_status 'default' (a provisional value, "
        "not yet confirmed by the project developer) or 'confirmed'. Never present a "
        "'default' value as confirmed — say explicitly that it is provisional/pending "
        "confirmation when you use it.\n"
        "5. open_questions lists facts no source can supply — only the project "
        "developer can. If an entry's status is 'open' (no answer yet), do NOT invent "
        "an answer — write '[To be confirmed by the project developer: <fact>]'. If "
        "'answered', use the answer given, exactly as provided.\n"
        "6. Where project-specific data this section needs is simply absent from the "
        "fact set (not listed among open_questions either — e.g. a description or "
        "measurement the project record hasn't captured yet), write a clear "
        "placeholder: '[INSERT: <specific data needed>]'. Never fabricate it.\n"
        "7. Write professional, technical content appropriate for submission to Gold "
        "Standard, in the style expected by a VVB (Validation/Verification Body).\n"
        f"8. {language_instruction}\n"
        "Respond with the section content only — no preamble, no repetition of the "
        "section title as a heading."
    )


def generate_prose_section_content(fact_set: dict[str, Any], *, model_override: str | None = None) -> tuple[str, str]:
    """Returns (section_text, model_used). Raises whatever call_openai() or
    validate_prose_section_content() raise — no automatic fallback to the
    old unsourced generic prompt exists here, deliberately: that prompt is
    exactly the path that hallucinated (docs/STATUS.md). A section that
    cannot be drafted from sourced facts must be surfaced as an error, not
    silently replaced by guessed text."""
    from carbongpt.core.openai_client import call_openai, _resolve_model

    document_language = fact_set.get("document_language") or "en"
    user_prompt = "Fact set:\n" + json.dumps(_stringify(fact_set), indent=2, ensure_ascii=False)
    text = call_openai(_system_prompt(document_language), user_prompt, temperature=0.3, max_tokens=2500,
                        model_override=model_override).strip()
    validate_prose_section_content(text, fact_set)
    return text, _resolve_model(model_override)


def _collect_explicit_citation_forms(node: Any) -> set[str]:
    """section_ref/page_ref values are stored as bare numbers under their
    own JSON keys (e.g. "section_ref": "14.2"), never as the literal
    phrase "§14.2" or "page 14.2" — the serialized fact text never
    contains that phrasing verbatim, so a legitimate citation like
    "§14.2 of RECH v5.0" would otherwise always be flagged as
    hallucinated. Same fix as defendability.py's page_ref handling
    (SPEC-04), generalized here because a prose section's fact set nests
    many parameters/sources, not just one."""
    forms: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if value in (None, ""):
                continue
            if key == "section_ref":
                forms.add(f"§{str(value).strip()}")
            elif key == "page_ref":
                forms.add(f"page{str(value).strip()}")
            forms |= _collect_explicit_citation_forms(value)
    elif isinstance(node, list):
        for item in node:
            forms |= _collect_explicit_citation_forms(item)
    return forms


def validate_prose_section_content(text: str, fact_set: dict[str, Any]) -> None:
    """Raises ProseSectionValidationError if `text` contains a number,
    section reference, or ALLCAPS methodology/tool/standard token not
    present anywhere in `fact_set`. Same mechanism as
    defendability.validate_generated_argument() and
    parameter_block_drafting.validate_parameter_block_content() — the
    regexes are imported and reused directly, not reimplemented."""
    fact_text = json.dumps(_stringify(fact_set), ensure_ascii=False)
    allowed_numbers = set(_NUMBER_RE.findall(fact_text))
    allowed_sections = {s.lower().replace(" ", "") for s in _SECTION_RE.findall(fact_text)}
    allowed_sections |= {f.lower().replace(" ", "") for f in _collect_explicit_citation_forms(fact_set)}
    allowed_tokens = set(_ALLCAPS_TOKEN_RE.findall(fact_text))

    found_numbers = set(_NUMBER_RE.findall(text))
    found_sections = {s.lower().replace(" ", "") for s in _SECTION_RE.findall(text)}
    found_tokens = set(_ALLCAPS_TOKEN_RE.findall(text)) - _STRUCTURAL_VOCABULARY

    unknown_numbers = found_numbers - allowed_numbers
    unknown_sections = found_sections - allowed_sections
    unknown_tokens = found_tokens - allowed_tokens

    if unknown_numbers or unknown_sections or unknown_tokens:
        raise ProseSectionValidationError(
            "Generated section references values absent from the fact set — "
            f"unknown numbers: {sorted(unknown_numbers)}, "
            f"unknown sections: {sorted(unknown_sections)}, "
            f"unknown methodology/tool/standard tokens: {sorted(unknown_tokens)}"
        )
