import streamlit as st
from carbongpt.core.er_simulator import (
    run_scenario,
    save_scenario,
    get_scenarios,
    get_scenario_detail,
    delete_scenario,
    run_sensitivity,
)
from carbongpt.core.parameter_engine import get_parameters_as_dict, get_project_parameters


def render_er_simulator(project):
    project_id = project["id"]
    methodology = (project.get("methodology") or "").upper().replace("GS-", "")

    st.subheader("Emission Reduction Scenario Simulator")

    if methodology not in ("VM0050", "TPDDTEC", "ACM0002", "AMS-I.D.", "AMSID"):
        st.warning(f"ER simulation is not yet available for methodology: {methodology}")
        return

    sim_tabs = st.tabs(["Live Simulator", "Saved Scenarios", "Sensitivity Analysis", "Carbon Finance"])

    with sim_tabs[0]:
        _render_live_simulator(project_id, methodology)

    with sim_tabs[1]:
        _render_saved_scenarios(project_id)

    with sim_tabs[2]:
        _render_sensitivity(project_id, methodology)

    with sim_tabs[3]:
        _render_finance(project_id, methodology)


def _render_live_simulator(project_id, methodology):
    st.markdown("**Adjust parameters to see emission reduction projections**")

    params = get_parameters_as_dict(project_id)
    if not params:
        st.info("Initialize parameters in the Parameters tab first.")
        return

    overrides = {}
    if methodology in ("VM0050", "TPDDTEC"):
        col1, col2 = st.columns(2)
        with col1:
            fNRB = st.slider("fNRB", 0.0, 1.0, _safe_float(params, "fNRB", 0.30), 0.01, key="sim_fNRB")
            overrides["fNRB"] = fNRB
            usage = st.slider("Usage Rate", 0.0, 1.0, _safe_float(params, "usage_rate", 0.90), 0.01, key="sim_usage")
            overrides["usage_rate"] = usage
            hh = st.number_input("Number of Households", min_value=1, value=int(_safe_float(params, "num_households", 1000)), step=100, key="sim_hh")
            overrides["num_households"] = hh

        with col2:
            if methodology == "VM0050":
                bl_cons = st.number_input("Baseline Fuel (t/hh/yr)", min_value=0.01, value=_safe_float(params, "baseline_fuel_consumption", 2.0), step=0.1, key="sim_bl_cons")
                overrides["baseline_fuel_consumption"] = bl_cons
                pj_cons = st.number_input("Project Fuel (t/hh/yr)", min_value=0.0, value=_safe_float(params, "project_fuel_consumption", 1.0), step=0.1, key="sim_pj_cons")
                overrides["project_fuel_consumption"] = pj_cons
            else:
                sfc_b = st.number_input("Baseline SFC (kg/person/yr)", min_value=0.0, value=_safe_float(params, "SFC_baseline", 400.0), step=10.0, key="sim_sfc_b")
                overrides["SFC_baseline"] = sfc_b
                sfc_p = st.number_input("Project SFC (kg/person/yr)", min_value=0.0, value=_safe_float(params, "SFC_project", 200.0), step=10.0, key="sim_sfc_p")
                overrides["SFC_project"] = sfc_p
            leakage = st.slider("Leakage Discount", 0.80, 1.0, _safe_float(params, "leakage_discount", 0.95), 0.01, key="sim_leak")
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
        _render_er_results(result)

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


def _render_er_results(result):
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

    years = result["years"]
    chart_data = {
        "Year": [y["calendar_year"] for y in years],
        "Baseline (tCO2e)": [y["baseline_emissions"] for y in years],
        "Project (tCO2e)": [y["project_emissions"] for y in years],
        "Net ER (tCO2e)": [y["net_er"] for y in years],
    }

    st.bar_chart(
        data={k: v for k, v in chart_data.items() if k != "Year"},
        use_container_width=True,
    )

    with st.expander("Year-by-Year Details"):
        table_rows = []
        for y in years:
            row = {
                "Year": y["calendar_year"],
                "Baseline (tCO2e)": f"{y['baseline_emissions']:,.1f}",
                "Project (tCO2e)": f"{y['project_emissions']:,.1f}",
                "Leakage (tCO2e)": f"{y['leakage']:,.1f}",
                "Net ER (tCO2e)": f"{y['net_er']:,.1f}",
            }
            if "usage_rate" in y:
                row["Usage Rate"] = f"{y['usage_rate']:.1%}"
            if "gross_revenue" in y and y["gross_revenue"] > 0:
                row["Revenue ($)"] = f"${y['gross_revenue']:,.0f}"
            table_rows.append(row)
        st.table(table_rows)

    params_used = result.get("parameters_used")
    if params_used:
        with st.expander("Parameters Used in Calculation"):
            param_rows = []
            for k, v in params_used.items():
                if isinstance(v, bool):
                    display = "Yes" if v else "No"
                elif isinstance(v, float):
                    display = f"{v:g}"
                else:
                    display = str(v)
                param_rows.append({"Parameter": k, "Value Used": display})
            st.table(param_rows)


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
