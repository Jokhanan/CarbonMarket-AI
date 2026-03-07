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
        {"param_key": "num_households", "param_name": "Number of households", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10000000, "is_ex_ante": True, "depends_on": []},
        {"param_key": "usage_rate", "param_name": "Usage rate (proportion of devices in use)", "category": "monitoring", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": False, "depends_on": []},
        {"param_key": "leakage_discount", "param_name": "Leakage discount factor", "category": "leakage", "unit": "fraction", "data_type": "number", "min_value": 0.8, "max_value": 1.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "CF", "param_name": "Wood-to-charcoal conversion factor", "category": "fuel_property", "unit": "kg wood/kg charcoal", "data_type": "number", "min_value": 2.0, "max_value": 8.0, "is_ex_ante": True, "tool_reference": "TOOL33", "depends_on": []},
        {"param_key": "baseline_efficiency", "param_name": "Baseline device thermal efficiency", "category": "baseline", "unit": "fraction", "data_type": "number", "min_value": 0.05, "max_value": 0.50, "is_ex_ante": True, "depends_on": []},
        {"param_key": "project_efficiency", "param_name": "Project device thermal efficiency", "category": "project", "unit": "fraction", "data_type": "number", "min_value": 0.10, "max_value": 0.80, "is_ex_ante": True, "depends_on": []},
        {"param_key": "household_size", "param_name": "Average household size", "category": "activity_data", "unit": "persons/household", "data_type": "number", "min_value": 1, "max_value": 20, "is_ex_ante": True, "depends_on": []},
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
        {"param_key": "num_households", "param_name": "Number of households", "category": "activity_data", "unit": "count", "data_type": "number", "min_value": 1, "max_value": 10000000, "is_ex_ante": True, "depends_on": []},
        {"param_key": "usage_rate", "param_name": "Usage rate (proportion of devices in use)", "category": "monitoring", "unit": "fraction", "data_type": "number", "min_value": 0.0, "max_value": 1.0, "is_ex_ante": False, "depends_on": []},
        {"param_key": "leakage_discount", "param_name": "Leakage discount factor", "category": "leakage", "unit": "fraction", "data_type": "number", "min_value": 0.8, "max_value": 1.0, "is_ex_ante": True, "depends_on": []},
        {"param_key": "CF", "param_name": "Wood-to-charcoal conversion factor", "category": "fuel_property", "unit": "kg wood/kg charcoal", "data_type": "number", "min_value": 2.0, "max_value": 8.0, "is_ex_ante": True, "tool_reference": "TOOL33", "depends_on": []},
        {"param_key": "household_size", "param_name": "Average household size", "category": "activity_data", "unit": "persons/household", "data_type": "number", "min_value": 1, "max_value": 20, "is_ex_ante": True, "depends_on": []},
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

        baseline_fuel = settings.get("baseline_fuel") or intake.get("baseline_fuel", "wood")
        project_fuel = settings.get("project_fuel") or intake.get("project_fuel", "")
        is_charcoal = baseline_fuel.lower() in ("charcoal", "green_charcoal")

        definitions = PARAMETER_DEFINITIONS.get(methodology, [])
        if not definitions:
            return {"error": f"No parameter definitions for methodology: {methodology}"}

        cur.execute("SELECT param_key, value, source_type FROM project_parameters WHERE project_id = %s AND source_type IN ('measured', 'user_override')", (project_id,))
        preserved = {row["param_key"]: row for row in cur.fetchall()}

        cur.execute("DELETE FROM project_parameters WHERE project_id = %s", (project_id,))

        defaults = get_defaults_for_methodology(methodology, country=country, baseline_fuel=baseline_fuel, project_fuel=project_fuel)
        param_values = defaults.get("parameters", {})

        inserted = 0
        for defn in definitions:
            value = None
            source_type = "default"
            source_reference = None

            if defn["param_key"] in preserved:
                old = preserved[defn["param_key"]]
                value = old["value"]
                source_type = old["source_type"]
                source_reference = "Preserved from previous initialization"
            else:
                value, source_type, source_reference = _resolve_parameter_value(
                    defn["param_key"], methodology, param_values, country, baseline_fuel, project_fuel, is_charcoal, intake, settings
                )

            cur.execute("""
                INSERT INTO project_parameters
                (project_id, param_key, param_name, category, value, unit, data_type,
                 source_type, source_reference, methodology_code, tool_reference,
                 min_value, max_value, is_ex_ante, depends_on, validation_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                project_id, defn["param_key"], defn["param_name"], defn["category"],
                str(value) if value is not None else None,
                defn.get("unit", ""), defn.get("data_type", "number"),
                source_type, source_reference, methodology,
                defn.get("tool_reference"),
                defn.get("min_value"), defn.get("max_value"),
                defn.get("is_ex_ante", True),
                defn.get("depends_on", []),
                "valid" if value is not None else "pending",
            ))
            inserted += 1

        return {"inserted": inserted, "methodology": methodology, "preserved": len(preserved)}


def _resolve_parameter_value(param_key, methodology, param_values, country, baseline_fuel, project_fuel, is_charcoal, intake, settings):
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
    elif param_key == "num_households":
        value = None
        source_type = "default"
        source_reference = "Must be provided by project developer"
    elif param_key == "household_size":
        value = 5.0
        source_type = "default"
        source_reference = "Common assumption (SSA average)"
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
            _run_validation(cur, updated)
        return updated


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
                COUNT(CASE WHEN source_type = 'user_override' THEN 1 END) as overrides
            FROM project_parameters WHERE project_id = %s
        """, (project_id,))
        return cur.fetchone()
