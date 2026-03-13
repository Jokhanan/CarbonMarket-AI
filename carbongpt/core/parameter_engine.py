import logging
from carbongpt.repository.db import get_cursor
from carbongpt.core.tool_defaults import (
    get_fnrb_for_country,
    get_fuel_defaults,
    get_defaults_for_methodology,
    TOOL33_OTHER_DEFAULTS,
    METHODOLOGY_SUPPLEMENTARY_PARAMS,
    LEAKAGE_DEFAULTS,
    GWP_VALUES,
    WOOD_TO_CHARCOAL_CF,
)

logger = logging.getLogger(__name__)

FUEL_CANONICAL_MAP = {
    "wood": "wood", "firewood": "wood", "biomass": "wood", "fuelwood": "wood", "bois": "wood",
    "charcoal": "charcoal", "charbon": "charcoal", "green_charcoal": "charcoal",
    "dung": "dung", "animal_dung": "dung", "cow_dung": "dung",
    "crop_residue": "crop_residue", "agricultural_residue": "crop_residue", "residue": "crop_residue",
    "kerosene": "kerosene",
    "lpg": "lpg", "gas": "lpg", "propane": "lpg",
}

FUEL_DISPLAY_LABELS = {
    "wood": "Wood / Firewood",
    "charcoal": "Charcoal",
    "dung": "Animal Dung",
    "crop_residue": "Crop Residue",
    "kerosene": "Kerosene",
    "lpg": "LPG",
    "other": "Other",
}

FUEL_CANONICAL_OPTIONS = list(FUEL_DISPLAY_LABELS.keys())


def normalize_fuel_type(raw_value):
    if not raw_value:
        return "wood"
    key = raw_value.strip().lower().replace(" ", "_").replace("-", "_")
    return FUEL_CANONICAL_MAP.get(key, "other")


def get_fuel_display_label(canonical_value):
    return FUEL_DISPLAY_LABELS.get(canonical_value, canonical_value)


PARAMETER_DEFINITIONS = {
    "VM0050": [
        # ── fNRB ────────────────────────────────────────────────────────────────
        # VM0050 §9.2 specifies three sources in priority order:
        #   1) UNFCCC national default values (draft acceptable; update on approval)
        #   2) CDM TOOL30, with a mandatory 26% uncertainty discount (Footnote 22):
        #      applied_fNRB = TOOL30_fNRB × (1 − 0.26)
        #   3) CDM TOOL33 v3 default values
        {"param_key": "fNRB", "param_name": "Fraction of non-renewable biomass (fNRB,y)", "category": "baseline",
         "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": True,
         "tool_reference": "UNFCCC national defaults / CDM TOOL30 (×0.74 discount) / CDM TOOL33 v3",
         "depends_on": [],
         "aliases": ["fraction of non-renewable biomass", "non-renewable biomass fraction", "f_NRB", "fNRB_y",
                     "fNRB,y", "fNRB,i,y", "fraction non-renewable", "non-renewable fraction"],
         "extraction_hint": (
             "Extract the fraction of non-renewable biomass (fNRB) used in baseline emissions (Eq. 1) or project "
             "emissions (Eq. 7). Sources in descending preference: (1) UNFCCC national default — note if draft; "
             "(2) CDM TOOL30 result multiplied by 0.74 (26% uncertainty discount per VM0050 Footnote 22); "
             "(3) CDM TOOL33 v3 Table 3 (national) or Table 2 (regional). "
             "Do NOT apply fNRB to fossil fuel baselines — it is only for woody biomass fuels."
         ),
         "noise_terms": []},

        # ── Fuel NCV (§9.1 NCVb,i / NCVp,j) ────────────────────────────────────
        # IPCC 2006 defaults: Wood = 0.0156 TJ/tonne (15.6 TJ/Gg), Charcoal = 0.0295 TJ/tonne (29.5 TJ/Gg)
        {"param_key": "NCV_baseline", "param_name": "Net calorific value — baseline fuel (NCVb,i)",
         "category": "fuel_property", "unit": "TJ/Gg", "data_type": "number", "min_value": 5.0, "max_value": 55.0,
         "is_ex_ante": True, "depends_on": [],
         "aliases": ["NCV_b", "NCVb,i", "net calorific value baseline", "NCV of baseline fuel",
                     "calorific value of wood", "calorific value of charcoal", "heating value baseline"],
         "extraction_hint": (
             "Extract the NCV for the BASELINE fuel only. IPCC 2006 defaults: wood = 15.6 TJ/Gg (0.0156 TJ/tonne), "
             "charcoal = 29.5 TJ/Gg (0.0295 TJ/tonne). Source preference: project-specific > national default > IPCC."
         ),
         "noise_terms": []},
        {"param_key": "NCV_project", "param_name": "Net calorific value — project fuel (NCVp,j)",
         "category": "fuel_property", "unit": "TJ/Gg", "data_type": "number", "min_value": 5.0, "max_value": 55.0,
         "is_ex_ante": True, "depends_on": [],
         "aliases": ["NCV_p", "NCVp,j", "net calorific value project", "NCV of project fuel",
                     "heating value project fuel"],
         "extraction_hint": (
             "Extract the NCV for the PROJECT fuel only. Do not confuse with baseline NCV. "
             "IPCC 2006 defaults: wood = 15.6 TJ/Gg, charcoal = 29.5 TJ/Gg. "
             "For LPG, bioethanol, or other fuels use national or IPCC source."
         ),
         "noise_terms": []},

        # ── CO2 emission factors (§9.1 EFb,i,CO2 / EFp,j,CO2) ────────────────
        # IPCC defaults: Wood = 112 tCO2/TJ
        # Charcoal: 112 tCO2/TJ combustion-only (renewable charcoal project, fNRB=0) OR
        #           165.22 tCO2/TJ incl. production (non-renewable biomass baseline)
        {"param_key": "EF_CO2_baseline", "param_name": "CO2 emission factor — baseline fuel (EFb,i,CO2)",
         "category": "emission_factor", "unit": "tCO2/TJ", "data_type": "number", "min_value": 0.0, "max_value": 250.0,
         "is_ex_ante": True, "depends_on": [],
         "aliases": ["EFb,i,CO2", "EF_b,f,CO2", "baseline CO2 emission factor", "CO2 EF baseline fuel",
                     "combustion emission factor baseline"],
         "extraction_hint": (
             "Extract the CO2 EF for the BASELINE fuel. IPCC 2006 defaults: wood = 112 tCO2/TJ. "
             "Charcoal (non-renewable baseline): 165.22 tCO2/TJ (combustion + production). "
             "Charcoal combustion-only: 112 tCO2/TJ (use when CF method applies or renewable charcoal). "
             "Source preference: project-specific > national > IPCC."
         ),
         "noise_terms": []},
        {"param_key": "EF_nonCO2_baseline", "param_name": "Non-CO2 emission factor — baseline fuel (EFb,i,nonCO2)",
         "category": "emission_factor", "unit": "tCO2e/TJ", "data_type": "number", "min_value": 0.0, "max_value": 100.0,
         "is_ex_ante": True, "depends_on": [],
         "aliases": ["EFb,i,nonCO2", "EF_b,f,nonCO2", "baseline non-CO2 emission factor",
                     "non-CO2 EF baseline", "CH4 N2O emission factor baseline"],
         "extraction_hint": (
             "Extract the non-CO2 (CH4 + N2O) EF for the BASELINE fuel (AR5 GWP). "
             "IPCC defaults: wood = 9.46 tCO2e/TJ, charcoal combustion-only = 5.865 tCO2e/TJ, "
             "charcoal incl. production = 44.83 tCO2e/TJ."
         ),
         "noise_terms": []},
        {"param_key": "EF_CO2_project", "param_name": "CO2 emission factor — project fuel (EFp,j,CO2)",
         "category": "emission_factor", "unit": "tCO2/TJ", "data_type": "number", "min_value": 0.0, "max_value": 200.0,
         "is_ex_ante": True, "depends_on": [],
         "aliases": ["EFp,j,CO2", "EF_p,f,CO2", "project CO2 emission factor"],
         "extraction_hint": (
             "Extract the CO2 EF for the PROJECT fuel. Zero for 100% renewable biomass or renewable electricity. "
             "Source preference: project-specific > national > IPCC."
         ),
         "noise_terms": []},
        {"param_key": "EF_nonCO2_project", "param_name": "Non-CO2 emission factor — project fuel (EFp,j,nonCO2)",
         "category": "emission_factor", "unit": "tCO2e/TJ", "data_type": "number", "min_value": 0.0, "max_value": 100.0,
         "is_ex_ante": True, "depends_on": [],
         "aliases": ["EFp,j,nonCO2", "EF_p,f,nonCO2", "project non-CO2 emission factor"],
         "extraction_hint": "Extract the non-CO2 EF for the PROJECT fuel only, not the baseline fuel.",
         "noise_terms": []},

        # ── Baseline fuel consumption (§8.1.1 / §9.1 BCex-ante,b,i / §9.2 BCb,i,y) ─
        # Ex-ante defaults (§8.1.1 Option 2): firewood = 0.5 t/capita/yr, charcoal = 0.13 t/capita/yr
        # BCb,i,y (monitored): updated biennially from control household KPT
        {"param_key": "BCex_ante_b_i", "param_name": "Ex-ante baseline fuel consumption per device (BCex-ante,b,i)",
         "category": "baseline", "unit": "tonnes/device/year", "data_type": "number", "min_value": 0.01,
         "max_value": 10.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["BCex-ante,b,i", "BC_ex_ante", "ex-ante baseline consumption", "baseline fuel use ex-ante",
                     "pre-project fuel consumption"],
         "extraction_hint": (
             "Extract the ex-ante annual average fuel quantity per baseline device (BCex-ante,b,i). "
             "VM0050 §8.1.1 Option 2 defaults (scaled by household size Hhi): "
             "firewood = 0.5 t/capita/yr; charcoal = 0.13 t/capita/yr. "
             "Option 1: from Kitchen Performance Test (KPT) at 90/10 confidence/precision."
         ),
         "noise_terms": []},
        {"param_key": "baseline_fuel_consumption", "param_name": "Baseline fuel consumption per device (BCb,i,y)",
         "category": "baseline", "unit": "tonnes/device/year", "data_type": "number", "min_value": 0.01,
         "max_value": 20.0, "is_ex_ante": False, "depends_on": [],
         "aliases": ["BCb,i,y", "BC_b,i,y", "baseline fuel consumption", "fuel consumption in baseline scenario",
                     "wood consumption baseline", "fuel use without project", "biennial KPT result"],
         "extraction_hint": (
             "Extract BCb,i,y — the monitored (biennial KPT) baseline fuel use in control households. "
             "Only extract if the document explicitly refers to monitored or follow-up baseline fuel consumption. "
             "Do NOT extract this field from KPT results labelled as ex-ante."
         ),
         "noise_terms": []},

        # ── Project fuel consumption (§8.2.1.1 BCp,j,k,y / §9.2) ──────────────
        {"param_key": "project_fuel_consumption", "param_name": "Project fuel consumption per device (BCp,j,k,y)",
         "category": "project", "unit": "tonnes/device/year", "data_type": "number", "min_value": 0.0,
         "max_value": 20.0, "is_ex_ante": False, "depends_on": [],
         "aliases": ["BCp,j,k,y", "BC_p,j,k,y", "project fuel consumption", "fuel use with improved stove",
                     "stove fuel consumption monitored", "KPT project result"],
         "extraction_hint": (
             "Extract BCp,j,k,y — the average fuel per project device from KPT or direct measurement. "
             "Only extract if text clearly refers to PROJECT stove fuel use, not baseline."
         ),
         "noise_terms": []},

        # ── Device counts (§9.2 Nj,k,y) ─────────────────────────────────────────
        {"param_key": "num_devices", "param_name": "Number of commissioned project devices (Nj,k,y)",
         "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1,
         "max_value": 10000000, "is_ex_ante": True, "depends_on": [],
         "aliases": ["number of stoves", "number of devices distributed", "total devices deployed",
                     "N_i,y", "N_j,k,y", "Nj,k,y", "devices commissioned", "number of project technologies"],
         "extraction_hint": (
             "Only extract the TOTAL number of project devices commissioned or distributed. "
             "Do NOT extract sample sizes, survey counts, or unit numbering."
         ),
         "noise_terms": [r"\bsample\b", r"\bjob", r"\bunit\s+number", r"\bnumber of units\b"]},
        {"param_key": "num_households", "param_name": "Number of households served",
         "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1,
         "max_value": 10000000, "is_ex_ante": True, "depends_on": [],
         "aliases": ["number of households", "total households", "number of families", "participating households"],
         "extraction_hint": (
             "Only extract the TOTAL number of households served or targeted by the project. "
             "Do NOT extract survey sample sizes or administrative counts."
         ),
         "noise_terms": [r"\bsample[sd]?\b", r"\bsurvey\b", r"\brespondent", r"\bsampling\b"]},
        {"param_key": "devices_per_household", "param_name": "Project devices per household",
         "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1,
         "max_value": 10, "is_ex_ante": True, "depends_on": []},
        {"param_key": "num_beneficiaries", "param_name": "Number of beneficiaries",
         "category": "activity_data", "unit": "persons", "data_type": "number", "min_value": 1,
         "max_value": 100000000, "is_ex_ante": True, "depends_on": ["num_households", "household_size"]},

        # ── Household size (§9.1 Hhi / Hhj,k) ────────────────────────────────────
        # VM0050 uses "equivalent standard male adults" per Guidelines for Woodfuel Surveys (FAO)
        {"param_key": "household_size", "param_name": "Average household size (Hhi / Hhj,k)",
         "category": "activity_data", "unit": "persons/household", "data_type": "number",
         "min_value": 1, "max_value": 20, "is_ex_ante": True, "depends_on": [],
         "aliases": ["average household size", "Hhi", "Hhj,k", "persons per household",
                     "family size", "members per household", "HH size", "adult equivalents per household"],
         "extraction_hint": (
             "Extract the average household size from the baseline survey (90/10 confidence/precision required). "
             "VM0050 uses 'equivalent standard male adults' per FAO woodfuel survey guidelines. "
             "Used to scale per-capita fuel consumption to per-device values."
         ),
         "noise_terms": [r"\bton\b", r"\btonne\b", r"\bcharcoal\b", r"\bfuel\b", r"\bkg\b"]},

        # ── Usage/adoption rate (§9.2 nj,k,y) ────────────────────────────────────
        # Option 1: SUMs (continuous); Option 2: annual adoption survey (90/10 CI, lower bound used)
        {"param_key": "usage_rate", "param_name": "Adoption/usage rate (nj,k,y)",
         "category": "monitoring", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0,
         "is_ex_ante": False, "depends_on": [],
         "aliases": ["adoption rate", "utilization rate", "active use rate", "n_j,k,y", "nj,k,y",
                     "proportion of devices in use", "proportion operating", "usage survey rate"],
         "extraction_hint": (
             "Extract the proportion of commissioned devices still in regular use (nj,k,y). "
             "VM0050 Option 1: measured by Stove Use Monitors (SUMs). "
             "Option 2: annual survey at 90/10 confidence/precision — use lower bound of confidence interval. "
             "Do not confuse with overall project scale or sample size."
         ),
         "noise_terms": []},
        {"param_key": "usage_rate_decay", "param_name": "Annual usage rate decay",
         "category": "monitoring", "unit": "fraction/year", "data_type": "number", "default": 0.02,
         "min_value": 0.0, "max_value": 0.10, "is_ex_ante": True, "depends_on": [],
         "description": "Annual reduction in nj,k,y per year (applied when monitoring data are not available)"},
        {"param_key": "usage_rate_floor", "param_name": "Minimum usage rate floor",
         "category": "monitoring", "unit": "fraction", "data_type": "number", "default": 0.50,
         "min_value": 0.0, "max_value": 1.0, "is_ex_ante": True, "depends_on": [],
         "description": "Usage rate cannot decay below this floor value"},

        # ── Thermal efficiency — baseline (§9.1 ηold,avg) ─────────────────────────
        # Default for three-stone fire: 15%. Other devices: WBT, manufacturer cert, or CDM TOOL33 v3.
        {"param_key": "baseline_efficiency", "param_name": "Weighted average baseline device efficiency (ηold,avg)",
         "category": "baseline", "unit": "fraction", "data_type": "number", "min_value": 0.05, "max_value": 0.50,
         "is_ex_ante": True, "depends_on": [],
         "aliases": ["baseline thermal efficiency", "ηold,avg", "eta_old,avg", "traditional stove efficiency",
                     "weighted average efficiency baseline", "three-stone fire efficiency"],
         "extraction_hint": (
             "Extract the weighted average thermal efficiency of the BASELINE devices being replaced (ηold,avg). "
             "VM0050 §9.1 default: 15% for three-stone fire or cookstove with no improved combustion or chimney. "
             "Other baseline devices: WBT survey, manufacturer cert, national standards body, or CDM TOOL33 v3. "
             "Do not extract project device efficiency here."
         ),
         "noise_terms": []},

        # ── Thermal efficiency — project (§9.2 ηnew,avg,y) ───────────────────────
        # Monitored annually. Aging must be accounted for:
        #   - Biomass/fossil: WBT or linear decrease to 25% terminal efficiency over device lifespan
        #   - Electric: annual measurement of heat absorbed / electrical energy input
        # Minimum thresholds (§4): biomass 25%, LPG/bioethanol 30%, hot plate 40%, induction 70%
        {"param_key": "project_efficiency", "param_name": "Weighted average project device efficiency (ηnew,avg,y)",
         "category": "project", "unit": "fraction", "data_type": "number", "min_value": 0.10, "max_value": 0.90,
         "is_ex_ante": True, "depends_on": [],
         "aliases": ["project thermal efficiency", "ηnew,avg,y", "eta_new,avg,y", "improved stove efficiency",
                     "weighted average efficiency project", "WBT result project device"],
         "extraction_hint": (
             "Extract the weighted average thermal efficiency of PROJECT devices (ηnew,avg,y). "
             "VM0050 §4 minimum thresholds: biomass EE/fuel-switch >= 25%, LPG/bioethanol >= 30%, "
             "hot plate/electric hob >= 40%, induction/other electric >= 70%. "
             "Aging must be accounted for annually (linear decay to 25% terminal for biomass/fossil devices)."
         ),
         "noise_terms": []},

        # ── Specific energy consumption for electric pressure cookers (§8.1.1.1, Eq. 5) ──
        # SCb,i and SCp,j in TJ/test/person — from Controlled Cooking Test (CCT)
        {"param_key": "SC_baseline", "param_name": "Specific energy consumption — baseline device (SCb,i)",
         "category": "baseline", "unit": "TJ/test/person", "data_type": "number", "min_value": 0.0,
         "max_value": 0.01, "is_ex_ante": True, "depends_on": [],
         "aliases": ["SCb,i", "SC_b,i", "specific energy consumption baseline", "CCT result baseline"],
         "extraction_hint": (
             "Extract SCb,i — specific energy consumption of the baseline device from a Controlled Cooking Test (CCT). "
             "Only applicable to electric pressure cooker projects (VM0050 §8.1.1.1 Eq. 5). "
             "Units: TJ/test/person. Must use same cooking tasks for baseline and project CCT."
         ),
         "noise_terms": []},
        {"param_key": "SC_project", "param_name": "Specific energy consumption — project device (SCp,j)",
         "category": "project", "unit": "TJ/test/person", "data_type": "number", "min_value": 0.0,
         "max_value": 0.01, "is_ex_ante": True, "depends_on": [],
         "aliases": ["SCp,j", "SC_p,j", "specific energy consumption project", "CCT result project electric"],
         "extraction_hint": (
             "Extract SCp,j — specific energy consumption of the PROJECT electric pressure cooker from CCT. "
             "Used in Eq. 5 to back-calculate baseline energy consumption. "
             "Same cooking tasks must be used in both baseline and project CCT."
         ),
         "noise_terms": []},

        # ── Electricity consumption — electric project devices (§9.2 ECp,j,k,y) ──
        # Monitored by direct metering (continuous). Units: MWh/device/year.
        {"param_key": "EC_electricity_project", "param_name": "Annual electricity consumption per device (ECp,j,k,y)",
         "category": "project", "unit": "MWh/device/year", "data_type": "number", "min_value": 0.01,
         "max_value": 50.0, "is_ex_ante": False, "depends_on": [],
         "aliases": ["ECp,j,k,y", "EC_p,j,k,y", "annual electricity consumption", "electricity use per device",
                     "metered electricity", "kWh per stove"],
         "extraction_hint": (
             "Extract ECp,j,k,y — annual electricity consumption per electric project device (MWh). "
             "VM0050 §9.2: measured by direct metering at 90/10 confidence/precision. "
             "Used in Eq. 5 (electric pressure cooker back-calculation) and Eq. 8 (project emissions). "
             "If given in kWh, divide by 1000."
         ),
         "noise_terms": []},

        # ── Grid emission factor (§9.2 EFel,y) ────────────────────────────────────
        # Source: CDM TOOL07. Zero for 100% renewable electricity sources.
        {"param_key": "EF_electricity", "param_name": "Grid electricity emission factor (EFel,y)",
         "category": "emission_factor", "unit": "tCO2e/MWh", "data_type": "number", "min_value": 0.0,
         "max_value": 3.0, "is_ex_ante": False, "depends_on": [],
         "tool_reference": "CDM TOOL07",
         "aliases": ["EFel,y", "EF_el", "grid EF", "electricity emission factor", "combined margin EF",
                     "electricity system EF", "tCO2e per MWh"],
         "extraction_hint": (
             "Extract EFel,y — the grid electricity emission factor in tCO2e/MWh (VM0050 Eq. 8). "
             "Source: CDM TOOL07. Zero where electricity is from 100% renewable sources. "
             "For mini-grid or decentralised systems: account for the non-renewable share only."
         ),
         "noise_terms": []},

        # ── T&D losses (§9.2 TDLj,y) ─────────────────────────────────────────────
        # Source: CDM TOOL05. Zero for self-generated renewable electricity.
        {"param_key": "TDL", "param_name": "Transmission and distribution losses (TDLj,y)",
         "category": "project", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 0.50,
         "is_ex_ante": False, "depends_on": [],
         "tool_reference": "CDM TOOL05",
         "aliases": ["TDLj,y", "TDL_j,y", "T&D losses", "transmission losses", "distribution losses",
                     "grid losses", "technical losses"],
         "extraction_hint": (
             "Extract TDLj,y — average technical T&D losses for the electricity grid serving project devices. "
             "Source: CDM TOOL05. Monitored once per monitoring period. "
             "Zero for self-generated on-site renewable electricity."
         ),
         "noise_terms": []},

        # ── Leakage (§8.3, Eq. 11) ────────────────────────────────────────────────
        # VM0050 applies a fixed 5% standard leakage deduction: ER = (BE - PE) × 0.95 − LERB,y
        # Both biomass leakage and fossil-fuel leakage use the 0.95 retention factor.
        # Renewable biomass leakage (LERB,y) calculated separately via CDM TOOL16.
        {"param_key": "leakage_discount", "param_name": "Leakage retention factor (VM0050 Eq. 11)",
         "category": "leakage", "unit": "fraction", "data_type": "number", "min_value": 0.90, "max_value": 1.0,
         "default": 0.95, "is_ex_ante": True, "depends_on": [],
         "aliases": ["leakage factor", "leakage deduction", "0.95 factor", "5% leakage deduction"],
         "extraction_hint": (
             "VM0050 §8.3 and Eq. 11 apply a fixed 0.95 retention factor (5% standard leakage deduction) "
             "to (BEy − PEy) for both non-renewable biomass and fossil fuel leakage. "
             "Renewable biomass leakage (LERB,y) is subtracted separately using CDM TOOL16."
         ),
         "noise_terms": []},

        # ── Wood-to-charcoal conversion factor (§9.1 CF) ─────────────────────────
        # CDM TOOL33 default: 4 t dry wood / t charcoal. Up to 6 with national substantiation.
        {"param_key": "CF", "param_name": "Wood-to-charcoal conversion factor (CF)",
         "category": "fuel_property", "unit": "t dry wood / t charcoal", "data_type": "number",
         "min_value": 2.0, "max_value": 8.0, "is_ex_ante": True,
         "tool_reference": "CDM TOOL33 v3", "depends_on": [],
         "aliases": ["conversion factor", "CF", "charcoal conversion factor", "wood to charcoal ratio",
                     "wood-to-charcoal factor"],
         "extraction_hint": (
             "Extract the wood-to-charcoal conversion factor (CF). CDM TOOL33 default: 4 t dry wood / t charcoal. "
             "VM0050 §9.1 allows up to 6 where substantiated by government-approved national or regional values. "
             "Only applicable when charcoal is used AND the CF method is chosen over direct charcoal EF method."
         ),
         "noise_terms": []},

        # ── Crediting period / project metadata ────────────────────────────────────
        {"param_key": "baseline_fuel", "param_name": "Baseline fuel type",
         "category": "baseline", "unit": "", "data_type": "text", "is_ex_ante": True, "depends_on": []},
        {"param_key": "project_fuel", "param_name": "Project fuel type",
         "category": "project", "unit": "", "data_type": "text", "is_ex_ante": True, "depends_on": []},
    ],
    "TPDDTEC": [
        {"param_key": "fNRB", "param_name": "Fraction of non-renewable biomass", "category": "baseline", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": True, "tool_reference": "CDM TOOL33 v3", "depends_on": [],
         "aliases": ["fraction of non-renewable biomass", "non-renewable biomass fraction", "f_NRB", "fNRB_y", "fNRB,i,y"],
         "extraction_hint": "Only extract the fraction of non-renewable biomass for the project region. Default values sourced from CDM TOOL33 v3 Table 3 (national) or Table 2 (regional). Project-specific calculation uses CDM TOOL30.",
         "noise_terms": []},
        {"param_key": "NCV_baseline", "param_name": "Net calorific value (baseline fuel)", "category": "fuel_property", "unit": "TJ/Gg", "data_type": "number", "min_value": 5.0, "max_value": 55.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["NCV_b", "net calorific value baseline", "NCV of baseline fuel"],
         "extraction_hint": "Extract the NCV for the BASELINE fuel type only.",
         "noise_terms": []},
        {"param_key": "NCV_project", "param_name": "Net calorific value (project fuel)", "category": "fuel_property", "unit": "TJ/Gg", "data_type": "number", "min_value": 5.0, "max_value": 55.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["NCV_p", "net calorific value project", "NCV of project fuel"],
         "extraction_hint": "Extract the NCV for the PROJECT fuel type only.",
         "noise_terms": []},
        {"param_key": "EF_CO2_baseline", "param_name": "CO2 emission factor (baseline fuel)", "category": "emission_factor", "unit": "tCO2/TJ", "data_type": "number", "min_value": 0.0, "max_value": 200.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["EF_b,f,CO2", "baseline CO2 emission factor"],
         "noise_terms": []},
        {"param_key": "EF_nonCO2_baseline", "param_name": "Non-CO2 emission factor (baseline fuel)", "category": "emission_factor", "unit": "tCO2e/TJ", "data_type": "number", "min_value": 0.0, "max_value": 100.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["EF_b,f,nonCO2", "baseline non-CO2 emission factor"],
         "noise_terms": []},
        {"param_key": "EF_CO2_project", "param_name": "CO2 emission factor (project fuel)", "category": "emission_factor", "unit": "tCO2/TJ", "data_type": "number", "min_value": 0.0, "max_value": 200.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["EF_p,f,CO2", "project CO2 emission factor"],
         "noise_terms": []},
        {"param_key": "EF_nonCO2_project", "param_name": "Non-CO2 emission factor (project fuel)", "category": "emission_factor", "unit": "tCO2e/TJ", "data_type": "number", "min_value": 0.0, "max_value": 100.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["EF_p,f,nonCO2", "project non-CO2 emission factor"],
         "noise_terms": []},
        {"param_key": "SFC_baseline", "param_name": "Baseline specific fuel consumption", "category": "baseline", "unit": "kg/person/year", "data_type": "number", "min_value": 0.01, "max_value": 5000, "is_ex_ante": False, "depends_on": [],
         "aliases": ["SFC_b,i", "baseline specific fuel consumption", "specific fuel consumption of the baseline scenario", "SFC baseline", "SFC_b", "traditional stove fuel consumption per person"],
         "extraction_hint": "Only extract if text clearly refers to the BASELINE scenario specific fuel consumption, not project.",
         "noise_terms": []},
        {"param_key": "SFC_project", "param_name": "Project specific fuel consumption", "category": "project", "unit": "kg/person/year", "data_type": "number", "min_value": 0.0, "max_value": 5000, "is_ex_ante": False, "depends_on": [],
         "aliases": ["SFC_p,i,y", "project specific fuel consumption", "specific fuel consumption of the project technology", "SFC project", "SFC_p", "improved stove fuel consumption per person"],
         "extraction_hint": "Only extract if text clearly refers to the PROJECT technology specific fuel consumption, not baseline.",
         "noise_terms": []},
        {"param_key": "num_devices", "param_name": "Number of devices/technologies deployed", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10000000, "is_ex_ante": True, "depends_on": [],
         "aliases": ["number of stoves", "number of devices distributed", "total devices deployed", "N_i,y", "N_j,k,y", "number of project technologies"],
         "extraction_hint": "Only extract the TOTAL number of project devices deployed or distributed. Do NOT extract sample sizes, survey counts, job counts, or unit numbering.",
         "noise_terms": [r"\bsample\b", r"\bjob", r"\bunit\s+number", r"\bnumber of units\b"]},
        {"param_key": "num_households", "param_name": "Number of households served", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10000000, "is_ex_ante": True, "depends_on": [],
         "aliases": ["number of households", "total households", "number of families", "participating households", "n_i,y"],
         "extraction_hint": "Only extract the TOTAL number of households served or targeted by the project. Do NOT extract survey sample sizes or administrative counts.",
         "noise_terms": [r"\bsample[sd]?\b", r"\bsurvey\b", r"\brespondent", r"\bsampling\b"]},
        {"param_key": "devices_per_household", "param_name": "Devices per household", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10, "is_ex_ante": True, "depends_on": []},
        {"param_key": "num_beneficiaries", "param_name": "Number of beneficiaries", "category": "activity_data", "unit": "persons", "data_type": "number", "min_value": 1, "max_value": 100000000, "is_ex_ante": True, "depends_on": ["num_households", "household_size"]},
        {"param_key": "usage_rate", "param_name": "Usage rate (proportion of devices in use)", "category": "monitoring", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": False, "depends_on": [],
         "aliases": ["adoption rate", "utilization rate", "active use rate", "proportion of devices in use", "usage survey rate", "n_i,y / N_i,y"],
         "noise_terms": []},
        {"param_key": "leakage_discount", "param_name": "Leakage discount factor", "category": "leakage", "unit": "fraction", "data_type": "number", "min_value": 0.8, "max_value": 1.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "CF", "param_name": "Wood-to-charcoal conversion factor", "category": "fuel_property", "unit": "kg wood/kg charcoal", "data_type": "number", "min_value": 2.0, "max_value": 8.0, "is_ex_ante": True, "tool_reference": "CDM TOOL33 v3", "depends_on": [],
         "aliases": ["conversion factor", "charcoal conversion factor", "wood to charcoal ratio"],
         "noise_terms": []},
        {"param_key": "household_size", "param_name": "Average household size", "category": "activity_data", "unit": "persons/household", "data_type": "number", "min_value": 1, "max_value": 20, "is_ex_ante": True, "depends_on": [],
         "aliases": ["average household size", "persons per household", "family size", "members per household", "HH size"],
         "extraction_hint": "Only extract values explicitly described as average household size or persons per household.",
         "noise_terms": [r"\bton\b", r"\btonne\b", r"\bcharcoal\b", r"\bfuel\b", r"\bkg\b"]},
        {"param_key": "usage_rate_decay", "param_name": "Annual usage rate decay", "category": "monitoring", "unit": "fraction/year", "data_type": "number", "default": 0.02, "min_value": 0.0, "max_value": 0.10, "is_ex_ante": True, "depends_on": [],
         "description": "Annual reduction in usage rate per year"},
        {"param_key": "usage_rate_floor", "param_name": "Minimum usage rate", "category": "monitoring", "unit": "fraction", "data_type": "number", "default": 0.50, "min_value": 0.0, "max_value": 1.0, "is_ex_ante": True, "depends_on": [],
         "description": "Minimum usage rate floor (usage cannot decay below this)"},
        {"param_key": "baseline_fuel", "param_name": "Baseline fuel type", "category": "baseline", "unit": "", "data_type": "text", "is_ex_ante": True, "depends_on": []},
    ],
    "ACM0002": [
        {"param_key": "EG_PJ_y", "param_name": "Net electricity generation (project)", "category": "project", "unit": "MWh/yr", "data_type": "number", "min_value": 0, "max_value": 100000000, "is_ex_ante": True, "depends_on": [],
         "aliases": ["net electricity generation", "project electricity output", "annual generation", "EG_PJ,y"],
         "extraction_hint": "Only extract the PROJECT electricity generation, not baseline or historical.",
         "noise_terms": []},
        {"param_key": "EF_grid", "param_name": "Grid emission factor", "category": "emission_factor", "unit": "tCO2/MWh", "data_type": "number", "min_value": 0.0, "max_value": 2.0, "is_ex_ante": True, "tool_reference": "TOOL07", "depends_on": [],
         "aliases": ["grid emission factor", "combined margin emission factor", "EF_grid,y", "CEF", "OM", "BM"],
         "noise_terms": []},
        {"param_key": "EG_historical", "param_name": "Historical electricity generation", "category": "baseline", "unit": "MWh/yr", "data_type": "number", "min_value": 0, "max_value": 100000000, "is_ex_ante": True, "depends_on": [],
         "aliases": ["historical generation", "baseline electricity", "past generation"],
         "extraction_hint": "Only extract HISTORICAL or BASELINE electricity generation, not project.",
         "noise_terms": []},
        {"param_key": "project_subtype", "param_name": "Project subtype", "category": "project", "unit": "", "data_type": "text", "is_ex_ante": True, "depends_on": []},
    ],
    "AMS-I.D.": [
        {"param_key": "EG_PJ_y", "param_name": "Net electricity generation (project)", "category": "project", "unit": "MWh/yr", "data_type": "number", "min_value": 0, "max_value": 900000, "is_ex_ante": True, "depends_on": [],
         "aliases": ["net electricity generation", "project electricity output", "annual generation", "EG_PJ,y"],
         "extraction_hint": "Only extract the PROJECT electricity generation.",
         "noise_terms": []},
        {"param_key": "EF_grid", "param_name": "Grid emission factor", "category": "emission_factor", "unit": "tCO2/MWh", "data_type": "number", "min_value": 0.0, "max_value": 2.0, "is_ex_ante": True, "tool_reference": "TOOL07", "depends_on": [],
         "aliases": ["grid emission factor", "combined margin emission factor", "EF_grid,y"],
         "noise_terms": []},
    ],
    # ── GS-MECD v1.2 — Metered & Measured Energy Cooking Devices ─────────────
    "MECD": [
        # ── Ex-ante fixed parameters (MECD 1–8) ──────────────────────────────
        {"param_key": "mecd_baseline_ef", "param_name": "Baseline emission factor (ex-ante, fixed)", "category": "baseline",
         "unit": "tCO2e/TJ", "data_type": "number", "min_value": 0.0, "max_value": 5000.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["EF_b,useful", "EF_b,input", "baseline emission factor MECD"],
         "extraction_hint": "Only extract the ex-ante baseline emission factor expressed per TJ of useful or input cooking energy."},
        {"param_key": "fNRB", "param_name": "Fraction of non-renewable biomass (MECD 13)", "category": "baseline",
         "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": True, "tool_reference": "CDM TOOL33 v3", "depends_on": [],
         "aliases": ["fNRB_i,y", "non-renewable biomass fraction", "fraction non-renewable biomass"],
         "extraction_hint": "Extract the fNRB fraction for the project region. Default values sourced from CDM TOOL33 v3 Table 3 (national) or Table 2 (regional). Project-specific calculation uses CDM TOOL30."},
        {"param_key": "eta_b", "param_name": "Baseline device efficiency (MECD 5)", "category": "baseline",
         "unit": "fraction", "data_type": "number", "min_value": 0.01, "max_value": 1.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["eta_b,i,j", "baseline efficiency", "baseline thermal efficiency"],
         "extraction_hint": "Extract the thermal efficiency of the baseline cooking device as a fraction (e.g. 0.10 for three-stone fire)."},
        {"param_key": "P_b", "param_name": "Baseline fuel consumption (MECD 1)", "category": "baseline",
         "unit": "tonnes/capita/year", "data_type": "number", "min_value": 0.0, "max_value": 10.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["P_b,i,j", "baseline fuel quantity", "baseline fuel amount"],
         "extraction_hint": "Extract the baseline per-capita fuel consumption in tonnes/capita/year."},
        {"param_key": "SC_b", "param_name": "Baseline specific energy consumption SC_b (MECD 7)", "category": "baseline",
         "unit": "MJ/person/event", "data_type": "number", "min_value": 0.01, "max_value": 50.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["SC_b", "specific energy consumption baseline", "SC baseline"],
         "extraction_hint": "Only relevant for Case 2 (EPC-type devices). Extract SC_b in MJ/person/event."},
        {"param_key": "SC_p", "param_name": "Project device specific energy consumption SC_p (MECD 8)", "category": "project",
         "unit": "MJ/person/event", "data_type": "number", "min_value": 0.001, "max_value": 50.0, "is_ex_ante": True, "depends_on": [],
         "aliases": ["SC_p", "specific energy consumption project", "SC project"],
         "extraction_hint": "Only relevant for Case 2 (EPC-type devices). Extract SC_p in MJ/person/event."},
        # ── Monitored parameters (MECD 9–15) ─────────────────────────────────
        {"param_key": "eta_p", "param_name": "Project device efficiency (MECD 9)", "category": "project",
         "unit": "fraction", "data_type": "number", "min_value": 0.01, "max_value": 1.0, "is_ex_ante": False, "depends_on": [],
         "aliases": ["eta_p,d,y", "project thermal efficiency", "project device efficiency"],
         "extraction_hint": "Extract the thermal efficiency of the PROJECT cooking device as a fraction (e.g. 0.85 for induction cooker)."},
        {"param_key": "EG_p_mwh", "param_name": "Annual electricity consumed by project device (MECD 10)", "category": "monitoring",
         "unit": "MWh/yr", "data_type": "number", "min_value": 0.0, "max_value": 1000000.0, "is_ex_ante": False, "depends_on": [],
         "aliases": ["EG_p,d,y", "project electricity consumption", "metered electricity", "monitored electricity"],
         "extraction_hint": "Extract total metered electricity consumed by all project devices in the monitoring period (MWh/year)."},
        {"param_key": "EF_el", "param_name": "Grid emission factor EF_el (MECD 11)", "category": "emission_factor",
         "unit": "tCO2e/MWh", "data_type": "number", "min_value": 0.0, "max_value": 2.0, "is_ex_ante": False, "tool_reference": "CDM TOOL05", "depends_on": [],
         "aliases": ["EF_el,y", "grid emission factor", "grid EF", "electricity emission factor"],
         "extraction_hint": "Extract the grid combined margin emission factor used for the project electricity supply."},
        {"param_key": "TDL", "param_name": "Transmission and distribution losses TDL (MECD 12)", "category": "project",
         "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 0.5, "is_ex_ante": False, "tool_reference": "CDM TOOL05", "depends_on": [],
         "aliases": ["TDL_j,y", "T&D losses", "transmission distribution losses", "grid losses"],
         "extraction_hint": "Extract T&D losses as a fraction (e.g. 0.08 for 8%). Always required for grid-connected project devices."},
        {"param_key": "P_p_kg", "param_name": "Annual fuel consumed by project device (MECD 14)", "category": "monitoring",
         "unit": "kg/yr", "data_type": "number", "min_value": 0.0, "max_value": 10000000.0, "is_ex_ante": False, "depends_on": [],
         "aliases": ["P_p,d,y", "project fuel consumption", "metered fuel consumption"],
         "extraction_hint": "Extract total metered fuel consumed by all project devices (kg/year). For non-electric project devices only."},
        {"param_key": "n_persons", "param_name": "Total persons covered by project devices", "category": "activity_data",
         "unit": "persons", "data_type": "number", "min_value": 1, "max_value": 100000000, "is_ex_ante": True, "depends_on": [],
         "aliases": ["number of persons", "total persons", "persons covered", "beneficiaries MECD"],
         "extraction_hint": "Extract the total number of persons whose cooking is covered by project devices (used for energy cap MECD 10)."},
        {"param_key": "num_devices", "param_name": "Number of project devices deployed", "category": "activity_data",
         "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10000000, "is_ex_ante": True, "depends_on": [],
         "aliases": ["number of stoves", "number of devices distributed", "total devices deployed", "N_i,y"],
         "extraction_hint": "Extract the TOTAL number of project cooking devices deployed."},
        {"param_key": "leakage_discount", "param_name": "Leakage factor (MECD 15)", "category": "leakage",
         "unit": "fraction", "data_type": "number", "min_value": 0.8, "max_value": 1.0, "is_ex_ante": True, "depends_on": []},
    ],
}


def get_extraction_metadata(methodology):
    import re as _re
    methodology_key = (methodology or "").upper().replace("GS-", "")
    methodology_key = _re.sub(r"[\s-]*V(?:ERSION\s*)?\d+(\.\d+)?$", "", methodology_key, flags=_re.IGNORECASE).strip()
    definitions = PARAMETER_DEFINITIONS.get(methodology_key, [])
    result = {}
    for d in definitions:
        if d.get("data_type") != "number":
            continue
        result[d["param_key"]] = {
            "aliases": d.get("aliases", []),
            "extraction_hint": d.get("extraction_hint", ""),
            "noise_terms": d.get("noise_terms", []),
            "category": d.get("category", ""),
        }
    return result


def _get_tool33_intake_value(intake, param_key):
    meth_params = (intake.get("methodology_parameters") or {})
    tool33_key_map = {
        "fNRB": "tool33_fNRB",
        "NCV_baseline": "tool33_bl_NCV",
        "NCV_project": "tool33_pj_NCV",
        "EF_CO2_baseline": "tool33_bl_EF_CO2",
        "EF_CO2_project": "tool33_pj_EF_CO2",
        "EF_nonCO2_baseline": "tool33_bl_EF_nonCO2",
        "EF_nonCO2_project": "tool33_pj_EF_nonCO2",
        "CF": "tool33_CF",
    }
    intake_key = tool33_key_map.get(param_key)
    if intake_key:
        val = meth_params.get(intake_key)
        if val is not None and str(val).strip():
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    return None


def initialize_project_parameters(project_id):
    with get_cursor() as cur:
        cur.execute("SELECT methodology, country, project_settings, project_intake FROM user_projects WHERE id = %s", (project_id,))
        project = cur.fetchone()
        if not project:
            return {"error": "Project not found"}

        import re as _re
        methodology = (project["methodology"] or "").upper().replace("GS-", "")
        methodology = _re.sub(r"[\s-]*V(?:ERSION\s*)?\d+(\.\d+)?$", "", methodology, flags=_re.IGNORECASE).strip()
        country = project.get("country", "")
        settings = project.get("project_settings") or {}
        intake = project.get("project_intake") or {}

        raw_baseline_fuel = settings.get("baseline_fuel") or intake.get("baseline_fuel", "wood")
        baseline_fuel = normalize_fuel_type(raw_baseline_fuel)
        raw_project_fuel = settings.get("project_fuel") or intake.get("project_fuel", "")
        if not raw_project_fuel and methodology in ("VM0050", "TPDDTEC"):
            raw_project_fuel = raw_baseline_fuel
        project_fuel = normalize_fuel_type(raw_project_fuel) if raw_project_fuel else ""
        is_charcoal = baseline_fuel == "charcoal"

        definitions = PARAMETER_DEFINITIONS.get(methodology, [])
        if not definitions:
            return {"error": f"No parameter definitions for methodology: {methodology}"}

        cur.execute("SELECT param_key, value, source_type, param_status FROM project_parameters WHERE project_id = %s AND source_type IN ('measured', 'user_override')", (project_id,))
        preserved = {row["param_key"]: row for row in cur.fetchall()}

        cur.execute("SELECT param_key, value, source_type, param_status FROM project_parameters WHERE project_id = %s AND param_status = 'confirmed'", (project_id,))
        for row in cur.fetchall():
            if row["param_key"] not in preserved:
                preserved[row["param_key"]] = row

        cur.execute("DELETE FROM project_parameters WHERE project_id = %s", (project_id,))

        defaults = get_defaults_for_methodology(methodology, country=country, baseline_fuel=raw_baseline_fuel, project_fuel=raw_project_fuel)
        param_values = defaults.get("parameters", {})

        intake_num_units = None
        po = intake.get("project_overview") or {}
        raw_units = po.get("num_units")
        if raw_units:
            try:
                intake_num_units = float(str(raw_units).replace(",", "").strip())
            except (ValueError, TypeError):
                pass

        intake_beneficiaries = None
        loc = intake.get("location") or {}
        raw_ben = loc.get("beneficiaries")
        if raw_ben:
            try:
                intake_beneficiaries = float(str(raw_ben).replace(",", "").strip())
            except (ValueError, TypeError):
                pass

        resolved_values = {}
        resolved_meta = {}
        inserted = 0
        for defn in definitions:
            value = None
            source_type = "default"
            source_reference = None
            param_status = "default"

            if defn["param_key"] in preserved:
                old = preserved[defn["param_key"]]
                value = old["value"]
                source_type = old["source_type"]
                source_reference = "Preserved from previous initialization"
                param_status = old.get("param_status", "confirmed")
            else:
                tool33_val = _get_tool33_intake_value(intake, defn["param_key"])
                if tool33_val is not None:
                    value = tool33_val
                    source_type = "user_override"
                    source_reference = "Seeded from CDM TOOL33 v3 setup values"
                    param_status = "confirmed"
                else:
                    value, source_type, source_reference = _resolve_parameter_value(
                        defn["param_key"], methodology, param_values, country,
                        baseline_fuel, project_fuel, is_charcoal, intake, settings,
                        intake_num_units=intake_num_units,
                        intake_beneficiaries=intake_beneficiaries,
                    )
                    value, source_type, source_reference = _resolve_with_definition_fallback(
                        defn, value, source_type, source_reference,
                    )

            resolved_values[defn["param_key"]] = value
            resolved_meta[defn["param_key"]] = (source_type, source_reference, param_status)

        _compute_derived_params(resolved_values, resolved_meta)

        for defn in definitions:
            pk = defn["param_key"]
            value = resolved_values.get(pk)
            source_type, source_reference, param_status = resolved_meta.get(pk, ("default", None, "default"))

            if value is None or (isinstance(value, str) and not value.strip()):
                param_status = "missing"
            elif param_status not in ("confirmed",) and source_type == "calculated":
                param_status = "estimated"
            elif param_status not in ("confirmed",) and source_type in ("default", "ipcc", "methodology"):
                param_status = "default"

            validation_status = "valid" if value is not None and str(value).strip() else "pending"

            cur.execute("""
                INSERT INTO project_parameters
                (project_id, param_key, param_name, category, value, unit, data_type,
                 source_type, source_reference, methodology_code, tool_reference,
                 min_value, max_value, is_ex_ante, depends_on, validation_status, param_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                project_id, defn["param_key"], defn["param_name"], defn["category"],
                str(value) if value is not None else None,
                defn.get("unit", ""), defn.get("data_type", "number"),
                source_type, source_reference, methodology,
                defn.get("tool_reference"),
                defn.get("min_value"), defn.get("max_value"),
                defn.get("is_ex_ante", True),
                defn.get("depends_on", []),
                validation_status,
                param_status,
            ))
            inserted += 1

        return {"inserted": inserted, "methodology": methodology, "preserved": len(preserved)}


def _resolve_parameter_value(param_key, methodology, param_values, country, baseline_fuel, project_fuel, is_charcoal, intake, settings, intake_num_units=None, intake_beneficiaries=None):
    value = None
    source_type = "default"
    source_reference = None

    intake_value = intake.get(param_key) or settings.get(param_key)
    if intake_value is not None and intake_value != "":
        try:
            value = float(intake_value)
            source_type = "user_override"
            source_reference = "Project intake / settings"
            return value, source_type, source_reference
        except (ValueError, TypeError):
            pass

    if param_key == "fNRB":
        fnrb = param_values.get("fNRB")
        if fnrb and isinstance(fnrb, dict):
            value = fnrb.get("value")
            source_type = "default"
            source_reference = fnrb.get("source", "CDM TOOL33 v3")
    elif param_key == "NCV_baseline":
        ncv = param_values.get("baseline_NCV")
        if ncv and isinstance(ncv, dict):
            value = ncv.get("value")
            source_reference = ncv.get("source", "IPCC 2006")
    elif param_key == "NCV_project":
        ncv = param_values.get("project_NCV")
        if ncv and isinstance(ncv, dict):
            value = ncv.get("value")
            source_reference = ncv.get("source", "IPCC 2006")
    elif param_key == "EF_CO2_baseline":
        ef = param_values.get("baseline_EF_CO2")
        if ef and isinstance(ef, dict):
            value = ef.get("value")
            source_reference = ef.get("source", "IPCC 2006")
    elif param_key == "EF_nonCO2_baseline":
        ef = param_values.get("baseline_EF_nonCO2")
        if ef and isinstance(ef, dict):
            value = ef.get("value")
            source_reference = ef.get("source", "IPCC 2006")
    elif param_key == "EF_CO2_project":
        ef = param_values.get("project_EF_CO2")
        if ef and isinstance(ef, dict):
            value = ef.get("value")
            source_reference = ef.get("source", "IPCC 2006")
    elif param_key == "EF_nonCO2_project":
        ef = param_values.get("project_EF_nonCO2")
        if ef and isinstance(ef, dict):
            value = ef.get("value")
            source_reference = ef.get("source", "IPCC 2006")
    elif param_key == "leakage_discount":
        ld = param_values.get("leakage_discount")
        if ld and isinstance(ld, dict):
            value = ld.get("value")
            source_reference = ld.get("source", "Methodology default")
    elif param_key == "CF":
        cf = param_values.get("CF")
        if cf and isinstance(cf, dict):
            value = cf.get("value")
            source_reference = cf.get("source", "CDM TOOL33 v3")
    elif param_key == "baseline_fuel_consumption":
        if is_charcoal:
            value = 0.1 * 5.0
            source_reference = "CDM TOOL33 v3 §5.4 default: 0.1 t charcoal/person/yr * 5 persons/hh"
        else:
            value = 0.4 * 5.0
            source_reference = "CDM TOOL33 v3 §5.4 default: 0.4 t wood/person/yr * 5 persons/hh"
    elif param_key == "SFC_baseline":
        if is_charcoal:
            value = 100.0
            source_reference = "CDM TOOL33 v3 §5.4 default: 0.1 t/person/yr = 100 kg/person/yr"
        else:
            value = 400.0
            source_reference = "CDM TOOL33 v3 §5.4 default: 0.4 t/person/yr = 400 kg/person/yr"
    elif param_key == "usage_rate":
        value = 0.90
        source_type = "default"
        source_reference = "Conservative ex-ante assumption (90%)"
    elif param_key == "num_devices":
        if intake_num_units is not None:
            value = intake_num_units
            source_type = "user_override"
            source_reference = "From project setup (Number of units)"
        else:
            value = None
            source_type = "default"
            source_reference = "Must be provided by project developer"
    elif param_key == "num_households":
        value = None
        source_type = "calculated"
        source_reference = "Derived: num_devices / devices_per_household"
    elif param_key == "devices_per_household":
        value = 1
        source_type = "default"
        source_reference = "Default: 1 device per household"
    elif param_key == "num_beneficiaries":
        if intake_beneficiaries is not None:
            value = intake_beneficiaries
            source_type = "user_override"
            source_reference = "From project setup (beneficiaries)"
        else:
            value = None
            source_type = "calculated"
            source_reference = "Derived: num_households x household_size (set value to override)"
    elif param_key == "household_size":
        value = 5.0
        source_type = "default"
        source_reference = "Common assumption (SSA average)"
    elif param_key == "SFC_project":
        value = None
        source_type = "default"
        source_reference = "Must be determined from project stove testing (Kitchen Performance Test or Water Boiling Test)"
    elif param_key == "baseline_fuel":
        value = baseline_fuel or "wood"
        source_type = "default"
        source_reference = "From project intake data (normalized)"
        return value, source_type, source_reference
    elif param_key == "baseline_efficiency":
        value = 0.15
        source_type = "default"
        source_reference = "CDM TOOL33 v3 §5.6 para 19(a) – three-stone fire default efficiency"
    elif param_key == "project_efficiency":
        value = None
        source_type = "default"
        source_reference = "Must be determined from testing (WBT)"

    if source_type == "default" and source_reference is None:
        source_reference = "IPCC 2006 / Methodology default"

    return value, source_type, source_reference


def _resolve_with_definition_fallback(defn, value, source_type, source_reference):
    if value is None and "default" in defn:
        return defn["default"], "default", defn.get("description") or "Methodology default"
    return value, source_type, source_reference


def _compute_derived_params(resolved_values, resolved_meta):
    def _safe_float(v):
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    num_devices = _safe_float(resolved_values.get("num_devices"))
    devices_per_hh = _safe_float(resolved_values.get("devices_per_household")) or 1.0
    household_size = _safe_float(resolved_values.get("household_size")) or 5.0

    src_type, src_ref, p_status = resolved_meta.get("num_households", ("default", None, "default"))
    cur_hh = _safe_float(resolved_values.get("num_households"))
    if cur_hh is None and num_devices is not None:
        computed_hh = num_devices / devices_per_hh
        resolved_values["num_households"] = computed_hh
        resolved_meta["num_households"] = (
            "calculated",
            f"Derived: {int(num_devices)} devices / {devices_per_hh:.0f} per household = {int(computed_hh)}",
            "estimated",
        )

    src_type_b, src_ref_b, p_status_b = resolved_meta.get("num_beneficiaries", ("default", None, "default"))
    cur_ben = _safe_float(resolved_values.get("num_beneficiaries"))
    if cur_ben is None and p_status_b != "confirmed":
        hh_val = _safe_float(resolved_values.get("num_households"))
        if hh_val is not None and household_size is not None:
            computed_ben = hh_val * household_size
            resolved_values["num_beneficiaries"] = computed_ben
            resolved_meta["num_beneficiaries"] = (
                "calculated",
                f"Derived: {int(hh_val)} households x {household_size:.0f} persons/hh = {int(computed_ben)}",
                "estimated",
            )


def get_project_parameters(project_id, category=None):
    with get_cursor() as cur:
        if category:
            cur.execute("""
                SELECT * FROM project_parameters
                WHERE project_id = %s AND category = %s
                ORDER BY category, param_key
            """, (project_id, category))
        else:
            cur.execute("""
                SELECT * FROM project_parameters
                WHERE project_id = %s
                ORDER BY category, param_key
            """, (project_id,))
        return cur.fetchall()


def _recompute_derived_after_update(cur, project_id, keys_to_recompute):
    cur.execute("""
        SELECT param_key, value, source_type, param_status FROM project_parameters
        WHERE project_id = %s AND applicable_year IS NULL
    """, (project_id,))
    all_rows = cur.fetchall()
    vals = {}
    for r in all_rows:
        vals[r["param_key"]] = r["value"]

    def _sf(v):
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    num_devices = _sf(vals.get("num_devices"))
    devices_per_hh = _sf(vals.get("devices_per_household")) or 1.0
    household_size = _sf(vals.get("household_size")) or 5.0

    for key in keys_to_recompute:
        existing = next((r for r in all_rows if r["param_key"] == key), None)
        if existing and existing["source_type"] == "user_override":
            continue

        computed = None
        ref = None
        if key == "num_households" and num_devices is not None:
            computed = num_devices / devices_per_hh
            ref = f"Derived: {int(num_devices)} devices / {devices_per_hh:.0f} per household = {int(computed)}"
        elif key == "num_beneficiaries":
            hh = _sf(vals.get("num_households"))
            if "num_households" in keys_to_recompute and num_devices is not None:
                hh = num_devices / devices_per_hh
            if hh is not None:
                computed = hh * household_size
                ref = f"Derived: {int(hh)} households x {household_size:.0f} persons/hh = {int(computed)}"

        if computed is not None:
            cur.execute("""
                UPDATE project_parameters
                SET value = %s, source_type = 'calculated', source_reference = %s,
                    param_status = 'estimated', updated_at = NOW()
                WHERE project_id = %s AND param_key = %s AND applicable_year IS NULL
                  AND source_type != 'user_override'
            """, (str(computed), ref, project_id, key))
            vals[key] = str(computed)


def update_parameter(project_id, param_key, value, source_type=None, source_reference=None, notes=None):
    with get_cursor() as cur:
        updates = ["value = %s", "updated_at = NOW()"]
        params = [str(value) if value is not None else None]

        if source_type:
            updates.append("source_type = %s")
            params.append(source_type)
        if source_reference:
            updates.append("source_reference = %s")
            params.append(source_reference)
        if notes is not None:
            updates.append("notes = %s")
            params.append(notes)

        params.extend([project_id, param_key])

        cur.execute(f"""
            UPDATE project_parameters
            SET {', '.join(updates)}
            WHERE project_id = %s AND param_key = %s AND applicable_year IS NULL
            RETURNING *
        """, params)

        updated = cur.fetchone()
        if updated:
            validation_result = _run_validation(cur, updated)
            is_valid = validation_result.get("status") == "valid"
            has_value = value is not None and str(value).strip() != ""
            if has_value and is_valid:
                cur.execute("""
                    UPDATE project_parameters SET param_status = 'confirmed'
                    WHERE id = %s
                """, (updated["id"],))
            elif not has_value:
                cur.execute("""
                    UPDATE project_parameters SET param_status = 'missing'
                    WHERE id = %s
                """, (updated["id"],))

        derivation_triggers = {
            "num_devices": ["num_households", "num_beneficiaries"],
            "devices_per_household": ["num_households", "num_beneficiaries"],
            "household_size": ["num_beneficiaries"],
            "num_households": ["num_beneficiaries"],
        }
        if param_key in derivation_triggers:
            _recompute_derived_after_update(cur, project_id, derivation_triggers[param_key])

        return updated


def confirm_parameter(project_id, param_key):
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM project_parameters
            WHERE project_id = %s AND param_key = %s AND applicable_year IS NULL
        """, (project_id, param_key))
        param = cur.fetchone()
        if not param:
            return None
        validation_result = _run_validation(cur, param)
        is_valid = validation_result.get("status") == "valid"
        has_value = param["value"] is not None and str(param["value"]).strip() != ""
        if has_value and is_valid:
            cur.execute("""
                UPDATE project_parameters SET param_status = 'confirmed', updated_at = NOW()
                WHERE id = %s
                RETURNING *
            """, (param["id"],))
            return cur.fetchone()
        return param


def validate_all_parameters(project_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM project_parameters WHERE project_id = %s", (project_id,))
        params = cur.fetchall()

        issues = []
        for p in params:
            result = _run_validation(cur, p)
            if result.get("status") != "valid":
                issues.append(result)

        return {"total": len(params), "valid": len(params) - len(issues), "issues": issues}


def _run_validation(cur, param):
    status = "valid"
    message = None

    if param["value"] is None or param["value"] == "":
        status = "pending"
        message = "Value not set"
    elif param["data_type"] == "number":
        try:
            val = float(param["value"])
            if param.get("min_value") is not None and val < param["min_value"]:
                status = "invalid"
                message = f"Value {val} is below minimum {param['min_value']}"
            elif param.get("max_value") is not None and val > param["max_value"]:
                status = "invalid"
                message = f"Value {val} exceeds maximum {param['max_value']}"
        except ValueError:
            status = "invalid"
            message = f"'{param['value']}' is not a valid number"

    cur.execute("""
        UPDATE project_parameters SET validation_status = %s, validation_message = %s
        WHERE id = %s
    """, (status, message, param["id"]))

    return {"param_key": param["param_key"], "status": status, "message": message}


def get_parameter_value(project_id, param_key):
    with get_cursor() as cur:
        cur.execute("""
            SELECT value FROM project_parameters
            WHERE project_id = %s AND param_key = %s AND applicable_year IS NULL
        """, (project_id, param_key))
        row = cur.fetchone()
        if row and row["value"] is not None:
            try:
                return float(row["value"])
            except (ValueError, TypeError):
                return row["value"]
        return None


def get_parameters_as_dict(project_id):
    params = get_project_parameters(project_id)
    result = {}
    for p in params:
        key = p["param_key"]
        val = p["value"]
        if val is not None and p["data_type"] == "number":
            try:
                val = float(val)
            except (ValueError, TypeError):
                pass
        result[key] = {
            "value": val,
            "unit": p["unit"],
            "source_type": p["source_type"],
            "source_reference": p["source_reference"],
            "validation_status": p["validation_status"],
            "param_status": p.get("param_status", "default"),
            "is_ex_ante": p["is_ex_ante"],
            "category": p["category"],
        }
    return result


def get_parameter_summary(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN validation_status = 'valid' THEN 1 END) as valid,
                COUNT(CASE WHEN validation_status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN validation_status = 'invalid' THEN 1 END) as invalid,
                COUNT(CASE WHEN validation_status = 'warning' THEN 1 END) as warnings,
                COUNT(CASE WHEN source_type = 'default' THEN 1 END) as defaults,
                COUNT(CASE WHEN source_type = 'measured' THEN 1 END) as measured,
                COUNT(CASE WHEN source_type = 'user_override' THEN 1 END) as overrides,
                COUNT(CASE WHEN param_status = 'confirmed' THEN 1 END) as confirmed,
                COUNT(CASE WHEN param_status = 'default' THEN 1 END) as status_default,
                COUNT(CASE WHEN param_status = 'estimated' THEN 1 END) as estimated,
                COUNT(CASE WHEN param_status = 'missing' THEN 1 END) as missing
            FROM project_parameters WHERE project_id = %s
        """, (project_id,))
        return cur.fetchone()
