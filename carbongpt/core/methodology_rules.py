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


# ── VM0050-specific constants (VCS v1.0, 9 October 2024) ────────────────────
#
# Sources:
#   §8.1.1 Option 2  — default fuel consumption per capita
#   §9.1            — "Data and Parameters Available at Validation" parameter tables
#   §4              — Applicability Conditions (efficiency thresholds)
#   §8.3 / Eq. 11  — Leakage 0.95 factor
#   Footnote 22     — TOOL30 uncertainty discount

# Default baseline fuel consumption (§8.1.1, Option 2 — IPCC-derived)
VM0050_DEFAULT_WOOD_CONSUMPTION_PER_CAPITA    = 0.50   # t/capita/yr, air-dried firewood
VM0050_DEFAULT_CHARCOAL_CONSUMPTION_PER_CAPITA = 0.13  # t/capita/yr

# Fuel NCV defaults — IPCC 2006 Guidelines (§9.1, NCVb,i / NCVp,j table)
VM0050_NCV_WOOD_TJ_PER_TON      = 0.0156   # TJ/tonne (= 15.6 TJ/Gg)
VM0050_NCV_CHARCOAL_TJ_PER_TON  = 0.0295   # TJ/tonne (= 29.5 TJ/Gg)

# CO2 emission factors — IPCC 2006 (§9.1, EFb,i,CO2 table)
VM0050_EF_CO2_WOOD                         = 112.0    # tCO2/TJ
VM0050_EF_CO2_CHARCOAL_COMBUSTION_ONLY     = 112.0    # tCO2/TJ — renewable charcoal in project, fNRB=0
VM0050_EF_CO2_CHARCOAL_WITH_PRODUCTION     = 165.22   # tCO2/TJ — non-renewable biomass baseline charcoal

# Non-CO2 emission factors — AR5 GWP (§9.1, EFb,i,nonCO2 table)
VM0050_EF_NONCO2_WOOD_AR5                           = 9.46    # tCO2e/TJ
VM0050_EF_NONCO2_CHARCOAL_COMBUSTION_ONLY_AR5       = 5.865   # tCO2e/TJ — combustion only
VM0050_EF_NONCO2_CHARCOAL_WITH_PRODUCTION_AR5       = 44.83   # tCO2e/TJ — combustion + production

# Wood-to-charcoal conversion factor (§9.1, CF table, CDM TOOL33 default)
VM0050_CF_DEFAULT                   = 4.0   # t dry wood / t charcoal
VM0050_CF_MAX_WITH_JUSTIFICATION    = 6.0   # max allowed with national/regional substantiation

# Baseline device efficiency defaults (§9.1, ηold,avg table)
VM0050_ETA_THREE_STONE_FIRE = 0.15   # 15% — default for three-stone fire / no improved air supply or chimney

# Minimum initial thermal efficiency thresholds (§4, Conditions 8–10)
VM0050_MIN_ETA_BIOMASS_EE_OR_FUEL_SWITCH = 0.25   # §4 cond. 8 — biomass efficient or fuel-switch devices
VM0050_MIN_ETA_LPG_BIOETHANOL            = 0.30   # §4 cond. 9 — LPG or bioethanol devices
VM0050_MIN_ETA_HOT_PLATE_ELECTRIC        = 0.40   # §4 cond. 10a — hot plates and electric hobs
VM0050_MIN_ETA_INDUCTION_ELECTRIC        = 0.70   # §4 cond. 10b — induction stoves and other electric

# Leakage: standard 5% deduction applied as 0.95 factor to (BE - PE) (§8.3, Eq. 11)
VM0050_LEAKAGE_RETENTION_FACTOR = 0.95

# fNRB: uncertainty discount when using CDM TOOL30 (Footnote 22)
# If fNRB from TOOL30 = 0.60, then applied fNRB = 0.60 × (1 − 0.26) = 0.444
VM0050_FNRB_TOOL30_UNCERTAINTY_DISCOUNT = 0.26

# LPG crediting sunset: credits cannot be issued for periods after 31 December 2045 (§4, cond. 11c)
VM0050_LPG_CREDITING_SUNSET_YEAR = 2045

# Confidence and precision requirement for all measurement campaigns (§6.2, §8.1.1, §8.2.1.1)
VM0050_REQUIRED_CONFIDENCE_PRECISION = "90/10"

# Backup generator threshold: if backup > 1% of annual electricity, must exclude that percentage of ERs
VM0050_BACKUP_GENERATOR_THRESHOLD_PCT = 1.0   # percent

# Self-generated renewable electricity: backup non-renewable cap
VM0050_SELF_GEN_NONRENEWABLE_MAX_PCT = 20.0   # percent


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


# ── VM0050 decision engine ───────────────────────────────────────────────────

#: Display labels for VM0050 project device types
VM0050_DEVICE_OPTIONS = [
    "biomass_ee",
    "biomass_switch",
    "lpg",
    "bioethanol",
    "electric_grid",
    "electric_self",
]

VM0050_DEVICE_DISPLAY = {
    "biomass_ee":    "Biomass improved stove (efficiency improvement, same fuel)",
    "biomass_switch": "Biomass fuel switch (e.g. wood → charcoal or vice versa)",
    "lpg":           "LPG stove (fossil fuel project device)",
    "bioethanol":    "Bioethanol stove",
    "electric_grid": "Electric stove / hot plate / induction (grid electricity)",
    "electric_self": "Electric stove (self-generated renewable electricity)",
}

VM0050_DEVICE_FUEL_CLASS = {
    "biomass_ee":    "biomass",
    "biomass_switch": "biomass",
    "lpg":           "fossil",
    "bioethanol":    "fossil",
    "electric_grid": "electric",
    "electric_self": "electric",
}

#: Which project emissions equation each device type uses (VM0050)
VM0050_DEVICE_PROJECT_EQ = {
    "biomass_ee":    "Eq. 7",
    "biomass_switch": "Eq. 7",
    "lpg":           "Eq. 8",
    "bioethanol":    "Eq. 8",
    "electric_grid": "Eq. 9",
    "electric_self": "Eq. 10",
}

#: ECi,y determination options for biomass-baseline projects
VM0050_EC_OPTIONS = [
    "option_2_default",
    "option_1_kpt",
    "eq3_efficiency",
    "eq5_cct",
]

VM0050_EC_OPTION_DISPLAY = {
    "option_2_default": "Option 2 — IPCC default (0.5 t/capita/yr wood or 0.13 t/capita/yr charcoal)",
    "option_1_kpt":     "Option 1 — Kitchen Performance Test (KPT, 90/10 confidence/precision)",
    "eq3_efficiency":   "Eq. 3 — Efficiency back-calculation from project device (same-fuel projects only)",
    "eq5_cct":          "Eq. 5 — Controlled Cooking Test ratio (electric pressure cooker only)",
}

VM0050_EC_OPTION_EQ = {
    "option_2_default": "Eq. 2",
    "option_1_kpt":     "Eq. 2",
    "eq3_efficiency":   "Eq. 3",
    "eq5_cct":          "Eq. 5",
}

#: fNRB source options for VM0050 (§9.2 priority order)
VM0050_FNRB_OPTIONS = [
    "unfccc_national",
    "tool30",
    "tool33_v3",
]

VM0050_FNRB_DISPLAY = {
    "unfccc_national": "UNFCCC national default (1st preference — draft values acceptable)",
    "tool30":          "CDM TOOL30 result × 0.74 (26% uncertainty discount, VM0050 Footnote 22)",
    "tool33_v3":       "CDM TOOL33 v3 Table 2 / Table 3 (regional or national default)",
}


def derive_vm0050_method(
    baseline_fuel: str,
    project_device: str,
    baseline_ec_option: str,
    fnrb_source: str = "unfccc_national",
) -> dict:
    """
    Derive the VM0050 calculation route from user-selected inputs.

    Parameters
    ----------
    baseline_fuel        : "wood" | "charcoal"
    project_device       : one of VM0050_DEVICE_OPTIONS
    baseline_ec_option   : one of VM0050_EC_OPTIONS
    fnrb_source          : one of VM0050_FNRB_OPTIONS

    Returns
    -------
    dict with keys:
        method_id          : str — compact identifier for this route
        method_label       : str — short human label
        baseline_eq        : str — "Eq. 1" for biomass baseline, "Eq. 6" for fossil baseline
        baseline_ec_eq     : str — "Eq. 2", "Eq. 3", or "Eq. 5"
        project_eq         : str — "Eq. 7", "Eq. 8", "Eq. 9", or "Eq. 10"
        leakage_eq         : str — always "Eq. 11 (0.95 factor)"
        fnrb_on_baseline   : bool — True for biomass baseline
        fnrb_on_project    : bool — True for biomass project device
        requires_kpt       : bool
        requires_cct       : bool
        requires_tool07    : bool
        requires_tool05    : bool
        min_eta_threshold  : float | None
        default_consumption: float | None — t/capita/yr if Option 2
        warnings           : list[str]
        reason             : str — one-line explanation
        blocked            : bool
        blocked_reason     : str
    """
    bl = (baseline_fuel or "wood").lower().strip()
    dev = (project_device or "biomass_ee").lower().strip()
    ec_opt = (baseline_ec_option or "option_2_default").lower().strip()
    fnrb_src = (fnrb_source or "unfccc_national").lower().strip()

    warnings_out: list[str] = []
    blocked = False
    blocked_reason = ""

    # VM0050 baseline is always biomass for most projects
    # (Eq. 1 for biomass baseline, Eq. 6 only when fossil baseline — very rare)
    fnrb_on_baseline = (bl in ("wood", "charcoal"))
    baseline_eq = "Eq. 1" if fnrb_on_baseline else "Eq. 6"

    fuel_class = VM0050_DEVICE_FUEL_CLASS.get(dev, "biomass")
    fnrb_on_project = (fuel_class == "biomass")
    project_eq = VM0050_DEVICE_PROJECT_EQ.get(dev, "Eq. 7")

    # Eq. 3 only valid when same fuel in baseline and project
    same_fuel_project = (dev in ("biomass_ee",))  # EE = same fuel; fuel switch = different
    if ec_opt == "eq3_efficiency" and not same_fuel_project:
        warnings_out.append(
            "Eq. 3 (efficiency back-calculation) is only valid when the project device uses the same fuel "
            "as the baseline. Switching to Option 2 default."
        )
        ec_opt = "option_2_default"

    # Eq. 5 only valid for electric pressure cookers
    if ec_opt == "eq5_cct" and dev not in ("electric_grid", "electric_self"):
        warnings_out.append(
            "Eq. 5 (CCT ratio) is only applicable to electric pressure cooker project devices. "
            "Switching to Option 2 default."
        )
        ec_opt = "option_2_default"

    baseline_ec_eq = VM0050_EC_OPTION_EQ.get(ec_opt, "Eq. 2")

    # Minimum efficiency thresholds by device type (§4)
    min_eta_map = {
        "biomass_ee":    VM0050_MIN_ETA_BIOMASS_EE_OR_FUEL_SWITCH,
        "biomass_switch": VM0050_MIN_ETA_BIOMASS_EE_OR_FUEL_SWITCH,
        "lpg":           VM0050_MIN_ETA_LPG_BIOETHANOL,
        "bioethanol":    VM0050_MIN_ETA_LPG_BIOETHANOL,
        "electric_grid": None,  # hot plate vs induction depends on sub-type; both noted in label
        "electric_self": None,
    }
    min_eta = min_eta_map.get(dev)

    # Default consumption for Option 2
    default_consumption = None
    if ec_opt == "option_2_default":
        default_consumption = (
            VM0050_DEFAULT_WOOD_CONSUMPTION_PER_CAPITA if bl == "wood"
            else VM0050_DEFAULT_CHARCOAL_CONSUMPTION_PER_CAPITA
        )

    # Tool requirements
    requires_kpt = ec_opt in ("option_1_kpt",)
    requires_cct = ec_opt == "eq5_cct"
    requires_tool07 = dev == "electric_grid"
    requires_tool05 = dev == "electric_grid"

    # LPG sunset warning (§4 cond. 11c)
    if dev == "lpg":
        warnings_out.append(
            f"LPG project devices: credits cannot be issued for periods after "
            f"{VM0050_LPG_CREDITING_SUNSET_YEAR}. Confirm crediting period end date."
        )

    # fNRB source note
    fnrb_label = VM0050_FNRB_DISPLAY.get(fnrb_src, fnrb_src)
    tool30_note = " (×0.74 applied)" if fnrb_src == "tool30" else ""

    # Build method_id
    method_id = f"{bl}_{dev}_{ec_opt}"

    # Human label
    dev_label = VM0050_DEVICE_DISPLAY.get(dev, dev)
    ec_label_short = {
        "option_2_default": "Option 2 (IPCC default)",
        "option_1_kpt":     "Option 1 (KPT)",
        "eq3_efficiency":   "Eq. 3 (η back-calc)",
        "eq5_cct":          "Eq. 5 (CCT)",
    }.get(ec_opt, ec_opt)

    method_label = f"{bl.capitalize()} baseline — {dev_label} — ECi,y via {ec_label_short}"

    reason = (
        f"Baseline: {baseline_eq} ({bl}, fNRB={'applied' if fnrb_on_baseline else 'not applied'}). "
        f"ECi,y: {baseline_ec_eq}. "
        f"Project: {project_eq} (fNRB={'applied' if fnrb_on_project else 'not applied'}). "
        f"fNRB source: {fnrb_label}{tool30_note}. "
        f"Leakage: Eq. 11 — 0.95 × (BE − PE)."
    )

    return {
        "method_id":           method_id,
        "method_label":        method_label,
        "baseline_eq":         baseline_eq,
        "baseline_ec_eq":      baseline_ec_eq,
        "project_eq":          project_eq,
        "leakage_eq":          "Eq. 11 — (BE − PE) × 0.95 − LERB,y",
        "fnrb_on_baseline":    fnrb_on_baseline,
        "fnrb_on_project":     fnrb_on_project,
        "requires_kpt":        requires_kpt,
        "requires_cct":        requires_cct,
        "requires_tool07":     requires_tool07,
        "requires_tool05":     requires_tool05,
        "min_eta_threshold":   min_eta,
        "default_consumption": default_consumption,
        "fnrb_source":         fnrb_src,
        "fnrb_source_label":   fnrb_label,
        "warnings":            warnings_out,
        "reason":              reason,
        "blocked":             blocked,
        "blocked_reason":      blocked_reason,
    }


def vm0050_hierarchy_html(method: dict) -> str:
    """
    Generate an HTML decision-tree card for a VM0050 method result.

    Renders four connected nodes — Baseline, ECi,y Route, Project Device,
    and Net ER — as a horizontal flow diagram using inline CSS only.
    Active nodes use colour-coded badges; requirement pills show what
    tools or surveys are needed.

    Parameters
    ----------
    method : dict returned by derive_vm0050_method()

    Returns
    -------
    HTML string suitable for st.markdown(..., unsafe_allow_html=True)
    """
    TEAL   = "#0d9488"
    BLUE   = "#2563eb"
    PURPLE = "#7c3aed"
    SLATE  = "#1e293b"
    AMBER  = "#b45309"

    fnrb_badge_colour = {"unfccc_national": TEAL, "tool30": BLUE, "tool33_v3": SLATE}.get(
        method.get("fnrb_source", "unfccc_national"), TEAL
    )
    fnrb_short = {
        "unfccc_national": "UNFCCC national",
        "tool30":          "TOOL30 ×0.74",
        "tool33_v3":       "TOOL33 v3",
    }.get(method.get("fnrb_source", "unfccc_national"), "UNFCCC national")

    dev_label_map = {
        "biomass_ee":    "Biomass EE stove",
        "biomass_switch": "Biomass fuel switch",
        "lpg":           "LPG stove",
        "bioethanol":    "Bioethanol stove",
        "electric_grid": "Electric (grid)",
        "electric_self": "Electric (self-gen)",
    }
    dev_key = method.get("method_id", "").split("_", 2)[-1].rsplit("_", 3)[0] if "_" in method.get("method_id", "") else ""
    # Derive device key more robustly from method_id: "wood_biomass_ee_option_2_default"
    mid = method.get("method_id", "")
    dev_disp = "Unknown"
    for dk, dl in dev_label_map.items():
        if dk in mid:
            dev_disp = dl
            break

    proj_eq = method.get("project_eq", "Eq. 7")
    proj_eq_colour = {
        "Eq. 7": TEAL, "Eq. 8": AMBER, "Eq. 9": BLUE, "Eq. 10": "#16a34a"
    }.get(proj_eq, TEAL)

    proj_eq_note_map = {
        "Eq. 7": "fNRB applied",
        "Eq. 8": "No fNRB (fossil fuel)",
        "Eq. 9": "EFel × ECp × (1+TDL)",
        "Eq. 10": "Zero / proportional",
    }
    proj_eq_note = proj_eq_note_map.get(proj_eq, "")

    ec_eq = method.get("baseline_ec_eq", "Eq. 2")
    ec_eq_note_map = {
        "Eq. 2": "BCb × NCVb",
        "Eq. 3": "ηnew/ηold × ECp",
        "Eq. 5": "SCb/SCp × ECp (CCT)",
    }
    ec_eq_note = ec_eq_note_map.get(ec_eq, "")

    bl_eq = method.get("baseline_eq", "Eq. 1")
    bl_note = "fNRB applied to CO2" if method.get("fnrb_on_baseline") else "No fNRB"

    # Requirement pills
    pills_html = ""
    pills = []
    if method.get("requires_kpt"):
        pills.append(("KPT required", "#dc2626"))
    if method.get("requires_cct"):
        pills.append(("CCT required", "#dc2626"))
    if method.get("requires_tool07"):
        pills.append(("CDM TOOL07", BLUE))
    if method.get("requires_tool05"):
        pills.append(("CDM TOOL05", BLUE))
    if method.get("min_eta_threshold"):
        pct = int(method["min_eta_threshold"] * 100)
        pills.append((f"Min. efficiency: {pct}%", AMBER))
    for txt, col in pills:
        pills_html += (
            f'<span style="background:{col};color:white;font-size:0.72em;'
            f'padding:2px 8px;border-radius:12px;margin-right:4px;white-space:nowrap;">'
            f'{txt}</span>'
        )

    # Warning pills
    warn_html = ""
    for w in method.get("warnings", []):
        warn_html += (
            f'<div style="background:#fef3c7;border:1px solid #f59e0b;border-radius:4px;'
            f'padding:4px 8px;font-size:0.78em;color:#92400e;margin-top:6px;">'
            f'{w}</div>'
        )

    def node(step_label, badge_text, badge_colour, sub_note, eq_label):
        return f"""
        <div style="min-width:148px;max-width:180px;flex:1;">
          <div style="font-size:0.68em;font-weight:700;color:#64748b;text-transform:uppercase;
                      letter-spacing:0.06em;margin-bottom:5px;">{step_label}</div>
          <div style="background:{badge_colour};color:white;padding:5px 10px;border-radius:5px;
                      font-size:0.8em;font-weight:700;line-height:1.3;">{badge_text}</div>
          <div style="font-size:0.75em;color:#374151;margin-top:4px;line-height:1.4;">{sub_note}</div>
          <div style="font-size:0.72em;color:#64748b;margin-top:2px;font-style:italic;">{eq_label}</div>
        </div>"""

    arrow = '<div style="margin-top:26px;color:#94a3b8;font-size:1.3em;flex-shrink:0;">&#8594;</div>'

    n1 = node("Baseline Emissions", f"{bl_eq} — Biomass ({method.get('method_id','').split('_')[0].capitalize()})", TEAL, bl_note, f"fNRB source: {fnrb_short}")
    n2 = node("ECi,y Route", ec_eq, BLUE, ec_eq_note, VM0050_EC_OPTION_DISPLAY.get(
        next((k for k in VM0050_EC_OPTION_EQ if VM0050_EC_OPTION_EQ[k] == ec_eq), "option_2_default"), ""
    )[:48] + "…" if len(VM0050_EC_OPTION_DISPLAY.get(
        next((k for k in VM0050_EC_OPTION_EQ if VM0050_EC_OPTION_EQ[k] == ec_eq), "option_2_default"), ""
    )) > 48 else VM0050_EC_OPTION_DISPLAY.get(
        next((k for k in VM0050_EC_OPTION_EQ if VM0050_EC_OPTION_EQ[k] == ec_eq), "option_2_default"), ""
    ))
    n3 = node("Project Emissions", f"{proj_eq} — {dev_disp}", proj_eq_colour, proj_eq_note, "")
    n4 = node("Net ER", "Eq. 11", SLATE, "(BE − PE) × 0.95 − LERB,y", "Leakage: 5% standard deduction")

    return f"""
<div style="background:var(--bg-secondary,#f8fafc);border:1px solid var(--border-subtle,#e2e8f0);
            border-radius:8px;padding:16px 18px 12px 18px;margin:8px 0;">
  <div style="font-size:0.78em;font-weight:700;color:#0d9488;margin-bottom:10px;
              text-transform:uppercase;letter-spacing:0.06em;">
    VM0050 v1.0 — Calculation Route
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start;">
    {n1}{arrow}{n2}{arrow}{n3}{arrow}{n4}
  </div>
  <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:4px;align-items:center;">
    <span style="font-size:0.72em;color:#64748b;margin-right:4px;">Requires:</span>
    {pills_html if pills_html else '<span style="font-size:0.72em;color:#64748b;">No additional surveys beyond standard monitoring</span>'}
  </div>
  {warn_html}
</div>"""
