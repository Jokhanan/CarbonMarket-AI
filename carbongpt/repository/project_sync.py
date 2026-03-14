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


def sync_all_projects(max_verra=None, max_gs=None):
    verra_result = sync_verra_projects(max_projects=max_verra)
    gs_result    = sync_gs_projects(max_projects=max_gs)

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
        )
        seed_methodology_library_from_db()
        meth_result = run_methodology_normalization_pass()
        logger.info("Methodology normalization: %s", meth_result)
    except Exception as e:
        logger.error("Methodology normalization failed: %s", e)
        meth_result = {"error": str(e)}

    return {
        "verra":                verra_result,
        "goldstandard":         gs_result,
        "total_synced":         verra_result.get("synced", 0) + gs_result.get("synced", 0),
        "country_normalization": country_result,
        "meth_normalization":    meth_result,
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
                logger.info(
                    "Scheduled sync complete — Verra: %d, GS: %d, total: %d",
                    result.get("verra", {}).get("synced", 0),
                    result.get("goldstandard", {}).get("synced", 0),
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
