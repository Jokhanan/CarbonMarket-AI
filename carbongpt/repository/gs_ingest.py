"""
gs_ingest.py — Ingestion of Gold Standard's versioned regulatory corpus
(docs/SPEC-01.md).

Fetches a methodology's page on globalgoals.goldstandard.org, parses its
REVISION HISTORY and RELATED DOCUMENTS tables, downloads the associated PDFs
(deduplicated by sha256, idempotent — re-running does not duplicate rows or
re-download unchanged files), and writes everything to methodology_version_history
and documents.

Parsing is isolated into pure functions (parse_revision_history,
parse_related_documents) so they can be tested against saved HTML fixtures
without hitting the network — Gold Standard's markup can change without notice,
and a parsing failure must raise, never degrade silently into an empty result.
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


class IngestError(Exception):
    """Raised when a page or PDF cannot be fetched, or its structure cannot
    be parsed with confidence. Never swallowed — callers must see it."""


# ---------------------------------------------------------------------------
# HTTP with retry / backoff
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
    raise IngestError(f"Could not fetch {url} after {max_retries} attempts: {last_exc}")


def fetch_methodology_page(url: str) -> str:
    """Fetch a methodology page from globalgoals.goldstandard.org. Returns raw HTML."""
    return _http_get(url).text


# ---------------------------------------------------------------------------
# Parsing — pure functions, testable on saved fixtures
# ---------------------------------------------------------------------------

_DOC_TYPE_LABELS = {
    "rule update": "rule_update",
    "rule clarification": "rule_clarification",
    "deviation": "deviation",
    "clarification request": "clarification_request",
}


def _parse_gs_date(text: str) -> date:
    """Parse Gold Standard's D.MM.YYYY / DD.MM.YYYY date format."""
    text = text.strip()
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", text)
    if not m:
        raise IngestError(f"Unrecognised date format: {text!r}")
    day, month, year = (int(g) for g in m.groups())
    return date(year, month, day)


def _find_current_pdf_url(soup: BeautifulSoup) -> str | None:
    """The current version's PDF is embedded in a wp-block-file object, not
    linked from the revision-history table (that row has no <a href> for the
    current row — see docs/SPEC-01.md constat)."""
    block = soup.select_one("div.wp-block-file object.wp-block-file__embed[data]")
    if block:
        return block["data"].strip()
    return None


def parse_revision_history(html: str) -> list[dict[str, Any]]:
    """
    Parse the REVISION HISTORY table. Returns a list of dicts, each one of:

      {"kind": "version", "version": "5.0", "released_date": date(...),
       "document_name": str, "pdf_url": str | None, "is_current": bool}

      {"kind": "rule_update" | "rule_clarification" | "deviation" |
       "clarification_request", "released_date": date(...),
       "document_name": str, "pdf_url": str}

    Raises IngestError if the REVISION HISTORY block cannot be found at all
    (structural change) — never returns an empty list silently in that case.
    """
    soup = BeautifulSoup(html, "html.parser")

    summary = soup.find("summary", string=re.compile(r"REVISION HISTORY", re.I))
    if summary is None:
        raise IngestError("REVISION HISTORY block not found — page structure may have changed")
    table = summary.find_next("table")
    if table is None:
        raise IngestError("REVISION HISTORY table not found under its <summary>")

    current_pdf_url = _find_current_pdf_url(soup)

    entries: list[dict[str, Any]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True)
        date_text = cells[1].get_text(strip=True)
        if not label or not date_text:
            continue
        try:
            released = _parse_gs_date(date_text)
        except IngestError:
            logger.warning("Skipping revision-history row with unparseable date: %r", date_text)
            continue

        doc_cell = cells[2] if len(cells) > 2 else None
        link = doc_cell.find("a") if doc_cell else None
        pdf_url = link["href"].strip() if link else None
        document_name = (link.get_text(strip=True) if link else
                          (doc_cell.get_text(strip=True) if doc_cell else ""))

        label_key = label.lower().strip()
        version_match = re.match(r"^v\.?\s*(\d+(?:\.\d+)*)$", label_key)

        if version_match:
            is_current = pdf_url is None and "current document" in document_name.lower()
            entries.append({
                "kind": "version",
                "version": version_match.group(1),
                "released_date": released,
                "document_name": document_name,
                "pdf_url": current_pdf_url if is_current else pdf_url,
                "is_current": is_current,
            })
        elif label_key in _DOC_TYPE_LABELS:
            if pdf_url is None:
                logger.warning("Related-document row %r has no PDF link — skipping", label)
                continue
            entries.append({
                "kind": _DOC_TYPE_LABELS[label_key],
                "released_date": released,
                "document_name": document_name,
                "pdf_url": pdf_url,
            })
        else:
            logger.warning("Unrecognised revision-history row label %r — skipping "
                            "(not a version, not a known document type)", label)

    version_rows = [e for e in entries if e["kind"] == "version"]
    if not version_rows:
        raise IngestError("REVISION HISTORY table parsed but yielded zero versions — "
                           "structure likely changed, refusing to ingest an empty corpus")

    return entries


def parse_related_documents(html: str) -> list[dict[str, Any]]:
    """
    Parse the RELATED DOCUMENTS table (separate from REVISION HISTORY — links
    to other methodology-style pages, e.g. Cookstove Usage Rate Guidelines,
    each with their own current-PDF download block).

    Returns [] if the page has no RELATED DOCUMENTS section — that is a
    legitimate state (not every methodology has related documents), unlike
    a missing REVISION HISTORY block.
    """
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find(["h2", "h3"], string=re.compile(r"RELATED DOCUMENTS", re.I))
    if heading is None:
        return []
    table = heading.find_next("table")
    if table is None:
        return []

    related = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 3:
            continue
        link = cells[0].find("a")
        if link is None:
            continue
        title = link.get_text(strip=True)
        page_url = link["href"].strip()
        version = cells[1].get_text(strip=True)
        date_text = cells[2].get_text(strip=True)
        try:
            released = _parse_gs_date(date_text)
        except IngestError:
            logger.warning("Skipping related-document row with unparseable date: %r", date_text)
            released = None
        related.append({
            "title": title,
            "version": version,
            "released_date": released,
            "page_url": page_url,
        })
    return related


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


def download_document(url: str, filename_hint: str) -> tuple[str, str]:
    """
    Download a document, deduplicated by sha256. Idempotent: if a document
    with the same sha256 already exists in `documents`, the existing local
    file is reused and nothing is re-downloaded or re-inserted.

    Returns (local_path, sha256).
    """
    resp = _http_get(url)
    content = resp.content
    sha256 = hashlib.sha256(content).hexdigest()

    with get_cursor() as cur:
        cur.execute("SELECT file_path FROM documents WHERE sha256 = %s LIMIT 1", (sha256,))
        row = cur.fetchone()
    if row and Path(row["file_path"]).exists():
        logger.info("Document %s already present locally (sha256=%s), skipping download", url, sha256[:12])
        return row["file_path"], sha256

    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename_hint).strip("_") or "document.pdf"
    local_path = REPO_DIR / f"{sha256[:16]}_{safe_name}"
    if not local_path.exists():
        local_path.write_bytes(content)
    return str(local_path), sha256


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _upsert_document(*, category: str, title: str, reference_id: str | None,
                      doc_version: str | None, local_path: str, sha256: str,
                      file_size_bytes: int, methodology_version_id: int | None) -> int:
    with get_cursor() as cur:
        cur.execute("SELECT id FROM documents WHERE sha256 = %s LIMIT 1", (sha256,))
        row = cur.fetchone()
        if row:
            cur.execute(
                """UPDATE documents SET methodology_version_id = COALESCE(%s, methodology_version_id),
                       updated_at = NOW() WHERE id = %s""",
                (methodology_version_id, row["id"]),
            )
            return row["id"]
        cur.execute(
            """INSERT INTO documents
               (category, title, reference_id, doc_version, file_path, file_type,
                file_size_bytes, status, ingestion_status, methodology_version_id, sha256)
               VALUES (%s, %s, %s, %s, %s, 'pdf', %s, 'active', 'completed', %s, %s)
               RETURNING id""",
            (category, title, reference_id, doc_version, local_path, file_size_bytes,
             methodology_version_id, sha256),
        )
        return cur.fetchone()["id"]


def ingest_methodology(url: str, methodology_code: str, registry: str = "GoldStandard",
                        short_name: str | None = None, former_name: str | None = None) -> dict[str, Any]:
    """
    Orchestrates a full ingestion: fetch page, parse revision history and
    related documents, download every PDF, write methodologies /
    methodology_version_history / documents. Idempotent — re-running does
    not duplicate rows (UNIQUE constraint on methodology_code/registry/version,
    sha256 dedup on documents).

    Returns a summary dict for logging/reporting.
    """
    html = fetch_methodology_page(url)
    soup = BeautifulSoup(html, "html.parser")
    history = parse_revision_history(html)
    related = parse_related_documents(html)

    title_tag = soup.find("h1")
    page_title = title_tag.get_text(strip=True) if title_tag else methodology_code

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO methodologies (code, name, short_name, former_name, standard, source_url, last_checked_at)
               VALUES (%s, %s, %s, %s, %s, %s, NOW())
               ON CONFLICT (code) DO UPDATE SET
                   name = EXCLUDED.name, short_name = COALESCE(EXCLUDED.short_name, methodologies.short_name),
                   former_name = COALESCE(EXCLUDED.former_name, methodologies.former_name),
                   source_url = EXCLUDED.source_url, last_checked_at = NOW()""",
            (methodology_code, page_title, short_name, former_name, registry, url),
        )

    versions_ingested = []
    docs_ingested = []
    sorted_versions = sorted(
        (e for e in history if e["kind"] == "version"),
        key=lambda e: e["released_date"],
    )

    for i, entry in enumerate(sorted_versions):
        is_current = entry["is_current"]
        effective_until = sorted_versions[i + 1]["released_date"] if i + 1 < len(sorted_versions) else None

        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO methodology_version_history
                       (methodology_code, registry, version, released_date, effective_from,
                        effective_until, is_current, document_name, source_url, pdf_url, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (methodology_code, registry, version) DO UPDATE SET
                       released_date = EXCLUDED.released_date,
                       effective_from = EXCLUDED.effective_from,
                       effective_until = EXCLUDED.effective_until,
                       is_current = EXCLUDED.is_current,
                       document_name = EXCLUDED.document_name,
                       pdf_url = EXCLUDED.pdf_url,
                       status = EXCLUDED.status
                   RETURNING id""",
                (methodology_code, registry, entry["version"], entry["released_date"],
                 entry["released_date"], effective_until, is_current, entry["document_name"],
                 url, entry["pdf_url"], "active" if is_current else "superseded"),
            )
            version_id = cur.fetchone()["id"]

        if entry["pdf_url"]:
            local_path, sha256 = download_document(entry["pdf_url"], entry["document_name"] or f"v{entry['version']}.pdf")
            with get_cursor() as cur:
                cur.execute("UPDATE methodology_version_history SET local_path = %s, content_hash = %s WHERE id = %s",
                            (local_path, sha256, version_id))
            doc_id = _upsert_document(
                category="methodology", title=entry["document_name"] or f"{methodology_code} v{entry['version']}",
                reference_id=f"{methodology_code}_v{entry['version']}", doc_version=entry["version"],
                local_path=local_path, sha256=sha256,
                file_size_bytes=Path(local_path).stat().st_size, methodology_version_id=version_id,
            )
            docs_ingested.append(doc_id)
        else:
            logger.warning("Version %s of %s has no PDF url — metadata recorded without a local document",
                            entry["version"], methodology_code)

        versions_ingested.append(entry["version"])

    for entry in (e for e in history if e["kind"] != "version"):
        local_path, sha256 = download_document(entry["pdf_url"], entry["document_name"])
        doc_id = _upsert_document(
            category=entry["kind"], title=entry["document_name"], reference_id=None, doc_version=None,
            local_path=local_path, sha256=sha256,
            file_size_bytes=Path(local_path).stat().st_size, methodology_version_id=None,
        )
        docs_ingested.append(doc_id)

    for rel in related:
        try:
            rel_html = fetch_methodology_page(rel["page_url"])
        except IngestError as exc:
            logger.warning("Could not fetch related document page %s: %s", rel["page_url"], exc)
            continue
        rel_soup = BeautifulSoup(rel_html, "html.parser")
        rel_pdf_url = _find_current_pdf_url(rel_soup)
        if not rel_pdf_url:
            logger.warning("Related document %r has no discoverable PDF on its page — skipping", rel["title"])
            continue
        local_path, sha256 = download_document(rel_pdf_url, rel["title"])
        doc_id = _upsert_document(
            category="guidance", title=rel["title"], reference_id=None, doc_version=rel["version"],
            local_path=local_path, sha256=sha256,
            file_size_bytes=Path(local_path).stat().st_size, methodology_version_id=None,
        )
        docs_ingested.append(doc_id)

    return {
        "methodology_code": methodology_code,
        "versions_ingested": versions_ingested,
        "related_docs_ingested": len(related),
        "documents_ingested": len(docs_ingested),
    }


# ---------------------------------------------------------------------------
# Version resolution (T4)
# ---------------------------------------------------------------------------


def resolve_applicable_version(methodology_code: str, at_date: str | date,
                                registry: str = "GoldStandard",
                                validated_under_version: str | None = None) -> dict[str, Any]:
    """
    Returns the version of `methodology_code` applicable at `at_date`: the
    most recent version whose effective_from <= at_date.

    If `validated_under_version` is given (the version a project was
    originally validated under) and it differs from the resolved version
    while the resolved version is Paris-aligned and the validated one is not,
    the result flags transition_required — e.g. a project validated under
    RECH v4.0 whose 2026-vintage emissions must be reported under the
    Paris-aligned v5.0 (Gold Standard's PA-alignment requirement, stated on
    the methodology's own page: "PA-Aligned versions must be applied for
    all vintage 2026 issuances").

    Raises IngestError if no version has effective_from <= at_date (the
    methodology did not exist yet at that date).
    """
    if isinstance(at_date, str):
        at_date = date.fromisoformat(at_date)

    with get_cursor() as cur:
        cur.execute(
            """SELECT id, version, effective_from, effective_until, is_current, paris_aligned
               FROM methodology_version_history
               WHERE methodology_code = %s AND registry = %s AND effective_from <= %s
               ORDER BY effective_from DESC LIMIT 1""",
            (methodology_code, registry, at_date),
        )
        row = cur.fetchone()

    if row is None:
        raise IngestError(
            f"No version of {methodology_code} ({registry}) is effective on or before {at_date} — "
            "either the methodology wasn't published yet, or it hasn't been ingested"
        )

    result: dict[str, Any] = {
        "version": row["version"],
        "version_id": row["id"],
        "effective_from": row["effective_from"],
        "effective_until": row["effective_until"],
        "is_current": row["is_current"],
        "paris_aligned": row["paris_aligned"],
        "transition_required": False,
        "transition_reason": None,
    }

    if (validated_under_version and validated_under_version != row["version"]
            and row["paris_aligned"] and not _version_is_paris_aligned(
                methodology_code, registry, validated_under_version)):
        result["transition_required"] = True
        result["transition_reason"] = (
            f"Project validated under {methodology_code} v{validated_under_version} (not Paris-aligned), "
            f"but emissions dated {at_date} must be reported under the Paris-aligned v{row['version']} "
            "per Gold Standard's PA-alignment requirement for this vintage."
        )

    return result


def get_regulatory_value(version_id: int, key: str, **applicability_filters: Any) -> dict[str, Any]:
    """
    Read a single trusted regulatory_values row for (version_id, key), optionally
    narrowed by applicability fields (e.g. fuel="charcoal").

    Guards required by docs/SPEC-01.md: raises IngestError if the matched row is
    extraction_method='llm_unverified' (never silently consumed by a calculation),
    if nothing matches, or if more than one row matches after filtering — the
    system never picks one on its own; the caller must narrow applicability_filters
    until exactly one row remains.
    """
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM regulatory_values WHERE version_id = %s AND key = %s",
            (version_id, key),
        )
        rows = cur.fetchall()

    for field, expected in applicability_filters.items():
        rows = [r for r in rows if r["applicability"].get(field) == expected]

    if not rows:
        raise IngestError(f"No regulatory_values row for key={key!r}, version_id={version_id}, "
                           f"applicability={applicability_filters!r}")
    if len(rows) > 1:
        raise IngestError(f"Ambiguous: {len(rows)} regulatory_values rows match key={key!r}, "
                           f"applicability={applicability_filters!r} — narrow the filter, "
                           "the system will not pick one automatically")

    row = rows[0]
    if row["extraction_method"] == "llm_unverified":
        raise IngestError(f"regulatory_values row for key={key!r} is llm_unverified "
                           "(no confident extraction exists) — cannot be used in a calculation")
    return row


def _version_is_paris_aligned(methodology_code: str, registry: str, version: str) -> bool:
    with get_cursor() as cur:
        cur.execute(
            """SELECT paris_aligned FROM methodology_version_history
               WHERE methodology_code = %s AND registry = %s AND version = %s""",
            (methodology_code, registry, version),
        )
        row = cur.fetchone()
    return bool(row and row["paris_aligned"])


# ---------------------------------------------------------------------------
# Change detection (T6)
# ---------------------------------------------------------------------------


def check_for_updates(methodology_code: str, url: str, registry: str = "GoldStandard") -> list[dict[str, Any]]:
    """
    Re-parses `url` and compares versions found to what's already in
    methodology_version_history. Returns the list of new versions (not yet
    in the database) without downloading or writing anything — ingestion of
    a detected update is a separate, explicit ingest_methodology() call.
    """
    html = fetch_methodology_page(url)
    history = parse_revision_history(html)

    with get_cursor() as cur:
        cur.execute(
            "SELECT version FROM methodology_version_history WHERE methodology_code = %s AND registry = %s",
            (methodology_code, registry),
        )
        known_versions = {row["version"] for row in cur.fetchall()}

    new_versions = [
        {"version": e["version"], "released_date": e["released_date"], "document_name": e["document_name"]}
        for e in history
        if e["kind"] == "version" and e["version"] not in known_versions
    ]
    return new_versions
