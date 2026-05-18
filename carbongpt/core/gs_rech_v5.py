"""
GS RECH v5.0 — Simplified Improved Cookstove Methodology
Gold Standard, approved 2023.

Stepwise baseline: BEunc → BEadj (×(1−DAF)) → BEy = MIN(BEadj, BEunc).
Since DAF ≥ 0, BEadj ≤ BEunc always, so BEy = BEadj in practice.

Leakage:
  LE_embodied : n_units × embodied_per_unit  (one-time, charged in year 1)
  LE_market   : (BEy − AEy) × 0.05           (market leakage, annual)

Consumption units follow CarbonGPT convention: t/device/year.
Per-capita cap: baseline_consumption / HNb ≤ PCAP (1.25 wood / 0.40 charcoal t/cap/yr).
"""

import logging

logger = logging.getLogger(__name__)

# Emission factors (GS RECH v5 / Gold Standard Annex 2)
_NCV = {"wood": 0.0156, "charcoal": 0.0295}       # TJ/t
_EF_CO2 = {"wood": 112.0, "charcoal": 165.22}      # tCO2/TJ  (charcoal incl. production)
_EF_NONCO2 = {"wood": 9.46, "charcoal": 44.83}     # tCO2e/TJ (charcoal incl. production)

# Per-capita consumption caps (RECH v5 §8.2)
_PCAP = {"wood": 1.25, "charcoal": 0.40}            # t/cap/an


def calculate_gs_rech_v5_er(params, crediting_years=5, start_year=2025):
    """
    Calculate GS RECH v5.0 emission reductions over a multi-year crediting period.

    params dict keys (all optional — defaults are shown):
      fNRB               (0.75)   fraction non-renewable biomass — CDM TOOL33 or A6.4 MEP012
      DAF                (0.025)  NetZero Ambition Factor — GS Tool 05
      N_distributed      (1000)   total stoves distributed
      adoption_rate      (0.82)   base-year fraction actively used (Up,y)
      adoption_rate_decay(0.02)   annual decay applied each subsequent year
      adoption_rate_floor(0.50)   minimum adoption rate
      stacking_factor    (0.0)    fraction of active users keeping old stove
      baseline_consumption(2.0)  t/stove/year (KPT or IPCC default)
      project_consumption (0.8)  t/stove/year (KPT)
      HNb                (5.0)   persons per household (for per-capita cap)
      baseline_fuel      ("wood") "wood" | "charcoal"
      project_fuel       ("wood") "wood" | "charcoal" — same or switch
      embodied           (0.017)  tCO2e/unit (GS default)
      n_units            (N_distributed) units used for LE_embodied calc

    Returns standard CarbonGPT ER result envelope (calculation_steps, years, summary, …).
    """
    fNRB = _pval(params, "fNRB", 0.75)
    DAF = _pval(params, "DAF", 0.025)
    N_distributed = _pval(params, "N_distributed", 1000)
    adoption_rate_base = _pval(params, "adoption_rate", 0.82)
    adoption_rate_decay = _pval(params, "adoption_rate_decay", 0.02)
    adoption_rate_floor = _pval(params, "adoption_rate_floor", 0.50)
    stacking_factor = _pval(params, "stacking_factor", 0.0)
    bl_consumption = _pval(params, "baseline_consumption", 2.0)   # t/stove/yr
    pj_consumption = _pval(params, "project_consumption", 0.8)    # t/stove/yr
    HNb = _pval(params, "HNb", 5.0)
    baseline_fuel = _ptext(params, "baseline_fuel", "wood").lower()
    project_fuel = _ptext(params, "project_fuel", baseline_fuel).lower()
    embodied = _pval(params, "embodied", 0.017)
    n_units = _pval(params, "n_units", N_distributed)

    # Validate fuel types; fall back to wood if unknown
    if baseline_fuel not in _NCV:
        baseline_fuel = "wood"
    if project_fuel not in _NCV:
        project_fuel = "wood"

    NCV_b = _NCV[baseline_fuel]
    EF_CO2_b = _EF_CO2[baseline_fuel]
    EF_nonCO2_b = _EF_NONCO2[baseline_fuel]

    NCV_p = _NCV[project_fuel]
    EF_CO2_p = _EF_CO2[project_fuel]
    EF_nonCO2_p = _EF_NONCO2[project_fuel]

    # Per-capita consumption cap (RECH v5 §8.2)
    PCAP = _PCAP[baseline_fuel]
    bl_per_cap = bl_consumption / HNb if HNb > 0 else bl_consumption
    _cap_applied = False
    _cap_warnings = []
    if bl_per_cap > PCAP:
        bl_consumption = PCAP * HNb
        _cap_applied = True
        _cap_warnings.append(
            f"Baseline consumption capped at {PCAP} t/cap/yr × {HNb} cap/hh = "
            f"{bl_consumption:.4f} t/stove/yr (was {bl_per_cap:.4f} t/cap/yr). "
            f"GS RECH v5 §8.2 hard cap applied."
        )

    # Stacking correction: households keeping the old stove reduce net credits
    stacking_correction = 1.0 - stacking_factor

    # Per-device energy content (TJ/device/yr)
    EC_b = bl_consumption * NCV_b
    EC_p = pj_consumption * NCV_p

    # Combined EF (tCO2e/TJ) — fNRB applies to CO2 term for biomass
    EF_comb_b = fNRB * EF_CO2_b + EF_nonCO2_b
    EF_comb_p = fNRB * EF_CO2_p + EF_nonCO2_p

    # Per-device baseline and activity emissions (before adoption/stacking)
    be_per_device = EC_b * EF_comb_b   # tCO2e/device/yr (BEunc basis)
    ae_per_device = EC_p * EF_comb_p   # tCO2e/device/yr

    # LE embodied (one-time charge, amortised to year 1 in this model)
    LE_emb_total = n_units * embodied

    calculation_steps = [
        {
            "step": 1, "canonical_key": "fNRB",
            "name": "Fraction of non-renewable biomass",
            "formula": "fNRB — CDM TOOL33 v03.0 national default (or A6.4 MEP012 if applicable)",
            "value": round(fNRB, 4), "unit": "fraction",
        },
        {
            "step": 2, "canonical_key": "DAF",
            "name": "NetZero Ambition Factor",
            "formula": "DAF — GS Tool 05 (published annually by Gold Standard)",
            "value": round(DAF, 4), "unit": "fraction",
        },
        {
            "step": 3, "canonical_key": "baseline_consumption",
            "name": "Baseline specific fuel consumption per device",
            "formula": (
                f"Pb = {bl_consumption:.4f} t/stove/yr"
                + (f" [capped from per-cap cap {PCAP} t/cap/yr × {HNb} cap/hh]" if _cap_applied else "")
            ),
            "value": round(bl_consumption, 6), "unit": "t/stove/yr",
        },
        {
            "step": 4, "canonical_key": "project_consumption",
            "name": "Project specific fuel consumption per device",
            "formula": f"Pp = {pj_consumption:.4f} t/stove/yr (KPT)",
            "value": round(pj_consumption, 6), "unit": "t/stove/yr",
        },
        {
            "step": 5, "canonical_key": "baseline_energy_tj",
            "name": "Baseline energy content per device",
            "formula": f"EC_b = Pb × NCV_b = {bl_consumption:.4f} × {NCV_b} = {EC_b:.6f} TJ/device/yr",
            "value": round(EC_b, 6), "unit": "TJ/device/yr",
        },
        {
            "step": 6, "canonical_key": "baseline_emissions_per_device",
            "name": "Baseline emissions per device (BEunc basis)",
            "formula": (
                f"EC_b × (fNRB × EF_CO2_b + EF_nonCO2_b) = "
                f"{EC_b:.6f} × ({fNRB} × {EF_CO2_b} + {EF_nonCO2_b}) = {be_per_device:.6f}"
            ),
            "value": round(be_per_device, 6), "unit": "tCO2e/device/yr",
        },
        {
            "step": 7, "canonical_key": "project_energy_tj",
            "name": "Project energy content per device",
            "formula": f"EC_p = Pp × NCV_p = {pj_consumption:.4f} × {NCV_p} = {EC_p:.6f} TJ/device/yr",
            "value": round(EC_p, 6), "unit": "TJ/device/yr",
        },
        {
            "step": 8, "canonical_key": "project_emissions_per_device",
            "name": "Project activity emissions per device",
            "formula": (
                f"EC_p × (fNRB × EF_CO2_p + EF_nonCO2_p) = "
                f"{EC_p:.6f} × ({fNRB} × {EF_CO2_p} + {EF_nonCO2_p}) = {ae_per_device:.6f}"
            ),
            "value": round(ae_per_device, 6), "unit": "tCO2e/device/yr",
        },
        {
            "step": 9, "canonical_key": "DAF_adjustment",
            "name": "Stepwise baseline: BEadj = BEunc × (1 − DAF)",
            "formula": f"BEadj/device = {be_per_device:.6f} × (1 − {DAF}) = {be_per_device*(1-DAF):.6f}",
            "value": round(be_per_device * (1 - DAF), 6), "unit": "tCO2e/device/yr",
        },
        {
            "step": 10, "canonical_key": "le_embodied",
            "name": "Embodied leakage (one-time, year 1)",
            "formula": f"n_units × embodied/unit = {n_units:.0f} × {embodied} = {LE_emb_total:.4f} tCO2e",
            "value": round(LE_emb_total, 4), "unit": "tCO2e (total)",
        },
    ]

    years = []
    total_er = 0.0
    total_be = 0.0
    total_pe = 0.0
    total_le = 0.0

    for y in range(crediting_years):
        year_num = y + 1
        cal_year = start_year + y

        adoption_rate = max(adoption_rate_base - y * adoption_rate_decay, adoption_rate_floor)
        N_active = N_distributed * adoption_rate * stacking_correction

        # Stepwise baseline
        BEy_unc = be_per_device * N_active        # BEunc
        BEy_adj = BEy_unc * (1.0 - DAF)           # BEadj
        BEy = min(BEy_adj, BEy_unc)               # BEy = BEadj (since DAF≥0)

        AEy = ae_per_device * N_active

        # Leakage
        LE_emb_y = LE_emb_total if year_num == 1 else 0.0
        LE_market = (BEy - AEy) * 0.05

        ERy = BEy - AEy - LE_emb_y - LE_market

        total_er += ERy
        total_be += BEy
        total_pe += AEy
        total_le += LE_emb_y + LE_market

        years.append({
            "year_number": year_num,
            "calendar_year": cal_year,
            "adoption_rate": round(adoption_rate, 4),
            "active_households": round(N_active, 0),
            "active_hh_formula": (
                f"max({adoption_rate_base} − {y}×{adoption_rate_decay}, {adoption_rate_floor})"
                f" × {N_distributed:.0f} × (1−{stacking_factor}) = {N_active:.0f}"
            ),
            "be_unc": round(BEy_unc, 2),
            "be_adj": round(BEy_adj, 2),
            "baseline_emissions": round(BEy, 2),
            "baseline_formula": (
                f"be/device({be_per_device:.4f}) × N_active({N_active:.0f}) × (1−DAF {DAF})"
            ),
            "project_emissions": round(AEy, 2),
            "project_formula": f"ae/device({ae_per_device:.4f}) × N_active({N_active:.0f})",
            "le_embodied": round(LE_emb_y, 4),
            "le_market": round(LE_market, 2),
            "leakage": round(LE_emb_y + LE_market, 2),
            "gross_er": round(BEy - AEy, 2),
            "net_er": round(ERy, 2),
            "net_er_formula": f"BEy({BEy:.2f}) − AEy({AEy:.2f}) − LE_emb({LE_emb_y:.2f}) − LE_mkt({LE_market:.2f})",
        })

    warnings = _cap_warnings[:]
    if DAF == 0:
        warnings.append("DAF = 0 : GS Tool 05 NetZero Ambition Factor is mandatory for RECH v5. Apply the year-specific value.")
    if stacking_factor > 0.3:
        warnings.append(
            f"Stacking factor {stacking_factor:.0%} is high — verify that the usage survey "
            f"supports this rate, as it significantly reduces credited emissions."
        )

    return {
        "calculation_steps": calculation_steps,
        "years": years,
        "warnings": warnings,
        "summary": {
            "total_er": round(total_er, 2),
            "total_baseline": round(total_be, 2),
            "total_project": round(total_pe, 2),
            "total_leakage": round(total_le, 2),
            "average_annual_er": round(total_er / crediting_years, 2) if crediting_years > 0 else 0,
            "crediting_years": crediting_years,
            "methodology": "GS-RECH-v5",
        },
        "parameters_used": {
            "fNRB": {"value": fNRB, "unit": "fraction", "description": "Fraction of non-renewable biomass"},
            "DAF": {"value": DAF, "unit": "fraction", "description": "NetZero Ambition Factor (GS Tool 05)"},
            "N_distributed": {"value": N_distributed, "unit": "count", "description": "Total stoves distributed"},
            "adoption_rate": {"value": adoption_rate_base, "unit": "fraction", "description": f"Base adoption rate (decays {adoption_rate_decay}/yr, floor {adoption_rate_floor})"},
            "stacking_factor": {"value": stacking_factor, "unit": "fraction", "description": "Fraction of active users retaining old stove"},
            "baseline_consumption": {"value": round(bl_consumption, 4), "unit": "t/stove/yr", "description": "Baseline specific fuel consumption (post-cap)"},
            "project_consumption": {"value": round(pj_consumption, 4), "unit": "t/stove/yr", "description": "Project specific fuel consumption"},
            "HNb": {"value": HNb, "unit": "persons/hh", "description": "Household size"},
            "baseline_fuel": {"value": baseline_fuel, "unit": "", "description": "Baseline fuel type"},
            "project_fuel": {"value": project_fuel, "unit": "", "description": "Project fuel type"},
            "NCV_baseline": {"value": NCV_b, "unit": "TJ/t", "description": "Net calorific value (baseline fuel)"},
            "EF_CO2_baseline": {"value": EF_CO2_b, "unit": "tCO2/TJ", "description": "CO2 emission factor (baseline)"},
            "EF_nonCO2_baseline": {"value": EF_nonCO2_b, "unit": "tCO2e/TJ", "description": "Non-CO2 emission factor (baseline)"},
            "embodied": {"value": embodied, "unit": "tCO2e/unit", "description": "Embodied emissions per stove"},
            "n_units": {"value": n_units, "unit": "count", "description": "Units for embodied LE calculation"},
            "LE_embodied_total": {"value": round(LE_emb_total, 4), "unit": "tCO2e", "description": "Total embodied leakage (year 1)"},
        },
    }


def _pval(params, key, default=0.0):
    if key in params:
        v = params[key]
        if isinstance(v, dict):
            v = v.get("value")
        if v is not None:
            try:
                return float(v)
            except (ValueError, TypeError):
                pass
    return default


def _ptext(params, key, default=""):
    if key in params:
        v = params[key]
        if isinstance(v, dict):
            v = v.get("value")
        if v is not None:
            return str(v)
    return default
