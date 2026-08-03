"""
gs_crosscutting_ingest.py — Ingestion des exigences transverses Gold
Standard (docs/SPEC-06.md, T2) : 101, 102, 103, 104, 118, 119, 201.

Réutilise `gs_template_ingest.py` (SPEC-05 T2) telle quelle plutôt que
`gs_ingest.py` (SPEC-01) : ces pages de « core documents » partagent le
défaut de balisage `<tr>` non fermé des pages de template — confirmé en
comparant `html.parser` (corrompt le comptage de cellules) et `lxml`
(correct), même méthode que pour le VPA-DD (SPEC-05 T0/T2). Rien n'est
dupliqué : `fetch_template_page`, `parse_template_revision_history` et
`download_document` sont importées directement.

Un document sur les sept a une structure différente : la page 118
(« Requirements for selection of Monitoring Indicators in the SDG Impact
Tool ») n'a aucun bloc REVISION HISTORY du tout — vérifié le 03.08.2026,
elle n'a publié qu'une seule version (v1.0, 18.10.2025) depuis sa
création, donc pas encore d'historique à afficher. `_parse_single_version`
gère ce cas séparément plutôt que de forcer le motif REVISION HISTORY sur
une page qui ne l'a pas.
"""

import logging
import re
from datetime import date
from typing import Any

from bs4 import BeautifulSoup

from carbongpt.repository.db import get_cursor
from carbongpt.repository.gs_template_ingest import (
    TemplateIngestError,
    _parse_gs_date,
    download_document,
    fetch_template_page,
    parse_template_revision_history,
)

logger = logging.getLogger(__name__)

# Vérifiés en ligne le 03.08.2026 (mêmes pages que le rapport de
# reconnaissance de cette session) — voir docs/SPEC-06.md Constat de départ.
CROSSCUTTING_DOCUMENTS: list[dict[str, str]] = [
    {"code": "101", "name": "Principles & Requirements",
     "url": "https://globalgoals.goldstandard.org/101-par-principles-requirements/"},
    {"code": "102", "name": "Stakeholder Consultation and Engagement Requirements",
     "url": "https://globalgoals.goldstandard.org/102-par-stakeholder-consultation-requirements/"},
    {"code": "103", "name": "Safeguarding Principles & Requirements",
     "url": "https://globalgoals.goldstandard.org/103-par-safeguarding-principles-requirements/"},
    {"code": "104", "name": "Gender Equality Requirements & Guidelines",
     "url": "https://globalgoals.goldstandard.org/104-par-gender-equality-requirements-and-guidelines/"},
    {"code": "118", "name": "Requirements for selection of Monitoring Indicators in the SDG Impact Tool",
     "url": "https://globalgoals.goldstandard.org/118_par_requirements-for-monitoring-indicator-selection/"},
    {"code": "119", "name": "Requirements for Paris Agreement Alignment",
     "url": "https://globalgoals.goldstandard.org/119_paa_pr_100-01-requirements-paris-agreement-alignment/"},
    {"code": "201", "name": "Community Services Activity Requirements",
     "url": "https://globalgoals.goldstandard.org/201-ar-community-services-activity-requirements/"},
]


def _parse_single_version(html: str) -> list[dict[str, Any]]:
    """Repli pour une page sans bloc REVISION HISTORY (confirmé : la page
    118 uniquement, à ce jour). Lit le lien de téléchargement du bloc
    `div.share-content` (« Download DOC ») pour l'URL et le numéro de
    version (tiré du nom de fichier, motif `_V<n>_`), et la date publiée
    affichée près du titre de la page (motif DD.MM.YYYY)."""
    soup = BeautifulSoup(html, "lxml")

    download_url = None
    for div in soup.find_all("div", class_="share-content"):
        label = div.find("div", class_="single-meta-info")
        if label and "download doc" in label.get_text(strip=True).lower():
            a = div.find("a", href=True)
            if a:
                download_url = a["href"]
                break
    if download_url is None:
        raise TemplateIngestError(
            "No REVISION HISTORY block and no 'Download DOC' link either — page structure unrecognised"
        )

    version_match = re.search(r"_[Vv](\d+(?:\.\d+)*)_", download_url)
    version = version_match.group(1) if version_match else "1.0"

    text = soup.get_text(" ", strip=True)
    date_match = re.search(r"\b(\d{1,2}\.\d{1,2}\.\d{4})\b", text)
    released_date = _parse_gs_date(date_match.group(1)) if date_match else None
    if released_date is None:
        logger.warning("Could not find a release date on the page for %s — recording without one", download_url)

    return [{
        "version": version,
        "released_date": released_date,
        "document_name": download_url.rsplit("/", 1)[-1],
        "download_url": download_url,
        "is_current": True,
    }]


def ingest_crosscutting_document(code: str, name: str, url: str) -> dict[str, Any]:
    """
    Fetches one cross-cutting document's page, parses its version history
    (REVISION HISTORY table, or the single-version fallback for pages that
    don't have one), downloads every version's file, writes
    crosscutting_requirements. Idempotent — same contract as
    gs_template_ingest.ingest_template().
    """
    html = fetch_template_page(url)
    try:
        history = parse_template_revision_history(html)
    except TemplateIngestError:
        history = _parse_single_version(html)

    sorted_versions = sorted(history, key=lambda e: e["released_date"] or date.min)
    versions_ingested = []

    for i, entry in enumerate(sorted_versions):
        effective_until = sorted_versions[i + 1]["released_date"] if i + 1 < len(sorted_versions) else None

        local_path = sha256 = None
        if entry["download_url"]:
            url_filename = entry["download_url"].rsplit("/", 1)[-1]
            filename_hint = url_filename if "." in url_filename else (entry["document_name"] or f"{code}_v{entry['version']}")
            try:
                local_path, sha256, _size = download_document(entry["download_url"], filename_hint)
            except TemplateIngestError as exc:
                logger.warning("Could not download %s v%s: %s", code, entry["version"], exc)
        else:
            logger.warning("Version %s of %s has no download link — metadata recorded, no local file",
                            entry["version"], code)

        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO crosscutting_requirements
                       (standard, code, name, version, released_date, effective_from, effective_until,
                        is_current, document_name, source_url, download_url, local_path, sha256, ingested_at)
                   VALUES ('GoldStandard', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                   ON CONFLICT (code, version) DO UPDATE SET
                       name = EXCLUDED.name, released_date = EXCLUDED.released_date,
                       effective_from = EXCLUDED.effective_from, effective_until = EXCLUDED.effective_until,
                       is_current = EXCLUDED.is_current, document_name = EXCLUDED.document_name,
                       source_url = EXCLUDED.source_url, download_url = EXCLUDED.download_url,
                       local_path = COALESCE(EXCLUDED.local_path, crosscutting_requirements.local_path),
                       sha256 = COALESCE(EXCLUDED.sha256, crosscutting_requirements.sha256),
                       ingested_at = NOW()""",
                (code, name, entry["version"], entry["released_date"], entry["released_date"],
                 effective_until, entry["is_current"], entry["document_name"], url,
                 entry["download_url"], local_path, sha256),
            )
        versions_ingested.append(entry["version"])

    return {"code": code, "versions_ingested": versions_ingested}


def ingest_all_crosscutting_documents() -> list[dict[str, Any]]:
    """Ingests all 7 documents listed in CROSSCUTTING_DOCUMENTS. Does not
    stop on the first failure — one document's page structure breaking
    shouldn't block the other six; failures are logged and included in
    the returned summary rather than silently skipped."""
    results = []
    for doc in CROSSCUTTING_DOCUMENTS:
        try:
            results.append(ingest_crosscutting_document(doc["code"], doc["name"], doc["url"]))
        except TemplateIngestError as exc:
            logger.error("Failed to ingest crosscutting document %s: %s", doc["code"], exc)
            results.append({"code": doc["code"], "error": str(exc)})
    return results
