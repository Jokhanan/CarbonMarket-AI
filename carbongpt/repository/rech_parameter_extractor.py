"""
rech_parameter_extractor.py — Extraction des paramètres de calcul de RECH
v5.0 (docs/SPEC-06.md, T3).

Cible RECH v5.0 spécifiquement, pas un extracteur générique de méthodologie
(portée explicite de SPEC-06 T3 : amorçage sur cette seule méthodologie).

RECH v5.0 organise ses paramètres en deux sections normatives dont le
texte d'introduction dit lui-même leur nature :

  §14.2 "Data and parameters not monitored" — 14.2.1 : "shall be determined
  ex-ante ... and shall remain fixed for the duration of the crediting
  period." (ICS 1 à 17, confirmé par lecture directe du PDF, 03.08.2026)

  §14.3 "Data and parameters monitored" — 14.3.1 : "shall be monitored
  during the crediting period." (ICS 18 à 26)

La section d'appartenance est donc le signal PRIMAIRE et non ambigu pour
`timing_classification` — plus fiable qu'analyser le seul contenu de
« Measurement and updating frequency », qui n'existe même pas pour les
paramètres de §14.2 (rien à monitorer, rien à re-mesurer). Le contenu de
ce champ sert de signal SECONDAIRE, pour détecter le cas explicite où la
méthodologie laisse un choix à la certification (fNRB, ICS 20, sous
§14.3 mais son propre texte dit "Determined ex-ante and fixed... OR
updated... biennially. The choice shall be confirmed at Design
Certification.") — un paramètre situé sous §14.3 dont le texte de
fréquence mentionne explicitement une option ex-ante fixe est classé
'both', jamais tranché vers l'un ou l'autre automatiquement (demande
explicite de l'utilisateur).

Extraction structurelle (pdfplumber, pas de LLM en première intention —
voir docs/SPEC-06.md T3) : chaque bloc "Parameter ID ..." a des champs à
labels connus, mais le PDF source les met en page sur deux colonnes
(étiquette étroite, valeur large). pdfplumber restitue ça en texte plat où
CHAQUE LIGNE mélange un fragment d'étiquette et un fragment de valeur côte
à côte (ex. "Measurement Determined ex-ante and fixed..." / "and updating
biennially..." / "frequency (Mandatory update at CP renewal)") — la
valeur n'est pas seulement coupée par l'étiquette, elle est intercalée
ENTRE ses fragments. Un simple aplatissement des espaces ne suffit pas
(essayé, a échoué silencieusement sur les 9 paramètres monitorés — voir
docs/STATUS.md) : il faut reconnaître, ligne par ligne, quel fragment
d'étiquette connu commence la ligne, retirer ce préfixe, et garder le
reste comme valeur — une petite machine à états sur les séquences de
fragments connues (`_LABEL_FRAGMENTS`), pas une regex globale.

Tout ce que produit ce module a extraction_method='llm_extracted' — jamais
'manual', jamais 'verified' sans que l'utilisateur ne le confirme
explicitement (même discipline que regulatory_values, SPEC-01).
"""

import logging
import re
from typing import Any

import pdfplumber

logger = logging.getLogger(__name__)

_PAGE_MARKER = "\x00PAGE:{}\x00"
_PAGE_MARKER_RE = re.compile(r"\x00PAGE:(\d+)\x00")

_SECTION_NOT_MONITORED = "14.2"  # ex ante — RECH's own words, see module docstring
_SECTION_MONITORED = "14.3"  # monitoring

_PARAM_ID_RE = re.compile(r"Parameter ID\s+([A-Za-z0-9 ]+?)(?=\s*\n)")

# Each field's label as it appears, fragment by fragment, one fragment
# per visual line in the source PDF's narrow left column — see module
# docstring. "Choice of data or" (ex ante blocks) is handled separately
# below: its continuation wording varies ("Requirement", "measurement
# methods and procedures:", "Hierarchy for non-standard fuels:"...), so it
# opens measurement_method directly rather than expecting a fixed fragment
# sequence — any stray label word absorbed into the value is a cosmetic
# blemish, not a functional problem, for an extraction_method='llm_extracted'
# field the user reviews before trusting.
_LABEL_FRAGMENTS: dict[str, list[str]] = {
    "key_label": ["Data/parameter:"],
    "unit": ["Data unit:"],
    # Present for some parameters only (ICS 7 confirmed) — a boundary that
    # must be recognised even though its own value isn't stored, otherwise
    # it silently bleeds into "unit"'s value (found while testing — the
    # user caught it in the delivered table: ICS 7's unit read "N/A
    # Equations N/A referred:").
    "equations_referred": ["Equations", "referred:"],
    "purpose": ["Purpose of data:"],
    "value_applied": ["Value(s) applied:"],
    "source_of_data": ["Source of data:"],
    "entity_responsible": ["Entity/person", "responsible for", "the", "measurement:"],
    "measuring_instrument": ["Measuring", "instrument(s):"],
    "type_of_instrument": ["Type of", "instrument"],
    "accuracy_class": ["Accuracy", "class"],
    "calibration_requirements": ["Calibration", "requirements"],
    "location": ["Location"],
    "qa_qc_procedures": ["QA/QC", "procedures:"],
    "treatment_of_uncertainty": ["Treatment of", "uncertainty"],
    "comments": ["Comments:"],
}

# Fields recognised as boundaries (so their content doesn't bleed into the
# NEXT field) but not stored — not part of methodology_parameters and not
# part of what the user asked to see (SPEC-06: identifiant/description/
# unité/source/méthode/fréquence/classification/section/page).
_IGNORED_FIELDS = {"measuring_instrument", "type_of_instrument", "accuracy_class",
                    "calibration_requirements", "location", "equations_referred"}

# "Measurement" alone opens either measurement_frequency_note ("...and
# updating frequency") or measurement_method ("...methods and procedures:")
# — which one is only known once a later line reveals the second fragment.
# Buffered as plain value text until then (see _extract_fields).
_AMBIGUOUS_SECOND_FRAGMENT: dict[str, tuple[str, str]] = {
    "and updating": ("measurement_frequency_note", "frequency"),
    "methods and": ("measurement_method", "procedures:"),
}

# Words that, if present in measurement_frequency_note, indicate the
# methodology offers an ex-ante-fixed alternative even though the
# parameter sits under §14.3 (monitored) — the fNRB case (ICS 20).
_EX_ANTE_ALTERNATIVE_RE = re.compile(r"ex-ante|fixed for the crediting period", re.I)
_PERIODIC_CADENCE_RE = re.compile(r"\b(annual|biennial|continuous|updated)\b", re.I)


class RechParameterExtractionError(Exception):
    """Raised when the parameter section cannot be located at all — never
    a silent empty result (same discipline as the other SPEC-05/06 parsers)."""


_PAGE_HEADER_RE = re.compile(
    r"^Reduced Emissions from Cooking and Heating \(RECH\) V5\.0 Published \d{2}/\d{2}/\d{4}\s*\n"
    r"GS4GG PAA M400-08\s*\n?",
    re.MULTILINE,
)
_PAGE_FOOTER_NUMBER_RE = re.compile(r"\n\d{1,3}\s*$")


def _extract_pages_with_markers(pdf_path: str, first_page: int, last_page: int) -> str:
    """1-indexed, inclusive. Concatenates page text with an invisible page
    marker between pages so a later match's page number can be recovered.

    Strips the repeated page header ("Reduced Emissions from Cooking and
    Heating...") and the bare page-number footer from each page's text —
    without this, a "Parameter ID" block spanning a page boundary picks up
    this boilerplate mid-field, corrupting whichever field happens to be
    open at the page break (found while testing against the real PDF,
    e.g. ICS 15 and ICS 19)."""
    try:
        pdf_ctx = pdfplumber.open(pdf_path)
    except Exception as exc:
        raise RechParameterExtractionError(f"Could not open {pdf_path!r} as a PDF: {exc}") from exc
    with pdf_ctx as pdf:
        chunks = []
        for page_num in range(first_page, last_page + 1):
            text = pdf.pages[page_num - 1].extract_text() or ""
            text = _PAGE_HEADER_RE.sub("", text)
            text = _PAGE_FOOTER_NUMBER_RE.sub("", text)
            chunks.append(_PAGE_MARKER.format(page_num) + text)
    return "\n".join(chunks)


def _page_for_offset(text: str, offset: int) -> str:
    page = None
    for m in _PAGE_MARKER_RE.finditer(text):
        if m.start() > offset:
            break
        page = m.group(1)
    return page or "?"


def _split_into_parameter_blocks(text: str) -> list[tuple[str, str, str]]:
    """Returns [(parameter_id, page_ref, block_text), ...], block_text
    running from one 'Parameter ID' marker to the next (or end of text)."""
    matches = list(_PARAM_ID_RE.finditer(text))
    if not matches:
        raise RechParameterExtractionError(
            "No 'Parameter ID' blocks found in the given page range — "
            "structure likely changed or the wrong pages were passed"
        )
    blocks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block_text = text[start:end]
        page_ref = _page_for_offset(text, m.start())
        blocks.append((m.group(1).strip(), page_ref, block_text))
    return blocks


def _extract_fields(block_text: str) -> dict[str, str]:
    """Line-based state machine — see module docstring for why a
    whitespace-flattening regex approach doesn't work here (value text is
    interleaved BETWEEN label fragments, not just wrapped after them).

    Walks each line of the block. At any point there is at most one
    "active" field expecting a specific next label fragment (or none). A
    line either (a) matches the active field's next expected fragment —
    consumed, remainder appended as value, advance to the next fragment ;
    (b) matches the first fragment of a not-yet-seen field — closes the
    previous field, opens the new one ; or (c) matches neither — treated
    as a value-continuation line for whichever field is currently open.
    "Measurement" is ambiguous between two fields until a later line
    reveals which (see _AMBIGUOUS_SECOND_FRAGMENT) — buffered until
    resolved, never guessed."""
    block_text = _PAGE_MARKER_RE.sub(" ", block_text)
    lines = [l.strip() for l in block_text.split("\n") if l.strip()]

    values: dict[str, list[str]] = {}
    active_field: str | None = None
    active_fragments: list[str] = []
    ambiguous_buffer: list[str] | None = None

    def start_field(name: str, remainder: str, fragments: list[str]) -> None:
        nonlocal active_field, active_fragments
        active_field, active_fragments = name, fragments
        if name not in _IGNORED_FIELDS:
            values.setdefault(name, [])
            if remainder:
                values[name].append(remainder)

    def append_active(text: str) -> None:
        if active_field and active_field not in _IGNORED_FIELDS and text:
            values.setdefault(active_field, []).append(text)

    for line in lines:
        # (0) Resolve a pending ambiguous "Measurement ..." opener.
        if ambiguous_buffer is not None:
            resolved = False
            for frag, (field_name, next_fragment) in _AMBIGUOUS_SECOND_FRAGMENT.items():
                if line.startswith(frag):
                    values[field_name] = ambiguous_buffer
                    remainder = line[len(frag):].strip()
                    active_field, active_fragments = field_name, [next_fragment]
                    if remainder:
                        values[field_name].append(remainder)
                    ambiguous_buffer = None
                    resolved = True
                    break
            if resolved:
                continue
            if not (line.startswith("Choice of data or") or line == "Comments:"
                     or line.startswith("Comments:") or line.startswith("Treatment of")):
                ambiguous_buffer.append(line)
                continue
            # else: fall through — a real new field started before the
            # ambiguity ever resolved; keep the buffer unassigned (dropped)
            # rather than guess which of the two fields it belonged to.
            ambiguous_buffer = None

        # (1) Continue the active field's expected next fragment?
        if active_field and active_fragments and line.startswith(active_fragments[0]):
            remainder = line[len(active_fragments[0]):].strip()
            active_fragments = active_fragments[1:]
            if remainder:
                append_active(remainder)
            continue

        # (2) Start of a brand-new known field?
        if line.startswith("Measurement") and not line.startswith("Measuring"):
            remainder = line[len("Measurement"):].strip()
            ambiguous_buffer = [remainder] if remainder else []
            active_field, active_fragments = None, []
            continue
        if line.startswith("Choice of data or"):
            remainder = line[len("Choice of data or"):].strip()
            start_field("measurement_method", remainder, [])
            continue
        if line.startswith("Description"):
            remainder = line[len("Description"):].lstrip(": ").strip()
            start_field("full_description", remainder, [])
            continue

        matched_new_field = False
        for name, fragments in _LABEL_FRAGMENTS.items():
            if line.startswith(fragments[0]):
                remainder = line[len(fragments[0]):].strip()
                start_field(name, remainder, fragments[1:])
                matched_new_field = True
                break
        if matched_new_field:
            continue

        # (3) Plain value-continuation line.
        append_active(line)

    return {k: " ".join(v).strip() for k, v in values.items()}


def _classify_timing(section_ref: str, measurement_frequency_note: str) -> str:
    if section_ref == _SECTION_NOT_MONITORED:
        return "ex_ante"
    # section_ref == _SECTION_MONITORED
    note = measurement_frequency_note or ""
    if _EX_ANTE_ALTERNATIVE_RE.search(note) and _PERIODIC_CADENCE_RE.search(note):
        return "both"
    return "monitoring"


def extract_rech_parameters(pdf_path: str, first_page: int = 50, last_page: int = 74) -> list[dict[str, Any]]:
    """
    Extracts every "Parameter ID" block from RECH v5.0's §14.2/§14.3 pages
    (default range confirmed 03.08.2026 — 26 parameters, ICS 1 through
    ICS 26, pages 50-74 of the ingested PDF).

    Returns a list of dicts shaped for methodology_parameters (minus
    methodology_version_id, added by the caller):

      {"parameter_id": "ICS 24", "key": ..., "description": ...,
       "unit": ..., "purpose": ..., "timing_classification": ...,
       "measurement_frequency_note": ..., "measurement_method": ...,
       "source_of_data": ..., "responsible_entity": ...,
       "qa_qc_procedures": ..., "section_ref": "14.3", "page_ref": "73"}

    Every row carries extraction_method (added by the caller at insert
    time, always 'llm_extracted' from this function — never 'manual',
    never 'verified' without the user's explicit say-so).

    Raises RechParameterExtractionError if no "Parameter ID" blocks are
    found at all in the given range.
    """
    text = _extract_pages_with_markers(pdf_path, first_page, last_page)
    raw_blocks = _split_into_parameter_blocks(text)

    section_boundary_offset = None
    m = re.search(rf"{re.escape(_SECTION_MONITORED)}\s*\|\s*Data and parameters monitored", text)
    if m:
        section_boundary_offset = m.start()

    results = []
    for parameter_id, page_ref, block_text in raw_blocks:
        fields = _extract_fields(block_text)

        # section_ref: which side of the §14.3 heading this block's own
        # "Parameter ID" marker fell on. Recomputed from the ORIGINAL
        # (unsplit) text's offsets rather than assumed from ICS numbering,
        # since numbering is a naming convention, not a structural fact.
        block_start_offset = text.find(f"Parameter ID {parameter_id}")
        section_ref = (
            _SECTION_MONITORED
            if section_boundary_offset is not None and block_start_offset > section_boundary_offset
            else _SECTION_NOT_MONITORED
        )

        timing = _classify_timing(section_ref, fields.get("measurement_frequency_note", ""))

        results.append({
            "parameter_id": parameter_id,
            "key": fields.get("key_label"),
            "description": fields.get("full_description") or fields.get("key_label"),
            "unit": fields.get("unit"),
            "purpose": fields.get("purpose"),
            "timing_classification": timing,
            "measurement_frequency_note": fields.get("measurement_frequency_note"),
            "measurement_method": fields.get("measurement_method"),
            "source_of_data": fields.get("source_of_data"),
            "responsible_entity": fields.get("responsible_entity"),
            "qa_qc_procedures": fields.get("qa_qc_procedures"),
            "section_ref": section_ref,
            "page_ref": page_ref,
        })

    if not results:
        raise RechParameterExtractionError("Parsed the page range but extracted zero parameters")
    return results


def store_rech_parameters(methodology_version_id: int, params: list[dict[str, Any]]) -> int:
    """
    Writes extract_rech_parameters()'s output to methodology_parameters.
    Idempotent: clears any previously stored parameters for this version
    first (re-extraction after a parser fix must not duplicate rows).

    Every row is inserted with extraction_method='llm_extracted' and
    verified_by/verified_at left NULL — nothing here is ever written as
    'manual' or pre-verified. Confirming a parameter is a separate,
    explicit step the user takes later, not something this function does
    on its behalf.
    """
    from carbongpt.repository.db import get_cursor

    with get_cursor() as cur:
        cur.execute("DELETE FROM methodology_parameters WHERE methodology_version_id = %s",
                    (methodology_version_id,))
        for p in params:
            cur.execute(
                """INSERT INTO methodology_parameters
                       (methodology_version_id, parameter_id, key, description, unit, purpose,
                        timing_classification, measurement_frequency_note, measurement_method,
                        source_of_data, responsible_entity, qa_qc_procedures, section_ref, page_ref,
                        extraction_method)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'llm_extracted')""",
                (methodology_version_id, p["parameter_id"], p["key"], p["description"], p["unit"],
                 p["purpose"], p["timing_classification"], p["measurement_frequency_note"],
                 p["measurement_method"], p["source_of_data"], p["responsible_entity"],
                 p["qa_qc_procedures"], p["section_ref"], p["page_ref"]),
            )
    return len(params)
