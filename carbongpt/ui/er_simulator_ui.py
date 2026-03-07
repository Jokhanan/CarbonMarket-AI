import streamlit as st
from carbongpt.core.er_simulator import (
    run_scenario,
    save_scenario,
    get_scenarios,
    get_scenario_detail,
    delete_scenario,
    run_sensitivity,
    export_er_to_excel,
)
from carbongpt.core.parameter_engine import get_parameters_as_dict, get_project_parameters


def render_er_simulator(project):
    project_id = project["id"]
    project_name = project.get("project_name") or project.get("name") or f"Project {project_id}"
    methodology = (project.get("methodology") or "").upper().replace("GS-", "")

    st.subheader("Emission Reduction Scenario Simulator")

    if methodology not in ("VM0050", "TPDDTEC", "ACM0002", "AMS-I.D.", "AMSID"):
        st.warning(f"ER simulation is not yet available for methodology: {methodology}")
        return

    sim_tabs = st.tabs(["Live Simulator", "Saved Scenarios", "Sensitivity Analysis", "Carbon Finance"])

    with sim_tabs[0]:
        _render_live_simulator(project_id, methodology, project_name)

    with sim_tabs[1]:
        _render_saved_scenarios(project_id)

    with sim_tabs[2]:
        _render_sensitivity(project_id, methodology)

    with sim_tabs[3]:
        _render_finance(project_id, methodology)


def _render_live_simulator(project_id, methodology, project_name="Project"):
    st.markdown("**Adjust parameters to see emission reduction projections**")

    params = get_parameters_as_dict(project_id)
    if not params:
        st.info("Initialize parameters in the Parameters tab first.")
        return

    overrides = {}
    if methodology in ("VM0050", "TPDDTEC"):
        st.markdown("**Activity Data**")
        col1, col2, col3 = st.columns(3)
        with col1:
            hh = st.number_input("Number of Households", min_value=1, value=int(_safe_float(params, "num_households", 1000)), step=100, key="sim_hh")
            overrides["num_households"] = hh
        with col2:
            hh_size = st.number_input("Household Size (persons)", min_value=1.0, value=_safe_float(params, "household_size", 5.0), step=0.5, key="sim_hh_size")
            overrides["household_size"] = hh_size
        with col3:
            usage = st.slider("Usage Rate", 0.0, 1.0, _safe_float(params, "usage_rate", 0.90), 0.01, key="sim_usage")
            overrides["usage_rate"] = usage

        st.markdown("**Fuel Consumption**")
        col1, col2, col3 = st.columns(3)
        with col1:
            fuel_options = ["wood", "charcoal"]
            current_fuel = _safe_text(params, "baseline_fuel", "wood")
            fuel_idx = fuel_options.index(current_fuel) if current_fuel in fuel_options else 0
            baseline_fuel = st.selectbox("Baseline Fuel", fuel_options, index=fuel_idx, key="sim_bl_fuel")
            overrides["baseline_fuel"] = baseline_fuel
        with col2:
            if methodology == "VM0050":
                bl_cons = st.number_input("Baseline Fuel (t/hh/yr)", min_value=0.01, value=_safe_float(params, "baseline_fuel_consumption", 2.0), step=0.1, key="sim_bl_cons")
                overrides["baseline_fuel_consumption"] = bl_cons
            else:
                sfc_b = st.number_input("Baseline SFC (kg/person/yr)", min_value=0.0, value=_safe_float(params, "SFC_baseline", 400.0), step=10.0, key="sim_sfc_b")
                overrides["SFC_baseline"] = sfc_b
        with col3:
            if methodology == "VM0050":
                pj_cons = st.number_input("Project Fuel (t/hh/yr)", min_value=0.0, value=_safe_float(params, "project_fuel_consumption", 1.0), step=0.1, key="sim_pj_cons")
                overrides["project_fuel_consumption"] = pj_cons
            else:
                sfc_p = st.number_input("Project SFC (kg/person/yr)", min_value=0.0, value=_safe_float(params, "SFC_project", 200.0), step=10.0, key="sim_sfc_p")
                overrides["SFC_project"] = sfc_p

        st.markdown("**Emission Factors & Fuel Properties**")
        col1, col2 = st.columns(2)
        with col1:
            fNRB = st.slider("fNRB", 0.0, 1.0, _safe_float(params, "fNRB", 0.30), 0.01, key="sim_fNRB")
            overrides["fNRB"] = fNRB
            ncv_b = st.number_input("NCV Baseline (TJ/Gg)", min_value=1.0, value=_safe_float(params, "NCV_baseline", 15.6), step=0.1, key="sim_ncv_b")
            overrides["NCV_baseline"] = ncv_b
            ef_co2_b = st.number_input("EF CO2 Baseline (tCO2/TJ)", min_value=0.0, value=_safe_float(params, "EF_CO2_baseline", 112.0), step=1.0, key="sim_ef_co2_b")
            overrides["EF_CO2_baseline"] = ef_co2_b
            ef_nco2_b = st.number_input("EF non-CO2 Baseline (tCO2e/TJ)", min_value=0.0, value=_safe_float(params, "EF_nonCO2_baseline", 9.46), step=0.1, key="sim_ef_nco2_b")
            overrides["EF_nonCO2_baseline"] = ef_nco2_b
        with col2:
            cf = st.number_input("CF (wood-to-charcoal)", min_value=1.0, value=_safe_float(params, "CF", 4.0), step=0.1, key="sim_cf", help="Only applied when baseline fuel is charcoal")
            overrides["CF"] = cf
            ncv_p = st.number_input("NCV Project (TJ/Gg)", min_value=1.0, value=_safe_float(params, "NCV_project", 15.6), step=0.1, key="sim_ncv_p")
            overrides["NCV_project"] = ncv_p
            ef_co2_p = st.number_input("EF CO2 Project (tCO2/TJ)", min_value=0.0, value=_safe_float(params, "EF_CO2_project", 112.0), step=1.0, key="sim_ef_co2_p")
            overrides["EF_CO2_project"] = ef_co2_p
            ef_nco2_p = st.number_input("EF non-CO2 Project (tCO2e/TJ)", min_value=0.0, value=_safe_float(params, "EF_nonCO2_project", 9.46), step=0.1, key="sim_ef_nco2_p")
            overrides["EF_nonCO2_project"] = ef_nco2_p

        st.markdown("**Leakage**")
        leakage = st.slider("Leakage Discount", 0.80, 1.0, _safe_float(params, "leakage_discount", 0.95), 0.01, key="sim_leak", help="0.95 = 5% leakage deduction")
        overrides["leakage_discount"] = leakage

    elif methodology in ("ACM0002", "AMS-I.D.", "AMSID"):
        col1, col2 = st.columns(2)
        with col1:
            eg = st.number_input("Net Generation (MWh/yr)", min_value=0, value=int(_safe_float(params, "EG_PJ_y", 50000)), step=1000, key="sim_eg")
            overrides["EG_PJ_y"] = eg
        with col2:
            ef = st.number_input("Grid EF (tCO2/MWh)", min_value=0.0, value=_safe_float(params, "EF_grid", 0.8), step=0.01, key="sim_ef")
            overrides["EF_grid"] = ef

    if st.button("Calculate", key="run_sim", type="primary"):
        with st.spinner("Calculating emission reductions..."):
            result = run_scenario(project_id, parameter_overrides=overrides)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state[f"sim_result_{project_id}"] = result
                st.session_state[f"sim_overrides_{project_id}"] = overrides

    result = st.session_state.get(f"sim_result_{project_id}")
    if result:
        _render_er_results(result, project_name=project_name)

        st.markdown("---")
        save_col1, save_col2 = st.columns([2, 1])
        with save_col1:
            scenario_name = st.text_input("Scenario Name", value="", placeholder="e.g. Base Case, Optimistic", key="save_name")
        with save_col2:
            is_baseline = st.checkbox("Set as baseline scenario", key="save_baseline")

        if st.button("Save Scenario", key="save_scenario"):
            if not scenario_name:
                st.warning("Enter a name for the scenario")
            else:
                saved = save_scenario(
                    project_id, scenario_name,
                    parameter_overrides=st.session_state.get(f"sim_overrides_{project_id}", {}),
                    is_baseline=is_baseline,
                )
                if "error" in saved:
                    st.error(saved["error"])
                else:
                    st.success(f"Scenario '{scenario_name}' saved (ID: {saved['scenario_id']})")


def _render_er_results(result, project_name="Project"):
    summary = result["summary"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total ER", f"{summary['total_er']:,.0f} tCO2e")
    with col2:
        st.metric("Average Annual ER", f"{summary['average_annual_er']:,.0f} tCO2e/yr")
    with col3:
        st.metric("Crediting Period", f"{summary['crediting_years']} years")

    if "total_net_revenue" in summary:
        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("Gross Revenue", f"${summary.get('total_gross_revenue', 0):,.0f}")
        with col5:
            st.metric("Net Revenue", f"${summary.get('total_net_revenue', 0):,.0f}")
        with col6:
            st.metric("Carbon Price", f"${summary.get('carbon_price', 0):,.2f}/tCO2e")

    excel_data = export_er_to_excel(result, project_name=project_name)
    if excel_data:
        st.download_button(
            label="Download Excel Workbook",
            data=excel_data,
            file_name=f"ER_Calculation_{project_name.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_excel_{id(result)}",
        )

    steps = result.get("calculation_steps", [])
    if steps:
        with st.expander("Step-by-Step Calculation (Formulas)", expanded=True):
            for s in steps:
                step_num = s.get("step", "")
                name = s.get("name", "")
                formula = s.get("formula", "")
                val = s.get("value", s.get("value_baseline", ""))
                unit = s.get("unit", "")
                if isinstance(val, float):
                    val_str = f"{val:g}"
                else:
                    val_str = str(val)
                st.markdown(f"**Step {step_num}: {name}**")
                st.code(f"{formula}\n= {val_str} {unit}", language=None)

    params_used = result.get("parameters_used")
    if params_used:
        with st.expander("Input Parameters"):
            param_rows = []
            for k, info in params_used.items():
                if isinstance(info, dict):
                    val = info.get("value", "")
                    unit = info.get("unit", "")
                    desc = info.get("description", "")
                    if isinstance(val, bool):
                        val_str = "Yes" if val else "No"
                    elif isinstance(val, float):
                        val_str = f"{val:g}"
                    else:
                        val_str = str(val)
                    param_rows.append({"Parameter": k, "Value": val_str, "Unit": unit, "Description": desc})
                else:
                    if isinstance(info, bool):
                        val_str = "Yes" if info else "No"
                    elif isinstance(info, float):
                        val_str = f"{info:g}"
                    else:
                        val_str = str(info)
                    param_rows.append({"Parameter": k, "Value": val_str, "Unit": "", "Description": ""})
            st.table(param_rows)

    years = result["years"]
    chart_data = {
        "Baseline (tCO2e)": [y["baseline_emissions"] for y in years],
        "Project (tCO2e)": [y["project_emissions"] for y in years],
        "Net ER (tCO2e)": [y["net_er"] for y in years],
    }
    st.bar_chart(data=chart_data, use_container_width=True)

    with st.expander("Year-by-Year Details (with formulas)"):
        for y in years:
            yr_label = f"Year {y['year_number']} ({y['calendar_year']})"
            st.markdown(f"**{yr_label}**")
            details = []
            details.append(f"Usage Rate = {y.get('usage_rate', 0):.2%}")
            details.append(f"Active HH = {y.get('active_households', 0):,.0f}")
            if y.get("baseline_formula"):
                details.append(f"BE_y = {y['baseline_formula']} = {y['baseline_emissions']:,.2f} tCO2e")
            else:
                details.append(f"BE_y = {y['baseline_emissions']:,.2f} tCO2e")
            if y.get("project_formula"):
                details.append(f"PE_y = {y['project_formula']} = {y['project_emissions']:,.2f} tCO2e")
            else:
                details.append(f"PE_y = {y['project_emissions']:,.2f} tCO2e")
            details.append(f"Gross ER = {y.get('gross_er', 0):,.2f} tCO2e")
            if y.get("leakage_formula"):
                details.append(f"LE_y = {y['leakage_formula']} = {y['leakage']:,.2f} tCO2e")
            if y.get("net_er_formula"):
                details.append(f"Net ER_y = {y['net_er_formula']} = {y['net_er']:,.2f} tCO2e")
            else:
                details.append(f"Net ER_y = {y['net_er']:,.2f} tCO2e")
            st.code("\n".join(details), language=None)

        st.markdown("**TOTALS**")
        st.code(
            f"Total Baseline Emissions = {summary.get('total_baseline', 0):,.2f} tCO2e\n"
            f"Total Project Emissions  = {summary.get('total_project', 0):,.2f} tCO2e\n"
            f"Total Leakage            = {summary.get('total_leakage', 0):,.2f} tCO2e\n"
            f"Total Net ER             = {summary['total_er']:,.2f} tCO2e\n"
            f"Average Annual ER        = {summary['average_annual_er']:,.2f} tCO2e/yr",
            language=None,
        )


def _render_saved_scenarios(project_id):
    scenarios = get_scenarios(project_id)
    if not scenarios:
        st.info("No saved scenarios yet. Use the Live Simulator to create and save scenarios.")
        return

    for s in scenarios:
        baseline_tag = " [BASELINE]" if s.get("is_baseline") else ""
        with st.expander(f"{s['name']}{baseline_tag} -- {s.get('calculated_at', '')}"[:80]):
            detail = get_scenario_detail(s["id"])
            if detail:
                summary = detail["scenario"].get("results_summary", {})
                if isinstance(summary, str):
                    import json
                    try:
                        summary = json.loads(summary)
                    except Exception:
                        summary = {}

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total ER", f"{summary.get('total_er', 0):,.0f} tCO2e")
                with col2:
                    st.metric("Annual ER", f"{summary.get('average_annual_er', 0):,.0f} tCO2e/yr")
                with col3:
                    if s.get("carbon_price_usd"):
                        st.metric("Carbon Price", f"${s['carbon_price_usd']:,.2f}")

                if detail["years"]:
                    er_data = {
                        "Year": [y["calendar_year"] for y in detail["years"]],
                        "Net ER": [float(y["net_er"]) for y in detail["years"]],
                    }
                    st.bar_chart(data={"Net ER": er_data["Net ER"]}, use_container_width=True)

            if st.button("Delete", key=f"del_scenario_{s['id']}"):
                delete_scenario(s["id"])
                st.success("Scenario deleted")
                st.rerun()


def _render_sensitivity(project_id, methodology):
    st.markdown("**Vary a single parameter to see its impact on emission reductions**")

    if methodology in ("VM0050", "TPDDTEC"):
        param_options = ["fNRB", "usage_rate", "num_households", "leakage_discount", "baseline_fuel_consumption", "SFC_baseline"]
    else:
        param_options = ["EG_PJ_y", "EF_grid"]

    col1, col2 = st.columns(2)
    with col1:
        selected_param = st.selectbox("Parameter to Vary", param_options, key="sens_param")
    with col2:
        variation = st.slider("Variation (%)", 5, 50, 20, 5, key="sens_var")

    if st.button("Run Sensitivity Analysis", key="run_sens", type="primary"):
        with st.spinner("Running sensitivity analysis..."):
            result = run_sensitivity(project_id, selected_param, variation_pct=variation)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state[f"sens_result_{project_id}"] = result

    sens_result = st.session_state.get(f"sens_result_{project_id}")
    if sens_result:
        st.markdown(f"**Parameter: {sens_result['param_key']}** (Base: {sens_result['base_value']:.4f})")

        results = sens_result["results"]
        chart_data = {
            "Change (%)": [r["pct_change"] for r in results],
            "Total ER (tCO2e)": [r["total_er"] for r in results],
        }

        st.line_chart(data={"Total ER (tCO2e)": chart_data["Total ER (tCO2e)"]}, use_container_width=True)

        base_er = sens_result["base_er"]
        if base_er > 0:
            min_er = min(r["total_er"] for r in results)
            max_er = max(r["total_er"] for r in results)
            range_pct = (max_er - min_er) / base_er * 100
            st.caption(f"ER range: {min_er:,.0f} to {max_er:,.0f} tCO2e ({range_pct:.1f}% variation)")


def _render_finance(project_id, methodology):
    st.markdown("**Carbon Finance Projections**")

    col1, col2, col3 = st.columns(3)
    with col1:
        carbon_price = st.number_input("Carbon Price ($/tCO2e)", min_value=0.0, value=10.0, step=0.5, key="fin_price")
        price_escalation = st.number_input("Annual Price Escalation (%)", min_value=0.0, value=2.0, step=0.5, key="fin_esc")
    with col2:
        developer_share = st.number_input("Developer Share (%)", min_value=0.0, max_value=100.0, value=80.0, step=5.0, key="fin_dev")
        buffer_pool = st.number_input("Buffer Pool (%)", min_value=0.0, max_value=30.0, value=5.0, step=1.0, key="fin_buf")
    with col3:
        admin_fee = st.number_input("Admin/Registry Fee (%)", min_value=0.0, max_value=20.0, value=2.0, step=0.5, key="fin_admin")

    if st.button("Calculate Finance", key="run_finance", type="primary"):
        with st.spinner("Calculating financial projections..."):
            result = run_scenario(project_id)
            if "error" in result:
                st.error(result["error"])
            else:
                from carbongpt.core.er_simulator import _add_finance
                _add_finance(result, carbon_price, price_escalation, developer_share, buffer_pool, admin_fee)
                st.session_state[f"fin_result_{project_id}"] = result

    fin_result = st.session_state.get(f"fin_result_{project_id}")
    if fin_result:
        _render_er_results(fin_result)

        st.markdown("---")
        scenario_name = st.text_input("Save as Finance Scenario", placeholder="e.g. Conservative $10", key="fin_save_name")
        if st.button("Save Finance Scenario", key="save_fin"):
            if scenario_name:
                saved = save_scenario(
                    project_id, scenario_name,
                    carbon_price=carbon_price,
                    price_escalation=price_escalation,
                    developer_share=developer_share,
                    buffer_pool=buffer_pool,
                    admin_fee=admin_fee,
                )
                if "error" not in saved:
                    st.success(f"Finance scenario saved (ID: {saved['scenario_id']})")


def _safe_float(params, key, default):
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


def _safe_text(params, key, default=""):
    if key in params:
        v = params[key]
        if isinstance(v, dict):
            v = v.get("value")
        if v is not None:
            return str(v)
    return default
