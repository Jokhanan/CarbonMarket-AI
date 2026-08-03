"""
non_deducible_facts.py — Faits que ni le template, ni la méthodologie, ni
les exigences transverses ne peuvent fournir (docs/SPEC-06.md, T6).

Aucune nouvelle table — réutilise `project_open_questions` (SPEC-03),
déjà le mécanisme du système pour tout fait qui doit être posé à
l'utilisateur plutôt que deviné (voir `parameter_resolver.py::
ask_or_get_kiln_question` pour le patron d'origine).

Une section « couverte » par une source d'exigence (SPEC-06 T4) n'est pas
pour autant entièrement déductible : la source fournit la RÈGLE, pas
toujours la VALEUR. Ce module catalogue précisément les endroits où,
même avec le template, RECH v5.0 et les 7 documents transverses tous
ingérés, il reste un choix ou un fait que seul le porteur de projet
connaît — distinct des « trous » structurels de SPEC-06 T4 (sections sans
aucune source), qui eux sont une lacune du système, pas une propriété
inhérente du fait.
"""

from typing import Any

# Chaque entrée : quel fait, pourquoi aucune source ne peut le fournir
# (même quand une source EXISTE pour la section qui le contient), quelle(s)
# section(s) du VPA-DD v3.0 il affecte (field_key, SPEC-05), et la source
# qui gouverne la RÈGLE (si une existe) sans fournir la VALEUR.
NON_DEDUCIBLE_FACT_CATEGORIES: list[dict[str, Any]] = [
    {
        "key": "gender_track_choice",
        "label": "Choix de la piste genre (sensible obligatoire vs responsive optionnelle)",
        "affected_sections": ["H196", "H212"],
        "governing_source": "104 (Gender Equality Requirements & Guidelines)",
        "why_not_deducible": (
            "104 impose la piste sensible au genre à tout projet et laisse la piste "
            "responsive (quantification de l'impact SDG 5) explicitement optionnelle "
            "— un choix de projet que le document ne tranche pas lui-même."
        ),
    },
    {
        "key": "vpa_scale_and_type",
        "label": "Échelle et type de VPA (Real case / Regular ; Micro/Small/Large scale)",
        "affected_sections": ["H27"],
        "governing_source": None,
        "why_not_deducible": (
            "Case à cocher du template (SPEC-05, Table 0/1 dans le VPA-DD v2.3) — "
            "dépend de la taille réelle du projet, aucun document ne la fixe."
        ),
    },
    {
        "key": "site_field_data",
        "label": "Données de terrain propres au site (coordonnées GPS, quantités de foyers "
                  "distribués, dates d'installation, résultats de test terrain KPT)",
        "affected_sections": ["H27", "H96"],
        "governing_source": "RECH v5.0 (définit QUELS champs sont requis — ICS 1, 15, 19, 21... — "
                             "pas leurs valeurs)",
        "why_not_deducible": (
            "Par construction : ce sont des faits du monde propres au projet, jamais "
            "des règles. RECH v5.0 dit quel paramètre est requis (ex. ICS 15, "
            "consommation de combustible baseline) mais ne peut jamais dire quelle est "
            "la valeur mesurée sur le terrain pour CE projet."
        ),
    },
    {
        "key": "corsia_a64_pacm_status",
        "label": "Statut CORSIA / enregistrement A6.4 ou PACM antérieur du projet",
        "affected_sections": ["H27"],
        "governing_source": "119 (Requirements for Paris Agreement Alignment)",
        "why_not_deducible": (
            "119 définit les EXIGENCES de diligence liées à ces statuts (nouvelles "
            "questions trouvées dans le v3.0, SPEC-05) mais le statut réel du projet "
            "(déjà enregistré ailleurs ou non) est un fait déclaratif du porteur de projet."
        ),
    },
    {
        "key": "contact_information_cme",
        "label": "Coordonnées administratives du CME (Coordinating/Managing Entity)",
        "affected_sections": ["H300"],
        "governing_source": None,
        "why_not_deducible": (
            "Section sans aucune source liée (SPEC-06 T4, gap structurel confirmé par "
            "find_unlinked_sections) — donnée purement administrative, jamais gouvernée "
            "par une exigence de contenu."
        ),
    },
]


def list_non_deducible_facts() -> list[dict[str, Any]]:
    """Static catalogue for the VPA-DD v3.0 / RECH v5.0 pairing this
    session covers. Not read from the database — this is the T6
    "esquisse" SPEC-06.md describes, not a fully wired system."""
    return NON_DEDUCIBLE_FACT_CATEGORIES


def ensure_open_questions_for_project(project_id: int) -> list[dict[str, Any]]:
    """
    Creates a project_open_questions row (SPEC-03's existing mechanism)
    for every category in NON_DEDUCIBLE_FACT_CATEGORIES not already
    present for this project. Idempotent — safe to call repeatedly, never
    duplicates or overwrites an already-open or already-answered question.

    Returns the current state (open or answered) of every category's
    question for this project, same shape as
    parameter_resolver.ask_or_get_kiln_question().
    """
    from carbongpt.repository.db import get_cursor

    results = []
    for cat in NON_DEDUCIBLE_FACT_CATEGORIES:
        with get_cursor() as cur:
            cur.execute(
                "SELECT id, status, answer_value FROM project_open_questions "
                "WHERE project_id = %s AND question_key = %s",
                (project_id, cat["key"]),
            )
            row = cur.fetchone()
        if row is not None:
            results.append({**dict(row), "key": cat["key"]})
            continue
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO project_open_questions
                       (project_id, question_key, question_text, blocks_param_keys, status)
                   VALUES (%s, %s, %s, %s, 'open')
                   RETURNING id, status, answer_value""",
                (project_id, cat["key"], cat["label"], cat["affected_sections"]),
            )
            results.append({**dict(cur.fetchone()), "key": cat["key"]})
    return results
