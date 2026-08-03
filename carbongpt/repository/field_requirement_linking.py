"""
field_requirement_linking.py — Liaison champ de template ↔ source
d'exigence (docs/SPEC-06.md, T4).

Amorçage manuel et documenté, pas une extraction automatique par
similarité de texte (délibérément — SPEC-06 l'écarte explicitement comme
une heuristique fragile). `SECTION_LINKS` et `PARAMETER_BLOCK_LINKS`
encodent une correspondance vérifiée à la main entre les 9 sections de
niveau 1 du VPA-DD v3.0 (SPEC-05 T7) et les 3 blocs de paramètres
(SPEC-05, parameter_block), d'une part, et leurs sources d'exigence
(RECH v5.0 ou l'un des 7 documents transverses, SPEC-06 T2) d'autre part.

Deux sections n'ont délibérément AUCUNE source liée : « Contact
information of CME » (donnée administrative pure, jamais gouvernée par
une exigence de contenu) et « LUF additional information » (Land-use &
Forests — hors périmètre RECH/cookstoves ; gouvernée par l'Activity
Requirement 203, non ingéré cette session). Ce ne sont pas des oublis —
elles sont documentées comme telles, et `find_unlinked_sections()` les
retrouve mécaniquement pour que rien ne dépende de cette liste restant à
jour à la main.

Une source liée à une section ne veut PAS dire que ce document remplit le
champ — il en fournit la RÈGLE (ce qui doit être respecté), pas
nécessairement la VALEUR. Beaucoup de champs correctement « couverts »
par une source restent malgré tout à demander à l'utilisateur pour leur
contenu concret — voir `non_deducible_facts.py` (T6).
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# (field_key, [(requirement_type, crosscutting_code | None), ...], note)
# requirement_type='methodology' always means "this methodology's own
# version" (methodology_version_id passed to link_vpa_dd_v3_sections),
# crosscutting_code is then None and ignored.
SECTION_LINKS: list[tuple[str, list[tuple[str, str | None]], str]] = [
    ("H27", [("crosscutting", "101"), ("crosscutting", "201")],
     "Éligibilité générale du projet (101) et éligibilité propre à l'activité — "
     "les cookstoves relèvent du périmètre Community Services (201)."),
    ("H96", [("methodology", None)],
     "Référence et applicabilité de la méthodologie, limites du projet, "
     "scénario de référence, calcul des réductions — tout vient de RECH v5.0 elle-même."),
    ("H196", [("crosscutting", "103"), ("crosscutting", "104")],
     "Le titre de la section combine explicitement les deux exigences : "
     "Safeguarding Principles & Requirements (103) et la piste sensible au genre, "
     "obligatoire, de 104."),
    ("H212", [("crosscutting", "104")],
     "Section dédiée entièrement à la certification genre (sensible obligatoire, "
     "responsive optionnelle) — Gender Equality Requirements & Guidelines."),
    ("H271", [("crosscutting", "118")],
     "Indicateurs de suivi du SDG Impact Tool — 118 gouverne leur sélection ; "
     "c'est aussi la source du patron de bloc T55 (SPEC-05)."),
    ("H285", [("crosscutting", "102")],
     "Stakeholder Consultation and Engagement Requirements."),
    ("H300", [],
     "Coordonnées administratives du CME (Coordinating/Managing Entity) — "
     "aucune exigence de contenu ne les gouverne, saisie utilisateur directe."),
    ("H303", [("crosscutting", "101")],
     "Appendices mélange plusieurs sujets (méthodologie, changements de conception, "
     "co-bénéfices) — lié ici à 101 comme référence générale la plus proche ; "
     "une liaison sous-section par sous-section serait plus précise, hors "
     "périmètre de cette session."),
    ("H318", [],
     "Land-use & Forests — hors périmètre RECH/cookstoves ; gouverné par "
     "l'Activity Requirement 203 (Land-use & Forests Activity Requirements), "
     "non ingéré (SPEC-06 T2 s'est limité aux 7 documents pertinents pour RECH)."),
]

PARAMETER_BLOCK_LINKS: list[tuple[str, list[tuple[str, str | None]], str]] = [
    ("T37", [("methodology", None)], "Patron ex ante — instancié depuis RECH v5.0 §14.2 (SPEC-06 T5)."),
    ("T40", [("methodology", None)], "Patron monitoring — instancié depuis RECH v5.0 §14.3 (SPEC-06 T5)."),
    ("T55", [("crosscutting", "118")],
     "Patron SDG — non instanciable depuis RECH (SPEC-06 T5 l'a remonté comme "
     "'unmapped_blocks') ; sa source réelle est le SDG Impact Tool (118)."),
]


def link_vpa_dd_v3_sections(template_version_id: int, methodology_version_id: int) -> dict[str, Any]:
    """
    Writes SECTION_LINKS and PARAMETER_BLOCK_LINKS into
    template_field_requirements for the given VPA-DD v3.0
    template_version_id and RECH v5.0 methodology_version_id. Idempotent:
    clears this template_version_id's rows first.

    Raises nothing on a missing crosscutting code — logs a warning and
    skips that one link rather than failing the whole batch (a document
    not yet ingested shouldn't block linking the others).
    """
    from carbongpt.repository.db import get_cursor

    written = 0
    skipped = []

    with get_cursor() as cur:
        cur.execute(
            "SELECT id, field_key FROM template_fields WHERE template_version_id = %s",
            (template_version_id,),
        )
        field_id_by_key = {row["field_key"]: row["id"] for row in cur.fetchall()}

        field_ids = list(field_id_by_key.values())
        if field_ids:
            cur.execute(
                "DELETE FROM template_field_requirements WHERE template_field_id = ANY(%s)",
                (field_ids,),
            )

        for field_key, sources, note in SECTION_LINKS + PARAMETER_BLOCK_LINKS:
            template_field_id = field_id_by_key.get(field_key)
            if template_field_id is None:
                logger.warning("field_key %r not found in template_version_id=%s — skipping",
                                field_key, template_version_id)
                continue
            for requirement_type, code in sources:
                if requirement_type == "methodology":
                    cur.execute(
                        """INSERT INTO template_field_requirements
                               (template_field_id, requirement_type, methodology_version_id, notes)
                           VALUES (%s, 'methodology', %s, %s)""",
                        (template_field_id, methodology_version_id, note),
                    )
                    written += 1
                else:
                    cur.execute(
                        "SELECT id FROM crosscutting_requirements WHERE code = %s AND is_current = true",
                        (code,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        logger.warning("crosscutting code %r has no current version ingested — skipping "
                                        "link for field_key %r", code, field_key)
                        skipped.append((field_key, code))
                        continue
                    cur.execute(
                        """INSERT INTO template_field_requirements
                               (template_field_id, requirement_type, crosscutting_requirement_id, notes)
                           VALUES (%s, 'crosscutting', %s, %s)""",
                        (template_field_id, row["id"], note),
                    )
                    written += 1

    return {"links_written": written, "skipped": skipped}


def find_unlinked_sections(template_version_id: int) -> list[dict[str, Any]]:
    """
    Returns the level-1 sections of a template version with zero rows in
    template_field_requirements — the real gaps, computed mechanically
    rather than trusted from a hand-maintained list (SECTION_LINKS above
    documents WHY H300/H318 are unlinked, but this function is what a
    caller should actually rely on to find them, including any gap this
    session's correspondence table didn't anticipate)."""
    from carbongpt.repository.db import get_cursor

    with get_cursor() as cur:
        cur.execute(
            """SELECT tf.id, tf.field_key, tf.title FROM template_fields tf
               WHERE tf.template_version_id = %s AND tf.field_type = 'prose'
                     AND (tf.position->>'heading_level')::int = 1
                     AND NOT EXISTS (
                         SELECT 1 FROM template_field_requirements tfr
                         WHERE tfr.template_field_id = tf.id
                     )
               ORDER BY (tf.position->>'paragraph_index')::int""",
            (template_version_id,),
        )
        return [dict(r) for r in cur.fetchall()]
