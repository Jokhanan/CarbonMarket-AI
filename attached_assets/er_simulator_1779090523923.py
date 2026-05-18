import logging
import json
import math
from carbongpt.repository.db import get_cursor
from carbongpt.core.parameter_engine import get_parameters_as_dict

logger = logging.getLogger(__name__)


def calculate_cookstove_er(params, crediting_years=7, start_year=2025, methodology="VM0050",
                           method_id=None):
    """
    Calculate cookstove emission reductions (simple yearly model).

    method_id : str | None
        For TPDDTEC projects pass "method_1", "method_2", or "method_3".
        Controls fNRB placement and SFC_b derivation.
        If None the legacy VM0050 path is used.

    fNRB placement (TPDDTEC v4.0):
        Baseline:        EC_b * (fNRB * EF_CO2_b + EF_nonCO2_b)
        Project (same fuel):  EC_p * (fNRB * EF_CO2_p + EF_nonCO2_p)
        Project (fuel switch, Method 3): EC_p * (EF_CO2_p + EF_nonCO2_p)  -- no fNRB
    """
    from carbongpt.core.methodology_rules import (
        TPDDTEC_NCV_WOOD_TJ_PER_GG,
        TPDDTEC_EF_CO2_WOOD,
        TPDDTEC_EF_NONCO2_WOOD_AR5,
        TPDDTEC_EF_CO2_CHARCOAL_WITH_PRODUCTION,
        TPDDTEC_EF_NONCO2_CHARCOAL_WITH_PRODUCTION_AR5,
        TPDDTEC_NCV_CHARCOAL_TJ_PER_GG,
        TPDDTEC_METHOD2_DEFAULT_CONSUMPTION,
        TPDDTEC_EF_CO2_CHARCOAL_CAP,
        TPDDTEC_EF_NONCO2_CHARCOAL_CAP_AR5,
    )

    fNRB = _pval(params, "fNRB", 0.30)
    # VM0050 §9.2 / Footnote 22: 26% uncertainty discount when fNRB source is CDM TOOL30
    _fnrb_source = _ptext(params, "fnrb_source", "")
    if _fnrb_source.lower() == "tool30":
        fNRB = fNRB * (1.0 - 0.26)
    hh_size = _pval(params, "household_size", 5.0)
    num_hh = _pval(params, "num_households", 1000)
    leakage_pct = 1.0 - _pval(params, "leakage_discount", 0.95)
    usage_rate_base = _pval(params, "usage_rate", 0.90)
    usage_rate_decay = _pval(params, "usage_rate_decay", 0.02)
    usage_rate_floor = _pval(params, "usage_rate_floor", 0.50)
    # R2: canonical device scale = households × devices_per_household
    # When devices_per_household is missing or 1, num_devices == num_hh → results unchanged.
    devices_per_hh = _pval(params, "devices_per_household", 1.0)
    num_devices = num_hh * devices_per_hh

    baseline_fuel = _ptext(params, "baseline_fuel", "wood")
    project_fuel = _ptext(params, "project_fuel", baseline_fuel)
    is_charcoal_baseline = baseline_fuel.lower() in ("charcoal", "charbon")
    is_charcoal_project = project_fuel.lower() in ("charcoal", "charbon")
    CF = _pval(params, "CF", 4.0 if is_charcoal_baseline else 1.0)

    is_tpddtec = methodology in ("TPDDTEC", "GS-TPDDTEC") or (method_id is not None and method_id.startswith("method_"))
    is_method_3 = (method_id == "method_3") or (is_tpddtec and baseline_fuel.lower() != project_fuel.lower())

    if is_tpddtec:
        if is_charcoal_baseline:
            NCV_b = _pval(params, "NCV_baseline", TPDDTEC_NCV_CHARCOAL_TJ_PER_GG)
            EF_CO2_b = _pval(params, "EF_CO2_baseline", TPDDTEC_EF_CO2_CHARCOAL_WITH_PRODUCTION)
            EF_nonCO2_b = _pval(params, "EF_nonCO2_baseline", TPDDTEC_EF_NONCO2_CHARCOAL_WITH_PRODUCTION_AR5)
        else:
            NCV_b = _pval(params, "NCV_baseline", TPDDTEC_NCV_WOOD_TJ_PER_GG)
            EF_CO2_b = _pval(params, "EF_CO2_baseline", TPDDTEC_EF_CO2_WOOD)
            EF_nonCO2_b = _pval(params, "EF_nonCO2_baseline", TPDDTEC_EF_NONCO2_WOOD_AR5)
        if is_charcoal_project:
            NCV_p = _pval(params, "NCV_project", TPDDTEC_NCV_CHARCOAL_TJ_PER_GG)
            EF_CO2_p = _pval(params, "EF_CO2_project", TPDDTEC_EF_CO2_CHARCOAL_WITH_PRODUCTION)
            EF_nonCO2_p = _pval(params, "EF_nonCO2_project", TPDDTEC_EF_NONCO2_CHARCOAL_WITH_PRODUCTION_AR5)
        else:
            NCV_p = _pval(params, "NCV_project", TPDDTEC_NCV_WOOD_TJ_PER_GG)
            EF_CO2_p = _pval(params, "EF_CO2_project", TPDDTEC_EF_CO2_WOOD)
            EF_nonCO2_p = _pval(params, "EF_nonCO2_project", TPDDTEC_EF_NONCO2_WOOD_AR5)
    else:
        NCV_b = _pval(params, "NCV_baseline", 15.6)
        EF_CO2_b = _pval(params, "EF_CO2_baseline", 112.0)
        EF_nonCO2_b = _pval(params, "EF_nonCO2_baseline", 9.46)
        NCV_p = _pval(params, "NCV_project", NCV_b)
        EF_CO2_p = _pval(params, "EF_CO2_project", EF_CO2_b)
        EF_nonCO2_p = _pval(params, "EF_nonCO2_project", EF_nonCO2_b)

    # TPDDTEC v4.0 — charcoal EF hard caps (ICS §8/9, Table A: 197.15 / 92.29 tCO2/TJ)
    # Applies to user-supplied parameter overrides; default values (165.22 / 44.83) are below cap.
    if is_tpddtec and is_charcoal_baseline:
        EF_CO2_b = min(EF_CO2_b, TPDDTEC_EF_CO2_CHARCOAL_CAP)
        EF_nonCO2_b = min(EF_nonCO2_b, TPDDTEC_EF_NONCO2_CHARCOAL_CAP_AR5)
    if is_tpddtec and is_charcoal_project:
        EF_CO2_p = min(EF_CO2_p, TPDDTEC_EF_CO2_CHARCOAL_CAP)
        EF_nonCO2_p = min(EF_nonCO2_p, TPDDTEC_EF_NONCO2_CHARCOAL_CAP_AR5)

    if methodology in ("VM0050",) and not is_tpddtec:
        bl_consumption = _pval(params, "baseline_fuel_consumption", hh_size * 0.5)
        pj_consumption = _pval(params, "project_fuel_consumption", bl_consumption * 0.5)
        consumption_label = "baseline_fuel_consumption"
        consumption_pj_label = "project_fuel_consumption"
    elif is_tpddtec and method_id == "method_2":
        # devices_per_hh already read at the top of the function
        # Method 2: derive baseline consumption directly from TPDDTEC default (t/device/yr)
        bl_consumption = TPDDTEC_METHOD2_DEFAULT_CONSUMPTION * hh_size / devices_per_hh
        pj_consumption = _pval(params, "project_fuel_consumption", bl_consumption * 0.5)
        consumption_label = (
            f"Method 2 locked default: {TPDDTEC_METHOD2_DEFAULT_CONSUMPTION} t/capita/yr × "
            f"{hh_size} persons / {devices_per_hh} device(s)/hh = {bl_consumption:.4f} t/device/yr"
        )
        consumption_pj_label = f"project_fuel_consumption = {pj_consumption:.4f} t/device/yr"
    else:
        # Method 1 / Method 3 / VM0050 fallback:
        # canonical parameter is baseline_fuel_consumption in t/device/yr
        bl_consumption = _pval(params, "baseline_fuel_consumption", 0.5)
        pj_consumption = _pval(params, "project_fuel_consumption", bl_consumption * 0.5)
        consumption_label = f"baseline_fuel_consumption = {bl_consumption:.4f} t/device/yr"
        consumption_pj_label = f"project_fuel_consumption = {pj_consumption:.4f} t/device/yr"

    # SFC_b cap: TPDDTEC v4.0 ICS 18 — hard cap at 0.95 t/person/yr; warn above 0.75
    _sfc_b_warnings = []
    _bl_per_person = bl_consumption / hh_size if hh_size > 0 else bl_consumption
    if is_tpddtec and _bl_per_person > 0.95:
        bl_consumption = 0.95 * hh_size
        _sfc_b_warnings.append(
            f"SFC_b capped at 0.95 t/person/yr (was {_bl_per_person:.3f} t/person/yr). TPDDTEC ICS 18 hard cap applied."
        )
    elif is_tpddtec and _bl_per_person > 0.75:
        _sfc_b_warnings.append(
            f"SFC_b = {_bl_per_person:.3f} t/person/yr exceeds 0.75 threshold. Third-party study required for justification (TPDDTEC ICS 18)."
        )

    # CF: NOT applied to consumption when charcoal EFs with-production are used.
    # EF_CO2_charcoal_with_production (165.22 tCO2/TJ) already encodes the production
    # inefficiency — multiplying consumption by CF would double-count those losses.
    # NCV_charcoal is used directly on charcoal tonnes consumed.
    bl_consumption_wood_equiv = bl_consumption
    cf_note = (
        f"Charcoal baseline: EF={EF_CO2_b} tCO2/TJ already includes production losses — CF not applied to consumption"
        if is_charcoal_baseline
        else f"Wood baseline: CF not applicable (CF={CF})"
    )
    pj_consumption_wood_equiv = pj_consumption

    ec_b = bl_consumption_wood_equiv * NCV_b / 1000.0
    ec_p = pj_consumption_wood_equiv * NCV_p / 1000.0

    be_per_hh = ec_b * (fNRB * EF_CO2_b + EF_nonCO2_b)

    # VM0050 Eq. 3 — Stove-stacking cross-check cap
    # If eta_new and eta_old provided, cap baseline energy to EC_est = EC_p × (eta_new / eta_old)
    _stove_stacking_applied = False
    _eta_new = _pval(params, "eta_new", 0.0) or _pval(params, "eta_project", 0.0)
    _eta_old = _pval(params, "eta_old", 0.0) or _pval(params, "eta_baseline", 0.0)
    if not is_method_3 and _eta_new > 0 and _eta_old > 0 and methodology == "VM0050":
        ec_b_est = ec_p * (_eta_new / _eta_old)
        if ec_b > ec_b_est:
            ec_b = ec_b_est
            be_per_hh = ec_b * (fNRB * EF_CO2_b + EF_nonCO2_b)
            _stove_stacking_applied = True

    # Detect electric project device path (VM0050 Eq. 8)
    # Electric pressure cooker projects: PE = EC_elec (MWh/device/yr) × EF_el (tCO2e/MWh) × (1+TDL)
    _electric_fuels = ("electric", "electricity", "electric_pressure_cooker", "epc")
    is_electric_project = project_fuel.lower() in _electric_fuels
    ec_elec = _pval(params, "EC_electricity_project", None)
    ef_el = _pval(params, "EF_electricity", None)
    tdl = _pval(params, "TDL", 0.0)

    if is_electric_project and ec_elec is not None and ef_el is not None:
        # VM0050 Eq. 8: project emissions from electric devices
        # EC_electricity_project is in MWh/device/yr; EF_electricity in tCO2e/MWh
        pe_per_hh = ec_elec * ef_el * (1.0 + tdl)
        pe_formula_str = (
            f"VM0050 Eq. 8 (electric device): EC_elec × EF_el × (1+TDL) = "
            f"{ec_elec:.4f} MWh × {ef_el:.4f} tCO2e/MWh × (1+{tdl:.4f}) = {pe_per_hh:.6f} tCO2e/device/yr"
        )
        # Override ec_p for the calculation_steps display
        ec_p = ec_elec * 0.0036  # approximate TJ equivalent for display only
    elif is_method_3:
        pe_per_hh = ec_p * (EF_CO2_p + EF_nonCO2_p)
        pe_formula_str = (
            f"EC_p × (EF_CO2_p + EF_nonCO2_p) [no fNRB on project fuel] = "
            f"{ec_p:.6f} × ({EF_CO2_p} + {EF_nonCO2_p})"
        )
    else:
        pe_per_hh = ec_p * (fNRB * EF_CO2_p + EF_nonCO2_p)
        pe_formula_str = (
            f"EC_p × (fNRB × EF_CO2_p + EF_nonCO2_p) = "
            f"{ec_p:.6f} × ({fNRB} × {EF_CO2_p} + {EF_nonCO2_p})"
        )

    calculation_steps = [
        {
            "step": 1,
            "canonical_key": "baseline_fuel_consumption",
            "name": "Baseline fuel consumption per device",
            "formula": consumption_label,
            "value": round(bl_consumption, 6),
            "unit": "t/device/yr",
        },
        {
            "step": 2,
            "canonical_key": "project_fuel_consumption",
            "name": "Project fuel consumption per device",
            "formula": consumption_pj_label,
            "value": round(pj_consumption, 6),
            "unit": "t/device/yr",
        },
        {
            "step": 3,
            "canonical_key": "cf_adjustment",
            "name": "CF adjustment (charcoal native vs wood-equivalent)",
            "formula": cf_note,
            "value_baseline": round(bl_consumption_wood_equiv, 6),
            "value_project": round(pj_consumption_wood_equiv, 6),
            "unit": "t wood-equiv/device/yr",
        },
        {
            "step": 4,
            "canonical_key": "baseline_energy_tj",
            "name": "Baseline energy content per device",
            "formula": f"bl_cons_wood_equiv × NCV_b / 1000 = {bl_consumption_wood_equiv:.6f} × {NCV_b} / 1000",
            "value": round(ec_b, 6),
            "unit": "TJ/device/yr",
        },
        {
            "step": 5,
            "canonical_key": "baseline_emissions_per_device",
            "name": "Baseline emissions per device (fNRB on CO2 term only)",
            "formula": f"EC_b × (fNRB × EF_CO2_b + EF_nonCO2_b) = {ec_b:.6f} × ({fNRB} × {EF_CO2_b} + {EF_nonCO2_b})",
            "value": round(be_per_hh, 6),
            "unit": "tCO2e/device/yr",
        },
        {
            "step": 6,
            "canonical_key": "project_energy_tj",
            "name": "Project energy content per device",
            "formula": f"pj_cons_wood_equiv × NCV_p / 1000 = {pj_consumption_wood_equiv:.6f} × {NCV_p} / 1000",
            "value": round(ec_p, 6),
            "unit": "TJ/device/yr",
        },
        {
            "step": 7,
            "canonical_key": "project_emissions_per_device",
            "name": "Project emissions per device",
            "formula": pe_formula_str,
            "value": round(pe_per_hh, 6),
            "unit": "tCO2e/device/yr",
        },
        {
            "step": 8,
            "canonical_key": "er_per_device_before_leakage",
            "name": "ER per device per year (before leakage)",
            "formula": f"BE_per_device - PE_per_device = {be_per_hh:.6f} - {pe_per_hh:.6f}",
            "value": round(be_per_hh - pe_per_hh, 6),
            "unit": "tCO2e/device/yr",
        },
    ]

    years = []
    total_er = 0.0
    total_be = 0.0
    total_pe = 0.0
    total_le = 0.0
    # Energy saved accumulator for AMS-II.G Large-scale threshold (60 GWh/yr)
    # ec_b / ec_p are in TJ/device/yr; 1 TJ = 1/3.6 GWh → divide by 3.6 to get GWh
    total_energy_saved_tj = 0.0

    for y in range(crediting_years):
        year_num = y + 1
        cal_year = start_year + y

        usage_rate = max(usage_rate_base - (y * usage_rate_decay), usage_rate_floor)
        # R2: scale by num_devices (= num_hh × devices_per_hh); defaults to num_hh when DPH=1
        active_devices = num_devices * usage_rate
        be_y = be_per_hh * active_devices
        pe_y = pe_per_hh * active_devices
        gross_er = be_y - pe_y
        le_y = gross_er * leakage_pct if leakage_pct > 0 else 0.0
        er_y = gross_er - le_y
        # Energy saved this year (TJ) = (baseline EC - project EC) per device × active devices
        energy_saved_tj_y = (ec_b - ec_p) * active_devices

        total_er += er_y
        total_be += be_y
        total_pe += pe_y
        total_le += le_y
        total_energy_saved_tj += energy_saved_tj_y

        years.append({
            "year_number": year_num,
            "calendar_year": cal_year,
            "usage_rate": round(usage_rate, 4),
            "active_households": round(active_devices, 2),   # field name preserved for compat; value = active devices
            "active_hh_formula": (
                f"max({usage_rate_base} - ({y} * {usage_rate_decay}), {usage_rate_floor})"
                f" × {int(num_hh)} hh × {devices_per_hh:.1f} DPH = {active_devices:.0f} devices"
            ),
            "be_per_hh": round(be_per_hh, 6),
            "pe_per_hh": round(pe_per_hh, 6),
            "baseline_emissions": round(be_y, 2),
            "baseline_formula": f"{be_per_hh:.4f} * {active_devices:.0f}",
            "project_emissions": round(pe_y, 2),
            "project_formula": f"{pe_per_hh:.4f} * {active_devices:.0f}",
            "gross_er": round(gross_er, 2),
            "leakage": round(le_y, 2),
            "leakage_formula": f"{gross_er:.2f} * {leakage_pct:.4f}" if leakage_pct > 0 else "0",
            "net_er": round(er_y, 2),
            "net_er_formula": f"{gross_er:.2f} - {le_y:.2f}",
        })

    # Average annual energy saved in GWh/yr (AMS-II.G scale threshold: 60 GWh/yr)
    avg_energy_saved_gwh_yr = round((total_energy_saved_tj / crediting_years) / 3.6, 2)

    _calc_warnings = _sfc_b_warnings[:]
    if _stove_stacking_applied:
        _calc_warnings.append("VM0050 Eq. 3 stove-stacking cap applied: baseline energy capped to EC_p × (eta_new / eta_old).")
    if _fnrb_source.lower() == "tool30":
        _calc_warnings.append(f"fNRB TOOL30 discount applied: fNRB × (1 - 0.26). Applied value = {fNRB:.4f}.")

    return {
        "calculation_steps": calculation_steps,
        "years": years,
        "warnings": _calc_warnings,
        "summary": {
            "total_er": round(total_er, 2),
            "total_baseline": round(total_be, 2),
            "total_project": round(total_pe, 2),
            "total_leakage": round(total_le, 2),
            "average_annual_er": round(total_er / crediting_years, 2),
            "energy_saved_gwh_yr": avg_energy_saved_gwh_yr,
            "crediting_years": crediting_years,
            "methodology": methodology,
        },
        "parameters_used": {
            "fNRB": {"value": fNRB, "unit": "fraction", "description": "Fraction of non-renewable biomass (applied to CO2 term only)"},
            "NCV_baseline": {"value": NCV_b, "unit": "TJ/Gg", "description": "Net calorific value (baseline fuel)"},
            "NCV_project": {"value": NCV_p, "unit": "TJ/Gg", "description": "Net calorific value (project fuel)"},
            "EF_CO2_baseline": {"value": EF_CO2_b, "unit": "tCO2/TJ", "description": "CO2 emission factor (baseline)"},
            "EF_nonCO2_baseline": {"value": EF_nonCO2_b, "unit": "tCO2e/TJ", "description": "Non-CO2 emission factor (baseline)"},
            "EF_CO2_project": {"value": EF_CO2_p, "unit": "tCO2/TJ", "description": "CO2 emission factor (project)"},
            "EF_nonCO2_project": {"value": EF_nonCO2_p, "unit": "tCO2e/TJ", "description": "Non-CO2 emission factor (project, fNRB excluded for Method 3)"},
            "CF": {"value": CF, "unit": "kg wood/kg charcoal", "description": "Charcoal-to-wood conversion factor"},
            "baseline_fuel": {"value": baseline_fuel, "unit": "", "description": "Baseline fuel type"},
            "project_fuel": {"value": project_fuel, "unit": "", "description": "Project fuel type"},
            "method_id": {"value": method_id or "legacy", "unit": "", "description": "TPDDTEC method (method_1/2/3) or legacy"},
            "is_method_3": {"value": is_method_3, "unit": "", "description": "True = different fuels (fNRB excluded from PE)"},
            "bl_consumption": {"value": round(bl_consumption, 4), "unit": "t/device/yr", "description": "Baseline consumption (raw)"},
            "bl_consumption_wood_equiv": {"value": round(bl_consumption_wood_equiv, 4), "unit": "t/device/yr", "description": "Baseline consumption (wood-equiv)"},
            "pj_consumption": {"value": round(pj_consumption, 4), "unit": "t/device/yr", "description": "Project consumption (raw)"},
            "pj_consumption_wood_equiv": {"value": round(pj_consumption_wood_equiv, 4), "unit": "t/device/yr", "description": "Project consumption (wood-equiv)"},
            "leakage_pct": {"value": leakage_pct, "unit": "fraction", "description": "Leakage deduction percentage"},
            "usage_rate": {"value": usage_rate_base, "unit": "fraction", "description": f"Initial usage rate (decays {usage_rate_decay}/yr, floor {usage_rate_floor})"},
            "usage_rate_decay": {"value": usage_rate_decay, "unit": "fraction/yr", "description": "Annual usage rate decay rate"},
            "usage_rate_floor": {"value": usage_rate_floor, "unit": "fraction", "description": "Minimum usage rate floor"},
            "num_households": {"value": round(num_hh), "unit": "count", "description": "Number of households served"},
            "devices_per_household": {"value": devices_per_hh, "unit": "count", "description": "Project devices per household"},
            "num_devices": {"value": round(num_devices), "unit": "count", "description": "Total commissioned devices (num_hh × DPH)"},
            "household_size": {"value": hh_size, "unit": "persons", "description": "Average household size"},
        },
    }


def calculate_cookstove_er_cohort(params, crediting_years=7, start_year=2025, methodology="VM0050",
                                   deployment_config=None, method_id=None):
    """
    Cohort-based cookstove ER model with deployment ramps, drop-off, and lifetime curves.

    method_id : str | None — pass "method_1", "method_2", or "method_3" for TPDDTEC.
    fNRB placement follows the same rules as calculate_cookstove_er.
    """
    if deployment_config is None:
        deployment_config = {}

    from carbongpt.core.methodology_rules import (
        TPDDTEC_NCV_WOOD_TJ_PER_GG,
        TPDDTEC_EF_CO2_WOOD,
        TPDDTEC_EF_NONCO2_WOOD_AR5,
        TPDDTEC_EF_CO2_CHARCOAL_WITH_PRODUCTION,
        TPDDTEC_EF_NONCO2_CHARCOAL_WITH_PRODUCTION_AR5,
        TPDDTEC_NCV_CHARCOAL_TJ_PER_GG,
        TPDDTEC_METHOD2_DEFAULT_CONSUMPTION,
        TPDDTEC_EF_CO2_CHARCOAL_CAP,
        TPDDTEC_EF_NONCO2_CHARCOAL_CAP_AR5,
    )

    fNRB = _pval(params, "fNRB", 0.30)
    # VM0050 §9.2 / Footnote 22: 26% uncertainty discount when fNRB source is CDM TOOL30
    _fnrb_source_c = _ptext(params, "fnrb_source", "")
    if _fnrb_source_c.lower() == "tool30":
        fNRB = fNRB * (1.0 - 0.26)
    num_hh = int(_pval(params, "num_households", 1000))
    hh_size = _pval(params, "household_size", 5.0)
    leakage_pct = 1.0 - _pval(params, "leakage_discount", 0.95)

    baseline_fuel = _ptext(params, "baseline_fuel", "wood")
    project_fuel = _ptext(params, "project_fuel", baseline_fuel)
    is_charcoal_baseline = baseline_fuel.lower() in ("charcoal", "charbon")
    is_charcoal_project = project_fuel.lower() in ("charcoal", "charbon")
    CF = _pval(params, "CF", 4.0 if is_charcoal_baseline else 1.0)

    is_tpddtec = methodology in ("TPDDTEC", "GS-TPDDTEC") or (method_id is not None and method_id.startswith("method_"))
    is_method_3 = (method_id == "method_3") or (is_tpddtec and baseline_fuel.lower() != project_fuel.lower())

    if is_tpddtec:
        if is_charcoal_baseline:
            NCV_b = _pval(params, "NCV_baseline", TPDDTEC_NCV_CHARCOAL_TJ_PER_GG)
            EF_CO2_b = _pval(params, "EF_CO2_baseline", TPDDTEC_EF_CO2_CHARCOAL_WITH_PRODUCTION)
            EF_nonCO2_b = _pval(params, "EF_nonCO2_baseline", TPDDTEC_EF_NONCO2_CHARCOAL_WITH_PRODUCTION_AR5)
        else:
            NCV_b = _pval(params, "NCV_baseline", TPDDTEC_NCV_WOOD_TJ_PER_GG)
            EF_CO2_b = _pval(params, "EF_CO2_baseline", TPDDTEC_EF_CO2_WOOD)
            EF_nonCO2_b = _pval(params, "EF_nonCO2_baseline", TPDDTEC_EF_NONCO2_WOOD_AR5)
        if is_charcoal_project:
            NCV_p = _pval(params, "NCV_project", TPDDTEC_NCV_CHARCOAL_TJ_PER_GG)
            EF_CO2_p = _pval(params, "EF_CO2_project", TPDDTEC_EF_CO2_CHARCOAL_WITH_PRODUCTION)
            EF_nonCO2_p = _pval(params, "EF_nonCO2_project", TPDDTEC_EF_NONCO2_CHARCOAL_WITH_PRODUCTION_AR5)
        else:
            NCV_p = _pval(params, "NCV_project", TPDDTEC_NCV_WOOD_TJ_PER_GG)
            EF_CO2_p = _pval(params, "EF_CO2_project", TPDDTEC_EF_CO2_WOOD)
            EF_nonCO2_p = _pval(params, "EF_nonCO2_project", TPDDTEC_EF_NONCO2_WOOD_AR5)
    else:
        NCV_b = _pval(params, "NCV_baseline", 15.6)
        EF_CO2_b = _pval(params, "EF_CO2_baseline", 112.0)
        EF_nonCO2_b = _pval(params, "EF_nonCO2_baseline", 9.46)
        NCV_p = _pval(params, "NCV_project", NCV_b)
        EF_CO2_p = _pval(params, "EF_CO2_project", EF_CO2_b)
        EF_nonCO2_p = _pval(params, "EF_nonCO2_project", EF_nonCO2_b)

    # TPDDTEC v4.0 — charcoal EF hard caps (ICS §8/9, Table A: 197.15 / 92.29 tCO2/TJ)
    # Applies to user-supplied parameter overrides; default values (165.22 / 44.83) are below cap.
    if is_tpddtec and is_charcoal_baseline:
        EF_CO2_b = min(EF_CO2_b, TPDDTEC_EF_CO2_CHARCOAL_CAP)
        EF_nonCO2_b = min(EF_nonCO2_b, TPDDTEC_EF_NONCO2_CHARCOAL_CAP_AR5)
    if is_tpddtec and is_charcoal_project:
        EF_CO2_p = min(EF_CO2_p, TPDDTEC_EF_CO2_CHARCOAL_CAP)
        EF_nonCO2_p = min(EF_nonCO2_p, TPDDTEC_EF_NONCO2_CHARCOAL_CAP_AR5)

    if methodology in ("VM0050",) and not is_tpddtec:
        bl_consumption = _pval(params, "baseline_fuel_consumption", hh_size * 0.5)
        pj_consumption = _pval(params, "project_fuel_consumption", bl_consumption * 0.5)
    elif is_tpddtec and method_id == "method_2":
        devices_per_hh = _pval(params, "devices_per_household", 1.0)
        bl_consumption = TPDDTEC_METHOD2_DEFAULT_CONSUMPTION * hh_size / devices_per_hh
        pj_consumption = _pval(params, "project_fuel_consumption", bl_consumption * 0.5)
    else:
        bl_consumption = _pval(params, "baseline_fuel_consumption", 0.5)
        pj_consumption = _pval(params, "project_fuel_consumption", bl_consumption * 0.5)

    # SFC_b cap: TPDDTEC v4.0 ICS 18 — hard cap at 0.95 t/person/yr; warn above 0.75
    _sfc_b_warnings_c = []
    _bl_per_person_c = bl_consumption / hh_size if hh_size > 0 else bl_consumption
    if is_tpddtec and _bl_per_person_c > 0.95:
        bl_consumption = 0.95 * hh_size
        _sfc_b_warnings_c.append(
            f"SFC_b capped at 0.95 t/person/yr (was {_bl_per_person_c:.3f} t/person/yr). TPDDTEC ICS 18 hard cap applied."
        )
    elif is_tpddtec and _bl_per_person_c > 0.75:
        _sfc_b_warnings_c.append(
            f"SFC_b = {_bl_per_person_c:.3f} t/person/yr exceeds 0.75 threshold. Third-party study required for justification (TPDDTEC ICS 18)."
        )

    # CF: NOT applied to consumption when charcoal EFs with-production are used.
    # EF_CO2_charcoal_with_production (165.22 tCO2/TJ) already encodes production losses.
    bl_consumption_wood_equiv = bl_consumption
    pj_consumption_wood_equiv = pj_consumption

    ec_b = bl_consumption_wood_equiv * NCV_b / 1000.0
    ec_p = pj_consumption_wood_equiv * NCV_p / 1000.0

    be_per_unit = ec_b * (fNRB * EF_CO2_b + EF_nonCO2_b)
    if is_method_3:
        pe_per_unit = ec_p * (EF_CO2_p + EF_nonCO2_p)
    else:
        pe_per_unit = ec_p * (fNRB * EF_CO2_p + EF_nonCO2_p)

    # VM0050 Eq. 3 — Stove-stacking cross-check cap (cohort path)
    _stove_stacking_applied_c = False
    _eta_new_c = _pval(params, "eta_new", 0.0) or _pval(params, "eta_project", 0.0)
    _eta_old_c = _pval(params, "eta_old", 0.0) or _pval(params, "eta_baseline", 0.0)
    if not is_method_3 and _eta_new_c > 0 and _eta_old_c > 0 and methodology == "VM0050":
        ec_b_est_c = ec_p * (_eta_new_c / _eta_old_c)
        if ec_b > ec_b_est_c:
            ec_b = ec_b_est_c
            be_per_unit = ec_b * (fNRB * EF_CO2_b + EF_nonCO2_b)
            _stove_stacking_applied_c = True

    er_per_unit = be_per_unit - pe_per_unit

    deployment_mode = deployment_config.get("deployment_mode", "instant")
    monthly_deployment = deployment_config.get("monthly_deployment", 500)
    custom_schedule = deployment_config.get("custom_schedule", [])
    deployment_timing = deployment_config.get("deployment_timing", "mid")
    tech_lifetime_years = deployment_config.get("tech_lifetime_years", 5.0)
    dropoff_mode = deployment_config.get("dropoff_mode", "annual_rate")
    annual_dropoff_rate = deployment_config.get("annual_dropoff_rate", 0.10)
    custom_dropoff_curve = deployment_config.get("custom_dropoff_curve", [])
    usage_rate_mode = deployment_config.get("usage_rate_mode", "fixed")
    usage_rate_fixed = deployment_config.get("usage_rate", 0.90)
    usage_curve = deployment_config.get("usage_curve", [])

    timing_factor_map = {"start": 1.0, "mid": 0.5, "end": 0.0}
    timing_factor = timing_factor_map.get(deployment_timing, 0.5)

    total_months = crediting_years * 12
    cohorts = []

    if deployment_mode == "instant":
        cohorts.append({"month": 0, "count": num_hh})
    elif deployment_mode == "fixed_monthly":
        deployed_so_far = 0
        month = 0
        while deployed_so_far < num_hh and month < total_months:
            batch = min(monthly_deployment, num_hh - deployed_so_far)
            if batch > 0:
                cohorts.append({"month": month, "count": batch})
                deployed_so_far += batch
            month += 1
    elif deployment_mode == "custom":
        if custom_schedule:
            for entry in custom_schedule:
                m = int(entry.get("month", 0))
                c = int(entry.get("count", 0))
                if c > 0 and m < total_months:
                    cohorts.append({"month": m, "count": c})
        if not cohorts:
            cohorts.append({"month": 0, "count": num_hh})

    def _get_survival(age_years):
        if age_years <= 0:
            return 1.0
        if age_years > tech_lifetime_years:
            return 0.0
        if dropoff_mode == "custom_curve" and custom_dropoff_curve:
            sorted_curve = sorted(custom_dropoff_curve, key=lambda x: x.get("year", 0))
            for i, point in enumerate(sorted_curve):
                py = point.get("year", 0)
                pv = point.get("survival_fraction", 1.0)
                if age_years <= py:
                    if i == 0:
                        prev_y, prev_v = 0, 1.0
                    else:
                        prev_y = sorted_curve[i - 1].get("year", 0)
                        prev_v = sorted_curve[i - 1].get("survival_fraction", 1.0)
                    if py == prev_y:
                        return pv
                    frac = (age_years - prev_y) / (py - prev_y)
                    return prev_v + frac * (pv - prev_v)
            return sorted_curve[-1].get("survival_fraction", 0.0)
        return (1.0 - annual_dropoff_rate) ** age_years

    def _get_usage(age_years):
        if usage_rate_mode == "curve" and usage_curve:
            sorted_uc = sorted(usage_curve, key=lambda x: x.get("year", 0))
            for i, point in enumerate(sorted_uc):
                py = point.get("year", 0)
                pv = point.get("rate", 0.9)
                if age_years <= py:
                    if i == 0:
                        return pv
                    prev_y = sorted_uc[i - 1].get("year", 0)
                    prev_v = sorted_uc[i - 1].get("rate", 0.9)
                    if py == prev_y:
                        return pv
                    frac = (age_years - prev_y) / (py - prev_y)
                    return prev_v + frac * (pv - prev_v)
            return sorted_uc[-1].get("rate", 0.5)
        return usage_rate_fixed

    years = []
    total_er = 0.0
    total_be = 0.0
    total_pe = 0.0
    total_le = 0.0
    cumulative_er = 0.0
    total_energy_saved_tj = 0.0   # for AMS-II.G Large-scale threshold (60 GWh/yr)
    deployment_timeline = []

    for y in range(crediting_years):
        year_num = y + 1
        cal_year = start_year + y
        year_start_month = y * 12
        year_end_month = (y + 1) * 12

        deployed_this_year = 0
        active_units = 0.0
        surviving_units = 0.0
        effectively_used = 0.0
        be_y = 0.0
        pe_y = 0.0

        for cohort in cohorts:
            cm = cohort["month"]
            cc = cohort["count"]

            if cm >= year_end_month:
                continue

            if cm >= year_start_month:
                deployed_this_year += cc
                months_active_in_year = year_end_month - cm
                if deployment_mode == "instant" and cm == 0:
                    fraction_of_year = 1.0
                else:
                    fraction_of_year = (months_active_in_year / 12.0) * timing_factor
                    fraction_of_year = max(fraction_of_year, 0.0)
            else:
                fraction_of_year = 1.0

            age_mid = (year_start_month + 6 - cm) / 12.0
            if cm >= year_start_month:
                age_mid = (cm + (year_end_month - cm) / 2.0 - cm) / 12.0
                age_mid = max((year_end_month - cm) / 2.0 / 12.0, 0.01)

            age_end = (year_end_month - cm) / 12.0

            if age_end > tech_lifetime_years:
                if age_end - 1.0 >= tech_lifetime_years:
                    continue
                fraction_alive = max(tech_lifetime_years - (age_end - 1.0), 0) / 1.0
                fraction_of_year *= fraction_alive

            survival = _get_survival(age_mid)
            surviving_count = cc * survival
            usage = _get_usage(age_mid)
            effective = surviving_count * usage

            active_units += surviving_count
            surviving_units += surviving_count
            effectively_used += effective * fraction_of_year

            cohort_be = be_per_unit * effective * fraction_of_year
            cohort_pe = pe_per_unit * effective * fraction_of_year
            be_y += cohort_be
            pe_y += cohort_pe

        gross_er = be_y - pe_y
        le_y = gross_er * leakage_pct if leakage_pct > 0 else 0.0
        er_y = gross_er - le_y

        total_er += er_y
        total_be += be_y
        total_pe += pe_y
        total_le += le_y
        cumulative_er += er_y
        # Energy saved this year (TJ) = (ec_b - ec_p) per device × effectively_used device-years
        total_energy_saved_tj += (ec_b - ec_p) * effectively_used

        cumulative_deployed = sum(c["count"] for c in cohorts if c["month"] < year_end_month)

        years.append({
            "year_number": year_num,
            "calendar_year": cal_year,
            "deployed_this_year": deployed_this_year,
            "cumulative_deployed": cumulative_deployed,
            "active_units": round(active_units, 0),
            "surviving_units": round(surviving_units, 0),
            "effectively_used": round(effectively_used, 0),
            "baseline_emissions": round(be_y, 2),
            "project_emissions": round(pe_y, 2),
            "gross_er": round(gross_er, 2),
            "leakage": round(le_y, 2),
            "net_er": round(er_y, 2),
            "cumulative_er": round(cumulative_er, 2),
        })

        deployment_timeline.append({
            "year": cal_year,
            "year_number": year_num,
            "deployed": deployed_this_year,
            "cumulative_deployed": cumulative_deployed,
            "active": round(active_units, 0),
            "surviving": round(surviving_units, 0),
            "effectively_used": round(effectively_used, 0),
            "net_er": round(er_y, 2),
            "cumulative_er": round(cumulative_er, 2),
        })

    # Full traceable per-unit emission chain (same canonical structure as calculate_cookstove_er)
    pe_formula_str_cohort = (
        f"EC_p × (EF_CO2_p + EF_nonCO2_p) [no fNRB, fuel switch] = {ec_p:.6f} × ({EF_CO2_p} + {EF_nonCO2_p})"
        if is_method_3 else
        f"EC_p × (fNRB × EF_CO2_p + EF_nonCO2_p) = {ec_p:.6f} × ({fNRB} × {EF_CO2_p} + {EF_nonCO2_p})"
    )
    if is_charcoal_baseline:
        cf_formula_cohort = f"Charcoal: EF={EF_CO2_b} tCO2/TJ includes production — CF not applied to consumption. SFC_b={bl_consumption:.6f} t charcoal/device/yr"
    else:
        cf_formula_cohort = f"Wood baseline: SFC_b={bl_consumption:.6f} t/device/yr"
    calculation_steps = [
        {"step": 1, "canonical_key": "baseline_fuel_consumption",
         "name": "Baseline fuel consumption per device",
         "formula": f"baseline_fuel_consumption = {bl_consumption:.6f} t/device/yr",
         "value": round(bl_consumption, 6), "unit": "t/device/yr"},
        {"step": 2, "canonical_key": "project_fuel_consumption",
         "name": "Project fuel consumption per device",
         "formula": f"project_fuel_consumption = {pj_consumption:.6f} t/device/yr",
         "value": round(pj_consumption, 6), "unit": "t/device/yr"},
        {"step": 3, "canonical_key": "cf_adjustment",
         "name": "CF-adjusted baseline wood-equivalent consumption",
         "formula": cf_formula_cohort,
         "value": round(bl_consumption_wood_equiv, 6), "unit": "t wood-equiv/device/yr"},
        {"step": 4, "canonical_key": "baseline_energy_tj",
         "name": "Baseline energy consumption",
         "formula": f"EC_b = SFC_b,we × NCV_b / 1000 = {bl_consumption_wood_equiv:.6f} × {NCV_b} / 1000",
         "value": round(ec_b, 6), "unit": "TJ/device/yr"},
        {"step": 5, "canonical_key": "baseline_emissions_per_device",
         "name": "Baseline emissions per device",
         "formula": f"BE/device = EC_b × (fNRB × EF_CO2_b + EF_nonCO2_b) = {ec_b:.6f} × ({fNRB} × {EF_CO2_b} + {EF_nonCO2_b})",
         "value": round(be_per_unit, 6), "unit": "tCO2e/device/yr"},
        {"step": 6, "canonical_key": "project_energy_tj",
         "name": "Project energy consumption",
         "formula": f"EC_p = SFC_p × NCV_p / 1000 = {pj_consumption_wood_equiv:.6f} × {NCV_p} / 1000",
         "value": round(ec_p, 6), "unit": "TJ/device/yr"},
        {"step": 7, "canonical_key": "project_emissions_per_device",
         "name": "Project emissions per device",
         "formula": pe_formula_str_cohort,
         "value": round(pe_per_unit, 6), "unit": "tCO2e/device/yr"},
        {"step": 8, "canonical_key": "er_per_device_before_leakage",
         "name": "ER per device per year (before leakage)",
         "formula": f"ER/device = BE/device − PE/device = {be_per_unit:.6f} − {pe_per_unit:.6f}",
         "value": round(er_per_unit, 6), "unit": "tCO2e/device/yr"},
        # Deployment configuration info (non-formula steps)
        {"step": 9, "name": "Deployment mode", "formula": deployment_mode, "value": deployment_mode, "unit": ""},
        {"step": 10, "name": "Total units to deploy", "formula": f"num_households = {num_hh}", "value": num_hh, "unit": "units"},
        {"step": 11, "name": "Technology lifetime", "formula": f"{tech_lifetime_years} years", "value": tech_lifetime_years, "unit": "years"},
        {"step": 12, "name": "Drop-off model",
         "formula": f"{dropoff_mode}: {annual_dropoff_rate*100:.1f}%/yr" if dropoff_mode == "annual_rate" else f"{dropoff_mode}: custom curve",
         "value": annual_dropoff_rate if dropoff_mode == "annual_rate" else "custom", "unit": ""},
        {"step": 13, "name": "Usage rate",
         "formula": f"{usage_rate_mode}: {usage_rate_fixed:.0%}" if usage_rate_mode == "fixed" else f"{usage_rate_mode}: custom curve",
         "value": usage_rate_fixed if usage_rate_mode == "fixed" else "custom", "unit": ""},
    ]
    # Add active_households alias for year table compatibility (= effectively_used from cohort)
    for yd in years:
        yd["active_households"] = yd.get("effectively_used", yd.get("active_units", 0))

    _cohort_warnings = _sfc_b_warnings_c[:]
    if _stove_stacking_applied_c:
        _cohort_warnings.append("VM0050 Eq. 3 stove-stacking cap applied: baseline energy capped to EC_p × (eta_new / eta_old).")
    if _fnrb_source_c.lower() == "tool30":
        _cohort_warnings.append(f"fNRB TOOL30 discount applied: fNRB × (1 - 0.26). Applied value = {fNRB:.4f}.")

    return {
        "calculation_steps": calculation_steps,
        "years": years,
        "warnings": _cohort_warnings,
        "deployment_timeline": deployment_timeline,
        "cohort_count": len(cohorts),
        "cohorts_summary": [{"month": c["month"], "count": c["count"]} for c in cohorts[:50]],
        "summary": {
            "total_er": round(total_er, 2),
            "total_baseline": round(total_be, 2),
            "total_project": round(total_pe, 2),
            "total_leakage": round(total_le, 2),
            "average_annual_er": round(total_er / crediting_years, 2) if crediting_years > 0 else 0,
            "energy_saved_gwh_yr": round((total_energy_saved_tj / crediting_years) / 3.6, 2) if crediting_years > 0 else 0,
            "crediting_years": crediting_years,
            "methodology": methodology,
            "deployment_mode": deployment_mode,
            "tech_lifetime_years": tech_lifetime_years,
            "peak_active_units": max((y["active_units"] for y in years), default=0),
            "peak_surviving_units": max((y["surviving_units"] for y in years), default=0),
        },
        "parameters_used": {
            "bl_consumption": {"value": round(bl_consumption, 6), "unit": "t/device/yr", "description": "Baseline specific fuel consumption per device"},
            "pj_consumption": {"value": round(pj_consumption, 6), "unit": "t/device/yr", "description": "Project specific fuel consumption per device"},
            "CF": {"value": CF, "unit": "kg wood/kg charcoal", "description": "Charcoal-to-wood conversion factor"},
            "NCV_baseline": {"value": NCV_b, "unit": "TJ/Gg", "description": "Net calorific value (baseline fuel)"},
            "fNRB": {"value": fNRB, "unit": "fraction", "description": "Fraction of non-renewable biomass"},
            "EF_CO2_baseline": {"value": EF_CO2_b, "unit": "tCO2/TJ", "description": "CO2 emission factor (baseline)"},
            "EF_nonCO2_baseline": {"value": EF_nonCO2_b, "unit": "tCO2e/TJ", "description": "Non-CO2 emission factor (baseline)"},
            "NCV_project": {"value": NCV_p, "unit": "TJ/Gg", "description": "Net calorific value (project fuel)"},
            "EF_CO2_project": {"value": EF_CO2_p, "unit": "tCO2/TJ", "description": "CO2 emission factor (project)"},
            "EF_nonCO2_project": {"value": EF_nonCO2_p, "unit": "tCO2e/TJ", "description": "Non-CO2 emission factor (project)"},
            "num_households": {"value": num_hh, "unit": "count", "description": "Total units to deploy"},
            "leakage_pct": {"value": leakage_pct, "unit": "fraction", "description": "Leakage deduction percentage"},
            "baseline_fuel": {"value": baseline_fuel, "unit": "", "description": "Baseline fuel type"},
            "deployment_mode": {"value": deployment_mode, "unit": "", "description": "Deployment ramp-up mode"},
            "tech_lifetime_years": {"value": tech_lifetime_years, "unit": "years", "description": "Technology operational lifetime"},
            "annual_dropoff_rate": {"value": annual_dropoff_rate, "unit": "fraction", "description": "Annual technology drop-off rate"},
            "usage_rate": {"value": usage_rate_fixed, "unit": "fraction", "description": "Technology usage rate"},
            "deployment_timing": {"value": deployment_timing, "unit": "", "description": "Timing within deployment period"},
        },
    }


def calculate_grid_er(params, crediting_years=7, start_year=2025, methodology="ACM0002"):
    eg_pj = _pval(params, "EG_PJ_y", 50000)
    ef_grid = _pval(params, "EF_grid", 0.8)
    eg_hist = _pval(params, "EG_historical", 0)
    subtype = _ptext(params, "project_subtype", "greenfield")

    if subtype == "greenfield":
        be_formula_desc = f"EG_PJ * EF_grid = {eg_pj:,.0f} * {ef_grid}"
        be_annual = eg_pj * ef_grid
    elif subtype == "capacity_addition":
        net_gen = max(eg_pj - eg_hist, 0)
        be_formula_desc = f"max(EG_PJ - EG_historical, 0) * EF_grid = max({eg_pj:,.0f} - {eg_hist:,.0f}, 0) * {ef_grid} = {net_gen:,.0f} * {ef_grid}"
        be_annual = net_gen * ef_grid
    else:
        be_formula_desc = f"EG_PJ * EF_grid = {eg_pj:,.0f} * {ef_grid}"
        be_annual = eg_pj * ef_grid

    calculation_steps = [
        {
            "step": 1,
            "canonical_key": "electricity_generation",
            "name": "Net electricity generation (project activity)",
            "formula": f"EG_PJ_y = {eg_pj:,.0f} MWh/yr",
            "value": eg_pj,
            "unit": "MWh/yr",
        },
        {
            "step": 2,
            "canonical_key": "grid_emission_factor",
            "name": "Grid emission factor",
            "formula": f"EF_grid = {ef_grid} tCO2/MWh",
            "value": ef_grid,
            "unit": "tCO2/MWh",
        },
    ]

    if subtype == "capacity_addition":
        calculation_steps.append({
            "step": 3,
            "canonical_key": "historical_generation",
            "name": "Historical electricity generation (baseline)",
            "formula": f"EG_historical = {eg_hist:,.0f} MWh/yr",
            "value": eg_hist,
            "unit": "MWh/yr",
        })
        calculation_steps.append({
            "step": 4,
            "canonical_key": "baseline_emissions_annual",
            "name": "Baseline emissions (annual)",
            "formula": be_formula_desc,
            "value": round(be_annual, 2),
            "unit": "tCO2e/yr",
        })
    else:
        calculation_steps.append({
            "step": 3,
            "canonical_key": "baseline_emissions_annual",
            "name": "Baseline emissions (annual)",
            "formula": be_formula_desc,
            "value": round(be_annual, 2),
            "unit": "tCO2e/yr",
        })

    calculation_steps.append({
        "step": len(calculation_steps) + 1,
        "canonical_key": "project_emissions_annual",
        "name": "Project emissions",
        "formula": "PE_y = 0 (renewable energy, zero direct emissions)",
        "value": 0.0,
        "unit": "tCO2e/yr",
    })
    calculation_steps.append({
        "step": len(calculation_steps) + 1,
        "canonical_key": "leakage_annual",
        "name": "Leakage",
        "formula": "LE_y = 0 (no leakage for grid-connected renewable energy)",
        "value": 0.0,
        "unit": "tCO2e/yr",
    })
    calculation_steps.append({
        "step": len(calculation_steps) + 1,
        "canonical_key": "net_er_annual",
        "name": "Net emission reductions (annual)",
        "formula": f"ER_y = BE_y - PE_y - LE_y = {be_annual:,.2f} - 0 - 0",
        "value": round(be_annual, 2),
        "unit": "tCO2e/yr",
    })

    years = []
    total_er = 0.0
    total_be = 0.0

    for y in range(crediting_years):
        year_num = y + 1
        cal_year = start_year + y
        be_y = be_annual
        pe_y = 0.0
        le_y = 0.0
        er_y = be_y - pe_y - le_y
        total_er += er_y
        total_be += be_y

        years.append({
            "year_number": year_num,
            "calendar_year": cal_year,
            "baseline_emissions": round(be_y, 2),
            "baseline_formula": f"{eg_pj:,.0f} * {ef_grid}" if subtype == "greenfield" else f"max({eg_pj:,.0f} - {eg_hist:,.0f}, 0) * {ef_grid}",
            "project_emissions": round(pe_y, 2),
            "project_formula": "0 (renewable)",
            "gross_er": round(er_y, 2),
            "leakage": round(le_y, 2),
            "leakage_formula": "0",
            "net_er": round(er_y, 2),
            "net_er_formula": f"{be_y:,.2f} - 0 - 0",
        })

    return {
        "calculation_steps": calculation_steps,
        "years": years,
        "summary": {
            "total_er": round(total_er, 2),
            "total_baseline": round(total_be, 2),
            "total_project": 0.0,
            "total_leakage": 0.0,
            "average_annual_er": round(total_er / crediting_years, 2),
            "crediting_years": crediting_years,
            "methodology": methodology,
        },
        "parameters_used": {
            "EG_PJ_y": {"value": eg_pj, "unit": "MWh/yr", "description": "Net electricity generation (project)"},
            "EF_grid": {"value": ef_grid, "unit": "tCO2/MWh", "description": "Grid emission factor"},
            "EG_historical": {"value": eg_hist, "unit": "MWh/yr", "description": "Historical electricity generation"},
            "project_subtype": {"value": subtype, "unit": "", "description": "Project subtype (greenfield/capacity_addition)"},
        },
    }


def _read_method_id(project_id):
    """Read method_id from methodology_settings stored in user_projects."""
    try:
        import json as _json
        with get_cursor() as cur:
            cur.execute("SELECT methodology_settings FROM user_projects WHERE id = %s", (project_id,))
            row = cur.fetchone()
        if not row or not row.get("methodology_settings"):
            return None
        raw = row["methodology_settings"]
        if isinstance(raw, str):
            raw = _json.loads(raw)
        if isinstance(raw, dict):
            return raw.get("calculation_method") or raw.get("method_id")
    except Exception as _exc:
        logger.warning("Could not read method_id for project %s: %s", project_id, _exc)
    return None


def _normalize_mecd_result(raw, crediting_years, start_year):
    """Wrap calculate_mecd_er output into the standard result envelope.

    Ensures all keys expected by save_scenario and _render_er_results are present:
    - summary        : {total_er, average_annual_er, crediting_years, deployment_mode}
    - years          : list for er_scenario_years DB inserts (year_number, calendar_year, …)
    - year_by_year   : same list (alias used by UI charts)
    - calculation_steps : list for workbook generation
    - parameters_used   : dict (empty for MECD — parameters are embedded in the raw data)
    """
    yearly = raw.get("yearly", [])
    total_er = raw.get("total_er_tCO2e", 0.0)
    avg_er = raw.get("avg_annual_er_tCO2e", 0.0)

    years = []
    for i, row in enumerate(yearly):
        years.append({
            "year_number": i + 1,
            "calendar_year": row.get("year", start_year + i),
            "baseline_emissions": row.get("BE_y", 0.0),
            "project_emissions": row.get("PE_y", 0.0),
            "leakage": row.get("LE_y", 0.0),
            "net_er": row.get("ER_y", 0.0),
            # aliases used by UI
            "year": row.get("year", start_year + i),
        })

    calc_steps = []
    if yearly:
        first = yearly[0]
        ef_b = raw.get("baseline_ef", {}).get("ef_b", 0.0)
        calc_steps.append({
            "step": 1, "canonical_key": "mecd_baseline_ef",
            "name": "Baseline emission factor (EF_b)", "label": "Baseline EF (tCO2e/TJ)",
            "value": ef_b, "unit": "tCO2e/TJ",
            "formula": raw.get("baseline_ef", {}).get("formula", ""),
        })
        calc_steps.append({
            "step": 2, "canonical_key": "mecd_baseline_emissions",
            "name": "Baseline emissions (BE_y)", "label": "Baseline emissions (tCO2e/yr)",
            "value": first.get("BE_y", 0.0), "unit": "tCO2e/yr",
            "formula": first.get("be_formula", ""),
        })
        if first.get("useful_energy_formula"):
            calc_steps.append({
                "step": 3, "canonical_key": "mecd_useful_energy",
                "name": "Useful project energy (EG_p,useful)", "label": "Useful project energy (TJ/yr)",
                "value": None, "unit": "TJ/yr",
                "formula": first.get("useful_energy_formula", ""),
            })
        calc_steps.append({
            "step": 4, "canonical_key": "mecd_project_emissions",
            "name": "Project emissions (PE_y)", "label": "Project emissions (tCO2e/yr)",
            "value": first.get("PE_y", 0.0), "unit": "tCO2e/yr",
            "formula": first.get("pe_formula", ""),
        })
        calc_steps.append({
            "step": 5, "canonical_key": "mecd_leakage",
            "name": "Leakage (LE_y)", "label": "Leakage (tCO2e/yr)",
            "value": first.get("LE_y", 0.0), "unit": "tCO2e/yr",
            "formula": first.get("le_formula", ""),
        })
        calc_steps.append({
            "step": 6, "canonical_key": "mecd_net_er",
            "name": "Net emission reductions (ER_y)", "label": "Net ER (tCO2e/yr)",
            "value": first.get("ER_y", 0.0), "unit": "tCO2e/yr",
            "formula": "BE_y - PE_y - LE_y",
        })

    return {
        "methodology": "GS-MECD",
        "summary": {
            "total_er": total_er,
            "average_annual_er": avg_er,
            "crediting_years": crediting_years,
            "deployment_mode": "instant",
        },
        "years": years,
        "year_by_year": years,
        "calculation_steps": calc_steps,
        "parameters_used": {},
        "warnings": raw.get("warnings", []),
        "_mecd_raw": raw,
    }


def run_scenario(project_id, scenario_id=None, parameter_overrides=None, deployment_config=None):
    params = get_parameters_as_dict(project_id)

    with get_cursor() as cur:
        cur.execute(
            "SELECT methodology, crediting_period_years, crediting_period_start, methodology_settings "
            "FROM user_projects WHERE id = %s",
            (project_id,),
        )
        project = cur.fetchone()
        if not project:
            return {"error": "Project not found"}

    methodology = (project["methodology"] or "").upper().replace("GS-", "")
    crediting_years = project.get("crediting_period_years") or 7
    start_year = 2025
    if project.get("crediting_period_start"):
        start_year = project["crediting_period_start"].year

    # Resolve method_id from stored methodology_settings
    method_id = None
    raw_settings = project.get("methodology_settings")
    if raw_settings:
        import json as _json
        if isinstance(raw_settings, str):
            try:
                raw_settings = _json.loads(raw_settings)
            except Exception:
                raw_settings = {}
        if isinstance(raw_settings, dict):
            method_id = raw_settings.get("calculation_method") or raw_settings.get("method_id")

    if parameter_overrides:
        for key, val in parameter_overrides.items():
            if key in params:
                params[key]["value"] = val
            else:
                params[key] = {"value": val}

    if methodology in ("VM0050", "TPDDTEC"):
        if deployment_config and deployment_config.get("deployment_mode") != "instant_legacy":
            result = calculate_cookstove_er_cohort(
                params, crediting_years, start_year, methodology, deployment_config,
                method_id=method_id,
            )
        else:
            result = calculate_cookstove_er(
                params, crediting_years, start_year, methodology,
                method_id=method_id,
            )
    elif methodology in ("RECH", "GS-RECH", "GS-RECH-V5", "RECH-V5", "GS_RECH_V5"):
        from carbongpt.core.gs_rech_v5 import calculate_gs_rech_v5_er
        result = calculate_gs_rech_v5_er(params, crediting_years=crediting_years, start_year=start_year)
    elif methodology in ("MECD", "GS-MECD"):
        from carbongpt.core.mecd_simulator import calculate_mecd_er
        raw = calculate_mecd_er(params, crediting_years=crediting_years, start_year=start_year)
        result = _normalize_mecd_result(raw, crediting_years, start_year)
    elif methodology in ("ACM0002", "AMS-I.D.", "AMSID"):
        result = calculate_grid_er(params, crediting_years, start_year, methodology)
    else:
        return {"error": f"ER calculation not implemented for methodology: {methodology}"}

    return result


VALID_SCENARIO_PURPOSES = ("exploratory", "comparison", "shortlisted", "selected_for_drafting", "archived")

_MICRO_SCALE_THRESHOLD_TCO2_YR = 10_000  # tCO2e/yr — GoldStandard micro-scale threshold
_LARGE_SCALE_THRESHOLD_GWH_YR  = 60.0   # GWh/yr   — CDM AMS-II.G Large-scale threshold


def _auto_update_scale_from_er(project_id, summary):
    """
    After a scenario is saved or selected, derive scale_classification from
    ER results and persist it to methodology_settings.

    Two-step classification per TPDDTEC v4.0 / CDM AMS-II.G:
        Step 1 — tCO2e/yr threshold (GoldStandard micro-scale):
            ≤ 10,000 tCO2e/yr  → Micro-scale

        Step 2 — GWh/yr threshold (CDM AMS-II.G Section 1 small-scale boundary):
            > 10,000 tCO2e/yr AND ≤ 60 GWh/yr energy saved  → Small-scale
            > 60 GWh/yr energy saved                          → Large-scale

    Note: energy_saved_gwh_yr is available in the summary only for TPDDTEC/VM0050
    cookstove simulations. If absent, the function only applies the tCO2e threshold.
    """
    try:
        annual_er = float(summary.get("average_annual_er") or 0)
        if annual_er <= 0:
            return  # No reliable ER yet — leave scale unset

        if annual_er <= _MICRO_SCALE_THRESHOLD_TCO2_YR:
            new_scale = "Micro-scale"
        else:
            energy_gwh = float(summary.get("energy_saved_gwh_yr") or 0)
            if energy_gwh > _LARGE_SCALE_THRESHOLD_GWH_YR:
                new_scale = "Large-scale"
            else:
                new_scale = "Small-scale"

        with get_cursor() as cur:
            cur.execute(
                "SELECT methodology_settings FROM user_projects WHERE id = %s",
                (project_id,),
            )
            row = cur.fetchone()
            if not row:
                return
            meth_settings = dict(row["methodology_settings"] or {})
            if meth_settings.get("scale_classification") == new_scale:
                return  # Already correct — skip update
            meth_settings["scale_classification"] = new_scale
            meth_settings["scale_classification_source"] = "er_simulation"

        from carbongpt.repository.store import update_user_project
        update_user_project(project_id, methodology_settings=meth_settings)
        energy_gwh = float(summary.get("energy_saved_gwh_yr") or 0)
        logging.info(
            "scale_classification auto-updated to %s for project %s "
            "(avg annual ER: %.0f tCO2e/yr, energy saved: %.1f GWh/yr)",
            new_scale, project_id, annual_er, energy_gwh,
        )
    except Exception:
        logging.exception("_auto_update_scale_from_er failed for project %s", project_id)


def save_scenario(project_id, name, description="", parameter_overrides=None,
                  carbon_price=None, price_escalation=0, developer_share=100,
                  buffer_pool=0, admin_fee=0, is_baseline=False, deployment_config=None,
                  scenario_purpose="exploratory"):
    if scenario_purpose not in VALID_SCENARIO_PURPOSES:
        scenario_purpose = "exploratory"

    result = run_scenario(project_id, parameter_overrides=parameter_overrides, deployment_config=deployment_config)
    if "error" in result:
        return result

    if carbon_price:
        _add_finance(result, carbon_price, price_escalation, developer_share, buffer_pool, admin_fee)

    if is_baseline and scenario_purpose == "exploratory":
        scenario_purpose = "shortlisted"

    with get_cursor() as cur:
        if scenario_purpose == "selected_for_drafting":
            cur.execute("""
                UPDATE er_scenarios SET scenario_purpose = 'shortlisted'
                WHERE project_id = %s AND scenario_purpose = 'selected_for_drafting'
            """, (project_id,))

        cur.execute("SELECT methodology, crediting_period_years FROM user_projects WHERE id = %s", (project_id,))
        project = cur.fetchone()

        cur.execute("""
            INSERT INTO er_scenarios
            (project_id, name, description, is_baseline, parameter_overrides,
             methodology_code, crediting_years, carbon_price_usd,
             price_escalation_pct, developer_share_pct, buffer_pool_pct,
             admin_fee_pct, results_summary, calculated_at, scenario_purpose)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            RETURNING id
        """, (
            project_id, name, description, is_baseline,
            json.dumps({**(parameter_overrides or {}), "__deployment_config": deployment_config} if deployment_config else (parameter_overrides or {})),
            project["methodology"],
            project.get("crediting_period_years") or 7,
            carbon_price, price_escalation, developer_share,
            buffer_pool, admin_fee,
            json.dumps(result["summary"]),
            scenario_purpose,
        ))
        scenario_id = cur.fetchone()["id"]

        if scenario_purpose == "selected_for_drafting":
            cur.execute("UPDATE user_projects SET selected_scenario_id = %s WHERE id = %s", (scenario_id, project_id))

        for yr in result["years"]:
            cur.execute("""
                INSERT INTO er_scenario_years
                (scenario_id, year_number, calendar_year, baseline_emissions,
                 project_emissions, leakage, net_er, gross_revenue,
                 deductions, net_revenue, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                scenario_id, yr["year_number"], yr["calendar_year"],
                yr["baseline_emissions"], yr["project_emissions"],
                yr["leakage"], yr["net_er"],
                yr.get("gross_revenue", 0), yr.get("deductions", 0),
                yr.get("net_revenue", 0), json.dumps(yr),
            ))

    result["scenario_id"] = scenario_id
    result["scenario_purpose"] = scenario_purpose

    # ── Auto-update scale_classification from ER results
    _auto_update_scale_from_er(project_id, result.get("summary", {}))

    return result


def get_scenarios(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM er_scenarios
            WHERE project_id = %s ORDER BY created_at DESC
        """, (project_id,))
        return cur.fetchall()


def get_scenario_detail(scenario_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM er_scenarios WHERE id = %s", (scenario_id,))
        scenario = cur.fetchone()
        if not scenario:
            return None

        cur.execute("""
            SELECT * FROM er_scenario_years
            WHERE scenario_id = %s ORDER BY year_number
        """, (scenario_id,))
        years = cur.fetchall()

        return {"scenario": scenario, "years": years}


def delete_scenario(scenario_id):
    with get_cursor() as cur:
        cur.execute("SELECT project_id, scenario_purpose FROM er_scenarios WHERE id = %s", (scenario_id,))
        row = cur.fetchone()
        if row and row["scenario_purpose"] == "selected_for_drafting":
            cur.execute("UPDATE user_projects SET selected_scenario_id = NULL WHERE id = %s", (row["project_id"],))
        cur.execute("DELETE FROM er_scenarios WHERE id = %s RETURNING id", (scenario_id,))
        return cur.fetchone()


def select_scenario_for_drafting(project_id, scenario_id):
    with get_cursor() as cur:
        cur.execute("SELECT id, results_summary FROM er_scenarios WHERE id = %s AND project_id = %s", (scenario_id, project_id))
        scenario_row = cur.fetchone()
        if not scenario_row:
            return {"error": f"Scenario {scenario_id} not found for project {project_id}"}

        cur.execute("""
            UPDATE er_scenarios
            SET scenario_purpose = 'shortlisted'
            WHERE project_id = %s AND scenario_purpose = 'selected_for_drafting'
        """, (project_id,))

        cur.execute("""
            UPDATE er_scenarios
            SET scenario_purpose = 'selected_for_drafting'
            WHERE id = %s AND project_id = %s
            RETURNING id, name
        """, (scenario_id, project_id))
        updated = cur.fetchone()

        cur.execute("""
            UPDATE user_projects SET selected_scenario_id = %s WHERE id = %s
        """, (scenario_id, project_id))

    # Auto-update scale from the selected scenario's ER results
    try:
        raw_summary = scenario_row.get("results_summary") or {}
        if isinstance(raw_summary, str):
            raw_summary = json.loads(raw_summary)
        _auto_update_scale_from_er(project_id, raw_summary)
    except Exception:
        pass

    return {"selected_scenario_id": updated["id"], "selected_scenario_name": updated["name"]}


def deselect_scenario(project_id):
    with get_cursor() as cur:
        cur.execute("""
            UPDATE er_scenarios
            SET scenario_purpose = 'shortlisted'
            WHERE project_id = %s AND scenario_purpose = 'selected_for_drafting'
            RETURNING id, name
        """, (project_id,))
        demoted = cur.fetchone()

        cur.execute("UPDATE user_projects SET selected_scenario_id = NULL WHERE id = %s", (project_id,))

        if demoted:
            return {"demoted_scenario_id": demoted["id"], "demoted_scenario_name": demoted["name"]}
        return {"message": "No scenario was selected"}


def update_scenario_purpose(project_id, scenario_id, purpose):
    if purpose not in VALID_SCENARIO_PURPOSES:
        return {"error": f"Invalid purpose: {purpose}. Must be one of {VALID_SCENARIO_PURPOSES}"}

    if purpose == "selected_for_drafting":
        return select_scenario_for_drafting(project_id, scenario_id)

    with get_cursor() as cur:
        cur.execute("SELECT scenario_purpose FROM er_scenarios WHERE id = %s AND project_id = %s", (scenario_id, project_id))
        row = cur.fetchone()
        if not row:
            return {"error": f"Scenario {scenario_id} not found for project {project_id}"}

        old_purpose = row["scenario_purpose"]
        if old_purpose == "selected_for_drafting":
            cur.execute("UPDATE user_projects SET selected_scenario_id = NULL WHERE id = %s", (project_id,))

        cur.execute("""
            UPDATE er_scenarios SET scenario_purpose = %s WHERE id = %s AND project_id = %s RETURNING id, name
        """, (purpose, scenario_id, project_id))
        updated = cur.fetchone()
        return {"scenario_id": updated["id"], "scenario_name": updated["name"], "purpose": purpose}


def get_selected_scenario(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT es.* FROM er_scenarios es
            JOIN user_projects up ON up.selected_scenario_id = es.id
            WHERE up.id = %s
        """, (project_id,))
        scenario = cur.fetchone()
        if not scenario:
            return None

        cur.execute("""
            SELECT * FROM er_scenario_years WHERE scenario_id = %s ORDER BY year_number
        """, (scenario["id"],))
        years = cur.fetchall()
        return {"scenario": scenario, "years": years}


def compare_scenarios(project_id, scenario_ids=None):
    with get_cursor() as cur:
        if scenario_ids:
            placeholders = ",".join(["%s"] * len(scenario_ids))
            cur.execute(f"""
                SELECT * FROM er_scenarios
                WHERE project_id = %s AND id IN ({placeholders})
                ORDER BY created_at DESC
            """, (project_id, *scenario_ids))
        else:
            cur.execute("""
                SELECT * FROM er_scenarios
                WHERE project_id = %s AND scenario_purpose != 'archived'
                ORDER BY created_at DESC
            """, (project_id,))
        scenarios = cur.fetchall()

        result = []
        for s in scenarios:
            summary = s.get("results_summary") or {}
            if isinstance(summary, str):
                try:
                    summary = json.loads(summary)
                except Exception:
                    summary = {}

            overrides = s.get("parameter_overrides") or {}
            if isinstance(overrides, str):
                try:
                    overrides = json.loads(overrides)
                except Exception:
                    overrides = {}
            clean_overrides = {k: v for k, v in overrides.items() if not str(k).startswith("__")}

            result.append({
                "id": s["id"],
                "name": s["name"],
                "scenario_purpose": s.get("scenario_purpose", "exploratory"),
                "is_baseline": s.get("is_baseline", False),
                "total_er": summary.get("total_er", 0),
                "average_annual_er": summary.get("average_annual_er", 0),
                "crediting_years": s.get("crediting_years", 7),
                "carbon_price_usd": s.get("carbon_price_usd"),
                "parameter_overrides": clean_overrides,
                "created_at": str(s.get("created_at", "")),
            })
        return {"scenarios": result, "count": len(result)}


def migrate_baseline_to_selected(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT selected_scenario_id FROM user_projects WHERE id = %s
        """, (project_id,))
        proj = cur.fetchone()
        if proj and proj.get("selected_scenario_id"):
            return {"migrated": False, "reason": "already_has_selected"}

        cur.execute("""
            SELECT id FROM er_scenarios
            WHERE project_id = %s AND scenario_purpose = 'selected_for_drafting'
            LIMIT 1
        """, (project_id,))
        if cur.fetchone():
            return {"migrated": False, "reason": "already_has_selected_purpose"}

        cur.execute("""
            SELECT id, name FROM er_scenarios
            WHERE project_id = %s AND is_baseline = true
              AND (scenario_purpose IS NULL OR scenario_purpose NOT IN ('selected_for_drafting'))
            ORDER BY calculated_at DESC
            LIMIT 1
        """, (project_id,))
        row = cur.fetchone()
        if row:
            scenario_id = row["id"]
            cur.execute("""
                UPDATE er_scenarios SET scenario_purpose = 'selected_for_drafting'
                WHERE id = %s
            """, (scenario_id,))
            cur.execute("""
                UPDATE user_projects SET selected_scenario_id = %s
                WHERE id = %s
            """, (scenario_id, project_id))
            return {"migrated": True, "scenario_id": scenario_id, "name": row["name"]}
    return {"migrated": False}


def run_sensitivity(project_id, param_key, variation_pct=20, steps=5):
    params = get_parameters_as_dict(project_id)
    if param_key not in params or params[param_key]["value"] is None:
        return {"error": f"Parameter {param_key} not found or has no value"}

    base_value = float(params[param_key]["value"])
    if base_value == 0:
        return {"error": f"Cannot run sensitivity on zero-value parameter {param_key}"}

    results = []
    for i in range(-steps, steps + 1):
        pct_change = (i / steps) * variation_pct
        test_value = base_value * (1 + pct_change / 100)
        overrides = {param_key: test_value}
        calc = run_scenario(project_id, parameter_overrides=overrides)
        if "error" not in calc:
            results.append({
                "pct_change": round(pct_change, 1),
                "param_value": round(test_value, 6),
                "total_er": calc["summary"]["total_er"],
                "annual_er": calc["summary"]["average_annual_er"],
            })

    base_calc = run_scenario(project_id)
    base_er = base_calc["summary"]["total_er"] if "error" not in base_calc else 0

    return {
        "param_key": param_key,
        "base_value": base_value,
        "base_er": base_er,
        "variation_pct": variation_pct,
        "results": results,
    }


def _add_finance(result, carbon_price, price_escalation=0, developer_share=100, buffer_pool=0, admin_fee=0):
    total_gross = 0
    total_deductions = 0
    total_net = 0

    for yr in result["years"]:
        y = yr["year_number"] - 1
        price = carbon_price * (1 + price_escalation / 100) ** y
        gross = yr["net_er"] * price
        buffer = gross * buffer_pool / 100
        admin = gross * admin_fee / 100
        deduct = buffer + admin
        net = (gross - deduct) * developer_share / 100

        yr["carbon_price"] = round(price, 2)
        yr["gross_revenue"] = round(gross, 2)
        yr["deductions"] = round(deduct, 2)
        yr["net_revenue"] = round(net, 2)
        yr["buffer_contribution"] = round(buffer, 2)

        total_gross += gross
        total_deductions += deduct
        total_net += net

    result["summary"]["total_gross_revenue"] = round(total_gross, 2)
    result["summary"]["total_deductions"] = round(total_deductions, 2)
    result["summary"]["total_net_revenue"] = round(total_net, 2)
    result["summary"]["carbon_price"] = carbon_price
    result["summary"]["developer_share_pct"] = developer_share



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
