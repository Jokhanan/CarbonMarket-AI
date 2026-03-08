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
        {"param_key": "fNRB", "param_name": "Fraction of non-renewable biomass", "category": "baseline", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": True, "tool_reference": "TOOL33", "depends_on": []},
        {"param_key": "NCV_baseline", "param_name": "Net calorific value (baseline fuel)", "category": "fuel_property", "unit": "TJ/Gg", "data_type": "number", "min_value": 5.0, "max_value": 55.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "NCV_project", "param_name": "Net calorific value (project fuel)", "category": "fuel_property", "unit": "TJ/Gg", "data_type": "number", "min_value": 5.0, "max_value": 55.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_CO2_baseline", "param_name": "CO2 emission factor (baseline fuel)", "category": "emission_factor", "unit": "tCO2/TJ", "data_type": "number", "min_value": 0.0, "max_value": 200.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_nonCO2_baseline", "param_name": "Non-CO2 emission factor (baseline fuel)", "category": "emission_factor", "unit": "tCO2e/TJ", "data_type": "number", "min_value": 0.0, "max_value": 100.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_CO2_project", "param_name": "CO2 emission factor (project fuel)", "category": "emission_factor", "unit": "tCO2/TJ", "data_type": "number", "min_value": 0.0, "max_value": 200.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_nonCO2_project", "param_name": "Non-CO2 emission factor (project fuel)", "category": "emission_factor", "unit": "tCO2e/TJ", "data_type": "number", "min_value": 0.0, "max_value": 100.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "baseline_fuel_consumption", "param_name": "Baseline fuel consumption per household", "category": "baseline", "unit": "tonnes/household/year", "data_type": "number", "min_value": 0.01, "max_value": 20.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "project_fuel_consumption", "param_name": "Project fuel consumption per household", "category": "project", "unit": "tonnes/household/year", "data_type": "number", "min_value": 0.0, "max_value": 20.0, "is_ex_ante": False, "depends_on": []},
        {"param_key": "num_devices", "param_name": "Number of devices/technologies deployed", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10000000, "is_ex_ante": True, "depends_on": []},
        {"param_key": "num_households", "param_name": "Number of households served", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10000000, "is_ex_ante": True, "depends_on": []},
        {"param_key": "devices_per_household", "param_name": "Devices per household", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10, "is_ex_ante": True, "depends_on": []},
        {"param_key": "num_beneficiaries", "param_name": "Number of beneficiaries", "category": "activity_data", "unit": "persons", "data_type": "number", "min_value": 1, "max_value": 100000000, "is_ex_ante": True, "depends_on": ["num_households", "household_size"]},
        {"param_key": "usage_rate", "param_name": "Usage rate (proportion of devices in use)", "category": "monitoring", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": False, "depends_on": []},
        {"param_key": "leakage_discount", "param_name": "Leakage discount factor", "category": "leakage", "unit": "fraction", "data_type": "number", "min_value": 0.8, "max_value": 1.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "CF", "param_name": "Wood-to-charcoal conversion factor", "category": "fuel_property", "unit": "kg wood/kg charcoal", "data_type": "number", "min_value": 2.0, "max_value": 8.0, "is_ex_ante": True, "tool_reference": "TOOL33", "depends_on": []},
        {"param_key": "baseline_efficiency", "param_name": "Baseline device thermal efficiency", "category": "baseline", "unit": "fraction", "data_type": "number", "min_value": 0.05, "max_value": 0.50, "is_ex_ante": True, "depends_on": []},
        {"param_key": "project_efficiency", "param_name": "Project device thermal efficiency", "category": "project", "unit": "fraction", "data_type": "number", "min_value": 0.10, "max_value": 0.80, "is_ex_ante": True, "depends_on": []},
        {"param_key": "household_size", "param_name": "Average household size", "category": "activity_data", "unit": "persons/household", "data_type": "number", "min_value": 1, "max_value": 20, "is_ex_ante": True, "depends_on": []},
        {"param_key": "baseline_fuel", "param_name": "Baseline fuel type", "category": "baseline", "unit": "", "data_type": "text", "is_ex_ante": True, "depends_on": []},
    ],
    "TPDDTEC": [
        {"param_key": "fNRB", "param_name": "Fraction of non-renewable biomass", "category": "baseline", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": True, "tool_reference": "TOOL33", "depends_on": []},
        {"param_key": "NCV_baseline", "param_name": "Net calorific value (baseline fuel)", "category": "fuel_property", "unit": "TJ/Gg", "data_type": "number", "min_value": 5.0, "max_value": 55.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "NCV_project", "param_name": "Net calorific value (project fuel)", "category": "fuel_property", "unit": "TJ/Gg", "data_type": "number", "min_value": 5.0, "max_value": 55.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_CO2_baseline", "param_name": "CO2 emission factor (baseline fuel)", "category": "emission_factor", "unit": "tCO2/TJ", "data_type": "number", "min_value": 0.0, "max_value": 200.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_nonCO2_baseline", "param_name": "Non-CO2 emission factor (baseline fuel)", "category": "emission_factor", "unit": "tCO2e/TJ", "data_type": "number", "min_value": 0.0, "max_value": 100.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_CO2_project", "param_name": "CO2 emission factor (project fuel)", "category": "emission_factor", "unit": "tCO2/TJ", "data_type": "number", "min_value": 0.0, "max_value": 200.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_nonCO2_project", "param_name": "Non-CO2 emission factor (project fuel)", "category": "emission_factor", "unit": "tCO2e/TJ", "data_type": "number", "min_value": 0.0, "max_value": 100.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "SFC_baseline", "param_name": "Baseline specific fuel consumption", "category": "baseline", "unit": "kg/person/year", "data_type": "number", "min_value": 0.01, "max_value": 5000, "is_ex_ante": False, "depends_on": []},
        {"param_key": "SFC_project", "param_name": "Project specific fuel consumption", "category": "project", "unit": "kg/person/year", "data_type": "number", "min_value": 0.0, "max_value": 5000, "is_ex_ante": False, "depends_on": []},
        {"param_key": "num_devices", "param_name": "Number of devices/technologies deployed", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10000000, "is_ex_ante": True, "depends_on": []},
        {"param_key": "num_households", "param_name": "Number of households served", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10000000, "is_ex_ante": True, "depends_on": []},
        {"param_key": "devices_per_household", "param_name": "Devices per household", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10, "is_ex_ante": True, "depends_on": []},
        {"param_key": "num_beneficiaries", "param_name": "Number of beneficiaries", "category": "activity_data", "unit": "persons", "data_type": "number", "min_value": 1, "max_value": 100000000, "is_ex_ante": True, "depends_on": ["num_households", "household_size"]},
        {"param_key": "usage_rate", "param_name": "Usage rate (proportion of devices in use)", "category": "monitoring", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": False, "depends_on": []},
        {"param_key": "leakage_discount", "param_name": "Leakage discount factor", "category": "leakage", "unit": "fraction", "data_type": "number", "min_value": 0.8, "max_value": 1.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "CF", "param_name": "Wood-to-charcoal conversion factor", "category": "fuel_property", "unit": "kg wood/kg charcoal", "data_type": "number", "min_value": 2.0, "max_value": 8.0, "is_ex_ante": True, "tool_reference": "TOOL33", "depends_on": []},
        {"param_key": "household_size", "param_name": "Average household size", "category": "activity_data", "unit": "persons/household", "data_type": "number", "min_value": 1, "max_value": 20, "is_ex_ante": True, "depends_on": []},
        {"param_key": "baseline_fuel", "param_name": "Baseline fuel type", "category": "baseline", "unit": "", "data_type": "text", "is_ex_ante": True, "depends_on": []},
    ],
    "ACM0002": [
        {"param_key": "EG_PJ_y", "param_name": "Net electricity generation (project)", "category": "project", "unit": "MWh/yr", "data_type": "number", "min_value": 0, "max_value": 100000000, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_grid", "param_name": "Grid emission factor", "category": "emission_factor", "unit": "tCO2/MWh", "data_type": "number", "min_value": 0.0, "max_value": 2.0, "is_ex_ante": True, "tool_reference": "TOOL07", "depends_on": []},
        {"param_key": "EG_historical", "param_name": "Historical electricity generation", "category": "baseline", "unit": "MWh/yr", "data_type": "number", "min_value": 0, "max_value": 100000000, "is_ex_ante": True, "depends_on": []},
        {"param_key": "project_subtype", "param_name": "Project subtype", "category": "project", "unit": "", "data_type": "text", "is_ex_ante": True, "depends_on": []},
    ],
    "AMS-I.D.": [
        {"param_key": "EG_PJ_y", "param_name": "Net electricity generation (project)", "category": "project", "unit": "MWh/yr", "data_type": "number", "min_value": 0, "max_value": 900000, "is_ex_ante": True, "depends_on": []},
        {"param_key": "EF_grid", "param_name": "Grid emission factor", "category": "emission_factor", "unit": "tCO2/MWh", "data_type": "number", "min_value": 0.0, "max_value": 2.0, "is_ex_ante": True, "tool_reference": "TOOL07", "depends_on": []},
    ],
}


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

        methodology = (project["methodology"] or "").upper().replace("GS-", "")
        country = project.get("country", "")
        settings = project.get("project_settings") or {}
        intake = project.get("project_intake") or {}

        raw_baseline_fuel = settings.get("baseline_fuel") or intake.get("baseline_fuel", "wood")
        baseline_fuel = normalize_fuel_type(raw_baseline_fuel)
        raw_project_fuel = settings.get("project_fuel") or intake.get("project_fuel", "")
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
                    source_reference = "Seeded from TOOL33 setup values"
                    param_status = "confirmed"
                else:
                    value, source_type, source_reference = _resolve_parameter_value(
                        defn["param_key"], methodology, param_values, country,
                        baseline_fuel, project_fuel, is_charcoal, intake, settings,
                        intake_num_units=intake_num_units,
                        intake_beneficiaries=intake_beneficiaries,
                    )

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
            source_reference = fnrb.get("source", "TOOL33")
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
            source_reference = cf.get("source", "TOOL33")
    elif param_key == "baseline_fuel_consumption":
        if is_charcoal:
            value = 0.1 * 5.0
            source_reference = "TOOL33 default: 0.1 t charcoal/person/yr * 5 persons/hh"
        else:
            value = 0.4 * 5.0
            source_reference = "TOOL33 default: 0.4 t wood/person/yr * 5 persons/hh"
    elif param_key == "SFC_baseline":
        if is_charcoal:
            value = 100.0
            source_reference = "TOOL33 derived: 0.1 t/person/yr = 100 kg/person/yr"
        else:
            value = 400.0
            source_reference = "TOOL33 default: 0.4 t/person/yr = 400 kg/person/yr"
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
        if intake_num_units is not None:
            value = intake_num_units
            source_type = "default"
            source_reference = "Derived from num_devices (1 device per household assumed)"
        else:
            value = None
            source_type = "default"
            source_reference = "Must be provided by project developer"
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
    elif param_key == "baseline_fuel":
        value = baseline_fuel or "wood"
        source_type = "default"
        source_reference = "From project intake data (normalized)"
        return value, source_type, source_reference
    elif param_key == "baseline_efficiency":
        value = 0.15
        source_type = "default"
        source_reference = "TOOL33 v03.0 para 19(a) - three-stone fire"
    elif param_key == "project_efficiency":
        value = None
        source_type = "default"
        source_reference = "Must be determined from testing (WBT)"

    if source_type == "default" and source_reference is None:
        source_reference = "IPCC 2006 / Methodology default"

    return value, source_type, source_reference


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
