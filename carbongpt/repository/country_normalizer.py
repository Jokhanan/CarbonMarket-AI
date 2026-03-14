"""
Country Normalization — Step 2

Three-layer approach:
  1. Exact dict lookup: RAW_TO_ISO maps known variants → ISO alpha-3
  2. Fuzzy fallback: difflib closest match with a 0.82 threshold
  3. NULL: unmapped countries stay NULL in country_iso (logged at WARNING level)

The `countries` table is seeded from COUNTRIES_SEED on first run.
The raw `carbon_projects.country` column is never modified.
"""

import difflib
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# COUNTRIES SEED — ISO 3166-1 alpha-3 with UN macro-region + sub-region
# ---------------------------------------------------------------------------
COUNTRIES_SEED: list[tuple[str, str, str, str]] = [
    # (iso3, canonical_name, region, subregion)
    ("AFG", "Afghanistan",                      "Asia",          "Southern Asia"),
    ("AGO", "Angola",                           "Africa",        "Sub-Saharan Africa"),
    ("ALB", "Albania",                          "Europe",        "Southern Europe"),
    ("ARE", "United Arab Emirates",             "Asia",          "Western Asia"),
    ("ARG", "Argentina",                        "Americas",      "South America"),
    ("ARM", "Armenia",                          "Asia",          "Western Asia"),
    ("AUS", "Australia",                        "Oceania",       "Australia and New Zealand"),
    ("AZE", "Azerbaijan",                       "Asia",          "Western Asia"),
    ("BDI", "Burundi",                          "Africa",        "Sub-Saharan Africa"),
    ("BEN", "Benin",                            "Africa",        "Sub-Saharan Africa"),
    ("BFA", "Burkina Faso",                     "Africa",        "Sub-Saharan Africa"),
    ("BGD", "Bangladesh",                       "Asia",          "Southern Asia"),
    ("BGR", "Bulgaria",                         "Europe",        "Eastern Europe"),
    ("BLZ", "Belize",                           "Americas",      "Central America"),
    ("BOL", "Bolivia",                          "Americas",      "South America"),
    ("BRA", "Brazil",                           "Americas",      "South America"),
    ("BTN", "Bhutan",                           "Asia",          "Southern Asia"),
    ("BWA", "Botswana",                         "Africa",        "Sub-Saharan Africa"),
    ("CAF", "Central African Republic",         "Africa",        "Sub-Saharan Africa"),
    ("CAN", "Canada",                           "Americas",      "Northern America"),
    ("CHE", "Switzerland",                      "Europe",        "Western Europe"),
    ("CHL", "Chile",                            "Americas",      "South America"),
    ("CHN", "China",                            "Asia",          "Eastern Asia"),
    ("CIV", "Côte d'Ivoire",                    "Africa",        "Sub-Saharan Africa"),
    ("CMR", "Cameroon",                         "Africa",        "Sub-Saharan Africa"),
    ("COD", "Democratic Republic of the Congo", "Africa",        "Sub-Saharan Africa"),
    ("COG", "Republic of the Congo",            "Africa",        "Sub-Saharan Africa"),
    ("COL", "Colombia",                         "Americas",      "South America"),
    ("COM", "Comoros",                          "Africa",        "Sub-Saharan Africa"),
    ("CPV", "Cape Verde",                       "Africa",        "Sub-Saharan Africa"),
    ("CRI", "Costa Rica",                       "Americas",      "Central America"),
    ("CUB", "Cuba",                             "Americas",      "Caribbean"),
    ("DOM", "Dominican Republic",               "Americas",      "Caribbean"),
    ("DZA", "Algeria",                          "Africa",        "Northern Africa"),
    ("ECU", "Ecuador",                          "Americas",      "South America"),
    ("EGY", "Egypt",                            "Africa",        "Northern Africa"),
    ("ERI", "Eritrea",                          "Africa",        "Sub-Saharan Africa"),
    ("ETH", "Ethiopia",                         "Africa",        "Sub-Saharan Africa"),
    ("FJI", "Fiji",                             "Oceania",       "Pacific Islands"),
    ("GHA", "Ghana",                            "Africa",        "Sub-Saharan Africa"),
    ("GIN", "Guinea",                           "Africa",        "Sub-Saharan Africa"),
    ("GMB", "The Gambia",                       "Africa",        "Sub-Saharan Africa"),
    ("GNB", "Guinea-Bissau",                    "Africa",        "Sub-Saharan Africa"),
    ("GTM", "Guatemala",                        "Americas",      "Central America"),
    ("GUY", "Guyana",                           "Americas",      "South America"),
    ("HND", "Honduras",                         "Americas",      "Central America"),
    ("HTI", "Haiti",                            "Americas",      "Caribbean"),
    ("IDN", "Indonesia",                        "Asia",          "South-eastern Asia"),
    ("IND", "India",                            "Asia",          "Southern Asia"),
    ("IRQ", "Iraq",                             "Asia",          "Western Asia"),
    ("JAM", "Jamaica",                          "Americas",      "Caribbean"),
    ("JOR", "Jordan",                           "Asia",          "Western Asia"),
    ("KEN", "Kenya",                            "Africa",        "Sub-Saharan Africa"),
    ("KGZ", "Kyrgyzstan",                       "Asia",          "Central Asia"),
    ("KHM", "Cambodia",                         "Asia",          "South-eastern Asia"),
    ("LAO", "Laos",                             "Asia",          "South-eastern Asia"),
    ("LBR", "Liberia",                          "Africa",        "Sub-Saharan Africa"),
    ("LKA", "Sri Lanka",                        "Asia",          "Southern Asia"),
    ("LSO", "Lesotho",                          "Africa",        "Sub-Saharan Africa"),
    ("MAR", "Morocco",                          "Africa",        "Northern Africa"),
    ("MDG", "Madagascar",                       "Africa",        "Sub-Saharan Africa"),
    ("MEX", "Mexico",                           "Americas",      "Central America"),
    ("MLI", "Mali",                             "Africa",        "Sub-Saharan Africa"),
    ("MMR", "Myanmar",                          "Asia",          "South-eastern Asia"),
    ("MOZ", "Mozambique",                       "Africa",        "Sub-Saharan Africa"),
    ("MRT", "Mauritania",                       "Africa",        "Sub-Saharan Africa"),
    ("MWI", "Malawi",                           "Africa",        "Sub-Saharan Africa"),
    ("MYS", "Malaysia",                         "Asia",          "South-eastern Asia"),
    ("NAM", "Namibia",                          "Africa",        "Sub-Saharan Africa"),
    ("NER", "Niger",                            "Africa",        "Sub-Saharan Africa"),
    ("NGA", "Nigeria",                          "Africa",        "Sub-Saharan Africa"),
    ("NIC", "Nicaragua",                        "Americas",      "Central America"),
    ("NPL", "Nepal",                            "Asia",          "Southern Asia"),
    ("NZL", "New Zealand",                      "Oceania",       "Australia and New Zealand"),
    ("PAK", "Pakistan",                         "Asia",          "Southern Asia"),
    ("PAN", "Panama",                           "Americas",      "Central America"),
    ("PER", "Peru",                             "Americas",      "South America"),
    ("PHL", "Philippines",                      "Asia",          "South-eastern Asia"),
    ("PNG", "Papua New Guinea",                 "Oceania",       "Pacific Islands"),
    ("PRY", "Paraguay",                         "Americas",      "South America"),
    ("ROU", "Romania",                          "Europe",        "Eastern Europe"),
    ("RUS", "Russia",                           "Europe",        "Eastern Europe"),
    ("RWA", "Rwanda",                           "Africa",        "Sub-Saharan Africa"),
    ("SDN", "Sudan",                            "Africa",        "Northern Africa"),
    ("SEN", "Senegal",                          "Africa",        "Sub-Saharan Africa"),
    ("SLB", "Solomon Islands",                  "Oceania",       "Pacific Islands"),
    ("SLE", "Sierra Leone",                     "Africa",        "Sub-Saharan Africa"),
    ("SLV", "El Salvador",                      "Americas",      "Central America"),
    ("SOM", "Somalia",                          "Africa",        "Sub-Saharan Africa"),
    ("SSD", "South Sudan",                      "Africa",        "Sub-Saharan Africa"),
    ("STP", "Sao Tome and Principe",            "Africa",        "Sub-Saharan Africa"),
    ("SUR", "Suriname",                         "Americas",      "South America"),
    ("SWZ", "Eswatini",                         "Africa",        "Sub-Saharan Africa"),
    ("TCD", "Chad",                             "Africa",        "Sub-Saharan Africa"),
    ("TGO", "Togo",                             "Africa",        "Sub-Saharan Africa"),
    ("THA", "Thailand",                         "Asia",          "South-eastern Asia"),
    ("TJK", "Tajikistan",                       "Asia",          "Central Asia"),
    ("TLS", "Timor-Leste",                      "Asia",          "South-eastern Asia"),
    ("TTO", "Trinidad and Tobago",              "Americas",      "Caribbean"),
    ("TUN", "Tunisia",                          "Africa",        "Northern Africa"),
    ("TUR", "Turkey",                           "Asia",          "Western Asia"),
    ("TZA", "Tanzania",                         "Africa",        "Sub-Saharan Africa"),
    ("UGA", "Uganda",                           "Africa",        "Sub-Saharan Africa"),
    ("UKR", "Ukraine",                          "Europe",        "Eastern Europe"),
    ("URY", "Uruguay",                          "Americas",      "South America"),
    ("USA", "United States",                    "Americas",      "Northern America"),
    ("UZB", "Uzbekistan",                       "Asia",          "Central Asia"),
    ("VEN", "Venezuela",                        "Americas",      "South America"),
    ("VNM", "Vietnam",                          "Asia",          "South-eastern Asia"),
    ("VUT", "Vanuatu",                          "Oceania",       "Pacific Islands"),
    ("WSM", "Samoa",                            "Oceania",       "Pacific Islands"),
    ("YEM", "Yemen",                            "Asia",          "Western Asia"),
    ("ZAF", "South Africa",                     "Africa",        "Sub-Saharan Africa"),
    ("ZMB", "Zambia",                           "Africa",        "Sub-Saharan Africa"),
    ("ZWE", "Zimbabwe",                         "Africa",        "Sub-Saharan Africa"),
]

# Build canonical_name → iso3 lookup
_NAME_TO_ISO: dict[str, str] = {row[1].lower(): row[0] for row in COUNTRIES_SEED}

# ---------------------------------------------------------------------------
# RAW → ISO MAPPING
# Covers known registry-specific name variants
# ---------------------------------------------------------------------------
RAW_TO_ISO: dict[str, str] = {
    # Democratic Republic of the Congo variants
    "Democratic Republic of Congo":             "COD",
    "Democratic Republic of the Congo":         "COD",
    "Congo, Democratic Republic of the":        "COD",
    "Congo, DR":                                "COD",
    "DR Congo":                                 "COD",
    "DRC":                                      "COD",
    # Republic of the Congo variants
    "Republic of the Congo":                    "COG",
    "Congo":                                    "COG",
    "Congo, Republic of the":                   "COG",
    # Tanzania variants
    "Tanzania, United Republic of":             "TZA",
    "United Republic of Tanzania":              "TZA",
    "Tanzania":                                 "TZA",
    # Vietnam variants
    "Viet Nam":                                 "VNM",
    "Viet nam":                                 "VNM",
    "Vietnam":                                  "VNM",
    # Bolivia variants
    "Bolivia (Plurinational State of)":         "BOL",
    "Bolivia, Plurinational State of":          "BOL",
    "Bolivia":                                  "BOL",
    # Venezuela variants
    "Venezuela (Bolivarian Republic of)":       "VEN",
    "Venezuela, Bolivarian Republic of":        "VEN",
    "Venezuela":                                "VEN",
    # Korea variants
    "Korea, Republic of":                       "KOR",
    "South Korea":                              "KOR",
    "Republic of Korea":                        "KOR",
    # Iran variants
    "Iran (Islamic Republic of)":               "IRN",
    "Iran":                                     "IRN",
    # Laos variants
    "Lao People's Democratic Republic":         "LAO",
    "Lao PDR":                                  "LAO",
    "Lao":                                      "LAO",
    "Laos":                                     "LAO",
    # Moldova variants
    "Moldova, Republic of":                     "MDA",
    "Republic of Moldova":                      "MDA",
    "Moldova":                                  "MDA",
    # Syria variants
    "Syrian Arab Republic":                     "SYR",
    "Syria":                                    "SYR",
    # Libya variants
    "Libya":                                    "LBY",
    "Libyan Arab Jamahiriya":                   "LBY",
    # Myanmar/Burma
    "Burma":                                    "MMR",
    "Myanmar":                                  "MMR",
    # Côte d'Ivoire variants
    "Cote d'Ivoire":                            "CIV",
    "Ivory Coast":                              "CIV",
    "Cote dIvoire":                             "CIV",
    # Eswatini/Swaziland
    "Swaziland":                                "SWZ",
    "Eswatini":                                 "SWZ",
    # Gambia
    "Gambia":                                   "GMB",
    "Gambia, The":                              "GMB",
    "The Gambia":                               "GMB",
    # Cape Verde
    "Cabo Verde":                               "CPV",
    "Cape Verde":                               "CPV",
    # Timor-Leste
    "East Timor":                               "TLS",
    "Timor-Leste":                              "TLS",
    # Sao Tome
    "Sao Tome and Principe":                    "STP",
    "São Tomé and Príncipe":                    "STP",
    # Straightforward aliases
    "Russia":                                   "RUS",
    "Russian Federation":                       "RUS",
    "Turkey":                                   "TUR",
    "Turkiye":                                  "TUR",
    "United States of America":                 "USA",
    "United States":                            "USA",
    "USA":                                      "USA",
    "UK":                                       "GBR",
    "United Kingdom":                           "GBR",
    "UAE":                                      "ARE",
    "Kyrgyz Republic":                          "KGZ",
    "Macedonia":                                "MKD",
    "North Macedonia":                          "MKD",
}

# Normalise all keys to lowercase for lookup
RAW_TO_ISO = {k.lower(): v for k, v in RAW_TO_ISO.items()}

# Build the full name list for fuzzy matching
_ALL_KNOWN_NAMES: dict[str, str] = {**_NAME_TO_ISO}
for raw, iso in RAW_TO_ISO.items():
    _ALL_KNOWN_NAMES[raw] = iso


def resolve_country_iso(raw_name: str) -> str | None:
    """
    Resolve a raw country name string to an ISO alpha-3 code.

    Order:
      1. Exact dict match (case-insensitive)
      2. Canonical-name match
      3. difflib fuzzy match (threshold ≥ 0.82)
      4. None — logs a WARNING
    """
    if not raw_name:
        return None

    normalized = raw_name.strip().lower()

    # 1. Exact match in RAW_TO_ISO or _NAME_TO_ISO
    if normalized in _ALL_KNOWN_NAMES:
        return _ALL_KNOWN_NAMES[normalized]

    # 2. difflib fuzzy match
    candidates = list(_ALL_KNOWN_NAMES.keys())
    matches = difflib.get_close_matches(normalized, candidates, n=1, cutoff=0.82)
    if matches:
        iso = _ALL_KNOWN_NAMES[matches[0]]
        logger.debug("Fuzzy-matched country %r → %s (via %r)", raw_name, iso, matches[0])
        return iso

    logger.warning("Could not resolve country ISO for: %r", raw_name)
    return None


# ---------------------------------------------------------------------------
# DB OPERATIONS
# ---------------------------------------------------------------------------
def seed_countries_table() -> int:
    """Insert COUNTRIES_SEED into the countries table. Safe to call repeatedly."""
    from carbongpt.repository.db import get_cursor

    inserted = 0
    try:
        with get_cursor() as cur:
            for iso3, name, region, subregion in COUNTRIES_SEED:
                cur.execute(
                    """
                    INSERT INTO countries (country_iso, country_name, region, subregion)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (country_iso) DO NOTHING
                    """,
                    (iso3, name, region, subregion),
                )
                inserted += 1
    except Exception as e:
        logger.error("Failed to seed countries table: %s", e)
        return 0

    logger.info("Countries table seeded with %d entries", inserted)
    return inserted


def run_country_normalization_pass() -> dict:
    """
    Update carbon_projects.country_iso for all rows where it is NULL or stale.
    Safe to call multiple times.
    Returns summary counts.
    """
    from carbongpt.repository.db import get_cursor

    logger.info("Starting country normalization pass...")
    total = resolved = unresolved = errors = 0

    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, country FROM carbon_projects WHERE country IS NOT NULL")
            rows = cur.fetchall()
    except Exception as e:
        logger.error("Failed to fetch carbon_projects for country normalization: %s", e)
        return {"total": 0, "resolved": 0, "unresolved": 0, "errors": 1}

    for row in rows:
        total += 1
        try:
            iso = resolve_country_iso(row["country"])
            if iso:
                with get_cursor() as cur:
                    cur.execute(
                        "UPDATE carbon_projects SET country_iso = %s WHERE id = %s",
                        (iso, row["id"]),
                    )
                resolved += 1
            else:
                unresolved += 1
        except Exception as e:
            errors += 1
            logger.warning("Country normalization failed for id=%s country=%r: %s",
                           row["id"], row.get("country"), e)

    logger.info(
        "Country normalization complete: %d rows, %d resolved, %d unresolved, %d errors",
        total, resolved, unresolved, errors,
    )
    return {"total": total, "resolved": resolved, "unresolved": unresolved, "errors": errors}
