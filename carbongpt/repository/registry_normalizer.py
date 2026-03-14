"""
registry_normalizer.py — Step 1 of the shared-core architecture.

Provides the canonical ref_registries seed and all registry resolution
functions.  All other modules must resolve registry identifiers through
this module rather than maintaining their own string constants.

Canonical registry_id slugs (stable, lowercase):
  verra        — Verra Registry (VCS / CCB / SD VISta)
  goldstandard — Gold Standard for the Global Goals (GS4GG)
  cdm          — UNFCCC CDM Registry
  j-credit     — Japan J-Credit Scheme
  art-trees    — ART TREES Registry
  gcc          — Global Carbon Council
  korea-ets    — Korea Emissions Trading Scheme
"""

import logging

logger = logging.getLogger(__name__)

# ── Canonical registry seed ──────────────────────────────────────────────────
# Each tuple: (registry_id, registry_name, registry_short, website)
REGISTRIES_SEED: list[tuple[str, str, str, str]] = [
    ("verra",        "Verra Registry",                       "VCS",      "https://registry.verra.org"),
    ("goldstandard", "Gold Standard for the Global Goals",   "GS4GG",    "https://registry.goldstandard.org"),
    ("cdm",          "UNFCCC CDM Registry",                  "CDM",      "https://cdm.unfccc.int"),
    ("j-credit",     "Japan J-Credit Scheme",                "J-Credit", "https://japancredit.go.jp"),
    ("art-trees",    "ART TREES Registry",                   "ART",      "https://www.artredd.org"),
    ("gcc",          "Global Carbon Council",                "GCC",      "https://www.globalcarboncouncil.com"),
    ("korea-ets",    "Korea Emissions Trading Scheme",       "K-ETS",    "https://ets.krx.co.kr"),
]

# ── Raw-value → canonical registry_id mapping ────────────────────────────────
# Covers every spelling variant seen in live registry data and the codebase.
# Keys are lowercased at module load time for case-insensitive lookup.
RAW_TO_REGISTRY_ID: dict[str, str] = {
    # Verra
    "verra":                              "verra",
    "verra registry":                     "verra",
    "vcs":                                "verra",
    "verified carbon standard":           "verra",
    "verra vcs":                          "verra",
    "vcs registry":                       "verra",
    # Gold Standard
    "goldstandard":                       "goldstandard",
    "gold standard":                      "goldstandard",
    "gold standard for the global goals": "goldstandard",
    "gs4gg":                              "goldstandard",
    "gs":                                 "goldstandard",
    # CDM
    "cdm":                                "cdm",
    "unfccc cdm":                         "cdm",
    "unfccc cdm registry":                "cdm",
    "clean development mechanism":        "cdm",
    "cdm/unfccc":                         "cdm",
    # J-Credit
    "j-credit":                           "j-credit",
    "j_credit":                           "j-credit",
    "j credit":                           "j-credit",
    "japan credit":                       "j-credit",
    "j-credit scheme":                    "j-credit",
    # ART TREES
    "art-trees":                          "art-trees",
    "art_trees":                          "art-trees",
    "art trees":                          "art-trees",
    "art":                                "art-trees",
    # GCC
    "gcc":                                "gcc",
    "global carbon council":              "gcc",
    # Korea ETS
    "korea-ets":                          "korea-ets",
    "korea ets":                          "korea-ets",
    "k-ets":                              "korea-ets",
}

# Lowercase-normalize all keys once at import time
RAW_TO_REGISTRY_ID = {k.lower(): v for k, v in RAW_TO_REGISTRY_ID.items()}

# ── In-memory cache: registry_id → full row dict ─────────────────────────────
_registry_cache: dict[str, dict] = {}


# ── Public API ────────────────────────────────────────────────────────────────

def resolve_registry_id(raw: str | None) -> str | None:
    """
    Return the canonical registry_id for a raw string, or None if unrecognised.
    Lookup is case-insensitive.
    """
    if not raw:
        return None
    return RAW_TO_REGISTRY_ID.get(raw.strip().lower())


def seed_ref_registries() -> int:
    """
    Upsert REGISTRIES_SEED into the ref_registries table.
    Safe to call on every startup — fully idempotent.
    Returns the number of rows upserted.
    """
    from carbongpt.repository.db import get_cursor

    with get_cursor() as cur:
        count = 0
        for registry_id, registry_name, registry_short, website in REGISTRIES_SEED:
            cur.execute(
                """
                INSERT INTO ref_registries
                    (registry_id, registry_name, registry_short, website)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (registry_id) DO UPDATE SET
                    registry_name  = EXCLUDED.registry_name,
                    registry_short = EXCLUDED.registry_short,
                    website        = EXCLUDED.website
                """,
                (registry_id, registry_name, registry_short, website),
            )
            count += 1

    logger.info("Seeded %d rows into ref_registries", count)
    _rebuild_cache()
    return count


def _rebuild_cache() -> None:
    """Reload the in-memory registry cache from the DB."""
    global _registry_cache
    try:
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute("SELECT * FROM ref_registries ORDER BY registry_name")
            rows = cur.fetchall()
        _registry_cache = {r["registry_id"]: dict(r) for r in rows}
    except Exception as e:
        logger.warning("Could not rebuild registry cache: %s", e)


def get_all_registries() -> list[dict]:
    """Return all canonical registries (from cache; rebuilds if empty)."""
    if not _registry_cache:
        _rebuild_cache()
    return list(_registry_cache.values())


def get_registry_display_name(registry_id: str | None) -> str:
    """
    Return the human-readable short name for a canonical registry_id.
    Falls back to the raw string if not found.
    """
    if not registry_id:
        return "Unknown"
    if not _registry_cache:
        _rebuild_cache()
    row = _registry_cache.get(registry_id)
    if row:
        return row.get("registry_short") or row.get("registry_name") or registry_id
    return registry_id


def run_registry_normalization_pass() -> dict:
    """
    Backfill ref_registry_id on carbon_projects rows where it is NULL.
    Works by resolving each distinct raw `registry` value through
    RAW_TO_REGISTRY_ID.  Rows with an already-resolved ref_registry_id
    are skipped — safe to call repeatedly.

    Returns a summary dict:
      total_distinct_raw  — how many distinct raw values were found
      resolved            — how many were successfully mapped
      unresolved          — how many could not be mapped
      unresolved_values   — the unmatched raw strings (for review)
    """
    from carbongpt.repository.db import get_cursor

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT registry
            FROM carbon_projects
            WHERE ref_registry_id IS NULL
              AND registry IS NOT NULL
            """
        )
        raw_values = [r["registry"] for r in cur.fetchall()]

    resolved   = 0
    unresolved = []

    for raw in raw_values:
        canonical = resolve_registry_id(raw)
        if canonical:
            with get_cursor() as cur:
                cur.execute(
                    """
                    UPDATE carbon_projects
                    SET ref_registry_id = %s
                    WHERE registry = %s AND ref_registry_id IS NULL
                    """,
                    (canonical, raw),
                )
            resolved += 1
        else:
            unresolved.append(raw)
            logger.warning("Registry normalization: no canonical ID for %r", raw)

    result = {
        "total_distinct_raw": len(raw_values),
        "resolved":           resolved,
        "unresolved":         len(unresolved),
        "unresolved_values":  unresolved,
    }
    logger.info("Registry normalization pass complete: %s", result)
    return result
