"""
Location utilities: country list, fNRB normalization, and Nominatim geocoding.
"""

import pycountry

# ---------------------------------------------------------------------------
# Country name normalization
# ---------------------------------------------------------------------------
# pycountry uses ISO 3166-1 official names which differ from TOOL33 keys
# for 9 countries.  This mapping converts pycountry → TOOL33 key so that
# fNRB lookup works seamlessly whichever name is stored in the DB.

PYCOUNTRY_TO_TOOL33 = {
    "Bolivia, Plurinational State of": "Bolivia",
    "Congo, The Democratic Republic of the": "Congo DR",
    "Côte d'Ivoire": "Cote d'Ivoire",
    "Iran, Islamic Republic of": "Iran",
    "Lao People's Democratic Republic": "Lao PDR",
    "Syrian Arab Republic": "Syria",
    "Tanzania, United Republic of": "Tanzania",
    "Türkiye": "Turkey",
    "Viet Nam": "Vietnam",
}

# Reverse: TOOL33 key → pycountry display name
TOOL33_TO_PYCOUNTRY = {v: k for k, v in PYCOUNTRY_TO_TOOL33.items()}

# Sorted list of all ISO 3166-1 country names for the UI selector
ALL_COUNTRIES: list[str] = sorted(c.name for c in pycountry.countries)


def normalize_to_tool33(pycountry_name: str) -> str:
    """Return the TOOL33_FNRB_BY_COUNTRY key for a pycountry display name.

    For the 81 exact matches this is a no-op.
    For the 9 exceptions the mapping is applied.
    Returns the input unchanged if not found in either mapping.
    """
    return PYCOUNTRY_TO_TOOL33.get(pycountry_name, pycountry_name)


def get_fnrb_for_country(pycountry_name: str) -> float | None:
    """Return the TOOL33 default fNRB for a country selected from the UI.

    Returns None if the country has no TOOL33 entry.
    """
    from carbongpt.core.tool_defaults import TOOL33_FNRB_BY_COUNTRY
    tool33_key = normalize_to_tool33(pycountry_name)
    return TOOL33_FNRB_BY_COUNTRY.get(tool33_key)


# ---------------------------------------------------------------------------
# Nominatim geocoding (OpenStreetMap, no API key required)
# ---------------------------------------------------------------------------

def geocode_location(query: str, country: str = "") -> dict | None:
    """Attempt to geocode a location string using Nominatim.

    Parameters
    ----------
    query   : free-text location (region, district, village, etc.)
    country : country name to restrict results (optional but improves accuracy)

    Returns
    -------
    dict with keys: latitude, longitude, display_name
    or None if the request fails or returns no results.

    The caller is responsible for showing an appropriate message on None.
    Timeout is 5 seconds — never blocks the UI.
    """
    try:
        import requests
        params = {
            "q": f"{query}, {country}" if country else query,
            "format": "json",
            "limit": 1,
        }
        headers = {"User-Agent": "CarbonGPT/1.0 (carbon project management platform)"}
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers,
            timeout=5,
        )
        results = resp.json()
        if results:
            r = results[0]
            return {
                "latitude": float(r["lat"]),
                "longitude": float(r["lon"]),
                "display_name": r.get("display_name", ""),
            }
        return None
    except Exception:
        return None
