import logging
import json
from carbongpt.repository.db import get_cursor
from carbongpt.core.parameter_engine import get_parameters_as_dict

logger = logging.getLogger(__name__)


def calculate_cookstove_er(params, crediting_years=7, start_year=2025, methodology="VM0050"):
    fNRB = _pval(params, "fNRB", 0.30)
    NCV_b = _pval(params, "NCV_baseline", 15.6)
    EF_CO2_b = _pval(params, "EF_CO2_baseline", 112.0)
    EF_nonCO2_b = _pval(params, "EF_nonCO2_baseline", 9.46)
    NCV_p = _pval(params, "NCV_project", NCV_b)
    EF_CO2_p = _pval(params, "EF_CO2_project", EF_CO2_b)
    EF_nonCO2_p = _pval(params, "EF_nonCO2_project", EF_nonCO2_b)
    leakage_pct = 1.0 - _pval(params, "leakage_discount", 0.95)
    usage_rate_base = _pval(params, "usage_rate", 0.90)
    num_hh = _pval(params, "num_households", 1000)
    hh_size = _pval(params, "household_size", 5.0)

    if methodology in ("VM0050",):
        bl_consumption = _pval(params, "baseline_fuel_consumption", hh_size * 0.4)
        pj_consumption = _pval(params, "project_fuel_consumption", bl_consumption * 0.5)
    else:
        sfc_b = _pval(params, "SFC_baseline", 400.0)
        sfc_p = _pval(params, "SFC_project", 200.0)
        bl_consumption = sfc_b * hh_size / 1000.0
        pj_consumption = sfc_p * hh_size / 1000.0

    years = []
    total_er = 0.0
    total_be = 0.0
    total_pe = 0.0
    total_le = 0.0

    for y in range(crediting_years):
        year_num = y + 1
        cal_year = start_year + y

        usage_rate = max(usage_rate_base - (y * 0.02), 0.50)

        ec_b = bl_consumption * NCV_b / 1000.0
        be_per_hh = ec_b * (EF_CO2_b + EF_nonCO2_b) * fNRB

        ec_p = pj_consumption * NCV_p / 1000.0
        pe_per_hh = ec_p * (EF_CO2_p + EF_nonCO2_p) * fNRB

        active_hh = num_hh * usage_rate
        be_y = be_per_hh * active_hh
        pe_y = pe_per_hh * active_hh
        gross_er = be_y - pe_y
        le_y = gross_er * leakage_pct if leakage_pct > 0 else 0.0
        er_y = gross_er - le_y

        total_er += er_y
        total_be += be_y
        total_pe += pe_y
        total_le += le_y

        years.append({
            "year_number": year_num,
            "calendar_year": cal_year,
            "baseline_emissions": round(be_y, 2),
            "project_emissions": round(pe_y, 2),
            "leakage": round(le_y, 2),
            "net_er": round(er_y, 2),
            "usage_rate": round(usage_rate, 4),
            "active_households": round(active_hh, 0),
        })

    return {
        "years": years,
        "summary": {
            "total_er": round(total_er, 2),
            "total_baseline": round(total_be, 2),
            "total_project": round(total_pe, 2),
            "total_leakage": round(total_le, 2),
            "average_annual_er": round(total_er / crediting_years, 2),
            "crediting_years": crediting_years,
            "methodology": methodology,
        },
    }


def calculate_grid_er(params, crediting_years=7, start_year=2025, methodology="ACM0002"):
    eg_pj = _pval(params, "EG_PJ_y", 50000)
    ef_grid = _pval(params, "EF_grid", 0.8)
    eg_hist = _pval(params, "EG_historical", 0)
    subtype = _ptext(params, "project_subtype", "greenfield")

    years = []
    total_er = 0.0

    for y in range(crediting_years):
        year_num = y + 1
        cal_year = start_year + y

        if subtype == "greenfield":
            be_y = eg_pj * ef_grid
        elif subtype == "capacity_addition":
            be_y = max(eg_pj - eg_hist, 0) * ef_grid
        else:
            be_y = eg_pj * ef_grid

        pe_y = 0.0
        le_y = 0.0
        er_y = be_y - pe_y - le_y
        total_er += er_y

        years.append({
            "year_number": year_num,
            "calendar_year": cal_year,
            "baseline_emissions": round(be_y, 2),
            "project_emissions": round(pe_y, 2),
            "leakage": round(le_y, 2),
            "net_er": round(er_y, 2),
        })

    return {
        "years": years,
        "summary": {
            "total_er": round(total_er, 2),
            "average_annual_er": round(total_er / crediting_years, 2),
            "crediting_years": crediting_years,
            "methodology": methodology,
        },
    }


def run_scenario(project_id, scenario_id=None, parameter_overrides=None):
    params = get_parameters_as_dict(project_id)

    with get_cursor() as cur:
        cur.execute("SELECT methodology, crediting_period_years, crediting_period_start FROM user_projects WHERE id = %s", (project_id,))
        project = cur.fetchone()
        if not project:
            return {"error": "Project not found"}

    methodology = (project["methodology"] or "").upper().replace("GS-", "")
    crediting_years = project.get("crediting_period_years") or 7
    start_year = 2025
    if project.get("crediting_period_start"):
        start_year = project["crediting_period_start"].year

    if parameter_overrides:
        for key, val in parameter_overrides.items():
            if key in params:
                params[key]["value"] = val
            else:
                params[key] = {"value": val}

    if methodology in ("VM0050", "TPDDTEC"):
        result = calculate_cookstove_er(params, crediting_years, start_year, methodology)
    elif methodology in ("ACM0002", "AMS-I.D.", "AMSID"):
        result = calculate_grid_er(params, crediting_years, start_year, methodology)
    else:
        return {"error": f"ER calculation not implemented for methodology: {methodology}"}

    return result


def save_scenario(project_id, name, description="", parameter_overrides=None,
                  carbon_price=None, price_escalation=0, developer_share=100,
                  buffer_pool=0, admin_fee=0, is_baseline=False):
    result = run_scenario(project_id, parameter_overrides=parameter_overrides)
    if "error" in result:
        return result

    if carbon_price:
        _add_finance(result, carbon_price, price_escalation, developer_share, buffer_pool, admin_fee)

    with get_cursor() as cur:
        cur.execute("SELECT methodology, crediting_period_years FROM user_projects WHERE id = %s", (project_id,))
        project = cur.fetchone()

        cur.execute("""
            INSERT INTO er_scenarios
            (project_id, name, description, is_baseline, parameter_overrides,
             methodology_code, crediting_years, carbon_price_usd,
             price_escalation_pct, developer_share_pct, buffer_pool_pct,
             admin_fee_pct, results_summary, calculated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            project_id, name, description, is_baseline,
            json.dumps(parameter_overrides or {}),
            project["methodology"],
            project.get("crediting_period_years") or 7,
            carbon_price, price_escalation, developer_share,
            buffer_pool, admin_fee,
            json.dumps(result["summary"]),
        ))
        scenario_id = cur.fetchone()["id"]

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
        cur.execute("DELETE FROM er_scenarios WHERE id = %s RETURNING id", (scenario_id,))
        return cur.fetchone()


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
