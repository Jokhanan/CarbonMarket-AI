"""
parameter_instantiation.py — Moteur d'instanciation (docs/SPEC-06.md, T5).

Pour chaque patron de bloc de template_fields (SPEC-05,
field_type='parameter_block'), détermine s'il correspond au patron ex
ante ou monitoring de la méthodologie — par inspection du contenu réel du
bloc dans le .docx (les libellés de ses lignes), pas par une convention
de nommage ou un comptage de lignes qui ne généraliserait pas — puis
instancie une copie du patron par paramètre `methodology_parameters` dont
`timing_classification` correspond. Un paramètre 'both' (ex. le fNRB de
RECH) est instancié dans les deux patrons — jamais tranché à la place de
l'utilisateur (exigence explicite).

Le VPA-DD v3.0 a trois patrons de bloc (SPEC-05 T7 : T37, T40, T55) mais
RECH v5.0 n'en couvre que deux avec ses propres paramètres — le troisième
(T55, paramètres SDG/développement durable) vient d'un document Gold
Standard séparé (doc 118, SPEC-06 T2, hors périmètre de cette session).
Un patron dont le contenu ne correspond ni à ex ante ni à monitoring
n'est pas instancié depuis RECH — il remonte dans `unmapped_blocks`,
jamais rempli au hasard.
"""

import logging
from typing import Any

import docx

logger = logging.getLogger(__name__)

# Marqueurs de contenu propres au patron "monitoring" (présents dans les
# libellés de ses lignes mais jamais dans le patron "ex ante" — vérifié
# sur T37/T40 du VPA-DD v3.0, 03.08.2026).
_MONITORING_MARKERS = (
    "qa/qc", "entity/person", "measuring instrument",
    "monitoring frequency", "measurement intervals",
)
# Marqueurs propres au patron SDG (T55) — ni ex ante ni monitoring au sens
# des paramètres de méthodologie de calcul.
_OTHER_BLOCK_MARKERS = ("sdg", "net benefit", "baseline value")


def _classify_block_pattern(local_path: str, table_index: int) -> str:
    """Retourne 'ex_ante' | 'monitoring' | 'other', déterminé en lisant les
    libellés réels des lignes du tableau — jamais deviné depuis son nombre
    de lignes ou sa position, qui ne sont pas des faits stables au sens où
    docs/SPEC-05.md l'exige pour `position` (ancrage réel, pas heuristique)."""
    doc = docx.Document(local_path)
    table = doc.tables[table_index]
    labels = " ".join(row.cells[0].text.strip().lower() for row in table.rows)
    if any(marker in labels for marker in _OTHER_BLOCK_MARKERS):
        return "other"
    if any(marker in labels for marker in _MONITORING_MARKERS):
        return "monitoring"
    return "ex_ante"


def instantiate_parameter_blocks(template_version_id: int, methodology_version_id: int) -> dict[str, Any]:
    """
    Croise les patrons de bloc d'un template (SPEC-05) avec les paramètres
    d'une méthodologie (SPEC-06 T3) pour produire, pour un projet sous
    cette méthodologie et ce template, le nombre réel de blocs à remplir.

    Retourne :
      {
        "ex_ante_block": {"field_key": "T37", "template_field_id": 123,
                           "instances": [<paramètre>, ...]} | None,
        "monitoring_block": {"field_key": "T40", "template_field_id": 130,
                              "instances": [...]} | None,
        "unmapped_blocks": [{"field_key": "T55", "reason": "..."}],
        "needs_review": [<paramètre incomplet — pas instancié>, ...],
      }

    Un paramètre `timing_classification='both'` (ex. fNRB) apparaît dans
    les deux `instances` — jamais choisi automatiquement pour l'un ou
    l'autre.

    Un paramètre dont `key` et `description` sont tous deux vides, ou dont
    la classification est 'monitoring'/'both' sans qu'aucune fréquence
    n'ait pu être extraite (contradiction avec sa propre classification),
    n'est PAS instancié silenciseusement — il va dans `needs_review`.
    """
    from carbongpt.repository.db import get_cursor

    with get_cursor() as cur:
        cur.execute(
            """SELECT tf.id, tf.field_key, tf.position, dtv.local_path
               FROM template_fields tf
               JOIN document_template_versions dtv ON dtv.id = tf.template_version_id
               WHERE tf.template_version_id = %s AND tf.field_type = 'parameter_block'
               ORDER BY tf.field_key""",
            (template_version_id,),
        )
        blocks = cur.fetchall()

        cur.execute(
            """SELECT * FROM methodology_parameters
               WHERE methodology_version_id = %s ORDER BY parameter_id""",
            (methodology_version_id,),
        )
        parameters = cur.fetchall()

    ex_ante_block = None
    monitoring_block = None
    unmapped_blocks = []

    for b in blocks:
        pattern = _classify_block_pattern(b["local_path"], b["position"]["table_index"])
        if pattern == "ex_ante":
            ex_ante_block = {"field_key": b["field_key"], "template_field_id": b["id"], "instances": []}
        elif pattern == "monitoring":
            monitoring_block = {"field_key": b["field_key"], "template_field_id": b["id"], "instances": []}
        else:
            unmapped_blocks.append({
                "field_key": b["field_key"],
                "reason": "Patron non couvert par les paramètres de cette méthodologie "
                          "(ex. bloc SDG — source: exigences transverses Gold Standard, "
                          "SPEC-06 T2, hors périmètre de cette session)",
            })

    needs_review = []
    for p in parameters:
        incomplete = (not p["key"] and not p["description"]) or (
            p["timing_classification"] in ("monitoring", "both") and not p["measurement_frequency_note"]
        )
        if incomplete:
            needs_review.append(dict(p))
            continue
        if p["timing_classification"] in ("ex_ante", "both") and ex_ante_block is not None:
            ex_ante_block["instances"].append(dict(p))
        if p["timing_classification"] in ("monitoring", "both") and monitoring_block is not None:
            monitoring_block["instances"].append(dict(p))

    return {
        "ex_ante_block": ex_ante_block,
        "monitoring_block": monitoring_block,
        "unmapped_blocks": unmapped_blocks,
        "needs_review": needs_review,
    }
