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
    CF = _pval(params, "CF", 1.0)
    leakage_pct = 1.0 - _pval(params, "leakage_discount", 0.95)
    usage_rate_base = _pval(params, "usage_rate", 0.90)
    num_hh = _pval(params, "num_households", 1000)
    hh_size = _pval(params, "household_size", 5.0)

    baseline_fuel = _ptext(params, "baseline_fuel", "wood")
    is_charcoal_baseline = baseline_fuel.lower() in ("charcoal", "charbon")

    if methodology in ("VM0050",):
        bl_consumption = _pval(params, "baseline_fuel_consumption", hh_size * 0.4)
        pj_consumption = _pval(params, "project_fuel_consumption", bl_consumption * 0.5)
        consumption_label = "baseline_fuel_consumption"
        consumption_pj_label = "project_fuel_consumption"
    else:
        sfc_b = _pval(params, "SFC_baseline", 400.0)
        sfc_p = _pval(params, "SFC_project", 200.0)
        bl_consumption = sfc_b * hh_size / 1000.0
        pj_consumption = sfc_p * hh_size / 1000.0
        consumption_label = f"SFC_baseline * household_size / 1000 = {sfc_b} * {hh_size} / 1000"
        consumption_pj_label = f"SFC_project * household_size / 1000 = {sfc_p} * {hh_size} / 1000"

    if is_charcoal_baseline and CF > 1.0:
        bl_consumption_wood_equiv = bl_consumption * CF
        pj_consumption_wood_equiv = pj_consumption * CF
        cf_note = f"Charcoal baseline: consumption * CF = {bl_consumption:.4f} * {CF} = {bl_consumption_wood_equiv:.4f} t wood-equiv/hh/yr"
    else:
        bl_consumption_wood_equiv = bl_consumption
        pj_consumption_wood_equiv = pj_consumption
        cf_note = f"Wood baseline: CF not applied (CF={CF})"

    ec_b = bl_consumption_wood_equiv * NCV_b / 1000.0
    be_per_hh = ec_b * (EF_CO2_b + EF_nonCO2_b) * fNRB
    ec_p = pj_consumption_wood_equiv * NCV_p / 1000.0
    pe_per_hh = ec_p * (EF_CO2_p + EF_nonCO2_p) * fNRB

    calculation_steps = [
        {
            "step": 1,
            "name": "Baseline fuel consumption per household",
            "formula": consumption_label,
            "value": round(bl_consumption, 6),
            "unit": "t/hh/yr",
        },
        {
            "step": 2,
            "name": "Project fuel consumption per household",
            "formula": consumption_pj_label,
            "value": round(pj_consumption, 6),
            "unit": "t/hh/yr",
        },
        {
            "step": 3,
            "name": "CF adjustment (charcoal-to-wood equivalent)",
            "formula": cf_note,
            "value_baseline": round(bl_consumption_wood_equiv, 6),
            "value_project": round(pj_consumption_wood_equiv, 6),
            "unit": "t wood-equiv/hh/yr",
        },
        {
            "step": 4,
            "name": "Baseline energy content per household",
            "formula": f"B_cons_wood_equiv * NCV_b / 1000 = {bl_consumption_wood_equiv:.6f} * {NCV_b} / 1000",
            "value": round(ec_b, 6),
            "unit": "TJ/hh/yr",
        },
        {
            "step": 5,
            "name": "Baseline emissions per household",
            "formula": f"EC_b * (EF_CO2_b + EF_nonCO2_b) * fNRB = {ec_b:.6f} * ({EF_CO2_b} + {EF_nonCO2_b}) * {fNRB}",
            "value": round(be_per_hh, 6),
            "unit": "tCO2e/hh/yr",
        },
        {
            "step": 6,
            "name": "Project energy content per household",
            "formula": f"P_cons_wood_equiv * NCV_p / 1000 = {pj_consumption_wood_equiv:.6f} * {NCV_p} / 1000",
            "value": round(ec_p, 6),
            "unit": "TJ/hh/yr",
        },
        {
            "step": 7,
            "name": "Project emissions per household",
            "formula": f"EC_p * (EF_CO2_p + EF_nonCO2_p) * fNRB = {ec_p:.6f} * ({EF_CO2_p} + {EF_nonCO2_p}) * {fNRB}",
            "value": round(pe_per_hh, 6),
            "unit": "tCO2e/hh/yr",
        },
        {
            "step": 8,
            "name": "ER per household per year (before leakage)",
            "formula": f"BE_per_hh - PE_per_hh = {be_per_hh:.6f} - {pe_per_hh:.6f}",
            "value": round(be_per_hh - pe_per_hh, 6),
            "unit": "tCO2e/hh/yr",
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

        usage_rate = max(usage_rate_base - (y * 0.02), 0.50)
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
            "usage_rate": round(usage_rate, 4),
            "active_households": round(active_hh, 2),
            "active_hh_formula": f"max({usage_rate_base} - ({y} * 0.02), 0.50) * {num_hh}",
            "be_per_hh": round(be_per_hh, 6),
            "pe_per_hh": round(pe_per_hh, 6),
            "baseline_emissions": round(be_y, 2),
            "baseline_formula": f"{be_per_hh:.4f} * {active_hh:.0f}",
            "project_emissions": round(pe_y, 2),
            "project_formula": f"{pe_per_hh:.4f} * {active_hh:.0f}",
            "gross_er": round(gross_er, 2),
            "leakage": round(le_y, 2),
            "leakage_formula": f"{gross_er:.2f} * {leakage_pct:.4f}" if leakage_pct > 0 else "0",
            "net_er": round(er_y, 2),
            "net_er_formula": f"{gross_er:.2f} - {le_y:.2f}",
        })

    return {
        "calculation_steps": calculation_steps,
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
        "parameters_used": {
            "fNRB": {"value": fNRB, "unit": "fraction", "description": "Fraction of non-renewable biomass"},
            "NCV_baseline": {"value": NCV_b, "unit": "TJ/Gg", "description": "Net calorific value (baseline fuel)"},
            "NCV_project": {"value": NCV_p, "unit": "TJ/Gg", "description": "Net calorific value (project fuel)"},
            "EF_CO2_baseline": {"value": EF_CO2_b, "unit": "tCO2/TJ", "description": "CO2 emission factor (baseline)"},
            "EF_nonCO2_baseline": {"value": EF_nonCO2_b, "unit": "tCO2e/TJ", "description": "Non-CO2 emission factor (baseline)"},
            "EF_CO2_project": {"value": EF_CO2_p, "unit": "tCO2/TJ", "description": "CO2 emission factor (project)"},
            "EF_nonCO2_project": {"value": EF_nonCO2_p, "unit": "tCO2e/TJ", "description": "Non-CO2 emission factor (project)"},
            "CF": {"value": CF, "unit": "kg wood/kg charcoal", "description": "Charcoal-to-wood conversion factor"},
            "baseline_fuel": {"value": baseline_fuel, "unit": "", "description": "Baseline fuel type"},
            "is_charcoal_baseline": {"value": is_charcoal_baseline, "unit": "", "description": "Charcoal baseline applied"},
            "bl_consumption": {"value": round(bl_consumption, 4), "unit": "t/hh/yr", "description": "Baseline consumption (raw)"},
            "bl_consumption_wood_equiv": {"value": round(bl_consumption_wood_equiv, 4), "unit": "t/hh/yr", "description": "Baseline consumption (wood-equiv)"},
            "pj_consumption": {"value": round(pj_consumption, 4), "unit": "t/hh/yr", "description": "Project consumption (raw)"},
            "pj_consumption_wood_equiv": {"value": round(pj_consumption_wood_equiv, 4), "unit": "t/hh/yr", "description": "Project consumption (wood-equiv)"},
            "leakage_pct": {"value": leakage_pct, "unit": "fraction", "description": "Leakage deduction percentage"},
            "usage_rate": {"value": usage_rate_base, "unit": "fraction", "description": "Initial usage rate (decays 2%/yr)"},
            "num_households": {"value": num_hh, "unit": "count", "description": "Number of households"},
            "household_size": {"value": hh_size, "unit": "persons", "description": "Average household size"},
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


def export_er_to_excel(result, project_name="Project"):
    import io
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        return None

    wb = openpyxl.Workbook()

    header_font = Font(bold=True, size=12)
    param_header_font = Font(bold=True, size=10, color="FFFFFF")
    formula_font = Font(italic=True, size=9, color="666666")
    number_format_2dp = '0.00'
    number_format_6dp = '0.000000'
    teal_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")
    light_fill = PatternFill(start_color="F0FDFA", end_color="F0FDFA", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    ws_params = wb.active
    ws_params.title = "Parameters"
    ws_params.append(["CarbonGPT - ER Calculation Workbook"])
    ws_params["A1"].font = Font(bold=True, size=14)
    ws_params.append([f"Project: {project_name}"])
    ws_params.append([f"Methodology: {result.get('summary', {}).get('methodology', 'N/A')}"])
    ws_params.append([])

    ws_params.append(["Parameter", "Value", "Unit", "Description"])
    for col in range(1, 5):
        cell = ws_params.cell(row=5, column=col)
        cell.font = param_header_font
        cell.fill = teal_fill
        cell.border = thin_border

    params_used = result.get("parameters_used", {})
    row = 6
    for key, info in params_used.items():
        if isinstance(info, dict):
            val = info.get("value", "")
            unit = info.get("unit", "")
            desc = info.get("description", "")
        else:
            val = info
            unit = ""
            desc = ""
        ws_params.append([key, val, unit, desc])
        for col in range(1, 5):
            ws_params.cell(row=row, column=col).border = thin_border
        if row % 2 == 0:
            for col in range(1, 5):
                ws_params.cell(row=row, column=col).fill = light_fill
        row += 1

    ws_params.column_dimensions['A'].width = 30
    ws_params.column_dimensions['B'].width = 18
    ws_params.column_dimensions['C'].width = 20
    ws_params.column_dimensions['D'].width = 45

    ws_steps = wb.create_sheet("Calculation Steps")
    ws_steps.append(["Step-by-Step Calculation Breakdown"])
    ws_steps["A1"].font = Font(bold=True, size=14)
    ws_steps.append([])

    ws_steps.append(["Step", "Description", "Formula / Calculation", "Result", "Unit"])
    for col in range(1, 6):
        cell = ws_steps.cell(row=3, column=col)
        cell.font = param_header_font
        cell.fill = teal_fill
        cell.border = thin_border

    steps = result.get("calculation_steps", [])
    row = 4
    for s in steps:
        step_num = s.get("step", "")
        name = s.get("name", "")
        formula = s.get("formula", "")
        val = s.get("value", s.get("value_baseline", ""))
        unit = s.get("unit", "")
        ws_steps.append([step_num, name, formula, val, unit])
        for col in range(1, 6):
            ws_steps.cell(row=row, column=col).border = thin_border
        ws_steps.cell(row=row, column=3).font = formula_font
        if isinstance(val, float):
            ws_steps.cell(row=row, column=4).number_format = number_format_6dp
        row += 1

    ws_steps.column_dimensions['A'].width = 8
    ws_steps.column_dimensions['B'].width = 45
    ws_steps.column_dimensions['C'].width = 70
    ws_steps.column_dimensions['D'].width = 18
    ws_steps.column_dimensions['E'].width = 20

    ws_years = wb.create_sheet("Year-by-Year Results")
    ws_years.append(["Year-by-Year Emission Reduction Calculations"])
    ws_years["A1"].font = Font(bold=True, size=14)
    ws_years.append([])

    year_headers = [
        "Year", "Calendar Year", "Usage Rate", "Active HH",
        "BE/hh (tCO2e)", "PE/hh (tCO2e)",
        "Baseline Emissions (tCO2e)", "BE Formula",
        "Project Emissions (tCO2e)", "PE Formula",
        "Gross ER (tCO2e)", "Leakage (tCO2e)", "Leakage Formula",
        "Net ER (tCO2e)", "Net ER Formula",
    ]
    ws_years.append(year_headers)
    for col in range(1, len(year_headers) + 1):
        cell = ws_years.cell(row=3, column=col)
        cell.font = param_header_font
        cell.fill = teal_fill
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True)

    years = result.get("years", [])
    row = 4
    for y in years:
        ws_years.append([
            y.get("year_number"),
            y.get("calendar_year"),
            y.get("usage_rate"),
            y.get("active_households"),
            y.get("be_per_hh"),
            y.get("pe_per_hh"),
            y.get("baseline_emissions"),
            y.get("baseline_formula", ""),
            y.get("project_emissions"),
            y.get("project_formula", ""),
            y.get("gross_er"),
            y.get("leakage"),
            y.get("leakage_formula", ""),
            y.get("net_er"),
            y.get("net_er_formula", ""),
        ])
        for col in range(1, len(year_headers) + 1):
            cell = ws_years.cell(row=row, column=col)
            cell.border = thin_border
            if isinstance(cell.value, float):
                cell.number_format = number_format_2dp
        for formula_col in [8, 10, 13, 15]:
            ws_years.cell(row=row, column=formula_col).font = formula_font
        if row % 2 == 0:
            for col in range(1, len(year_headers) + 1):
                ws_years.cell(row=row, column=col).fill = light_fill
        row += 1

    summary = result.get("summary", {})
    row += 1
    ws_years.cell(row=row, column=1, value="TOTALS").font = Font(bold=True, size=11)
    ws_years.cell(row=row, column=7, value=summary.get("total_baseline", 0)).font = Font(bold=True)
    ws_years.cell(row=row, column=7).number_format = number_format_2dp
    ws_years.cell(row=row, column=9, value=summary.get("total_project", 0)).font = Font(bold=True)
    ws_years.cell(row=row, column=9).number_format = number_format_2dp
    ws_years.cell(row=row, column=12, value=summary.get("total_leakage", 0)).font = Font(bold=True)
    ws_years.cell(row=row, column=12).number_format = number_format_2dp
    ws_years.cell(row=row, column=14, value=summary.get("total_er", 0)).font = Font(bold=True)
    ws_years.cell(row=row, column=14).number_format = number_format_2dp
    for col in range(1, len(year_headers) + 1):
        ws_years.cell(row=row, column=col).border = Border(top=Side(style='double'))

    for col_letter in ['A','B','C','D','E','F']:
        ws_years.column_dimensions[col_letter].width = 14
    for col_letter in ['G','H','I','J','K','L','M','N','O']:
        ws_years.column_dimensions[col_letter].width = 22

    if "total_gross_revenue" in summary:
        ws_fin = wb.create_sheet("Carbon Finance")
        ws_fin.append(["Carbon Finance Projections"])
        ws_fin["A1"].font = Font(bold=True, size=14)
        ws_fin.append([])
        ws_fin.append(["Carbon Price ($/tCO2e)", summary.get("carbon_price", 0)])
        ws_fin.append(["Developer Share (%)", summary.get("developer_share_pct", 100)])
        ws_fin.append(["Total Gross Revenue ($)", summary.get("total_gross_revenue", 0)])
        ws_fin.append(["Total Deductions ($)", summary.get("total_deductions", 0)])
        ws_fin.append(["Total Net Revenue ($)", summary.get("total_net_revenue", 0)])
        ws_fin.column_dimensions['A'].width = 30
        ws_fin.column_dimensions['B'].width = 20

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


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
