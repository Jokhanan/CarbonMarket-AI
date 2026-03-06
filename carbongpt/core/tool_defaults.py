"""
Structured default values from CDM TOOL33 and methodology-specific references.

These are official values from CDM Tool 33 "Default values of fraction of
non-renewable biomass (fNRB)" and associated parameters used by cookstove
and renewable energy methodologies.

Sources:
- CDM TOOL33 v05.0 (Default values for common parameters)
- IPCC 2006 Guidelines for National GHG Inventories, Volume 2 (Energy)
- VM0050 v1.0 (Energy Efficiency and Fuel-Switch Measures in Cookstoves)
- GS TPDDTEC v4.0 (Technologies to Displace Decentralized Thermal Energy)
- ACM0002 v22.0 (Grid-connected electricity from renewable sources)
- AMS-I.D. v18.0 (Grid-connected renewable electricity generation)
"""

TOOL33_FNRB_BY_COUNTRY = {
    "Afghanistan": 0.96, "Angola": 0.73, "Bangladesh": 0.88,
    "Benin": 0.89, "Burkina Faso": 0.84, "Burundi": 0.97,
    "Cambodia": 0.65, "Cameroon": 0.82, "Central African Republic": 0.72,
    "Chad": 0.90, "Colombia": 0.40, "Comoros": 0.97,
    "Congo": 0.75, "Congo DR": 0.88, "Cote d'Ivoire": 0.72,
    "Djibouti": 0.98, "Ecuador": 0.25, "Egypt": 0.98,
    "El Salvador": 0.90, "Eritrea": 0.95, "Ethiopia": 0.88,
    "Gabon": 0.30, "Gambia": 0.81, "Ghana": 0.72,
    "Guatemala": 0.72, "Guinea": 0.74, "Guinea-Bissau": 0.71,
    "Haiti": 0.89, "Honduras": 0.71, "India": 0.74,
    "Indonesia": 0.42, "Kenya": 0.82, "Lao PDR": 0.39,
    "Lesotho": 0.86, "Liberia": 0.59, "Madagascar": 0.77,
    "Malawi": 0.90, "Mali": 0.77, "Mauritania": 0.97,
    "Mexico": 0.53, "Mozambique": 0.80, "Myanmar": 0.59,
    "Namibia": 0.56, "Nepal": 0.76, "Nicaragua": 0.72,
    "Niger": 0.97, "Nigeria": 0.74, "Pakistan": 0.83,
    "Papua New Guinea": 0.14, "Paraguay": 0.18, "Peru": 0.32,
    "Philippines": 0.54, "Rwanda": 0.96, "Senegal": 0.82,
    "Sierra Leone": 0.74, "Somalia": 0.98, "South Africa": 0.66,
    "South Sudan": 0.78, "Sri Lanka": 0.56, "Sudan": 0.87,
    "Swaziland": 0.83, "Tanzania": 0.85, "Thailand": 0.39,
    "Togo": 0.71, "Uganda": 0.85, "Vietnam": 0.37,
    "Zambia": 0.66, "Zimbabwe": 0.77,
}

FNRB_DEFAULT_WITH_DISCOUNT = 0.44
FNRB_UNCERTAINTY_DISCOUNT = 0.26

FUEL_NCV = {
    "wood": {"value": 15.6, "unit": "TJ/Gg", "source": "IPCC 2006 default for air-dried wood", "note": "Equivalent to 15.6 GJ/tonne"},
    "charcoal": {"value": 29.5, "unit": "TJ/Gg", "source": "IPCC 2006 default", "note": "Equivalent to 29.5 GJ/tonne"},
    "LPG": {"value": 47.3, "unit": "TJ/Gg", "source": "IPCC 2006 default", "note": "Equivalent to 47.3 GJ/tonne"},
    "kerosene": {"value": 43.8, "unit": "TJ/Gg", "source": "IPCC 2006 default"},
    "bioethanol": {"value": 27.0, "unit": "TJ/Gg", "source": "IPCC 2006 default"},
    "diesel": {"value": 43.0, "unit": "TJ/Gg", "source": "IPCC 2006 default"},
    "natural_gas": {"value": 48.0, "unit": "TJ/Gg", "source": "IPCC 2006 default"},
    "coal": {"value": 25.8, "unit": "TJ/Gg", "source": "IPCC 2006 default for other bituminous coal"},
    "biomass_briquettes": {"value": 17.0, "unit": "TJ/Gg", "source": "IPCC 2006 estimate for compressed biomass"},
    "crop_residues": {"value": 12.0, "unit": "TJ/Gg", "source": "IPCC 2006 estimate"},
    "dung": {"value": 10.0, "unit": "TJ/Gg", "source": "IPCC 2006 estimate for dried dung"},
}

FUEL_EF_CO2 = {
    "wood": {"value": 112.0, "unit": "tCO2/TJ", "source": "IPCC 2006 default", "note": "For non-renewable biomass combustion"},
    "charcoal": {"value": 112.0, "unit": "tCO2/TJ", "source": "IPCC 2006 / TPDDTEC methodology default"},
    "LPG": {"value": 63.1, "unit": "tCO2/TJ", "source": "IPCC 2006 default"},
    "kerosene": {"value": 71.9, "unit": "tCO2/TJ", "source": "IPCC 2006 default"},
    "bioethanol": {"value": 0.0, "unit": "tCO2/TJ", "source": "IPCC 2006 (biogenic, zero net CO2)", "note": "Biogenic CO2 not counted"},
    "diesel": {"value": 74.1, "unit": "tCO2/TJ", "source": "IPCC 2006 default"},
    "natural_gas": {"value": 56.1, "unit": "tCO2/TJ", "source": "IPCC 2006 default"},
    "coal": {"value": 94.6, "unit": "tCO2/TJ", "source": "IPCC 2006 default"},
}

FUEL_EF_NONCO2 = {
    "wood": {"value": 4.03, "unit": "tCO2e/TJ", "source": "TPDDTEC methodology default", "note": "Includes CH4 and N2O"},
    "charcoal": {"value": 1.59, "unit": "tCO2e/TJ", "source": "TPDDTEC methodology default"},
    "LPG": {"value": 0.10, "unit": "tCO2e/TJ", "source": "IPCC 2006 default"},
    "kerosene": {"value": 0.10, "unit": "tCO2e/TJ", "source": "IPCC 2006 default"},
    "bioethanol": {"value": 0.42, "unit": "tCO2e/TJ", "source": "IPCC 2006 estimate"},
    "diesel": {"value": 0.10, "unit": "tCO2e/TJ", "source": "IPCC 2006 default"},
    "coal": {"value": 0.15, "unit": "tCO2e/TJ", "source": "IPCC 2006 default"},
}

WOOD_TO_CHARCOAL_CF = {
    "default": {"value": 6.0, "unit": "tonnes dry wood / tonne charcoal", "source": "VM0050 default (up to 6)", "note": "Can use lower value if substantiated by government data"},
    "efficient_kiln": {"value": 4.0, "unit": "tonnes dry wood / tonne charcoal", "source": "Improved kiln estimate"},
}

LEAKAGE_DEFAULTS = {
    "cookstove_renewable_biomass": {"value": 0.95, "unit": "discount factor", "source": "VM0050 (5% leakage discount)"},
    "grid_renewable": {"value": 0.95, "unit": "discount factor", "source": "ACM0002 (5% leakage discount)"},
}

GWP_VALUES = {
    "CO2": {"value": 1, "source": "IPCC AR5"},
    "CH4": {"value": 28, "source": "IPCC AR5 (100-year)"},
    "N2O": {"value": 265, "source": "IPCC AR5 (100-year)"},
    "SF6": {"value": 23500, "source": "IPCC AR5"},
}


METHODOLOGY_EQUATIONS = {
    "VM0050": {
        "name": "VM0050 - Energy Efficiency and Fuel-Switch Measures in Cookstoves",
        "equations": [
            {
                "id": "VM0050_Eq1",
                "name": "Baseline Emissions",
                "formula": "BE_y = SUM_i [ EC_b,i,y * (EF_b,i,CO2 + EF_b,i,nonCO2) * fNRB_y ]",
                "description": "Total baseline emissions in year y from all baseline device types",
                "parameters": ["EC_b,i,y", "EF_b,i,CO2", "EF_b,i,nonCO2", "fNRB_y"],
            },
            {
                "id": "VM0050_Eq2",
                "name": "Baseline Energy Consumption",
                "formula": "EC_b,i,y = BC_b,i,y * NCV_b,i",
                "description": "Energy consumption of baseline device type i in year y",
                "parameters": ["BC_b,i,y", "NCV_b,i"],
            },
            {
                "id": "VM0050_Eq3",
                "name": "Project Emissions (fuel)",
                "formula": "PE_fuel,y = SUM_j,k [ EC_p,j,k,y * (EF_p,j,CO2 + EF_p,j,nonCO2) * fNRB_y * n_j,k,y ]",
                "description": "Project emissions from fuel consumption of project devices",
                "parameters": ["EC_p,j,k,y", "EF_p,j,CO2", "EF_p,j,nonCO2", "fNRB_y", "n_j,k,y"],
            },
            {
                "id": "VM0050_Eq4",
                "name": "Project Emissions (electricity)",
                "formula": "PE_elec,y = SUM_j,k [ EC_elec,j,k,y * EF_el,y * (1 + TDL_j,y) ]",
                "description": "Project emissions from electricity consumption",
                "parameters": ["EC_elec,j,k,y", "EF_el,y", "TDL_j,y"],
            },
            {
                "id": "VM0050_Eq5",
                "name": "Emission Reductions",
                "formula": "ER_y = BE_y - PE_y - LE_y",
                "description": "Net GHG emission reductions in year y",
                "parameters": ["BE_y", "PE_y", "LE_y"],
            },
            {
                "id": "VM0050_Eq6",
                "name": "Usage Rate Adjustment",
                "formula": "n_j,k,y = N_j,k,y_surveyed_still_using / N_j,k,y_surveyed_total",
                "description": "Proportion of project devices still in regular use",
                "parameters": ["N_j,k,y_surveyed_still_using", "N_j,k,y_surveyed_total"],
            },
        ],
    },
    "TPDDTEC": {
        "name": "TPDDTEC - Technologies to Displace Decentralized Thermal Energy Consumption",
        "equations": [
            {
                "id": "TPDDTEC_Eq1",
                "name": "Emission Reductions (Method 1 - same fuel)",
                "formula": "ER_y = SUM_i [ (SFC_b,i - SFC_p,i,y) * N_i,y * n_i,y * NCV_f * (EF_CO2 + EF_nonCO2) * fNRB ]",
                "description": "When baseline and project fuels are the same",
                "parameters": ["SFC_b,i", "SFC_p,i,y", "N_i,y", "n_i,y", "NCV_f", "EF_CO2", "EF_nonCO2", "fNRB"],
            },
            {
                "id": "TPDDTEC_Eq2",
                "name": "Emission Reductions (Method 2 - different fuels)",
                "formula": "ER_y = SUM_i [ SFC_b,i * N_i,y * n_i,y * NCV_b * (EF_b,CO2 + EF_b,nonCO2) * fNRB - SFC_p,i,y * N_i,y * n_i,y * NCV_p * (EF_p,CO2 + EF_p,nonCO2) ]",
                "description": "When baseline and project fuels are different",
                "parameters": ["SFC_b,i", "SFC_p,i,y", "N_i,y", "n_i,y", "NCV_b", "NCV_p", "EF_b,CO2", "EF_b,nonCO2", "EF_p,CO2", "EF_p,nonCO2", "fNRB"],
            },
            {
                "id": "TPDDTEC_Eq3",
                "name": "Baseline Specific Fuel Consumption",
                "formula": "SFC_b,i = SUM(fuel_consumed_per_test) / n_tests",
                "description": "Baseline fuel consumption per cooking task from KPT or WBT",
                "parameters": ["fuel_consumed_per_test", "n_tests"],
            },
            {
                "id": "TPDDTEC_Eq4",
                "name": "Project Specific Fuel Consumption",
                "formula": "SFC_p,i,y = SFC_p,1 * (n_new,i,1 / n_new,i,y)",
                "description": "Project fuel consumption adjusted for aging/degradation",
                "parameters": ["SFC_p,1", "n_new,i,1", "n_new,i,y"],
            },
        ],
    },
    "ACM0002": {
        "name": "ACM0002 - Grid-connected electricity generation from renewable sources",
        "equations": [
            {
                "id": "ACM0002_Eq1",
                "name": "Emission Reductions",
                "formula": "ER_y = BE_y - PE_y - LE_y",
                "description": "Net emission reductions in year y",
                "parameters": ["BE_y", "PE_y", "LE_y"],
            },
            {
                "id": "ACM0002_Eq2",
                "name": "Baseline Emissions (Greenfield)",
                "formula": "BE_y = EG_PJ,y * EF_grid,y",
                "description": "Baseline emissions for new greenfield plant",
                "parameters": ["EG_PJ,y", "EF_grid,y"],
            },
            {
                "id": "ACM0002_Eq3",
                "name": "Baseline Emissions (Capacity Addition)",
                "formula": "BE_y = max(EG_PJ,y - EG_historical, 0) * EF_grid,y",
                "description": "Baseline emissions for capacity addition to existing plant",
                "parameters": ["EG_PJ,y", "EG_historical", "EF_grid,y"],
            },
            {
                "id": "ACM0002_Eq4",
                "name": "Baseline Emissions (Retrofit)",
                "formula": "BE_y = EG_PJ,y * EF_grid,y (if DATE_BaselineRetrofit has passed) else (EG_PJ,y - EG_historical) * EF_grid,y",
                "description": "Baseline emissions for retrofit/rehabilitation/replacement",
                "parameters": ["EG_PJ,y", "EF_grid,y", "EG_historical", "DATE_BaselineRetrofit"],
            },
            {
                "id": "ACM0002_Eq5",
                "name": "Grid Emission Factor",
                "formula": "EF_grid,y = (EF_OM,y * w_OM + EF_BM,y * w_BM)",
                "description": "Combined margin emission factor (see TOOL07 for calculation)",
                "parameters": ["EF_OM,y", "EF_BM,y", "w_OM", "w_BM"],
            },
            {
                "id": "ACM0002_Eq6",
                "name": "Leakage",
                "formula": "LE_y = 0 (for most renewable projects)",
                "description": "Leakage for most project types is zero; reservoir hydro has specific requirements",
                "parameters": [],
            },
        ],
    },
    "AMS-I.D.": {
        "name": "AMS-I.D. - Grid-connected renewable electricity generation",
        "equations": [
            {
                "id": "AMSID_Eq1",
                "name": "Emission Reductions",
                "formula": "ER_y = BE_y - PE_y - LE_y",
                "description": "Net emission reductions in year y",
                "parameters": ["BE_y", "PE_y", "LE_y"],
            },
            {
                "id": "AMSID_Eq2",
                "name": "Baseline Emissions (Greenfield)",
                "formula": "BE_y = EG_PJ,facility,y * EF_grid,y",
                "description": "Baseline emissions for greenfield plant",
                "parameters": ["EG_PJ,facility,y", "EF_grid,y"],
            },
            {
                "id": "AMSID_Eq3",
                "name": "Baseline Emissions (Capacity Addition)",
                "formula": "BE_y = max(EG_PJ,facility,y - EG_baseline,y, 0) * EF_grid,y",
                "description": "Baseline emissions for capacity addition",
                "parameters": ["EG_PJ,facility,y", "EG_baseline,y", "EF_grid,y"],
            },
            {
                "id": "AMSID_Eq4",
                "name": "Project Emissions",
                "formula": "PE_y = 0 (for most renewable sources)",
                "description": "Project emissions are typically zero for wind, solar, run-of-river hydro",
                "parameters": [],
            },
        ],
    },
}

METHODOLOGY_SUPPLEMENTARY_PARAMS = {
    "VM0050": [
        {
            "symbol": "CF",
            "name": "Wood-to-charcoal conversion factor",
            "unit": "tonnes dry wood / tonne charcoal",
            "category": "methodology_default",
            "source": "CDM TOOL33 / VM0050 default: up to 6",
            "default_value": "6.0",
            "description": "Used when charcoal is the baseline or project fuel. Can use lower value if substantiated.",
        },
        {
            "symbol": "n_j,k,y",
            "name": "Usage rate / proportion of devices still in use",
            "unit": "fraction (0-1)",
            "category": "monitored",
            "source": "Monitoring surveys",
            "description": "Proportion of commissioned project devices still being used regularly. Determined from follow-up surveys.",
        },
        {
            "symbol": "EC_p,j,k,y",
            "name": "Electricity consumption of electric project devices",
            "unit": "MWh/yr",
            "category": "monitored",
            "source": "Metering",
            "description": "Annual electricity consumption by electric project devices (e.g., electric cookstoves). Only applicable when project device uses electricity.",
        },
        {
            "symbol": "EF_el,y",
            "name": "Grid emission factor",
            "unit": "tCO2/MWh",
            "category": "calculated",
            "source": "CDM TOOL07",
            "description": "Emission factor of the electricity system. Required when project devices use electricity.",
        },
        {
            "symbol": "TDL_j,y",
            "name": "Transmission and distribution losses",
            "unit": "fraction",
            "category": "methodology_default",
            "source": "National electricity utility data",
            "description": "Average technical T&D losses for providing electricity to project devices.",
        },
    ],
    "TPDDTEC": [
        {
            "symbol": "SFC_b,i",
            "name": "Baseline specific fuel consumption",
            "unit": "kg/task or kg/person/year",
            "category": "monitored",
            "source": "KPT or WBT field testing",
            "description": "Baseline fuel consumption per cooking task or per capita, determined from field testing (Kitchen Performance Test or Water Boiling Test).",
        },
        {
            "symbol": "SFC_p,i,y",
            "name": "Project specific fuel consumption",
            "unit": "kg/task or kg/person/year",
            "category": "monitored",
            "source": "KPT or WBT field testing",
            "description": "Project fuel consumption adjusted for aging/degradation over time.",
        },
        {
            "symbol": "n_i,y",
            "name": "Usage rate / drop-off rate",
            "unit": "fraction (0-1)",
            "category": "monitored",
            "source": "Usage surveys",
            "description": "Fraction of distributed devices still in active use during year y.",
        },
        {
            "symbol": "BC_ex-ante,b,i",
            "name": "Ex-ante baseline consumption per capita",
            "unit": "TJ/capita/year",
            "category": "methodology_default",
            "source": "CDM TOOL33 or national data",
            "description": "Default baseline energy consumption value scaled by household size.",
        },
    ],
    "ACM0002": [
        {
            "symbol": "EG_historical",
            "name": "Historical annual average electricity generation",
            "unit": "MWh/yr",
            "category": "project_input",
            "source": "Project site records",
            "description": "Annual average historical net electricity generation delivered to the grid. Used for capacity addition and retrofit scenarios.",
        },
        {
            "symbol": "sigma_historical",
            "name": "Standard deviation of historical generation",
            "unit": "MWh",
            "category": "calculated",
            "source": "Calculated from EG_historical data",
            "description": "Standard deviation of annual average historical net electricity generation.",
        },
        {
            "symbol": "Cap_BL",
            "name": "Installed capacity before project",
            "unit": "MW",
            "category": "project_input",
            "source": "Project site",
            "description": "Installed capacity of the power plant before project implementation. Required for hydro projects to check 15 W/m2 threshold.",
        },
        {
            "symbol": "A_BL",
            "name": "Reservoir area before project",
            "unit": "km2",
            "category": "project_input",
            "source": "Project site / GIS",
            "description": "Area of the reservoir(s) measured at the water surface, before project implementation.",
        },
        {
            "symbol": "EF_Res",
            "name": "Default emission factor for reservoirs",
            "unit": "tCO2e/yr",
            "category": "methodology_default",
            "source": "EB 23 decision",
            "default_value": "90 gCO2eq/kWh for power density < 4 W/m2",
            "description": "Default emission factor for GHG emissions from water reservoirs of hydro plants.",
        },
        {
            "symbol": "DATE_BaselineRetrofit",
            "name": "Expected equipment replacement date",
            "unit": "date",
            "category": "project_input",
            "source": "Project developer / CDM TOOL10",
            "description": "Point in time when existing equipment would need to be replaced absent the project activity.",
        },
    ],
    "AMS-I.D.": [
        {
            "symbol": "EG_PJ,facility,y",
            "name": "Net electricity generation supplied to grid",
            "unit": "MWh/yr",
            "category": "monitored",
            "source": "Electricity meter(s)",
            "description": "Quantity of net electricity generation supplied by the project plant/unit to the grid in year y.",
        },
        {
            "symbol": "EF_grid,y",
            "name": "Grid emission factor",
            "unit": "tCO2/MWh",
            "category": "methodology_default",
            "source": "CDM TOOL07 or national grid factor",
            "description": "CO2 emission factor of the grid electricity. Calculated using TOOL07 or from national/regional data.",
        },
        {
            "symbol": "EG_baseline,y",
            "name": "Baseline electricity generation",
            "unit": "MWh/yr",
            "category": "project_input",
            "source": "Historical plant records",
            "description": "Baseline electricity generation for capacity addition and retrofit scenarios.",
        },
    ],
}

CDM_TOOLS_REFERENCED = {
    "VM0050": {
        "TOOL01": "Tool for demonstration and assessment of additionality",
        "TOOL03": "Tool to calculate project or leakage CO2 emissions from fossil fuel combustion",
        "TOOL05": "Baseline, project and/or leakage emissions from electricity consumption",
        "TOOL07": "Tool to calculate the emission factor for an electricity system",
        "TOOL12": "Project and leakage emissions from transportation of freight",
        "TOOL15": "Upstream leakage emissions associated with fossil fuel use",
        "TOOL16": "Project and leakage emissions from biomass",
        "TOOL24": "Common practice analysis",
        "TOOL30": "Fraction of non-renewable biomass (fNRB)",
        "TOOL33": "Default values for common parameters",
    },
    "TPDDTEC": {
        "TOOL01": "Tool for demonstration and assessment of additionality",
        "TOOL19": "Demonstration of additionality of microscale project activities",
        "TOOL21": "Demonstration of additionality of small-scale project activities",
        "TOOL30": "Fraction of non-renewable biomass (fNRB)",
    },
    "ACM0002": {
        "TOOL01": "Tool for demonstration and assessment of additionality",
        "TOOL02": "Combined tool to identify baseline scenario and demonstrate additionality",
        "TOOL03": "Tool to calculate CO2 emissions from fossil fuel combustion",
        "TOOL05": "Baseline/project/leakage emissions from electricity consumption",
        "TOOL07": "Tool to calculate the emission factor for an electricity system",
        "TOOL10": "Tool to determine the remaining lifetime of equipment",
        "TOOL11": "Assessment of the validity of the original/current baseline",
        "TOOL32": "Positive list of technologies",
    },
    "AMS-I.D.": {
        "TOOL07": "Tool to calculate the emission factor for an electricity system",
    },
}

VCS_TOOLS_REFERENCED = {
    "VM0050": {
        "VT0008": "VCS Additionality Assessment Tool",
        "VT0010": "VCS Emissions Testing Tool",
    },
}


def get_fnrb_for_country(country):
    if not country:
        return None
    direct = TOOL33_FNRB_BY_COUNTRY.get(country)
    if direct is not None:
        return {
            "value": direct,
            "value_with_discount": round(direct * (1 - FNRB_UNCERTAINTY_DISCOUNT), 4),
            "uncertainty_discount": FNRB_UNCERTAINTY_DISCOUNT,
            "unit": "fraction",
            "source": f"CDM TOOL33 country-specific default for {country}",
            "note": f"Raw fNRB = {direct}. With 26% uncertainty discount = {round(direct * (1 - FNRB_UNCERTAINTY_DISCOUNT), 4)}",
        }
    for k, v in TOOL33_FNRB_BY_COUNTRY.items():
        if k.lower() == country.lower():
            return {
                "value": v,
                "value_with_discount": round(v * (1 - FNRB_UNCERTAINTY_DISCOUNT), 4),
                "uncertainty_discount": FNRB_UNCERTAINTY_DISCOUNT,
                "unit": "fraction",
                "source": f"CDM TOOL33 country-specific default for {k}",
                "note": f"Raw fNRB = {v}. With 26% uncertainty discount = {round(v * (1 - FNRB_UNCERTAINTY_DISCOUNT), 4)}",
            }
    return {
        "value": FNRB_DEFAULT_WITH_DISCOUNT,
        "value_with_discount": FNRB_DEFAULT_WITH_DISCOUNT,
        "uncertainty_discount": FNRB_UNCERTAINTY_DISCOUNT,
        "unit": "fraction",
        "source": "CDM TOOL33 generic default (fNRB=0.44 with 26% uncertainty discount)",
        "note": "No country-specific value found. Using conservative default.",
    }


def get_fuel_defaults(fuel_type):
    fuel_key = fuel_type.lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "woody_biomass": "wood", "firewood": "wood", "fuelwood": "wood",
        "non_renewable_biomass": "wood", "renewable_biomass": "wood",
        "lpg": "LPG", "liquefied_petroleum_gas": "LPG",
        "green_charcoal": "charcoal", "biomass_briquette": "biomass_briquettes",
    }
    fuel_key = aliases.get(fuel_key, fuel_key)

    result = {}
    if fuel_key in FUEL_NCV:
        result["NCV"] = FUEL_NCV[fuel_key]
    if fuel_key in FUEL_EF_CO2:
        result["EF_CO2"] = FUEL_EF_CO2[fuel_key]
    if fuel_key in FUEL_EF_NONCO2:
        result["EF_nonCO2"] = FUEL_EF_NONCO2[fuel_key]
    return result if result else None


def get_defaults_for_methodology(methodology_code, country=None, baseline_fuel=None, project_fuel=None):
    code = methodology_code.upper().replace("GS-", "")
    result = {
        "parameters": {},
        "equations": [],
        "tools_referenced": {},
        "supplementary_params": [],
    }

    if code in ("VM0050", "TPDDTEC"):
        if country:
            result["parameters"]["fNRB"] = get_fnrb_for_country(country)

        if baseline_fuel:
            bf = get_fuel_defaults(baseline_fuel)
            if bf:
                for k, v in bf.items():
                    result["parameters"][f"baseline_{k}"] = v

        if project_fuel:
            pf = get_fuel_defaults(project_fuel)
            if pf:
                for k, v in pf.items():
                    result["parameters"][f"project_{k}"] = v

        result["parameters"]["CF"] = WOOD_TO_CHARCOAL_CF["default"]
        result["parameters"]["leakage_discount"] = LEAKAGE_DEFAULTS["cookstove_renewable_biomass"]

    if code in ("ACM0002", "AMS-I.D."):
        result["parameters"]["leakage_discount"] = LEAKAGE_DEFAULTS["grid_renewable"]

    result["parameters"]["GWP"] = GWP_VALUES

    meth_key = code if code != "GS-TPDDTEC" else "TPDDTEC"
    if meth_key in METHODOLOGY_EQUATIONS:
        result["equations"] = METHODOLOGY_EQUATIONS[meth_key]["equations"]

    if meth_key in CDM_TOOLS_REFERENCED:
        result["tools_referenced"] = CDM_TOOLS_REFERENCED[meth_key]
    if meth_key in VCS_TOOLS_REFERENCED:
        result["tools_referenced"].update(VCS_TOOLS_REFERENCED[meth_key])

    if meth_key in METHODOLOGY_SUPPLEMENTARY_PARAMS:
        result["supplementary_params"] = METHODOLOGY_SUPPLEMENTARY_PARAMS[meth_key]

    return result


def enrich_methodology_parameters(parsed_data, methodology_code, country=None):
    if not parsed_data or not isinstance(parsed_data, dict):
        return parsed_data

    code = methodology_code.upper().replace("GS-", "")
    supplementary = METHODOLOGY_SUPPLEMENTARY_PARAMS.get(code, [])
    if not supplementary:
        return parsed_data

    existing_params = parsed_data.get("parameters", [])
    if not isinstance(existing_params, list):
        return parsed_data

    existing_symbols = set()
    for p in existing_params:
        if isinstance(p, dict):
            sym = p.get("symbol", "").lower().replace(" ", "")
            existing_symbols.add(sym)

    added = 0
    for sp in supplementary:
        sym_check = sp["symbol"].lower().replace(" ", "")
        if sym_check not in existing_symbols:
            existing_params.append(sp)
            existing_symbols.add(sym_check)
            added += 1

    parsed_data["parameters"] = existing_params
    return parsed_data
