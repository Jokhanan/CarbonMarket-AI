"""
Methodology Normalization — Step 1

Three-layer extraction:
  1. Regex: extract structured codes (VM0006, ACM0002, TPDDTEC, …)
  2. Fallback lookup: match raw segment against known display-name variants
  3. Log: all unmatched raw strings go to methodology_normalization_log for review

No raw values in carbon_projects are modified.  New data lives only in:
  - methodology_library       (reference table)
  - project_methodology_codes (junction)
  - methodology_normalization_log (review queue)
"""

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. REGEX — extract structured methodology codes from raw strings
# ---------------------------------------------------------------------------
_CODE_RE = re.compile(
    r'\b('
    r'AR-ACM\d{4}'
    r'|AR-AM\d{4}'
    r'|AR-AMS-[IVX]+\.[A-Z]+'
    r'|ACM\d{4}'
    r'|AM\d{4}'
    r'|AMS-[IVX]+\.[A-Z]+(?:\.\d+)?'
    r'|VM\d{4}'
    r'|VMR\d{4}'
    r'|VMD\d{4}'
    r'|TPDDTEC'
    r'|GS-MECD'
    r'|GS-[A-Z]{2,10}'
    r')\b',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 2. FAMILY MAP — code → (family, sector, technology, registry)
# ---------------------------------------------------------------------------
_FAMILY_MAP: dict[str, tuple[str, str, str, str]] = {
    # Clean Cooking
    "TPDDTEC":    ("Clean Cooking", "Energy demand",      "Cookstove",            "Gold Standard"),
    "GS-MECD":    ("Clean Cooking", "Energy demand",      "Cookstove",            "Gold Standard"),
    "VM0006":     ("Clean Cooking", "Energy demand",      "Cookstove",            "Verra"),
    "AMS-I.E":    ("Clean Cooking", "Energy demand",      "Cookstove",            "CDM"),
    "AMS-II.G":   ("Clean Cooking", "Energy demand",      "Cookstove",            "CDM"),
    "AMS-II.L":   ("Clean Cooking", "Energy demand",      "Efficient appliance",  "CDM"),
    "AMS-III.AR": ("Clean Cooking", "Energy demand",      "Cookstove",            "CDM"),
    # Renewable Electricity
    "ACM0002":    ("Renewable Electricity", "Energy industries", "Grid-connected",  "CDM"),
    "AMS-I.D":    ("Renewable Electricity", "Energy industries", "Grid-connected",  "CDM"),
    "AMS-I.A":    ("Renewable Electricity", "Energy demand",     "Solar PV",        "CDM"),
    "AMS-I.F":    ("Renewable Electricity", "Energy demand",     "Solar PV",        "CDM"),
    "AMS-I.C":    ("Renewable Electricity", "Energy demand",     "Wind/Hydro",      "CDM"),
    "VM0050":     ("Renewable Electricity", "Energy industries", "Grid-connected",  "Verra"),
    "VM0041":     ("Renewable Electricity", "Energy industries", "Micro-hydro",     "Verra"),
    "ACM0006":    ("Renewable Electricity", "Energy industries", "Biomass",         "CDM"),
    "AM0014":     ("Renewable Electricity", "Energy industries", "Cogeneration",    "CDM"),
    # REDD+ / Avoided Deforestation
    "VM0007":     ("REDD+",  "Land use", "Avoided deforestation", "Verra"),
    "VM0009":     ("REDD+",  "Land use", "Avoided deforestation", "Verra"),
    "VM0015":     ("REDD+",  "Land use", "Avoided deforestation", "Verra"),
    "VM0026":     ("REDD+",  "Land use", "Avoided deforestation", "Verra"),
    "VM0048":     ("REDD+",  "Land use", "Avoided deforestation", "Verra"),
    "VM0007":     ("REDD+",  "Land use", "Avoided deforestation", "Verra"),
    # Improved Forest Management
    "VM0012":     ("Improved Forest Management", "Land use", "IFM", "Verra"),
    "VM0042":     ("Improved Forest Management", "Land use", "IFM", "Verra"),
    "VM0010":     ("Improved Forest Management", "Land use", "IFM", "Verra"),
    # Blue Carbon
    "VM0033":     ("Blue Carbon", "Land use", "Coastal wetlands", "Verra"),
    "VM0036":     ("Blue Carbon", "Land use", "Tidal wetlands",   "Verra"),
    # Agriculture / Soil
    "VM0017":     ("Agriculture", "Agriculture", "Soil carbon",     "Verra"),
    "VM0021":     ("Agriculture", "Agriculture", "Rice cultivation","Verra"),
    "VM0022":     ("Agriculture", "Agriculture", "Agricultural land","Verra"),
    "VM0032":     ("Agriculture", "Agriculture", "Crop residues",   "Verra"),
    # Landfill Gas / Waste
    "ACM0001":    ("Landfill Gas",        "Waste handling", "Landfill gas",       "CDM"),
    "VM0030":     ("Landfill Gas",        "Waste handling", "Landfill gas",       "Verra"),
    "AMS-III.G":  ("Landfill Gas",        "Waste handling", "Landfill gas",       "CDM"),
    # Methane / Manure / Wastewater
    "ACM0010":    ("Methane Capture",     "Agriculture",    "Manure management",  "CDM"),
    "AMS-III.D":  ("Methane Recovery",    "Waste handling", "Anaerobic digestion","CDM"),
    "ACM0014":    ("Wastewater Treatment","Waste handling", "Wastewater",         "CDM"),
    "AMS-III.F":  ("Methane Capture",     "Agriculture",    "Manure management",  "CDM"),
    "AMS-III.R":  ("Methane Capture",     "Agriculture",    "Manure management",  "CDM"),
    # Energy Efficiency
    "AMS-II.C":   ("Energy Efficiency",   "Energy demand",  "Thermal",            "CDM"),
    "AMS-II.E":   ("Energy Efficiency",   "Energy demand",  "Lighting",           "CDM"),
    "AM0046":     ("Energy Efficiency",   "Energy demand",  "Efficient bulbs",    "CDM"),
    "AMS-II.J":   ("Energy Efficiency",   "Energy demand",  "Cookstove/thermal",  "CDM"),
    # Transport
    "ACM0016":    ("Transport",           "Transport",      "Mass Rapid Transit", "CDM"),
    "AM0031":     ("Transport",           "Transport",      "Bus Rapid Transit",  "CDM"),
    # Industrial / Chemical
    "ACM0019":    ("Industrial Gas",      "Chemical",       "N2O destruction",    "CDM"),
    "AM0001":     ("Industrial Gas",      "Chemical",       "HFC-23 destruction", "CDM"),
    "ACM0012":    ("Waste Energy Recovery","Energy industries","Waste heat",       "CDM"),
}

# Normalise keys to uppercase for lookup
_FAMILY_MAP = {k.upper(): v for k, v in _FAMILY_MAP.items()}

# ---------------------------------------------------------------------------
# 3. PREFIX FAMILY MAP — fallback for unmapped specific codes
#    Returns (family, registry) only — sector/tech left NULL
# ---------------------------------------------------------------------------
_PREFIX_FAMILY: list[tuple[str, str, str]] = [
    ("AR-ACM", "Afforestation/Reforestation CDM", "CDM"),
    ("AR-AM",  "Afforestation/Reforestation CDM", "CDM"),
    ("AR-AMS", "Afforestation/Reforestation Small-scale CDM", "CDM"),
    ("ACM",    "Large-scale Consolidated CDM", "CDM"),
    ("AMS",    "Small-scale CDM",              "CDM"),
    ("AM",     "CDM Methodology",              "CDM"),
    ("VMR",    "Verra VCS Methodology",        "Verra"),
    ("VMD",    "Verra VCS Module",             "Verra"),
    ("VM",     "Verra VCS Methodology",        "Verra"),
    ("GS",     "Gold Standard Methodology",    "Gold Standard"),
]

# ---------------------------------------------------------------------------
# 4. DISPLAY NAME VARIANT → code fallback lookup
#    Handles cases where the raw string has a human-readable name only
# ---------------------------------------------------------------------------
_NAME_VARIANTS: dict[str, str] = {
    "tpddtec":                              "TPDDTEC",
    "tpddtec v4.0":                         "TPDDTEC",
    "tpddtec v3.1":                         "TPDDTEC",
    "gs-mecd":                              "GS-MECD",
    "gs mecd":                              "GS-MECD",
    "mecd":                                 "GS-MECD",
    "grid-connected electricity":           "ACM0002",
    "grid connected electricity":           "ACM0002",
    "renewable energy":                     "ACM0002",
    "improved cookstoves":                  "TPDDTEC",
    "improved cook stoves":                 "TPDDTEC",
    "clean cookstoves":                     "TPDDTEC",
    "cookstoves":                           "TPDDTEC",
    "redd+":                                "VM0007",
    "redd":                                 "VM0007",
    "avoided deforestation":                "VM0007",
    "ifm":                                  "VM0012",
    "improved forest management":           "VM0012",
    "landfill gas":                         "ACM0001",
    "solar":                                "AMS-I.D",
    "solar pv":                             "AMS-I.D",
    "wind":                                 "ACM0002",
    "hydropower":                           "ACM0002",
    "manure management":                    "ACM0010",
    "wastewater treatment":                 "ACM0014",
    "biogas":                               "AMS-III.D",
    "transport":                            "ACM0016",
    "mass rapid transit":                   "ACM0016",
    "energy efficiency":                    "AMS-II.C",
}


def _lookup_by_name_variant(segment: str) -> str | None:
    return _NAME_VARIANTS.get(segment.strip().lower())


def _family_from_code(code: str) -> tuple[str | None, str | None, str | None, str | None]:
    """Return (family, sector, technology, registry) for a known code."""
    upper = code.upper()
    if upper in _FAMILY_MAP:
        return _FAMILY_MAP[upper]
    for prefix, family, registry in _PREFIX_FAMILY:
        if upper.startswith(prefix.upper()):
            return family, None, None, registry
    return None, None, None, None


# ---------------------------------------------------------------------------
# 5. CORE EXTRACTION
# ---------------------------------------------------------------------------
def extract_codes_from_raw(raw: str) -> list[dict]:
    """
    Split a raw methodology string on '; ' and attempt extraction for each segment.

    Returns a list of dicts:
      { code, is_primary, raw_segment, matched_by: 'regex'|'name_variant'|None }
    """
    if not raw:
        return []

    segments = [s.strip() for s in re.split(r"[;,\n]+", raw) if s.strip()]
    results = []

    for i, seg in enumerate(segments):
        match = _CODE_RE.search(seg)
        if match:
            code = match.group(0).upper()
            results.append({
                "code":        code,
                "is_primary":  i == 0,
                "raw_segment": seg[:300],
                "matched_by":  "regex",
            })
            continue

        fallback = _lookup_by_name_variant(seg)
        if fallback:
            results.append({
                "code":        fallback,
                "is_primary":  i == 0,
                "raw_segment": seg[:300],
                "matched_by":  "name_variant",
            })
            continue

        results.append({
            "code":        None,
            "is_primary":  i == 0,
            "raw_segment": seg[:300],
            "matched_by":  None,
        })

    return results


# ---------------------------------------------------------------------------
# 6. DATABASE OPERATIONS
# ---------------------------------------------------------------------------
def ensure_methodology_in_library(code: str) -> None:
    """Insert a provisional row into methodology_library if not present."""
    from carbongpt.repository.db import get_cursor
    family, sector, technology, registry = _family_from_code(code)
    display_name = code
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO methodology_library
                    (methodology_code, display_name, methodology_family, registry, sector, technology)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (methodology_code) DO NOTHING
                """,
                (code, display_name, family, registry or "Any", sector, technology),
            )
    except Exception as e:
        logger.warning("Failed to upsert methodology_library for %s: %s", code, e)


def _log_unknown(raw_string: str, raw_segment: str) -> None:
    """Upsert an unmatched raw string into methodology_normalization_log."""
    from carbongpt.repository.db import get_cursor
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO methodology_normalization_log
                    (raw_string, raw_segment, occurrence_count, last_seen)
                VALUES (%s, %s, 1, NOW())
                ON CONFLICT (raw_string) DO UPDATE
                    SET occurrence_count = methodology_normalization_log.occurrence_count + 1,
                        last_seen = NOW()
                """,
                (raw_string[:300], raw_segment[:300]),
            )
    except Exception as e:
        logger.warning("Failed to log unknown methodology '%s': %s", raw_string[:80], e)


def normalize_project_methodologies(project_id: int, project_db_id: int, raw_methodology: str) -> int:
    """
    Process one project's raw methodology string.
    Inserts rows into project_methodology_codes.
    Logs unmatched segments.

    Returns count of codes successfully linked.
    """
    from carbongpt.repository.db import get_cursor

    if not raw_methodology:
        return 0

    extractions = extract_codes_from_raw(raw_methodology)
    linked = 0

    for item in extractions:
        code = item["code"]
        seg  = item["raw_segment"]

        if code is None:
            if seg:
                _log_unknown(seg, seg)
                logger.debug("Unmatched methodology segment: %r (project_id=%s)", seg[:80], project_id)
            continue

        ensure_methodology_in_library(code)

        try:
            with get_cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO project_methodology_codes
                        (project_id, methodology_code, is_primary, raw_segment)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (project_id, methodology_code) DO UPDATE
                        SET raw_segment = EXCLUDED.raw_segment
                    """,
                    (project_db_id, code, item["is_primary"], seg),
                )
                linked += 1
        except Exception as e:
            logger.warning("Failed to link project %s → code %s: %s", project_id, code, e)

    return linked


def run_methodology_normalization_pass() -> dict:
    """
    Full normalization pass over all rows in carbon_projects.
    Safe to call multiple times — uses ON CONFLICT DO UPDATE/NOTHING.

    Returns summary counts.
    """
    from carbongpt.repository.db import get_cursor

    logger.info("Starting methodology normalization pass...")
    total = linked = unmatched = errors = 0

    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, registry_id, methodology FROM carbon_projects WHERE methodology IS NOT NULL")
            rows = cur.fetchall()
    except Exception as e:
        logger.error("Failed to fetch carbon_projects for normalization: %s", e)
        return {"total": 0, "linked": 0, "unmatched": 0, "errors": 1}

    for row in rows:
        total += 1
        try:
            n = normalize_project_methodologies(
                row["registry_id"], row["id"], row["methodology"]
            )
            linked   += n
            unmatched += 1 if n == 0 else 0
        except Exception as e:
            errors += 1
            logger.warning("Normalization failed for project id=%s: %s", row["id"], e)

    logger.info(
        "Methodology normalization complete: %d projects, %d codes linked, "
        "%d fully unmatched, %d errors",
        total, linked, unmatched, errors,
    )
    return {"total": total, "linked": linked, "unmatched": unmatched, "errors": errors}


def seed_methodology_library_from_db() -> int:
    """
    Seed methodology_library from CDM_METHODOLOGY_NAMES in methodology_db.py.
    Called once at startup / after schema init.
    """
    from carbongpt.repository.db import get_cursor
    from carbongpt.repository.methodology_db import CDM_METHODOLOGY_NAMES, METHODOLOGY_FAMILIES

    inserted = 0
    try:
        with get_cursor() as cur:
            for code, (name, sector) in CDM_METHODOLOGY_NAMES.items():
                prefix = re.match(r'^([A-Za-z\-]+)', code)
                prefix_key = prefix.group(1).rstrip("-") if prefix else ""
                fam_info   = METHODOLOGY_FAMILIES.get(prefix_key, {})
                family_label = fam_info.get("category", "CDM Methodology")
                registry     = fam_info.get("standard", "CDM")

                mapped = _FAMILY_MAP.get(code.upper())
                if mapped:
                    family_label, sector_m, technology, registry = mapped
                    sector = sector_m or sector

                cur.execute(
                    """
                    INSERT INTO methodology_library
                        (methodology_code, display_name, methodology_family, registry, sector)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (methodology_code) DO NOTHING
                    """,
                    (code, name[:200], family_label, registry, sector[:100] if sector else None),
                )
                inserted += 1

            for code, (family, sector, technology, registry) in _FAMILY_MAP.items():
                display = code
                cur.execute(
                    """
                    INSERT INTO methodology_library
                        (methodology_code, display_name, methodology_family, registry, sector, technology)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (methodology_code) DO NOTHING
                    """,
                    (code, display, family, registry, sector, technology),
                )
                inserted += 1

    except Exception as e:
        logger.error("Failed to seed methodology_library: %s", e)
        return 0

    logger.info("Seeded methodology_library with %d entries", inserted)
    return inserted
