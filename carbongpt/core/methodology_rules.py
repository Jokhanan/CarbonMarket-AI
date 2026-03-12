"""
Methodology-driven rules for Setup flow.

Centralizes derivable metadata so the UI can auto-fill fields
instead of asking the user redundant questions.
"""

CREDITING_PERIOD_DEFAULTS = {
    "GoldStandard": 5,
    "Verra": 7,
    "CDM": 7,
}

METHODOLOGY_METADATA = {
    "TPDDTEC": {
        "activity_type": "Energy efficiency",
        "sectoral_scope": "Energy demand",
        "scale_options": ["Micro-scale", "Small-scale", "Large-scale"],
        "fuel_field_mode": "methodology_choices",
    },
    "GS-MECD": {
        "activity_type": "Energy efficiency / Fuel switch",
        "sectoral_scope": "Energy demand",
        "scale_options": [],
        "fuel_field_mode": "methodology_choices",
    },
    "VM0050": {
        "activity_type": "Energy efficiency",
        "sectoral_scope": "Energy demand",
        "scale_options": [],
        "fuel_field_mode": "methodology_choices",
    },
    "ACM0002": {
        "activity_type": "Greenfield",
        "sectoral_scope": "Energy industries (renewable sources)",
        "scale_options": ["Large-scale"],
        "fuel_field_mode": "not_applicable",
    },
    "AMS-I.D.": {
        "activity_type": "Greenfield",
        "sectoral_scope": "Energy industries (renewable sources)",
        "scale_options": ["Small-scale"],
        "fuel_field_mode": "not_applicable",
    },
}

# ── TPDDTEC-specific constants ──────────────────────────────────────────────

TPDDTEC_BASELINE_FUEL_OPTIONS = ["wood", "charcoal"]
TPDDTEC_PROJECT_FUEL_OPTIONS = ["wood", "charcoal"]

TPDDTEC_FUEL_DISPLAY = {
    "wood": "Wood (firewood)",
    "charcoal": "Charcoal",
}

TPDDTEC_SCALE_OPTIONS = [
    "Micro-scale",
    "Small-scale",
    "Large-scale",
]

TPDDTEC_SCALE_DESCRIPTIONS = {
    "Micro-scale": "10,000 tCO2e/yr or less",
    "Small-scale": "Up to 60 GWh/yr energy saving",
    "Large-scale": "More than 60 GWh/yr energy saving",
}

# Method 2 default baseline consumption constants (from TPDDTEC v4.0 ICS 14)
TPDDTEC_METHOD2_DEFAULT_CONSUMPTION = 0.5    # tonnes/capita/year fuelwood
TPDDTEC_METHOD2_THRESHOLD_CONSUMPTION = 0.75  # t/capita/yr — above this needs justification
TPDDTEC_METHOD2_CAP_CONSUMPTION = 0.95        # t/capita/yr — hard cap, never exceeded

# NCV in TJ/ton (TPDDTEC methodology unit — same as 15.6 TJ/Gg or 15.6 GJ/t)
TPDDTEC_NCV_WOOD_TJ_PER_TON = 0.0156
TPDDTEC_EF_CO2_WOOD = 112.0       # tCO2/TJ — locked in Method 2
TPDDTEC_EF_NONCO2_WOOD_AR5 = 9.46 # tCO2e/TJ — locked in Method 2

# Charcoal EFs (with production — methodology default, TPDDTEC v4.0 ICS 8/9)
TPDDTEC_EF_CO2_CHARCOAL_WITH_PRODUCTION = 165.22
TPDDTEC_EF_NONCO2_CHARCOAL_WITH_PRODUCTION_AR5 = 44.83
TPDDTEC_EF_CO2_CHARCOAL_CAP = 197.15
TPDDTEC_EF_NONCO2_CHARCOAL_CAP_AR5 = 92.29
TPDDTEC_NCV_CHARCOAL_TJ_PER_TON = 0.0295


# ── MECD-specific constants ──────────────────────────────────────────────────

MECD_DEVICE_OPTIONS = [
    "electric_cookstove",
    "electric_pressure_cooker",
    "lpg_cookstove",
    "biogas_cookstove",
    "bioethanol_cookstove",
]

MECD_DEVICE_DISPLAY = {
    "electric_cookstove": "Electric cookstove (induction / DC / AC heating)",
    "electric_pressure_cooker": "Electric pressure cooker (EPC)",
    "lpg_cookstove": "LPG cookstove",
    "biogas_cookstove": "Biogas cookstove",
    "bioethanol_cookstove": "Bio-ethanol cookstove",
}

# Fuel type (electric vs fossil/bio-fuel) derived from device
MECD_DEVICE_FUEL_TYPE = {
    "electric_cookstove": "electric",
    "electric_pressure_cooker": "electric",
    "lpg_cookstove": "lpg",
    "biogas_cookstove": "biogas",
    "bioethanol_cookstove": "bioethanol",
}

# Case 1 = WBT applicable; Case 2 = WBT not applicable (EPC, ratio logic)
MECD_DEVICE_CASE = {
    "electric_cookstove": "1",
    "electric_pressure_cooker": "2",
    "lpg_cookstove": "1",
    "biogas_cookstove": "1",
    "bioethanol_cookstove": "1",
}

# ER eligibility: "both" = fuel-switch + efficiency; "efficiency_only" = fossil fuel rule §2.2.1(g)
MECD_DEVICE_ER_ELIGIBILITY = {
    "electric_cookstove": "both",
    "electric_pressure_cooker": "both",
    "lpg_cookstove": "efficiency_only",
    "biogas_cookstove": "both",
    "bioethanol_cookstove": "both",
}

MECD_BASELINE_FUEL_OPTIONS = [
    "wood_three_stone",
    "wood_other_biomass",
    "charcoal",
    "lpg",
    "kerosene",
    "biogas",
]

MECD_BASELINE_FUEL_DISPLAY = {
    "wood_three_stone": "Wood – three-stone fire",
    "wood_other_biomass": "Wood – other conventional biomass stove",
    "charcoal": "Charcoal – conventional cookstove",
    "lpg": "LPG – conventional stove",
    "kerosene": "Kerosene – conventional stove",
    "biogas": "Biogas – conventional use",
}

MECD_REGION_OPTIONS = ["africa", "asia"]
MECD_REGION_DISPLAY = {
    "africa": "Sub-Saharan Africa",
    "asia": "Asia",
}


def get_methodology_metadata(code):
    if not code:
        return None
    normalized = code.upper().replace("GS-", "").strip()
    meta = METHODOLOGY_METADATA.get(normalized)
    if meta:
        return dict(meta)
    for key, val in METHODOLOGY_METADATA.items():
        if key.upper() == normalized:
            return dict(val)
    return None


def get_crediting_period_default(standard):
    return CREDITING_PERIOD_DEFAULTS.get(standard, 7)


def has_methodology_fuel_choices(code, meth_parsed=None):
    if meth_parsed:
        context_dims = meth_parsed.get("context_dimensions", [])
        fuel_keys = {"baseline_fuel", "project_fuel"}
        for dim in context_dims:
            if dim.get("dimension_key", "") in fuel_keys:
                return True
        return False
    meta = get_methodology_metadata(code)
    if not meta:
        return False
    return meta.get("fuel_field_mode") == "methodology_choices"


# ── TPDDTEC method derivation ────────────────────────────────────────────────

def derive_tpddtec_method(baseline_fuel, project_fuel, scale, baseline_approach="measured"):
    """
    Derive the correct TPDDTEC method and methodology from project configuration.

    Parameters
    ----------
    baseline_fuel : str  — "wood" or "charcoal"
    project_fuel  : str  — "wood" or "charcoal"
    scale         : str  — "Micro-scale", "Small-scale", or "Large-scale"
    baseline_approach : str — "default" or "measured"
                        Only relevant when same fuel; ignored otherwise.

    Returns
    -------
    dict with keys:
        method_id      : "method_1" | "method_2" | "method_3"
        method_label   : human-readable label
        method_number  : 1 | 2 | 3
        reason         : plain-English explanation
        baseline_approach_locked : bool — True when approach is forced by fuel/scale
        approach_lock_reason     : str  — why it is locked (if locked)
        method2_available        : bool — whether Method 2 is an option
    """
    bl = (baseline_fuel or "").lower().strip()
    pj = (project_fuel or "").lower().strip()
    sc = (scale or "").lower()

    same_fuel = (bl == pj)
    is_charcoal_any = (bl == "charcoal" or pj == "charcoal")
    is_large_scale = "large" in sc
    is_micro_or_small = not is_large_scale

    method2_available = (
        same_fuel
        and bl == "wood"
        and is_micro_or_small
    )

    if not same_fuel:
        return {
            "method_id": "method_3",
            "method_label": "Method 3",
            "method_number": 3,
            "reason": (
                f"Different fuels ({_fuel_label(bl)} baseline, {_fuel_label(pj)} project) — "
                "emission reductions from fuel switch and efficiency gains."
            ),
            "baseline_approach_locked": True,
            "approach_lock_reason": "Method 3 always requires measured field test data (BFT and PFT).",
            "method2_available": False,
        }

    # Same fuel from here
    if bl == "charcoal":
        return {
            "method_id": "method_1",
            "method_label": "Method 1",
            "method_number": 1,
            "reason": (
                "Same fuel (charcoal) — Method 1 applies. "
                "Method 2 is not available for charcoal; measured field test data is required."
            ),
            "baseline_approach_locked": True,
            "approach_lock_reason": (
                "Method 2 is restricted to woody biomass (fuelwood) only. "
                "Your project uses charcoal — measured baseline consumption (BFT) is required."
            ),
            "method2_available": False,
        }

    if is_large_scale:
        return {
            "method_id": "method_1",
            "method_label": "Method 1",
            "method_number": 1,
            "reason": (
                "Same fuel (wood), large-scale project — Method 1 applies. "
                "Method 2 is only available for micro-scale and small-scale projects."
            ),
            "baseline_approach_locked": True,
            "approach_lock_reason": (
                "Method 2 is restricted to micro-scale and small-scale projects. "
                "Measured baseline consumption (BFT) is required for large-scale projects."
            ),
            "method2_available": False,
        }

    # Same fuel, wood, micro or small-scale — user chooses approach
    if baseline_approach == "default":
        return {
            "method_id": "method_2",
            "method_label": "Method 2",
            "method_number": 2,
            "reason": (
                "Same fuel (wood), micro/small-scale, using methodology default baseline "
                "(0.5 t/capita/year fuelwood). No Baseline Performance Field Test needed."
            ),
            "baseline_approach_locked": False,
            "approach_lock_reason": "",
            "method2_available": True,
        }
    else:
        return {
            "method_id": "method_1",
            "method_label": "Method 1",
            "method_number": 1,
            "reason": (
                "Same fuel (wood), using measured baseline fuel consumption from "
                "Baseline Performance Field Test (BFT)."
            ),
            "baseline_approach_locked": False,
            "approach_lock_reason": "",
            "method2_available": True,
        }


def derive_methodology_from_fuels(standard, baseline_fuel, project_fuel):
    """
    Derive the methodology name from the standard and fuel combination.

    Returns
    -------
    dict with keys:
        methodology     : str — e.g. "TPDDTEC"
        methodology_display : str — human label
        note            : str — explanation or redirect message
        blocked         : bool — True if this combination cannot be served by known methodology
    """
    bl = (baseline_fuel or "").lower().strip()
    pj = (project_fuel or "").lower().strip()

    if standard == "Verra":
        return {
            "methodology": "VM0050",
            "methodology_display": "VM0050",
            "note": "Verra VCS cookstove projects use VM0050.",
            "blocked": False,
        }

    if standard == "GoldStandard":
        biomass_fuels = {"wood", "charcoal"}
        bl_is_biomass = bl in biomass_fuels
        pj_is_biomass = pj in biomass_fuels

        if bl_is_biomass and pj_is_biomass:
            return {
                "methodology": "TPDDTEC",
                "methodology_display": "TPDDTEC v4.0",
                "note": "Gold Standard cookstove projects with biomass fuels use TPDDTEC.",
                "blocked": False,
            }

        if pj in ("lpg", "electric", "electricity", "biogas", "natural_gas"):
            return {
                "methodology": None,
                "methodology_display": "Metered & Measured",
                "note": (
                    "Projects introducing LPG or electricity as project fuel use the "
                    "'Methodology for Metered & Measured Energy Cooking Devices'. "
                    "TPDDTEC v4.0 does not cover new projects with fossil fuel project fuels "
                    "(Footnote 1, Table 1)."
                ),
                "blocked": True,
            }

    return {
        "methodology": None,
        "methodology_display": "Unknown",
        "note": "Could not determine methodology from the selected combination.",
        "blocked": True,
    }


def get_tpddtec_method_badge_info(method_id):
    """Return display label and color for a TPDDTEC method badge."""
    badges = {
        "method_1": {
            "label": "TPDDTEC — Method 1",
            "description": "Same fuel, measured baseline (BFT required)",
            "color": "#0d9488",
        },
        "method_2": {
            "label": "TPDDTEC — Method 2",
            "description": "Same fuel (wood), methodology default baseline (0.5 t/capita/yr)",
            "color": "#0d9488",
        },
        "method_3": {
            "label": "TPDDTEC — Method 3",
            "description": "Different fuels — fuel switch + efficiency gains",
            "color": "#0d9488",
        },
    }
    return badges.get(method_id, {"label": "TPDDTEC", "description": "", "color": "#0d9488"})


def compute_sfc_b_method2(household_size, devices_per_household=1):
    """
    Derive SFC_b (t/technology*day) for Method 2 from the TPDDTEC default.

    Formula: 0.5 t/capita/yr × household_size / devices_per_household / 365
    """
    return TPDDTEC_METHOD2_DEFAULT_CONSUMPTION * household_size / devices_per_household / 365.0


def _fuel_label(fuel_key):
    return TPDDTEC_FUEL_DISPLAY.get(fuel_key, fuel_key or "unknown fuel")
