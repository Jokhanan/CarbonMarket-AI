import hashlib
import logging
import os
import re
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

REPO_DIR = Path(__file__).resolve().parent.parent.parent / "document_repository"
REPO_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "CarbonGPT/1.0 (compliance-research-tool)"
RATE_LIMIT_DELAY = 2


def _download_file(url: str, dest_path: Path) -> bool:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=60,
            stream=True,
        )
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.warning("Failed to download %s: %s", url, e)
        return False


def _content_hash(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_already_stored(reference_id: str) -> dict | None:
    try:
        from carbongpt.repository.store import find_document_by_reference
        return find_document_by_reference(reference_id)
    except Exception:
        return None


def fetch_verra_methodology_list() -> list[dict]:
    url = "https://verra.org/program-methodology/vcs-program-standard/vcs-program-methodologies-active/"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        logger.error("Failed to fetch Verra methodology list: %s", e)
        return []

    methodologies = []
    pattern = re.compile(
        r'<a[^>]*href="(https://verra\.org/methodologies/[^"]+)"[^>]*>.*?'
        r'(VM\d{4})\b.*?'
        r'\*\*([^*]+)\*\*',
        re.DOTALL | re.IGNORECASE,
    )
    link_pattern = re.compile(
        r'href="(https://verra\.org/methodologies/(vm\d{4})[^"]*)"',
        re.IGNORECASE,
    )

    for match in link_pattern.finditer(html):
        detail_url = match.group(1)
        code = match.group(2).upper()
        if code not in [m["code"] for m in methodologies]:
            methodologies.append({
                "code": code,
                "detail_url": detail_url,
                "source": "verra",
            })

    logger.info("Found %d Verra methodologies from catalog", len(methodologies))
    return methodologies


def fetch_verra_methodology_pdf(detail_url: str) -> dict | None:
    try:
        resp = requests.get(detail_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        logger.warning("Failed to fetch methodology detail page %s: %s", detail_url, e)
        return None

    pdf_pattern = re.compile(
        r'href="(https://verra\.org/[^"]*\.pdf)"',
        re.IGNORECASE,
    )
    title_pattern = re.compile(r'<h1[^>]*>([^<]+)</h1>', re.IGNORECASE)

    title_match = title_pattern.search(html)
    title = title_match.group(1).strip() if title_match else "Unknown Methodology"

    pdf_urls = []
    for m in pdf_pattern.finditer(html):
        pdf_url = m.group(1)
        if "methodology" in pdf_url.lower() or "vm0" in pdf_url.lower() or "vmr" in pdf_url.lower():
            pdf_urls.append(pdf_url)

    if not pdf_urls:
        for m in pdf_pattern.finditer(html):
            pdf_urls.append(m.group(1))

    if not pdf_urls:
        return None

    return {
        "title": title,
        "pdf_url": pdf_urls[0],
        "all_pdf_urls": pdf_urls,
    }


def fetch_cdm_methodology_list() -> list[dict]:
    methodologies = []

    for meth_type, base_url in [
        ("large-scale", "https://cdm.unfccc.int/methodologies/PAmethodologies/approved"),
        ("small-scale", "https://cdm.unfccc.int/methodologies/SSCmethodologies/approved"),
    ]:
        try:
            resp = requests.get(base_url, headers={"User-Agent": USER_AGENT}, timeout=30)
            resp.raise_for_status()
            html = resp.text

            if meth_type == "large-scale":
                pattern = re.compile(
                    r'href="(/methodologies/PAmethodologies/approved/[^"]*)"[^>]*>.*?(AM\d{4}|ACM\d{4})',
                    re.DOTALL | re.IGNORECASE,
                )
            else:
                pattern = re.compile(
                    r'href="(/methodologies/SSCmethodologies/approved/[^"]*)"[^>]*>.*?(AMS[^<\s]{2,10})',
                    re.DOTALL | re.IGNORECASE,
                )

            for match in pattern.finditer(html):
                detail_path = match.group(1)
                code = match.group(2).upper().strip()
                detail_url = f"https://cdm.unfccc.int{detail_path}"
                if code not in [m["code"] for m in methodologies]:
                    methodologies.append({
                        "code": code,
                        "detail_url": detail_url,
                        "source": "cdm",
                        "type": meth_type,
                    })
        except Exception as e:
            logger.warning("Failed to fetch CDM %s methodology list: %s", meth_type, e)

    logger.info("Found %d CDM methodologies", len(methodologies))
    return methodologies


def fetch_gs_methodology_list() -> list[dict]:
    url = "https://www.goldstandard.org/project-developers/standard-documents"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        logger.error("Failed to fetch Gold Standard methodology list: %s", e)
        return []

    methodologies = []
    pdf_pattern = re.compile(
        r'href="([^"]*(?:methodology|standard)[^"]*\.pdf)"',
        re.IGNORECASE,
    )

    for match in pdf_pattern.finditer(html):
        pdf_url = match.group(1)
        if not pdf_url.startswith("http"):
            pdf_url = f"https://www.goldstandard.org{pdf_url}"
        filename = pdf_url.rsplit("/", 1)[-1]
        code = filename.replace(".pdf", "").replace("-", "_")[:30]
        if code not in [m["code"] for m in methodologies]:
            methodologies.append({
                "code": code,
                "detail_url": pdf_url,
                "pdf_url": pdf_url,
                "source": "goldstandard",
            })

    logger.info("Found %d Gold Standard methodology documents", len(methodologies))
    return methodologies


def sync_methodologies(
    sources: list[str] = None,
    max_per_source: int = 50,
    dry_run: bool = False,
) -> dict:
    if sources is None:
        sources = ["verra", "cdm", "goldstandard"]

    results = {
        "sources_checked": sources,
        "total_found": 0,
        "already_stored": 0,
        "newly_downloaded": 0,
        "ingestion_started": 0,
        "errors": 0,
        "details": [],
    }

    all_methodologies = []

    if "verra" in sources:
        verra_list = fetch_verra_methodology_list()
        all_methodologies.extend(verra_list[:max_per_source])

    if "cdm" in sources:
        cdm_list = fetch_cdm_methodology_list()
        all_methodologies.extend(cdm_list[:max_per_source])

    if "goldstandard" in sources:
        gs_list = fetch_gs_methodology_list()
        all_methodologies.extend(gs_list[:max_per_source])

    results["total_found"] = len(all_methodologies)

    api_key = os.getenv("OPENAI_API_KEY")

    for meth in all_methodologies:
        code = meth["code"]
        source = meth["source"]
        reference_id = f"{source}_{code}"

        existing = _is_already_stored(reference_id)
        if existing:
            results["already_stored"] += 1
            results["details"].append({
                "code": code,
                "source": source,
                "status": "already_stored",
                "doc_id": existing.get("id"),
            })
            continue

        if dry_run:
            results["details"].append({
                "code": code,
                "source": source,
                "status": "would_download",
            })
            continue

        pdf_url = meth.get("pdf_url")
        title = meth.get("title", code)

        if not pdf_url and source == "verra":
            time.sleep(RATE_LIMIT_DELAY)
            detail = fetch_verra_methodology_pdf(meth["detail_url"])
            if detail:
                pdf_url = detail["pdf_url"]
                title = detail.get("title", code)

        if not pdf_url:
            results["details"].append({
                "code": code,
                "source": source,
                "status": "no_pdf_found",
            })
            results["errors"] += 1
            continue

        filename = f"{reference_id}.pdf"
        dest_path = REPO_DIR / filename

        if dest_path.exists():
            results["already_stored"] += 1
            results["details"].append({
                "code": code,
                "source": source,
                "status": "file_exists",
            })
            continue

        time.sleep(RATE_LIMIT_DELAY)
        if not _download_file(pdf_url, dest_path):
            results["errors"] += 1
            results["details"].append({
                "code": code,
                "source": source,
                "status": "download_failed",
            })
            continue

        results["newly_downloaded"] += 1

        standard_slug_map = {
            "verra": "verra",
            "cdm": "cdm",
            "goldstandard": "goldstandard",
        }

        try:
            from carbongpt.repository.store import create_document, list_standard_versions

            sv_id = None
            slug = standard_slug_map.get(source)
            if slug:
                versions = list_standard_versions()
                for v in versions:
                    if v.get("standard_slug") == slug or (
                        slug == "verra" and "verra" in v.get("standard_name", "").lower()
                    ):
                        sv_id = v["id"]
                        break

            doc_id = create_document(
                standard_version_id=sv_id,
                category="methodology",
                title=title,
                file_path=str(dest_path),
                file_type="pdf",
                reference_id=reference_id,
                doc_version=None,
                file_size_bytes=dest_path.stat().st_size,
            )

            results["details"].append({
                "code": code,
                "source": source,
                "status": "downloaded",
                "doc_id": doc_id,
                "pdf_url": pdf_url,
            })

            if api_key:
                import threading
                from carbongpt.repository.ingestion import ingest_document

                thread = threading.Thread(
                    target=_safe_ingest,
                    args=(doc_id, str(dest_path), api_key),
                    daemon=True,
                )
                thread.start()
                results["ingestion_started"] += 1
        except Exception as e:
            logger.error("Failed to store methodology %s: %s", code, e)
            results["errors"] += 1
            results["details"].append({
                "code": code,
                "source": source,
                "status": "store_failed",
                "error": str(e),
            })

    return results


def _safe_ingest(doc_id, file_path, api_key):
    try:
        from carbongpt.repository.ingestion import ingest_document
        ingest_document(doc_id, file_path, api_key)
    except Exception as e:
        logger.error("Ingestion failed for doc %s: %s", doc_id, e)


_scheduler_started = False


def start_weekly_sync():
    global _scheduler_started
    if _scheduler_started:
        return
    _scheduler_started = True

    import threading

    interval = int(os.getenv("CARBONGPT_SYNC_INTERVAL_HOURS", "168"))  # 168 = 7 days
    interval_seconds = interval * 3600

    def _run_periodic():
        time.sleep(30)
        logger.info("Running initial methodology sync on startup...")
        try:
            result = sync_methodologies(max_per_source=20)
            logger.info(
                "Initial sync complete: %d found, %d new, %d errors",
                result["total_found"],
                result["newly_downloaded"],
                result["errors"],
            )
        except Exception as e:
            logger.error("Initial sync failed: %s", e)
        while True:
            time.sleep(interval_seconds)
            logger.info("Running scheduled methodology sync...")
            try:
                result = sync_methodologies(max_per_source=20)
                logger.info(
                    "Scheduled sync complete: %d found, %d new, %d errors",
                    result["total_found"],
                    result["newly_downloaded"],
                    result["errors"],
                )
            except Exception as e:
                logger.error("Scheduled sync failed: %s", e)

    thread = threading.Thread(target=_run_periodic, daemon=True)
    thread.start()
    logger.info("Methodology sync scheduler started (interval: %d hours)", interval)
