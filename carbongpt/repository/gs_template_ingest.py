"""
gs_template_ingest.py — Ingestion of Gold Standard's official document
templates (docs/SPEC-05.md, T2).

Same contract as gs_ingest.py (SPEC-01): parsing isolated into pure
functions, testable on saved HTML fixtures; idempotent; raises explicitly
rather than degrading silently if the page structure changes.

Deliberately a SEPARATE module from gs_ingest.py rather than an extension
of it: template pages (t-prereview-*, t-perfcert-*) use a different, more
fragile REVISION HISTORY markup than methodology pages. Confirmed while
writing this module (03.08.2026) — every early-version <tr> on a template
page is unclosed (no </tr>), which Python's stdlib 'html.parser' (used by
gs_ingest.py, works fine there) parses as literal nesting: a naive
find_all('td') on one row silently accumulates every subsequent row's
cells too. BeautifulSoup with the 'lxml' parser closes each <tr> at the
next <tr>, like a browser would — confirmed correct against the live
VPA-DD page (17 clean 3-cell rows). Use 'lxml' here; gs_ingest.py is left
untouched since its own pages don't have this defect.

The current version's download link is NOT in a wp-block-file embed (that
was specific to methodology pages) — it sits in a `div.share-content`
block near the top of the page, before the REVISION HISTORY table, as a
`<a class="share-icon ...">` whose href ends in .docx/.doc and contains
the current version's own filename pattern. Confirmed for VPA-DD v3.0.
"""

import hashlib
import logging
import re
import time
from datetime import date
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

REPO_DIR = Path(__file__).resolve().parent.parent.parent / "document_repository"
REPO_DIR.mkdir(parents=True, exist_ok=True)

_USER_AGENT = (
    "CarbonGPT-Ingest/1.0 (+regulatory corpus ingestion; "
    "contact via repository issue tracker)"
)
_TIMEOUT = 30
_MAX_RETRIES = 4


class TemplateIngestError(Exception):
    """Raised when a template page or file cannot be fetched, or its
    structure cannot be parsed with confidence. Never swallowed."""


# ---------------------------------------------------------------------------
# HTTP with retry / backoff — same pattern as gs_ingest.py
# ---------------------------------------------------------------------------


def _http_get(url: str, timeout: int = _TIMEOUT, max_retries: int = _MAX_RETRIES) -> requests.Response:
    headers = {"User-Agent": _USER_AGENT}
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                delay = 2**attempt
                logger.warning("Fetch failed for %s (attempt %d/%d): %s — retrying in %ds",
                               url, attempt + 1, max_retries, exc, delay)
                time.sleep(delay)
    raise TemplateIngestError(f"Could not fetch {url} after {max_retries} attempts: {last_exc}")


def fetch_template_page(url: str) -> str:
    """Fetch a template page from globalgoals.goldstandard.org. Returns raw HTML."""
    return _http_get(url).text


# ---------------------------------------------------------------------------
# Parsing — pure functions, testable on saved fixtures
# ---------------------------------------------------------------------------


def _parse_gs_date(text: str) -> date:
    """Same D.MM.YYYY / DD.MM.YYYY format as gs_ingest.py's methodology pages."""
    text = text.strip()
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", text)
    if not m:
        raise TemplateIngestError(f"Unrecognised date format: {text!r}")
    day, month, year = (int(g) for g in m.groups())
    return date(year, month, day)


def _find_current_document_url(soup: BeautifulSoup, version: str) -> str | None:
    """The current version's file isn't linked from the revision-history
    table (that row has no <a href>, same as gs_ingest.py's methodology
    pages) — it's a separate download link near the top of the page. Match
    by version number appearing in the href, restricted to .docx/.doc, and
    prefer the one NOT containing 'Guide' or 'TC' (track changes)."""
    version_token = re.sub(r"[.\s]", "", version)  # "3.0" -> "30"
    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not (href.lower().endswith(".docx") or href.lower().endswith(".doc")):
            continue
        href_token = re.sub(r"[.\s]", "", href)
        if re.search(rf"[Vv]{re.escape(version_token)}(?![0-9])", href_token):
            candidates.append(href)
    # Prefer the plain template over its "Guide" or "TC" (track-changes) siblings.
    plain = [h for h in candidates if "guide" not in h.lower() and "_tc" not in h.lower()
             and "-tc-" not in h.lower()]
    if plain:
        return plain[0]
    return candidates[0] if candidates else None


def parse_template_revision_history(html: str, version_for_current_url: str | None = None) -> list[dict[str, Any]]:
    """
    Parse the REVISION HISTORY table of a template page. Returns a list of:

      {"version": "3.0", "released_date": date(...), "document_name": str,
       "download_url": str | None, "is_current": bool}

    Raises TemplateIngestError if the REVISION HISTORY block cannot be
    found, or if it parses to zero versions — never returns an empty list
    silently in that case (same discipline as gs_ingest.py).
    """
    soup = BeautifulSoup(html, "lxml")

    summary = soup.find("summary", string=re.compile(r"REVISION HISTORY", re.I))
    if summary is None:
        raise TemplateIngestError("REVISION HISTORY block not found — page structure may have changed")
    table = summary.find_next("table")
    if table is None:
        raise TemplateIngestError("REVISION HISTORY table not found under its <summary>")

    entries: list[dict[str, Any]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True)
        date_text = cells[1].get_text(strip=True)
        if not label or not date_text:
            continue
        try:
            released = _parse_gs_date(date_text)
        except TemplateIngestError:
            logger.warning("Skipping revision-history row with unparseable date: %r", date_text)
            continue

        # Only rows whose label is a bare version number ("v.3.0") are real
        # template versions — "TRACK CHANGES", "v.X Guide" etc. are siblings
        # of the same version, not versions of their own (SPEC-05 scope: the
        # template itself, not its guide/track-changes companions).
        version_match = re.match(r"^v\.?\s*(\d+(?:\.\d+)*)$", label.lower())
        if not version_match:
            continue

        doc_cell = cells[2] if len(cells) > 2 else None
        link = doc_cell.find("a") if doc_cell else None
        download_url = link["href"].strip() if link else None
        document_name = (link.get_text(strip=True) if link else
                          (doc_cell.get_text(strip=True) if doc_cell else ""))
        is_current = download_url is None and "current document" in document_name.lower()

        if is_current:
            download_url = _find_current_document_url(soup, version_match.group(1))
            if download_url is None:
                logger.warning("Current version v%s has no discoverable download link on the page",
                                version_match.group(1))

        entries.append({
            "version": version_match.group(1),
            "released_date": released,
            "document_name": document_name,
            "download_url": download_url,
            "is_current": is_current,
        })

    if not entries:
        raise TemplateIngestError("REVISION HISTORY table parsed but yielded zero versions — "
                                   "structure likely changed, refusing to ingest an empty result")
    return entries


# ---------------------------------------------------------------------------
# Download — same dedup-by-sha256 pattern as gs_ingest.py
# ---------------------------------------------------------------------------


def download_document(url: str, filename_hint: str) -> tuple[str, str, int]:
    """
    Download a document, deduplicated by sha256 against files already on
    disk in document_repository/. Idempotent: if a file with the same
    sha256 already exists locally, nothing is re-downloaded.

    Returns (local_path, sha256, file_size_bytes).
    """
    resp = _http_get(url)
    content = resp.content
    sha256 = hashlib.sha256(content).hexdigest()

    for existing in REPO_DIR.glob(f"{sha256[:16]}_*"):
        return str(existing), sha256, existing.stat().st_size

    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename_hint).strip("_") or "template.docx"
    local_path = REPO_DIR / f"{sha256[:16]}_{safe_name}"
    if not local_path.exists():
        local_path.write_bytes(content)
    return str(local_path), sha256, len(content)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def ingest_template(url: str, standard: str, doc_type: str, name: str | None = None) -> dict[str, Any]:
    """
    Fetch a template page, parse its revision history, download every
    version's file, write document_templates / document_template_versions.
    Idempotent — re-running does not duplicate rows (UNIQUE constraints on
    (standard, doc_type) and (template_id, version)) or re-download
    unchanged files (sha256 dedup).

    Does NOT parse .docx structure into template_fields — that is T3
    (template_docx_parser.parse_template_structure), called separately per
    version once downloaded.

    Returns a summary dict for logging/reporting.
    """
    html = fetch_template_page(url)
    history = parse_template_revision_history(html)

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO document_templates (standard, doc_type, name, source_url, last_checked_at)
               VALUES (%s, %s, %s, %s, NOW())
               ON CONFLICT (standard, doc_type) DO UPDATE SET
                   name = COALESCE(EXCLUDED.name, document_templates.name),
                   source_url = EXCLUDED.source_url, last_checked_at = NOW()
               RETURNING id""",
            (standard, doc_type, name, url),
        )
        template_id = cur.fetchone()["id"]

    sorted_versions = sorted(history, key=lambda e: e["released_date"])
    versions_ingested = []

    for i, entry in enumerate(sorted_versions):
        effective_until = sorted_versions[i + 1]["released_date"] if i + 1 < len(sorted_versions) else None

        local_path = sha256 = None
        if entry["download_url"]:
            # Prefer the URL's own filename (carries the real extension) over
            # document_name — for the current version, document_name is a
            # description ("CURRENT DOCUMENT- VPA Design Document"), not a
            # filename, and would otherwise strip the .docx/.doc extension.
            url_filename = entry["download_url"].rsplit("/", 1)[-1]
            filename_hint = url_filename if "." in url_filename else (
                entry["document_name"] or f"{doc_type}_v{entry['version']}.docx"
            )
            try:
                local_path, sha256, _size = download_document(entry["download_url"], filename_hint)
            except TemplateIngestError as exc:
                logger.warning("Could not download %s v%s: %s", doc_type, entry["version"], exc)
        else:
            logger.warning("Version %s of %s/%s has no download link — metadata recorded, no local file",
                            entry["version"], standard, doc_type)

        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO document_template_versions
                       (template_id, version, released_date, effective_from, effective_until,
                        is_current, document_name, download_url, local_path, sha256, ingested_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                   ON CONFLICT (template_id, version) DO UPDATE SET
                       released_date = EXCLUDED.released_date,
                       effective_from = EXCLUDED.effective_from,
                       effective_until = EXCLUDED.effective_until,
                       is_current = EXCLUDED.is_current,
                       document_name = EXCLUDED.document_name,
                       download_url = EXCLUDED.download_url,
                       local_path = COALESCE(EXCLUDED.local_path, document_template_versions.local_path),
                       sha256 = COALESCE(EXCLUDED.sha256, document_template_versions.sha256),
                       ingested_at = NOW()""",
                (template_id, entry["version"], entry["released_date"], entry["released_date"],
                 effective_until, entry["is_current"], entry["document_name"], entry["download_url"],
                 local_path, sha256),
            )
        versions_ingested.append(entry["version"])

    return {
        "standard": standard, "doc_type": doc_type,
        "template_id": template_id, "versions_ingested": versions_ingested,
    }


# ---------------------------------------------------------------------------
# Structural analysis orchestration (T3 module = template_docx_parser.py;
# this is the glue that writes its output to template_fields and stamps
# parsed_at, kept here rather than in the parser so that module stays a
# pure, fixture-testable function with no database dependency)
# ---------------------------------------------------------------------------


def analyze_template_version(template_version_id: int) -> dict[str, Any]:
    """
    Loads document_template_versions.local_path for `template_version_id`,
    runs template_docx_parser.parse_template_structure() on it, and writes
    the result to template_fields. Idempotent: clears any previous fields
    for this version first (re-analysis after a parser fix must not
    duplicate rows), same spirit as parameter_resolver.py's
    DELETE-then-INSERT for project_parameter_alternatives.

    Raises TemplateIngestError if the version has no local_path (not
    downloaded yet — analysis is not a substitute for T2's ingestion).
    """
    from carbongpt.repository.template_docx_parser import parse_template_structure

    with get_cursor() as cur:
        cur.execute(
            "SELECT local_path, version FROM document_template_versions WHERE id = %s",
            (template_version_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise TemplateIngestError(f"No document_template_versions row with id={template_version_id}")
    if not row["local_path"]:
        raise TemplateIngestError(
            f"document_template_versions id={template_version_id} (v{row['version']}) has no local_path — "
            "not downloaded yet, run ingest_template() first"
        )

    fields = parse_template_structure(row["local_path"])

    with get_cursor() as cur:
        cur.execute("DELETE FROM template_fields WHERE template_version_id = %s", (template_version_id,))
        for f in fields:
            import json as _json
            cur.execute(
                """INSERT INTO template_fields
                       (template_version_id, field_key, parent_section, title, field_type, position)
                   VALUES (%s, %s, %s, %s, %s, %s::jsonb)""",
                (template_version_id, f["field_key"], f["parent_section"], f["title"],
                 f["field_type"], _json.dumps(f["position"])),
            )
        cur.execute(
            "UPDATE document_template_versions SET parsed_at = NOW() WHERE id = %s",
            (template_version_id,),
        )

    return {"template_version_id": template_version_id, "version": row["version"], "fields_extracted": len(fields)}


# ---------------------------------------------------------------------------
# Change detection (T9 — not implemented this session, stub raises)
# ---------------------------------------------------------------------------


def check_for_template_updates(url: str, standard: str, doc_type: str) -> list[dict[str, Any]]:
    """Same spirit as gs_ingest.check_for_updates() — re-parses `url`,
    returns versions not yet in document_template_versions, downloads
    nothing. Implemented now (cheap reuse of parse_template_revision_history)
    even though full T9 tooling (scheduling, endpoints) is next session."""
    history = parse_template_revision_history(fetch_template_page(url))

    with get_cursor() as cur:
        cur.execute(
            """SELECT dtv.version FROM document_template_versions dtv
               JOIN document_templates dt ON dt.id = dtv.template_id
               WHERE dt.standard = %s AND dt.doc_type = %s""",
            (standard, doc_type),
        )
        known_versions = {row["version"] for row in cur.fetchall()}

    return [
        {"version": e["version"], "released_date": e["released_date"], "document_name": e["document_name"]}
        for e in history if e["version"] not in known_versions
    ]
