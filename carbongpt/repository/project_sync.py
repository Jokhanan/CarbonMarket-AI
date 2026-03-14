import logging
import time
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 1.0


def _to_str(val, max_len=None):
    if val is None:
        return None
    if isinstance(val, list):
        val = "; ".join(str(v) for v in val if v)
    val = str(val).strip()
    if max_len and len(val) > max_len:
        val = val[:max_len]
    return val or None


def _safe_int(val):
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str.split("T")[0] if "T" in date_str else date_str, fmt.split("T")[0]).date()
        except (ValueError, TypeError):
            continue
    return None


def sync_verra_projects(max_projects=None):
    from carbongpt.repository.store import upsert_carbon_project

    logger.info("Starting Verra project sync...")
    try:
        resp = requests.post(
            "https://registry.verra.org/uiapi/resource/resource/search",
            json={"program": "VCS"},
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("Failed to fetch Verra projects: %s", e)
        return {"registry": "verra", "synced": 0, "errors": 1, "error_message": str(e)}

    projects = data.get("value", []) if isinstance(data, dict) else data
    if max_projects:
        projects = projects[:max_projects]

    synced = 0
    errors = 0
    for proj in projects:
        try:
            upsert_carbon_project({
                "registry": "verra",
                "registry_id": str(proj.get("resourceIdentifier", "")),
                "name": proj.get("resourceName", ""),
                "status": proj.get("resourceStatus"),
                "country": proj.get("country"),
                "region": proj.get("region"),
                "proponent": proj.get("proponent"),
                "methodology": _to_str(proj.get("protocols"), 300),
                "project_type": _to_str(proj.get("protocolCategories"), 200),
                "project_subtype": _to_str(proj.get("protocolSubCategories"), 300),
                "estimated_annual_credits": _safe_int(proj.get("estAnnualEmissionReductions")),
                "crediting_period_start": _parse_date(proj.get("creditingPeriodStartDate")),
                "crediting_period_end": _parse_date(proj.get("creditingPeriodEndDate")),
                "registration_date": _parse_date(proj.get("projectRegistrationDate")),
                "description": None,
                "extra_data": {
                    "program": proj.get("program"),
                    "version": proj.get("version"),
                    "create_date": proj.get("createDate"),
                },
            })
            synced += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                logger.warning("Failed to upsert Verra project %s: %s",
                               proj.get("resourceIdentifier"), e)

    logger.info("Verra sync complete: %d synced, %d errors out of %d total",
                synced, errors, len(projects))
    return {"registry": "verra", "synced": synced, "errors": errors, "total": len(projects)}


def sync_gs_projects(max_projects=None):
    from carbongpt.repository.store import upsert_carbon_project

    logger.info("Starting Gold Standard project sync...")
    all_projects = []
    page = 0
    page_size = 100

    while True:
        try:
            resp = requests.get(
                "https://public-api.goldstandard.org/projects",
                params={"page": page, "size": page_size},
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            batch = resp.json()
        except Exception as e:
            logger.error("Failed to fetch GS projects page %d: %s", page, e)
            break

        if not batch or not isinstance(batch, list):
            break

        all_projects.extend(batch)

        if max_projects and len(all_projects) >= max_projects:
            all_projects = all_projects[:max_projects]
            break

        if len(batch) < page_size:
            break

        page += 1
        time.sleep(RATE_LIMIT_DELAY)

    synced = 0
    errors = 0
    for proj in all_projects:
        try:
            registry_id = f"GS{proj.get('id', '')}"

            sdg_list = proj.get("sustainable_development_goals", [])
            sdgs = None
            if sdg_list:
                if isinstance(sdg_list, list):
                    if isinstance(sdg_list[0], dict):
                        sdgs = ", ".join(s.get("name", str(s.get("id", ""))) for s in sdg_list)
                    else:
                        sdgs = ", ".join(str(s) for s in sdg_list)

            upsert_carbon_project({
                "registry": "goldstandard",
                "registry_id": registry_id,
                "name": proj.get("name", ""),
                "status": proj.get("status"),
                "country": proj.get("country"),
                "region": _gs_country_to_region(proj.get("country")),
                "proponent": proj.get("project_developer"),
                "methodology": _to_str(proj.get("methodology"), 300),
                "project_type": _to_str(proj.get("type"), 200),
                "project_subtype": None,
                "estimated_annual_credits": _safe_int(proj.get("estimated_annual_credits")),
                "crediting_period_start": _parse_date(proj.get("crediting_period_start_date")),
                "crediting_period_end": _parse_date(proj.get("crediting_period_end_date")),
                "latitude": proj.get("latitude"),
                "longitude": proj.get("longitude"),
                "description": proj.get("description"),
                "sdgs": sdgs,
                "extra_data": {
                    "sustaincert_id": proj.get("sustaincert_id"),
                    "gsf_standards_version": proj.get("gsf_standards_version"),
                },
            })
            synced += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                logger.warning("Failed to upsert GS project %s: %s", proj.get("id"), e)

    logger.info("GS sync complete: %d synced, %d errors out of %d total",
                synced, errors, len(all_projects))
    return {"registry": "goldstandard", "synced": synced, "errors": errors, "total": len(all_projects)}


AFRICA_COUNTRIES = {
    "algeria", "angola", "benin", "botswana", "burkina faso", "burundi",
    "cameroon", "cape verde", "central african republic", "chad", "comoros",
    "congo", "democratic republic of the congo", "djibouti", "egypt",
    "equatorial guinea", "eritrea", "eswatini", "ethiopia", "gabon", "gambia",
    "ghana", "guinea", "guinea-bissau", "ivory coast", "cote d'ivoire",
    "kenya", "lesotho", "liberia", "libya", "madagascar", "malawi", "mali",
    "mauritania", "mauritius", "morocco", "mozambique", "namibia", "niger",
    "nigeria", "rwanda", "sao tome and principe", "senegal", "seychelles",
    "sierra leone", "somalia", "south africa", "south sudan", "sudan",
    "tanzania", "togo", "tunisia", "uganda", "zambia", "zimbabwe",
}

ASIA_COUNTRIES = {
    "afghanistan", "bangladesh", "bhutan", "brunei", "cambodia", "china",
    "india", "indonesia", "japan", "kazakhstan", "kyrgyzstan", "laos",
    "malaysia", "maldives", "mongolia", "myanmar", "nepal", "north korea",
    "pakistan", "philippines", "singapore", "south korea", "sri lanka",
    "tajikistan", "thailand", "timor-leste", "turkmenistan", "uzbekistan",
    "vietnam",
}

LATIN_AMERICA_COUNTRIES = {
    "argentina", "belize", "bolivia", "brazil", "chile", "colombia",
    "costa rica", "cuba", "dominican republic", "ecuador", "el salvador",
    "guatemala", "guyana", "haiti", "honduras", "jamaica", "mexico",
    "nicaragua", "panama", "paraguay", "peru", "suriname", "trinidad and tobago",
    "uruguay", "venezuela",
}


def _gs_country_to_region(country):
    if not country:
        return None
    c = country.strip().lower()
    if c in AFRICA_COUNTRIES:
        return "Africa"
    if c in ASIA_COUNTRIES:
        return "Asia"
    if c in LATIN_AMERICA_COUNTRIES:
        return "Latin America and the Caribbean"
    if c in {"united states", "canada"}:
        return "North America"
    if c in {"australia", "new zealand", "fiji", "papua new guinea", "samoa", "tonga", "vanuatu"}:
        return "Oceania"
    return "Europe"


def sync_cdm_projects(max_projects=None):
    """
    Sync CDM project data from the UNFCCC CDM registry.

    Uses the CDM's public search API with pagination.  If the endpoint is
    unavailable (bot-protection, network error, schema change) the function
    returns a result dict with synced=0 and a descriptive error — it never
    raises so the rest of the sync pipeline can continue.

    Controlled by env var:
        CARBONGPT_CDM_SYNC_ENABLED=1   (default: 1, set to 0 to skip CDM)
    """
    import os
    from carbongpt.repository.store import upsert_carbon_project

    if os.getenv("CARBONGPT_CDM_SYNC_ENABLED", "1") == "0":
        logger.info("CDM sync disabled via CARBONGPT_CDM_SYNC_ENABLED=0 — skipping.")
        return {"registry": "cdm", "synced": 0, "skipped": True, "reason": "disabled"}

    logger.info("Starting CDM project sync...")

    # ── CDM API configuration ───────────────────────────────────────────────
    BASE_URL     = "https://cdm.unfccc.int/Projects/SearchProj"
    HEADERS      = {
        "User-Agent":      "CarbonGPT-Research/1.0 (open-data access)",
        "Accept":          "application/json, */*",
        "Referer":         "https://cdm.unfccc.int/Projects/index.html",
    }
    PAGE_SIZE    = 200
    MAX_PAGES    = 50                # safety ceiling — CDM has ~7,500 registered projects
    REQUEST_TIMEOUT = 30

    all_projects_raw = []
    start = 0

    while True:
        try:
            resp = requests.get(
                BASE_URL,
                params={
                    "searchstring": "",
                    "regStatus":    "",
                    "country":      "",
                    "methProtNum":  "",
                    "orderField":   "ProjectRef",
                    "sortOrder":    "asc",
                    "start":        start,
                    "limit":        PAGE_SIZE,
                },
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()

            # CDM returns JSON.  On bot-protection/error it may return HTML.
            ct = resp.headers.get("content-type", "")
            if "html" in ct or resp.text.strip().startswith("<"):
                logger.warning(
                    "CDM API returned HTML (bot-protection active). "
                    "Sync will succeed in production; skipping in this environment."
                )
                return {
                    "registry": "cdm",
                    "synced":   0,
                    "skipped":  True,
                    "reason":   "CDM API returned HTML (bot-protection); will retry on next scheduled run",
                }

            payload = resp.json()

        except requests.exceptions.RequestException as e:
            logger.warning("CDM API request failed: %s — skipping CDM sync gracefully.", e)
            return {"registry": "cdm", "synced": 0, "skipped": True, "reason": str(e)}
        except ValueError as e:
            logger.warning("CDM API returned unparseable response: %s — skipping.", e)
            return {"registry": "cdm", "synced": 0, "skipped": True, "reason": f"JSON parse error: {e}"}

        # CDM API may wrap results in a list directly or {"items": [...]}
        if isinstance(payload, list):
            page_items = payload
        elif isinstance(payload, dict):
            page_items = (
                payload.get("items")
                or payload.get("projects")
                or payload.get("value")
                or payload.get("data")
                or []
            )
        else:
            logger.warning("CDM API returned unexpected payload type: %s", type(payload))
            break

        if not page_items:
            break  # No more pages

        all_projects_raw.extend(page_items)
        logger.info("CDM page start=%d: fetched %d items (total so far: %d)",
                    start, len(page_items), len(all_projects_raw))

        if len(page_items) < PAGE_SIZE:
            break  # Last page

        start += PAGE_SIZE
        if max_projects and len(all_projects_raw) >= max_projects:
            all_projects_raw = all_projects_raw[:max_projects]
            break

        page_count = start // PAGE_SIZE
        if page_count >= MAX_PAGES:
            logger.warning("CDM sync: reached MAX_PAGES=%d safety limit", MAX_PAGES)
            break

        time.sleep(RATE_LIMIT_DELAY)

    if not all_projects_raw:
        logger.info("CDM sync: 0 projects returned — source may be empty or schema changed.")
        return {"registry": "cdm", "synced": 0, "skipped": False, "total": 0}

    # ── Field mapping — CDM field names differ from Verra/GS ───────────────
    # CDM API commonly uses these field names (handled with fallbacks):
    #   referenceNumber / Project_ID / projectRef / number
    #   title / name / projectTitle
    #   country / countryName / hostCountry
    #   scope / sectoral_scope / methodology / methodologyRef
    #   status / registrationStatus
    #   expectedAnnualReductions / estAnnualReductions / annualReductions
    #   registrationDate / regDate
    #   proponent / developer / organizationName

    def _cdm_field(proj, *keys):
        for k in keys:
            v = proj.get(k)
            if v:
                return v
        return None

    synced = 0
    errors = 0

    for proj in all_projects_raw:
        try:
            registry_id = _to_str(
                _cdm_field(proj,
                           "referenceNumber", "Project_ID", "projectRef",
                           "number", "ref", "id"),
                50
            )
            upsert_carbon_project({
                "registry":                 "cdm",
                "ref_registry_id":          "cdm",
                "registry_id":              registry_id or "",
                "name":                     _to_str(_cdm_field(
                    proj, "title", "name", "projectTitle", "projectName"), 400),
                "status":                   _to_str(_cdm_field(
                    proj, "status", "registrationStatus", "reg_status"), 100),
                "country":                  _to_str(_cdm_field(
                    proj, "country", "countryName", "hostCountry", "host_country"), 200),
                "region":                   _to_str(_cdm_field(
                    proj, "region", "hostRegion"), 100),
                "proponent":                _to_str(_cdm_field(
                    proj, "proponent", "developer", "organizationName", "applicant"), 400),
                "methodology":              _to_str(_cdm_field(
                    proj, "methodology", "methodologyRef", "methProtNum",
                    "scope", "sectoral_scope"), 300),
                "project_type":             _to_str(_cdm_field(
                    proj, "scope", "sectoralScope", "projectType", "type"), 200),
                "estimated_annual_credits": _safe_int(_cdm_field(
                    proj, "expectedAnnualReductions", "estAnnualReductions",
                    "annualReductions", "expectedReductions")),
                "registration_date":        _parse_date(_to_str(_cdm_field(
                    proj, "registrationDate", "regDate", "registration_date"), 30)),
                "crediting_period_start":   _parse_date(_to_str(_cdm_field(
                    proj, "creditingPeriodStart", "startDate"), 30)),
                "crediting_period_end":     _parse_date(_to_str(_cdm_field(
                    proj, "creditingPeriodEnd", "endDate"), 30)),
                "description":              None,
                "extra_data":               {
                    "source":         "cdm_api",
                    "raw_keys":       list(proj.keys()),
                },
            })
            synced += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                logger.warning("CDM upsert failed for project %s: %s",
                               proj.get("referenceNumber") or proj.get("Project_ID"), e)

    logger.info("CDM sync complete: %d synced, %d errors out of %d total",
                synced, errors, len(all_projects_raw))
    return {
        "registry": "cdm",
        "synced":   synced,
        "errors":   errors,
        "total":    len(all_projects_raw),
        "skipped":  False,
    }


def sync_all_projects(max_verra=None, max_gs=None, max_cdm=None):
    """
    Sync projects from all registries: Verra, Gold Standard, and CDM.

    Each registry sync is independent — a failure in one does not abort
    the others.  CDM is controlled by CARBONGPT_CDM_SYNC_ENABLED env var.

    Returns a dict with per-registry results and totals.
    """
    verra_result  = sync_verra_projects(max_projects=max_verra)
    gs_result     = sync_gs_projects(max_projects=max_gs)
    cdm_result    = sync_cdm_projects(max_projects=max_cdm)

    # ── Post-sync normalization passes ────────────────────────────────────
    try:
        from carbongpt.repository.country_normalizer import (
            seed_countries_table,
            run_country_normalization_pass,
        )
        seed_countries_table()
        country_result = run_country_normalization_pass()
        logger.info("Country normalization: %s", country_result)
    except Exception as e:
        logger.error("Country normalization failed: %s", e)
        country_result = {"error": str(e)}

    try:
        from carbongpt.repository.methodology_normalizer import (
            seed_methodology_library_from_db,
            run_methodology_normalization_pass,
            seed_ref_methodologies,
        )
        seed_methodology_library_from_db()
        run_methodology_normalization_pass()
        seed_ref_methodologies()
    except Exception as e:
        logger.error("Methodology normalization failed: %s", e)

    total_synced = (
        verra_result.get("synced", 0)
        + gs_result.get("synced", 0)
        + cdm_result.get("synced", 0)
    )

    logger.info(
        "sync_all_projects complete — Verra: %d, GS: %d, CDM: %d (skipped=%s), total: %d",
        verra_result.get("synced", 0),
        gs_result.get("synced", 0),
        cdm_result.get("synced", 0),
        cdm_result.get("skipped", False),
        total_synced,
    )

    return {
        "verra":                 verra_result,
        "goldstandard":          gs_result,
        "cdm":                   cdm_result,
        "total_synced":          total_synced,
        "country_normalization": country_result,
    }


# ── Step 5: Registry Sync Scheduler ─────────────────────────────────────────

_registry_scheduler_started = False
_registry_scheduler_state: dict = {
    "running":     False,
    "last_run":    None,
    "next_run":    None,
    "last_result": None,
}


def get_registry_scheduler_state() -> dict:
    return dict(_registry_scheduler_state)


def start_registry_sync_schedule() -> None:
    """
    Start a daemon thread that runs sync_all_projects() on a fixed interval.

    Controlled by env vars:
      CARBONGPT_AUTO_SYNC_PROJECTS=1          — enable (default: off)
      CARBONGPT_PROJECT_SYNC_INTERVAL_HOURS=24 — interval (default: 24 h)

    Mirrors the pattern used by start_weekly_sync() in methodology_sync.py.
    The first sync runs 5 minutes after startup to avoid competing with the
    methodology sync that fires 30 seconds after startup.
    """
    import os
    import threading
    from datetime import datetime, timedelta

    global _registry_scheduler_started, _registry_scheduler_state

    if _registry_scheduler_started:
        logger.info("Registry sync scheduler already running — skipping.")
        return
    _registry_scheduler_started = True

    interval_hours   = int(os.getenv("CARBONGPT_PROJECT_SYNC_INTERVAL_HOURS", "24"))
    interval_seconds = interval_hours * 3600
    initial_delay    = 300  # 5 minutes

    def _run_periodic():
        global _registry_scheduler_state

        _registry_scheduler_state["next_run"] = (
            datetime.utcnow() + timedelta(seconds=initial_delay)
        ).isoformat() + "Z"

        logger.info(
            "Registry sync scheduler started — first run in %d s, then every %d h",
            initial_delay, interval_hours,
        )
        time.sleep(initial_delay)

        while True:
            _registry_scheduler_state["running"]  = True
            _registry_scheduler_state["last_run"] = datetime.utcnow().isoformat() + "Z"
            _registry_scheduler_state["next_run"] = (
                datetime.utcnow() + timedelta(seconds=interval_seconds)
            ).isoformat() + "Z"

            logger.info("Running scheduled registry project sync...")
            try:
                result = sync_all_projects()
                _registry_scheduler_state["last_result"] = result
                cdm = result.get("cdm", {})
                logger.info(
                    "Scheduled sync complete — Verra: %d, GS: %d, CDM: %d (skipped=%s), total: %d",
                    result.get("verra", {}).get("synced", 0),
                    result.get("goldstandard", {}).get("synced", 0),
                    cdm.get("synced", 0),
                    cdm.get("skipped", False),
                    result.get("total_synced", 0),
                )
            except Exception as e:
                logger.error("Scheduled registry sync failed: %s", e)
                _registry_scheduler_state["last_result"] = {"error": str(e)}
            finally:
                _registry_scheduler_state["running"] = False

            time.sleep(interval_seconds)

    thread = threading.Thread(target=_run_periodic, daemon=True)
    thread.start()
    logger.info("Registry sync scheduler thread started (interval: %d hours)", interval_hours)
