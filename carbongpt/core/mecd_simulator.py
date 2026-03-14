"""
Gold Standard – Methodology for Metered & Measured Energy Cooking Devices v1.2
Emission Reduction Calculator

Reference: GS MECD v1.2, published 13 December 2022
Two Cases:
  Case 1 – thermal efficiency determinable by WBT (all non-EPC metered devices)
  Case 2 – efficiency not determinable by WBT, ratio logic (EPC and similar)
"""

import logging
import math

logger = logging.getLogger(__name__)

# ── Baseline fuel default library (MECD 1, 2, 3, 4, 5) ──────────────────────
# P_b_default: tonnes/capita/year (MECD 1 suppressed-demand defaults)
# eta_b: fraction (MECD 5 defaults)
# NCV_default: TJ/Gg  (= GJ/t = MJ/kg — canonical unit, consistent with er_simulator)
#   IPCC source values are published as TJ/Gg.  Old TJ/tonne notation was numerically
#   identical but labelled differently; all formulas now use NCV / 1000 (Gg per tonne).
# EF_CO2: tCO2/TJ (MECD 3)
# EF_nonCO2: tCO2e/TJ AR5 GWP (MECD 4)
# uses_fnrb: True for woody biomass (MECD 13)

MECD_BASELINE_FUEL_LIBRARY = {
    "wood_three_stone": {
        "label": "Wood – three-stone fire",
        "fuel_family": "wood",
        "P_b_default": 0.5,
        "eta_b_default": 0.10,
        "NCV_default": 15.6,           # TJ/Gg  (IPCC 2006 default for wood)
        "EF_CO2_default": 112.0,
        "EF_nonCO2_default": 9.46,
        "uses_fnrb": True,
    },
    "wood_other_biomass": {
        "label": "Wood – other conventional biomass cookstove",
        "fuel_family": "wood",
        "P_b_default": 0.5,
        "eta_b_default": 0.20,
        "NCV_default": 15.6,           # TJ/Gg
        "EF_CO2_default": 112.0,
        "EF_nonCO2_default": 9.46,
        "uses_fnrb": True,
    },
    "charcoal": {
        "label": "Charcoal – conventional cookstove",
        "fuel_family": "charcoal",
        "P_b_default": 0.13,
        "eta_b_default": 0.20,
        "NCV_default": 29.5,           # TJ/Gg  (IPCC 2006 default for charcoal)
        "EF_CO2_default": 165.22,      # includes production (MECD 3)
        "EF_nonCO2_default": 44.83,    # AR5, includes production (MECD 4)
        "uses_fnrb": True,
    },
    "lpg": {
        "label": "LPG – conventional stove",
        "fuel_family": "lpg",
        "P_b_default": None,           # no suppressed-demand default for LPG
        "eta_b_default": None,         # from manufacturer spec
        "NCV_default": 47.13,          # TJ/Gg  (IPCC 2006 LPG default)
        "EF_CO2_default": 63.1,        # IPCC default (tCO2/TJ)
        "EF_nonCO2_default": 0.0,
        "uses_fnrb": False,
    },
    "kerosene": {
        "label": "Kerosene – conventional stove",
        "fuel_family": "kerosene",
        "P_b_default": None,
        "eta_b_default": None,
        "NCV_default": 43.4,           # TJ/Gg  (IPCC 2006 kerosene default)
        "EF_CO2_default": 71.9,
        "EF_nonCO2_default": 0.0,
        "uses_fnrb": False,
    },
    "biogas": {
        "label": "Biogas – conventional use",
        "fuel_family": "biogas",
        "P_b_default": None,
        "eta_b_default": 0.35,
        "NCV_default": 22.4,           # TJ/Gg  (approx IPCC default for biogas)
        "EF_CO2_default": 0.0,         # biogenic – typically 0 in GS
        "EF_nonCO2_default": 0.0,
        "uses_fnrb": False,
    },
}

# Sanity assertion: NCV values must be in TJ/Gg (order-of-magnitude 10–50 for biomass/fossil)
assert 10.0 < MECD_BASELINE_FUEL_LIBRARY["wood_three_stone"]["NCV_default"] < 25.0, \
    "wood NCV out of TJ/Gg range — check unit"
assert 20.0 < MECD_BASELINE_FUEL_LIBRARY["charcoal"]["NCV_default"] < 40.0, \
    "charcoal NCV out of TJ/Gg range — check unit"
assert 30.0 < MECD_BASELINE_FUEL_LIBRARY["lpg"]["NCV_default"] < 60.0, \
    "LPG NCV out of TJ/Gg range — check unit"

# EF caps for charcoal (MECD 3 / 4)
MECD_EF_CO2_CHARCOAL_CAP = 197.15         # tCO2/TJ
MECD_EF_NONCO2_CHARCOAL_CAP_AR5 = 92.29   # tCO2e/TJ

# MECD 7/8: SC defaults (MJ/person/event) for small projects (<10,000 tCO2/yr)
# Used only for Case 2 (EPC-type devices)
MECD_SC_DEFAULTS = {
    "africa": {
        "charcoal": 3.92,
        "lpg": 0.96,
        "firewood": None,   # not provided in methodology for Africa
    },
    "asia": {
        "firewood": 2.83,
        "charcoal": 2.02,
        "lpg": 0.69,
    },
}
MECD_SC_P_EPC_DEFAULTS = {
    "africa": 0.258,   # EPC project device, Africa (MJ/person/event)
    "asia": 0.162,     # EPC project device, Asia (MJ/person/event)
}

# MECD 10: energy use cap for crediting (electricity, Eq. 4 and 6 only)
MECD_CAP_ELECTRICITY_KWH_CAPITA_DAY = 1.0

# MECD 14: fuel use cap for crediting (fuel, Eq. 6/7 only)
MECD_CAP_FUEL_GJ_CAPITA_DAY = 0.0045


# ── Step 1: Baseline emission factor ─────────────────────────────────────────

def _pval(params: dict, key: str, default: float = 0.0,
          lo: float = None, hi: float = None) -> float:
    """
    Read a numeric parameter from a dict that may contain either:
      - plain float/int/str  (e.g. from calculate_mecd_er test callers)
      - {"value": ..., ...}  (e.g. from get_parameters_as_dict() / parameter engine)

    Validation:
      - Returns `default` when key is missing, value is None, or cannot be cast to float.
      - Returns `default` when lo/hi bounds are provided and the value falls outside them,
        preventing silent zero/empty overrides of library defaults.
    """
    v = params.get(key)
    if isinstance(v, dict):
        v = v.get("value")
    if v is None:
        return default
    try:
        fv = float(v)
    except (ValueError, TypeError):
        return default
    if lo is not None and fv < lo:
        return default
    if hi is not None and fv > hi:
        return default
    return fv


def compute_mecd_baseline_ef(case: str, baseline_fuels: list) -> dict:
    """
    Compute the ex-ante baseline emission factor (fixed for crediting period).

    Case 1 (Eq. 1): EF_b,useful = numerator / denominator
        numerator:   Σ P_b × share × (EF_CO2 × fNRB + EF_nonCO2) × NCV
        denominator: Σ P_b × share × NCV × eta_b

    Case 2 (Eq. 2): EF_b,input
        same numerator, denominator = Σ P_b × share × NCV (no efficiency)

    Parameters
    ----------
    case : "1" or "2"
    baseline_fuels : list of dicts, each containing:
        fuel_key   : key in MECD_BASELINE_FUEL_LIBRARY
        share_pct  : 0–100 (must sum to 100 across all rows)
        P_b        : float | None  – override tonnes/capita/yr (None = use default)
        eta_b      : float | None  – override efficiency fraction
        NCV        : float | None  – override NCV (TJ/tonne)
        EF_CO2     : float | None  – override tCO2/TJ
        EF_nonCO2  : float | None  – override tCO2e/TJ
        fnrb       : float  – fraction non-renewable biomass (0.0 for fossil)

    Returns
    -------
    dict with ef_b (tCO2e/TJ), label, unit, numerator, denominator, fuel_rows
    """
    numerator = 0.0
    denominator = 0.0
    fuel_rows = []

    for fuel in baseline_fuels:
        fk = fuel.get("fuel_key", "wood_three_stone")
        lib = MECD_BASELINE_FUEL_LIBRARY.get(fk, MECD_BASELINE_FUEL_LIBRARY["wood_three_stone"])

        share = fuel.get("share_pct", 100.0) / 100.0

        P_b = fuel["P_b"] if fuel.get("P_b") is not None else (lib["P_b_default"] or 0.5)
        eta_b = fuel["eta_b"] if fuel.get("eta_b") is not None else (lib["eta_b_default"] or 0.10)
        NCV = fuel["NCV"] if fuel.get("NCV") is not None else lib["NCV_default"]
        EF_CO2 = fuel["EF_CO2"] if fuel.get("EF_CO2") is not None else lib["EF_CO2_default"]
        EF_nonCO2 = fuel["EF_nonCO2"] if fuel.get("EF_nonCO2") is not None else lib["EF_nonCO2_default"]
        fnrb = fuel.get("fnrb", 0.0) if lib["uses_fnrb"] else 0.0

        # Cap charcoal EFs at methodology maximum
        if lib["fuel_family"] == "charcoal":
            EF_CO2 = min(EF_CO2, MECD_EF_CO2_CHARCOAL_CAP)
            EF_nonCO2 = min(EF_nonCO2, MECD_EF_NONCO2_CHARCOAL_CAP_AR5)

        # Numerator component (same for both cases)
        # NCV is in TJ/Gg; dividing by 1000 converts to TJ/t for mass-energy product.
        # NCV appears in both numerator and denominator so ef_b is scale-invariant
        # for single-fuel cases, but the /1000 keeps intermediate units correct (TJ/yr).
        num_component = P_b * share * (EF_CO2 * fnrb + EF_nonCO2) * NCV / 1000.0

        # Denominator component
        if case == "1":
            den_component = P_b * share * NCV / 1000.0 * eta_b
        else:
            den_component = P_b * share * NCV / 1000.0

        numerator += num_component
        denominator += den_component

        fuel_rows.append({
            "fuel_key": fk,
            "label": lib["label"],
            "share_pct": round(share * 100, 1),
            "P_b": P_b,
            "eta_b": eta_b,
            "NCV": NCV,
            "EF_CO2": EF_CO2,
            "EF_nonCO2": EF_nonCO2,
            "fnrb": fnrb,
            "uses_fnrb": lib["uses_fnrb"],
            "num_component": round(num_component, 8),
            "den_component": round(den_component, 8),
        })

    ef_b = (numerator / denominator) if denominator > 0.0 else 0.0
    label = "EF_b,useful" if case == "1" else "EF_b,input"

    return {
        "ef_b": ef_b,
        "label": label,
        "unit": "tCO2e/TJ",
        "numerator": numerator,
        "denominator": denominator,
        "fuel_rows": fuel_rows,
        "formula": (
            f"{label} = {numerator:.6f} / {denominator:.6f} = {ef_b:.4f} tCO2e/TJ"
            if denominator > 0 else "Denominator is zero – check parameters"
        ),
    }


# ── Step 2: Useful project energy (Case 1 only) ───────────────────────────────

def _apply_electricity_cap(eg_mwh: float, n_persons: float) -> tuple:
    """Apply 1 kWh/capita/day cap to electricity for Eq. 4 and 6. Returns (capped, note)."""
    if n_persons <= 0:
        return eg_mwh, None
    max_mwh = n_persons * MECD_CAP_ELECTRICITY_KWH_CAPITA_DAY * 365.0 / 1000.0
    if eg_mwh > max_mwh:
        return max_mwh, f"Capped at {max_mwh:.1f} MWh (1 kWh/capita/day × {n_persons:.0f} persons × 365)"
    return eg_mwh, None


def _apply_fuel_cap(p_kg: float, ncv_tj_per_gg: float, n_persons: float) -> tuple:
    """Apply 0.0045 GJ/capita/day cap to fuel for Eq. 6/7. Returns (capped_kg, note).

    ncv_tj_per_gg : NCV in TJ/Gg  (canonical unit — divide by 1000 to get TJ/t).
    """
    if n_persons <= 0 or ncv_tj_per_gg <= 0:
        return p_kg, None
    max_gj = n_persons * MECD_CAP_FUEL_GJ_CAPITA_DAY * 365.0
    max_tj = max_gj / 1000.0
    # NCV [TJ/Gg] → NCV [TJ/t] = NCV / 1000; max_t = max_tj / (NCV/1000) = max_tj * 1000 / NCV
    max_t = max_tj * 1000.0 / ncv_tj_per_gg
    max_kg = max_t * 1000.0
    if p_kg > max_kg:
        return max_kg, f"Capped at {max_kg:.1f} kg (0.0045 GJ/capita/day × {n_persons:.0f} persons × 365)"
    return p_kg, None


def compute_useful_energy_electric(eg_p_mwh: float, eta_p: float, n_persons: float = 0) -> dict:
    """Eq. 6: EG_p,useful = Σ(EG_p,d × 0.0036 × η_p)"""
    eg_capped, cap_note = _apply_electricity_cap(eg_p_mwh, n_persons)
    eg_useful_tj = eg_capped * 0.0036 * eta_p
    return {
        "EG_p_useful_TJ": eg_useful_tj,
        "eg_p_mwh_input": eg_p_mwh,
        "eg_p_mwh_used": eg_capped,
        "cap_applied": cap_note is not None,
        "cap_note": cap_note,
        "formula": f"EG_p ({eg_capped:.2f} MWh) × 0.0036 × η_p ({eta_p:.3f}) = {eg_useful_tj:.4f} TJ",
    }


def compute_useful_energy_fuel(p_p_kg: float, ncv_p: float, eta_p: float, n_persons: float = 0) -> dict:
    """Eq. 7: EG_p,useful = Σ(P_p,d × NCV_p × η_p)

    ncv_p : NCV in TJ/Gg  (canonical unit).  Divide by 1000 to convert to TJ/t
    before multiplying fuel mass in tonnes so the product is in TJ.
    """
    p_capped, cap_note = _apply_fuel_cap(p_p_kg, ncv_p, n_persons)
    p_capped_t = p_capped / 1000.0
    eg_useful_tj = p_capped_t * (ncv_p / 1000.0) * eta_p
    return {
        "EG_p_useful_TJ": eg_useful_tj,
        "p_p_kg_input": p_p_kg,
        "p_p_kg_used": p_capped,
        "cap_applied": cap_note is not None,
        "cap_note": cap_note,
        "formula": (
            f"P_p ({p_capped_t:.4f} t) × NCV_p ({ncv_p:.4f} TJ/Gg ÷ 1000)"
            f" × η_p ({eta_p:.3f}) = {eg_useful_tj:.6f} TJ"
        ),
    }


# ── Step 3: Baseline emissions ────────────────────────────────────────────────

def compute_baseline_emissions(case: str, ef_b: float,
                                eg_p_useful_tj: float = 0.0,
                                eg_p_mwh: float = 0.0,
                                sc_b_mj: float = None,
                                sc_p_mj: float = None,
                                n_persons: float = 0) -> dict:
    """
    Case 1 (Eq. 3): BE = EG_p,useful × EF_b,useful
    Case 2 (Eq. 4): BE = Σ(EG_p,d × (SC_b/SC_p) × 0.0036 × EF_b,input)
                    with cap applied to EG_p,d for this equation only.
    """
    if case == "1":
        be_y = eg_p_useful_tj * ef_b
        return {
            "BE_y": be_y,
            "formula": (
                f"EG_p,useful ({eg_p_useful_tj:.4f} TJ) × EF_b,useful ({ef_b:.4f} tCO2e/TJ)"
                f" = {be_y:.2f} tCO2e"
            ),
        }
    else:
        if not sc_b_mj or not sc_p_mj or sc_p_mj == 0:
            return {"BE_y": 0.0, "error": "SC_b or SC_p missing for Case 2"}
        eg_capped, cap_note = _apply_electricity_cap(eg_p_mwh, n_persons)
        sc_ratio = sc_b_mj / sc_p_mj
        be_y = eg_capped * sc_ratio * 0.0036 * ef_b
        return {
            "BE_y": be_y,
            "sc_ratio": sc_ratio,
            "eg_capped_mwh": eg_capped,
            "cap_note": cap_note,
            "formula": (
                f"EG_p ({eg_capped:.2f} MWh) × (SC_b/SC_p) ({sc_b_mj:.4f}/{sc_p_mj:.4f} = {sc_ratio:.4f})"
                f" × 0.0036 × EF_b,input ({ef_b:.4f}) = {be_y:.2f} tCO2e"
            ),
        }


# ── Step 4: Project emissions ─────────────────────────────────────────────────

def compute_project_emissions_electric(eg_p_mwh: float, ef_el: float, tdl: float) -> dict:
    """
    Eq. 8: PE = Σ(EG_p,d × EF_el × (1 + TDL))
    NOTE: always uses real metered value – no cap.
    """
    pe_y = eg_p_mwh * ef_el * (1.0 + tdl)
    return {
        "PE_y": pe_y,
        "formula": (
            f"EG_p ({eg_p_mwh:.2f} MWh) × EF_el ({ef_el:.4f} tCO2e/MWh)"
            f" × (1 + TDL {tdl:.4f}) = {pe_y:.2f} tCO2e"
        ),
    }


def compute_project_emissions_fuel(p_p_kg: float, ncv_p: float, ef_p: float) -> dict:
    """
    Eq. 9: PE = Σ(P_p,d × NCV_p × EF_p)
    NOTE: always uses real metered value – no cap.

    ncv_p : NCV in TJ/Gg  (canonical unit).  Divide by 1000 to convert to TJ/t
    before multiplying fuel mass in tonnes.
    """
    p_p_t = p_p_kg / 1000.0
    pe_y = p_p_t * (ncv_p / 1000.0) * ef_p
    return {
        "PE_y": pe_y,
        "formula": (
            f"P_p ({p_p_t:.4f} t) × NCV_p ({ncv_p:.4f} TJ/Gg ÷ 1000)"
            f" × EF_p ({ef_p:.2f} tCO2e/TJ) = {pe_y:.2f} tCO2e"
        ),
    }


# ── Full crediting-period ER calculator ───────────────────────────────────────

def calculate_mecd_er(params: dict, crediting_years: int = 5, start_year: int = 2025) -> dict:
    """
    Calculate MECD emission reductions across the crediting period.

    Required params keys
    --------------------
    mecd_case         : "1" or "2"
    project_fuel_type : "electric" | "lpg" | "biogas" | "bioethanol"
    baseline_fuels    : list of fuel row dicts (see compute_mecd_baseline_ef)
    n_persons         : int/float  total persons covered (for cap check)
    leakage_option    : "option_1" (5%) | "option_2"

    Case 1 – electric
        eg_p_mwh_annual : float  monitored electricity (MWh/yr)
        eta_p           : float  project device efficiency (fraction)
        ef_el           : float  grid EF (tCO2e/MWh)
        tdl             : float  T&D losses (fraction, required for electric)

    Case 1 – fuel
        p_p_kg_annual   : float  monitored fuel (kg/yr)
        ncv_p           : float  project fuel NCV (TJ/Gg — canonical unit; divide by 1000 to get TJ/t)
        eta_p           : float  project device efficiency (fraction)
        ef_p            : float  project fuel EF (tCO2e/TJ)

    Case 2 – EPC electric
        eg_p_mwh_annual : float  monitored electricity (MWh/yr)
        sc_b_mj         : float  SC_b (MJ/person/event)
        sc_p_mj         : float  SC_p (MJ/person/event)
        ef_el           : float  grid EF (tCO2e/MWh)
        tdl             : float  T&D losses

    Leakage option_2 extra key
        leakage_pct     : float  leakage as fraction of gross ER
    """

    # ── Read top-level params — handles both flat floats and {"value": ...} dicts ──
    # _pval() returns the library/methodology default if the value is missing, None,
    # non-numeric, or outside the lo/hi validation bounds, preventing silent zero overrides.
    case = str(params.get("mecd_case", "1"))
    project_fuel_type = params.get("project_fuel_type", "electric")
    is_electric = (project_fuel_type == "electric")
    baseline_fuels = params.get("baseline_fuels", [])

    n_persons = _pval(params, "n_persons", 1000.0, lo=1.0)
    leakage_option = params.get("leakage_option", "option_1")

    # fNRB: the parameter engine stores it as "fNRB"; some callers use "fnrb" (lowercase).
    # Try fNRB first, fall back to fnrb, fall back to 0.30 if neither is valid 0–1.
    top_level_fnrb = _pval(params, "fNRB",
                            _pval(params, "fnrb", 0.30, lo=0.0, hi=1.0),
                            lo=0.0, hi=1.0)

    if not baseline_fuels:
        baseline_fuels = [{
            "fuel_key": "wood_three_stone",
            "share_pct": 100.0,
            "fnrb": top_level_fnrb,
        }]

    # Step 1: Baseline EF — computed once, fixed for the period
    bf_result = compute_mecd_baseline_ef(case, baseline_fuels)
    ef_b = bf_result["ef_b"]

    yearly = []
    total_er = 0.0

    for yr in range(crediting_years):
        year = start_year + yr

        # Steps 2–3: useful energy + baseline emissions
        if case == "1":
            if is_electric:
                eg_mwh = _pval(params, "eg_p_mwh_annual", 0.0, lo=0.0)
                eta_p  = _pval(params, "eta_p", 0.85, lo=0.001, hi=1.0)
                ue = compute_useful_energy_electric(eg_mwh, eta_p, n_persons)
                be_res = compute_baseline_emissions("1", ef_b, eg_p_useful_tj=ue["EG_p_useful_TJ"])
            else:
                p_kg  = _pval(params, "p_p_kg_annual", 0.0, lo=0.0)
                ncv_p = _pval(params, "ncv_p", 47.13, lo=1.0, hi=1000.0)  # TJ/Gg
                eta_p = _pval(params, "eta_p", 0.55, lo=0.001, hi=1.0)
                ue = compute_useful_energy_fuel(p_kg, ncv_p, eta_p, n_persons)
                be_res = compute_baseline_emissions("1", ef_b, eg_p_useful_tj=ue["EG_p_useful_TJ"])
        else:
            eg_mwh  = _pval(params, "eg_p_mwh_annual", 0.0, lo=0.0)
            sc_b_mj = _pval(params, "sc_b_mj", 3.92, lo=0.001)
            sc_p_mj = _pval(params, "sc_p_mj", 0.258, lo=0.001)
            ue = None
            be_res = compute_baseline_emissions(
                "2", ef_b,
                eg_p_mwh=eg_mwh,
                sc_b_mj=sc_b_mj, sc_p_mj=sc_p_mj,
                n_persons=n_persons,
            )

        # Step 4: Project emissions — always use real metered value, never capped
        if is_electric:
            eg_raw = _pval(params, "eg_p_mwh_annual", 0.0, lo=0.0)
            ef_el  = _pval(params, "ef_el", 0.50, lo=0.0, hi=2.0)
            tdl    = _pval(params, "tdl", 0.05, lo=0.0, hi=0.5)
            pe_res = compute_project_emissions_electric(eg_raw, ef_el, tdl)
        else:
            p_kg_raw = _pval(params, "p_p_kg_annual", 0.0, lo=0.0)
            ncv_p    = _pval(params, "ncv_p", 47.13, lo=1.0, hi=1000.0)  # TJ/Gg
            ef_p     = _pval(params, "ef_p", 63.1, lo=0.0)
            pe_res = compute_project_emissions_fuel(p_kg_raw, ncv_p, ef_p)

        be_y = be_res["BE_y"]
        pe_y = pe_res["PE_y"]
        gross_er = be_y - pe_y

        # Step 5: Leakage (Eq. 10 uses gross ER for Option 1)
        if leakage_option == "option_1":
            le_y = max(0.0, gross_er * 0.05)
            le_formula = f"Gross ER × 5% = {gross_er:.2f} × 0.05 = {le_y:.2f} tCO2e"
        else:
            le_pct = _pval(params, "leakage_pct", 0.05, lo=0.0, hi=1.0)
            le_y = max(0.0, gross_er * le_pct)
            le_formula = f"Gross ER × {le_pct:.1%} = {gross_er:.2f} × {le_pct:.3f} = {le_y:.2f} tCO2e"

        er_y = max(0.0, be_y - pe_y - le_y)
        total_er += er_y

        row = {
            "year": year,
            "BE_y": round(be_y, 2),
            "PE_y": round(pe_y, 2),
            "LE_y": round(le_y, 2),
            "ER_y": round(er_y, 2),
            "be_formula": be_res.get("formula", ""),
            "pe_formula": pe_res.get("formula", ""),
            "le_formula": le_formula,
        }
        if ue:
            row["useful_energy_formula"] = ue.get("formula", "")
            row["cap_applied"] = ue.get("cap_applied", False)
            row["cap_note"] = ue.get("cap_note")
        yearly.append(row)

    return {
        "methodology": "GS-MECD",
        "version": "1.2",
        "case": case,
        "project_fuel_type": project_fuel_type,
        "crediting_years": crediting_years,
        "start_year": start_year,
        "baseline_ef": {
            "ef_b": round(ef_b, 4),
            "label": bf_result["label"],
            "unit": "tCO2e/TJ",
            "formula": bf_result["formula"],
            "fuel_rows": bf_result["fuel_rows"],
        },
        "yearly": yearly,
        "total_er_tCO2e": round(total_er, 2),
        "avg_annual_er_tCO2e": round(total_er / crediting_years, 2) if crediting_years else 0.0,
        "n_persons": n_persons,
        "leakage_option": leakage_option,
    }
