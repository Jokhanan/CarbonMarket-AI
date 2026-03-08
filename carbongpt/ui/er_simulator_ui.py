import streamlit as st
import pandas as pd
from carbongpt.core.er_simulator import (
    run_scenario,
    save_scenario,
    get_scenarios,
    get_scenario_detail,
    delete_scenario,
    run_sensitivity,
    export_er_to_excel,
    select_scenario_for_drafting,
    deselect_scenario,
    update_scenario_purpose,
    get_selected_scenario,
    compare_scenarios,
    VALID_SCENARIO_PURPOSES,
)
from carbongpt.core.parameter_engine import (
    get_parameters_as_dict,
    get_project_parameters,
    FUEL_CANONICAL_OPTIONS,
    FUEL_DISPLAY_LABELS,
    get_fuel_display_label,
)


def render_er_simulator(project):
    project_id = project["id"]
    project_name = project.get("project_name") or project.get("name") or f"Project {project_id}"
    methodology = (project.get("methodology") or "").upper().replace("GS-", "")

    _er_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>'
    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-green">{_er_icon}</span>
        <span class="section-header-text">Emission Reduction Scenario Simulator</span>
    </span>
    """, unsafe_allow_html=True)

    if methodology not in ("VM0050", "TPDDTEC", "ACM0002", "AMS-I.D.", "AMSID"):
        st.warning(f"ER simulation is not yet available for methodology: {methodology}")
        return

    all_params = get_project_parameters(project_id)
    pending_count = sum(1 for p in all_params if p.get("value") is None)
    if not all_params:
        st.markdown(
            '<span class="readiness-banner readiness-banner-warning">'
            '<span class="readiness-banner-icon">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>'
            '</span>'
            'Parameters not yet initialized. Go to the Parameters tab first to set up your project inputs.'
            '</span>',
            unsafe_allow_html=True,
        )
    elif pending_count > 0:
        st.markdown(
            f'<span class="readiness-banner readiness-banner-warning">'
            f'<span class="readiness-banner-icon">'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>'
            f'</span>'
            f'{pending_count} parameter{"s" if pending_count != 1 else ""} still missing values. The simulator will use defaults, but results may be less accurate.'
            f'</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span class="readiness-banner readiness-banner-ready">'
            f'<span class="readiness-banner-icon">'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>'
            f'</span>'
            f'All {len(all_params)} parameters configured. Simulation results will reflect your project data.'
            f'</span>',
            unsafe_allow_html=True,
        )

    sim_tabs = st.tabs(["Live Simulator", "Saved Scenarios", "Compare", "Sensitivity Analysis", "Carbon Finance"])

    with sim_tabs[0]:
        _render_live_simulator(project_id, methodology, project_name)

    with sim_tabs[1]:
        _render_saved_scenarios(project_id)

    with sim_tabs[2]:
        _render_scenario_comparison(project_id)

    with sim_tabs[3]:
        _render_sensitivity(project_id, methodology)

    with sim_tabs[4]:
        _render_finance(project_id, methodology)


def _render_param_value_display(label, value, unit, param_status, source_type):
    status_icons = {
        "confirmed": '<span style="color:green;font-weight:bold;">OK</span>',
        "default": '<span style="color:gray;">DEF</span>',
        "estimated": '<span style="color:orange;">EST</span>',
        "missing": '<span style="color:red;">--</span>',
    }
    icon = status_icons.get(param_status, '<span style="color:gray;">--</span>')
    if isinstance(value, float):
        val_str = f"{value:g}"
    elif value is not None:
        val_str = str(value)
    else:
        val_str = "(not set)"
    unit_str = f" {unit}" if unit else ""
    st.markdown(
        f'{icon} **{label}**: {val_str}{unit_str} <span style="color:gray;font-size:0.85em;">({source_type})</span>',
        unsafe_allow_html=True,
    )


def _render_live_simulator(project_id, methodology, project_name="Project"):
    st.markdown("**Project parameter values are shown below. Enable overrides to adjust for this scenario.**")

    params = get_parameters_as_dict(project_id)
    if not params:
        st.info("Initialize parameters in the Parameters tab first.")
        return

    overrides = {}
    deployment_config = {}

    is_cookstove = methodology in ("VM0050", "TPDDTEC")

    if is_cookstove:
        sim_mode = st.radio(
            "Simulation mode",
            ["Simple", "Advanced"],
            horizontal=True,
            key=f"sim_mode_{project_id}",
            help="Simple: basic deployment settings. Advanced: custom schedules, curves, and timing.",
        )
        is_advanced = sim_mode == "Advanced"

        with st.container(border=True):
            st.markdown("**Project Values** (from Parameters tab)")

            pv_col1, pv_col2, pv_col3 = st.columns(3)
            with pv_col1:
                _render_param_value_display("Devices", _safe_float(params, "num_devices", None), "", _safe_status(params, "num_devices"), _safe_source(params, "num_devices"))
                _render_param_value_display("Households", _safe_float(params, "num_households", None), "", _safe_status(params, "num_households"), _safe_source(params, "num_households"))
                _render_param_value_display("HH Size", _safe_float(params, "household_size", None), "persons", _safe_status(params, "household_size"), _safe_source(params, "household_size"))
            with pv_col2:
                _render_param_value_display("fNRB", _safe_float(params, "fNRB", None), "", _safe_status(params, "fNRB"), _safe_source(params, "fNRB"))
                _render_param_value_display("NCV bl", _safe_float(params, "NCV_baseline", None), "TJ/Gg", _safe_status(params, "NCV_baseline"), _safe_source(params, "NCV_baseline"))
                _render_param_value_display("EF CO2 bl", _safe_float(params, "EF_CO2_baseline", None), "tCO2/TJ", _safe_status(params, "EF_CO2_baseline"), _safe_source(params, "EF_CO2_baseline"))
            with pv_col3:
                fuel_val = _safe_text(params, "baseline_fuel", "wood")
                _render_param_value_display("Fuel", get_fuel_display_label(fuel_val), "", _safe_status(params, "baseline_fuel"), _safe_source(params, "baseline_fuel"))
                _render_param_value_display("Leakage", _safe_float(params, "leakage_discount", None), "", _safe_status(params, "leakage_discount"), _safe_source(params, "leakage_discount"))
                _render_param_value_display("Usage", _safe_float(params, "usage_rate", None), "", _safe_status(params, "usage_rate"), _safe_source(params, "usage_rate"))

        enable_overrides = st.checkbox("Override parameter values for this scenario", key=f"sim_override_toggle_{project_id}")

        if enable_overrides:
            st.markdown("**Scenario Overrides** (these values apply to this scenario only)")
            col1, col2 = st.columns(2)
            with col1:
                hh = st.number_input("Devices to Deploy", min_value=1, value=int(_safe_float(params, "num_devices", _safe_float(params, "num_households", 1000))), step=100, key="sim_hh")
                overrides["num_devices"] = hh
                overrides["num_households"] = hh
                hh_size = st.number_input("Household Size (persons)", min_value=1.0, value=_safe_float(params, "household_size", 5.0), step=0.5, key="sim_hh_size")
                overrides["household_size"] = hh_size
            with col2:
                fuel_options = [f for f in FUEL_CANONICAL_OPTIONS if f not in ("other",)]
                current_fuel = _safe_text(params, "baseline_fuel", "wood")
                fuel_idx = fuel_options.index(current_fuel) if current_fuel in fuel_options else 0
                baseline_fuel = st.selectbox("Baseline Fuel", fuel_options, index=fuel_idx, key="sim_bl_fuel", format_func=get_fuel_display_label)
                overrides["baseline_fuel"] = baseline_fuel

            st.markdown("**Fuel Consumption**")
            fc_col1, fc_col2 = st.columns(2)
            with fc_col1:
                if methodology == "VM0050":
                    bl_cons = st.number_input("Baseline Fuel (t/hh/yr)", min_value=0.01, value=_safe_float(params, "baseline_fuel_consumption", 2.0), step=0.1, key="sim_bl_cons")
                    overrides["baseline_fuel_consumption"] = bl_cons
                else:
                    sfc_b = st.number_input("Baseline SFC (kg/person/yr)", min_value=0.0, value=_safe_float(params, "SFC_baseline", 400.0), step=10.0, key="sim_sfc_b")
                    overrides["SFC_baseline"] = sfc_b
            with fc_col2:
                if methodology == "VM0050":
                    pj_cons = st.number_input("Project Fuel (t/hh/yr)", min_value=0.0, value=_safe_float(params, "project_fuel_consumption", 1.0), step=0.1, key="sim_pj_cons")
                    overrides["project_fuel_consumption"] = pj_cons
                else:
                    sfc_p = st.number_input("Project SFC (kg/person/yr)", min_value=0.0, value=_safe_float(params, "SFC_project", 200.0), step=10.0, key="sim_sfc_p")
                    overrides["SFC_project"] = sfc_p

            st.markdown("**Emission Factors & Fuel Properties**")
            ef_col1, ef_col2 = st.columns(2)
            with ef_col1:
                fNRB = st.slider("fNRB", 0.0, 1.0, _safe_float(params, "fNRB", 0.30), 0.01, key="sim_fNRB")
                overrides["fNRB"] = fNRB
                ncv_b = st.number_input("NCV Baseline (TJ/Gg)", min_value=1.0, value=_safe_float(params, "NCV_baseline", 15.6), step=0.1, key="sim_ncv_b")
                overrides["NCV_baseline"] = ncv_b
                ef_co2_b = st.number_input("EF CO2 Baseline (tCO2/TJ)", min_value=0.0, value=_safe_float(params, "EF_CO2_baseline", 112.0), step=1.0, key="sim_ef_co2_b")
                overrides["EF_CO2_baseline"] = ef_co2_b
                ef_nco2_b = st.number_input("EF non-CO2 Baseline (tCO2e/TJ)", min_value=0.0, value=_safe_float(params, "EF_nonCO2_baseline", 9.46), step=0.1, key="sim_ef_nco2_b")
                overrides["EF_nonCO2_baseline"] = ef_nco2_b
            with ef_col2:
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

        st.markdown("**Deployment Ramp-up**")
        deploy_hh = int(_safe_float(params, "num_devices", _safe_float(params, "num_households", 1000)))
        if "num_devices" in overrides:
            deploy_hh = int(overrides["num_devices"])
        deploy_options = ["Instant deployment", "Fixed monthly deployment"]
        if is_advanced:
            deploy_options.append("Custom deployment schedule")
        deploy_choice = st.radio("How are technologies deployed?", deploy_options, horizontal=True, key=f"sim_deploy_mode_{project_id}")

        if deploy_choice == "Instant deployment":
            deployment_config["deployment_mode"] = "instant"
        elif deploy_choice == "Fixed monthly deployment":
            deployment_config["deployment_mode"] = "fixed_monthly"
            monthly_rate = st.number_input(
                "Units deployed per month", min_value=1,
                value=min(500, deploy_hh),
                step=100, key="sim_monthly_deploy",
            )
            deployment_config["monthly_deployment"] = monthly_rate
            months_needed = (deploy_hh + monthly_rate - 1) // monthly_rate
            st.caption(f"Full deployment in approximately {months_needed} months ({months_needed / 12:.1f} years)")
        elif deploy_choice == "Custom deployment schedule":
            deployment_config["deployment_mode"] = "custom"
            st.caption("Define deployment batches by month (month 0 = start of crediting period)")
            custom_df = st.data_editor(
                pd.DataFrame({"Month": [0, 6, 12], "Units": [200, 400, 400]}),
                num_rows="dynamic",
                key=f"sim_custom_schedule_{project_id}",
            )
            schedule = []
            for _, row in custom_df.iterrows():
                m = int(row.get("Month", 0))
                c = int(row.get("Units", 0))
                if c > 0:
                    schedule.append({"month": m, "count": c})
            deployment_config["custom_schedule"] = schedule
            total_custom = sum(s["count"] for s in schedule)
            st.caption(f"Total scheduled: {total_custom:,} units")

        st.markdown("**Technology Lifetime & Drop-off**")
        lt_col1, lt_col2 = st.columns(2)
        with lt_col1:
            lifetime = st.number_input("Technology Lifetime (years)", min_value=1.0, max_value=30.0, value=5.0, step=1.0, key="sim_lifetime")
            deployment_config["tech_lifetime_years"] = lifetime
        with lt_col2:
            if not is_advanced:
                dropoff = st.slider("Annual Drop-off Rate", 0.0, 0.50, 0.10, 0.01, key="sim_dropoff", help="Fraction of units that stop working each year")
                deployment_config["dropoff_mode"] = "annual_rate"
                deployment_config["annual_dropoff_rate"] = dropoff
            else:
                dropoff_mode = st.radio("Drop-off model", ["Annual rate", "Custom curve"], horizontal=True, key=f"sim_dropoff_mode_{project_id}")
                if dropoff_mode == "Annual rate":
                    dropoff = st.slider("Annual Drop-off Rate", 0.0, 0.50, 0.10, 0.01, key="sim_dropoff_adv")
                    deployment_config["dropoff_mode"] = "annual_rate"
                    deployment_config["annual_dropoff_rate"] = dropoff
                else:
                    deployment_config["dropoff_mode"] = "custom_curve"
                    st.caption("Define survival fraction by technology age (year)")
                    dropoff_df = st.data_editor(
                        pd.DataFrame({"Year": [1, 2, 3, 4, 5], "Survival Fraction": [0.95, 0.88, 0.80, 0.70, 0.55]}),
                        num_rows="dynamic",
                        key=f"sim_dropoff_curve_{project_id}",
                    )
                    curve = []
                    for _, row in dropoff_df.iterrows():
                        curve.append({"year": float(row.get("Year", 0)), "survival_fraction": float(row.get("Survival Fraction", 1.0))})
                    deployment_config["custom_dropoff_curve"] = curve

        st.markdown("**Usage Rate**")
        if not is_advanced:
            usage = st.slider("Usage Rate", 0.0, 1.0, _safe_float(params, "usage_rate", 0.90), 0.01, key="sim_usage", help="Fraction of surviving units actually being used")
            deployment_config["usage_rate_mode"] = "fixed"
            deployment_config["usage_rate"] = usage
        else:
            usage_mode = st.radio("Usage model", ["Fixed rate", "Custom curve"], horizontal=True, key=f"sim_usage_mode_{project_id}")
            if usage_mode == "Fixed rate":
                usage = st.slider("Usage Rate", 0.0, 1.0, _safe_float(params, "usage_rate", 0.90), 0.01, key="sim_usage_adv")
                deployment_config["usage_rate_mode"] = "fixed"
                deployment_config["usage_rate"] = usage
            else:
                deployment_config["usage_rate_mode"] = "curve"
                st.caption("Define usage rate by technology age (year)")
                usage_df = st.data_editor(
                    pd.DataFrame({"Year": [1, 2, 3, 4, 5], "Usage Rate": [0.95, 0.90, 0.85, 0.78, 0.70]}),
                    num_rows="dynamic",
                    key=f"sim_usage_curve_{project_id}",
                )
                ucurve = []
                for _, row in usage_df.iterrows():
                    ucurve.append({"year": float(row.get("Year", 0)), "rate": float(row.get("Usage Rate", 0.9))})
                deployment_config["usage_curve"] = ucurve

        if is_advanced:
            st.markdown("**Deployment Timing**")
            timing = st.radio(
                "When within a period are newly deployed units active?",
                ["Start of period", "Mid-period (default)", "End of period"],
                index=1, horizontal=True,
                key=f"sim_timing_{project_id}",
            )
            timing_map = {"Start of period": "start", "Mid-period (default)": "mid", "End of period": "end"}
            deployment_config["deployment_timing"] = timing_map.get(timing, "mid")

    elif methodology in ("ACM0002", "AMS-I.D.", "AMSID"):
        with st.container(border=True):
            st.markdown("**Project Values** (from Parameters tab)")
            _render_param_value_display("Net Generation", _safe_float(params, "EG_PJ_y", None), "MWh/yr", _safe_status(params, "EG_PJ_y"), _safe_source(params, "EG_PJ_y"))
            _render_param_value_display("Grid EF", _safe_float(params, "EF_grid", None), "tCO2/MWh", _safe_status(params, "EF_grid"), _safe_source(params, "EF_grid"))

        enable_overrides = st.checkbox("Override parameter values for this scenario", key=f"sim_override_toggle_grid_{project_id}")
        if enable_overrides:
            col1, col2 = st.columns(2)
            with col1:
                eg = st.number_input("Net Generation (MWh/yr)", min_value=0, value=int(_safe_float(params, "EG_PJ_y", 50000)), step=1000, key="sim_eg")
                overrides["EG_PJ_y"] = eg
            with col2:
                ef = st.number_input("Grid EF (tCO2/MWh)", min_value=0.0, value=_safe_float(params, "EF_grid", 0.8), step=0.01, key="sim_ef")
                overrides["EF_grid"] = ef

    if st.button("Calculate", key="run_sim", type="primary"):
        with st.spinner("Calculating emission reductions..."):
            result = run_scenario(project_id, parameter_overrides=overrides,
                                 deployment_config=deployment_config if deployment_config else None)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state[f"sim_result_{project_id}"] = result
                st.session_state[f"sim_overrides_{project_id}"] = overrides
                st.session_state[f"sim_deploy_config_{project_id}"] = deployment_config

    result = st.session_state.get(f"sim_result_{project_id}")
    if result:
        _render_er_results(result, project_name=project_name)

        if result.get("deployment_timeline"):
            _render_deployment_charts(result)

        st.markdown("---")
        save_col1, save_col2, save_col3 = st.columns([2, 1, 1])
        with save_col1:
            scenario_name = st.text_input("Scenario Name", value="", placeholder="e.g. Base Case, Optimistic", key="save_name")
        with save_col2:
            purpose_labels = {
                "exploratory": "Exploratory",
                "comparison": "Comparison",
                "shortlisted": "Shortlisted",
                "selected_for_drafting": "Select for PDD",
            }
            purpose_options = list(purpose_labels.keys())
            purpose_display = list(purpose_labels.values())
            purpose_idx = st.selectbox(
                "Scenario Purpose",
                range(len(purpose_options)),
                format_func=lambda i: purpose_display[i],
                key="save_purpose",
            )
            selected_purpose = purpose_options[purpose_idx]
        with save_col3:
            is_baseline = st.checkbox("Set as baseline scenario", key="save_baseline")

        if st.button("Save Scenario", key="save_scenario"):
            if not scenario_name:
                st.warning("Enter a name for the scenario")
            else:
                saved = save_scenario(
                    project_id, scenario_name,
                    parameter_overrides=st.session_state.get(f"sim_overrides_{project_id}", {}),
                    is_baseline=is_baseline,
                    deployment_config=st.session_state.get(f"sim_deploy_config_{project_id}"),
                    scenario_purpose=selected_purpose,
                )
                if "error" in saved:
                    st.error(saved["error"])
                else:
                    purpose_label = purpose_labels.get(saved.get("scenario_purpose", ""), "")
                    st.success(f"Scenario '{scenario_name}' saved ({purpose_label})")

        st.markdown("---")
        st.markdown(
            '<span class="readiness-banner readiness-banner-info">'
            '<span class="readiness-banner-icon">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>'
            '</span>'
            'Next: Use these results when drafting your PDD (Write / Draft tab) or run an Audit Simulation to check project readiness.'
            '</span>',
            unsafe_allow_html=True,
        )


def _render_deployment_charts(result):
    timeline = result.get("deployment_timeline", [])
    if not timeline:
        return

    with st.expander("Deployment & Technology Dynamics", expanded=True):
        years_labels = [str(t["year"]) for t in timeline]

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**Deployment Ramp-up**")
            deploy_df = pd.DataFrame({
                "Year": years_labels,
                "Deployed (year)": [t["deployed"] for t in timeline],
                "Cumulative Deployed": [t["cumulative_deployed"] for t in timeline],
            }).set_index("Year")
            st.bar_chart(deploy_df[["Deployed (year)"]], use_container_width=True)

        with chart_col2:
            st.markdown("**Active vs Surviving Technologies**")
            active_df = pd.DataFrame({
                "Year": years_labels,
                "Active": [t["active"] for t in timeline],
                "Surviving": [t["surviving"] for t in timeline],
                "Effectively Used": [t["effectively_used"] for t in timeline],
            }).set_index("Year")
            st.line_chart(active_df, use_container_width=True)

        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            st.markdown("**Annual Emission Reductions**")
            er_df = pd.DataFrame({
                "Year": years_labels,
                "Net ER (tCO2e)": [t["net_er"] for t in timeline],
            }).set_index("Year")
            st.bar_chart(er_df, use_container_width=True)

        with chart_col4:
            st.markdown("**Cumulative Emission Reductions**")
            cum_df = pd.DataFrame({
                "Year": years_labels,
                "Cumulative ER (tCO2e)": [t["cumulative_er"] for t in timeline],
            }).set_index("Year")
            st.area_chart(cum_df, use_container_width=True)

        st.markdown("**Year-by-Year Deployment Summary**")
        summary_data = []
        for t in timeline:
            summary_data.append({
                "Year": t["year"],
                "Deployed": int(t["deployed"]),
                "Cumulative": int(t["cumulative_deployed"]),
                "Active": int(t["active"]),
                "Surviving": int(t["surviving"]),
                "Effectively Used": int(t["effectively_used"]),
                "Net ER (tCO2e)": f"{t['net_er']:,.0f}",
                "Cumulative ER": f"{t['cumulative_er']:,.0f}",
            })
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)


def _render_er_results(result, project_name="Project"):
    summary = result["summary"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total ER", f"{summary['total_er']:,.0f} tCO2e")
    with col2:
        st.metric("Average Annual ER", f"{summary['average_annual_er']:,.0f} tCO2e/yr")
    with col3:
        st.metric("Crediting Period", f"{summary['crediting_years']} years")

    if summary.get("deployment_mode") and summary["deployment_mode"] != "instant":
        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("Peak Active Units", f"{summary.get('peak_active_units', 0):,.0f}")
        with col5:
            st.metric("Peak Surviving", f"{summary.get('peak_surviving_units', 0):,.0f}")
        with col6:
            st.metric("Tech Lifetime", f"{summary.get('tech_lifetime_years', 0)} years")

    if "total_net_revenue" in summary:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            st.metric("Gross Revenue", f"${summary.get('total_gross_revenue', 0):,.0f}")
        with col_f2:
            st.metric("Net Revenue", f"${summary.get('total_net_revenue', 0):,.0f}")
        with col_f3:
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

    with st.expander("Year-by-Year Details"):
        year_detail_rows = []
        for y in years:
            row = {
                "Year": f"{y['year_number']} ({y['calendar_year']})",
                "Baseline (tCO2e)": f"{y['baseline_emissions']:,.2f}",
                "Project (tCO2e)": f"{y['project_emissions']:,.2f}",
                "Gross ER": f"{y.get('gross_er', 0):,.2f}",
                "Leakage": f"{y['leakage']:,.2f}",
                "Net ER": f"{y['net_er']:,.2f}",
            }
            if "active_units" in y:
                row["Active Units"] = f"{y['active_units']:,.0f}"
                row["Surviving"] = f"{y['surviving_units']:,.0f}"
                row["Eff. Used"] = f"{y['effectively_used']:,.0f}"
            if "usage_rate" in y:
                row["Usage Rate"] = f"{y['usage_rate']:.2%}"
            year_detail_rows.append(row)
        st.dataframe(pd.DataFrame(year_detail_rows), use_container_width=True, hide_index=True)

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

    purpose_labels = {
        "exploratory": "Exploratory",
        "comparison": "Comparison",
        "shortlisted": "Shortlisted",
        "selected_for_drafting": "SELECTED FOR PDD",
        "archived": "Archived",
    }

    show_archived = st.checkbox("Show archived scenarios", key="show_archived_scenarios", value=False)
    visible = [s for s in scenarios if show_archived or s.get("scenario_purpose") != "archived"]
    archived_count = sum(1 for s in scenarios if s.get("scenario_purpose") == "archived")
    if archived_count > 0 and not show_archived:
        st.caption(f"{archived_count} archived scenario(s) hidden")

    for s in visible:
        purpose = s.get("scenario_purpose", "exploratory")
        purpose_label = purpose_labels.get(purpose, purpose)
        baseline_tag = " [BASELINE]" if s.get("is_baseline") else ""
        is_selected = purpose == "selected_for_drafting"

        label_prefix = "[SELECTED] " if is_selected else ""
        with st.expander(f"{label_prefix}{s['name']}{baseline_tag} -- {purpose_label}"[:90], expanded=is_selected):
            detail = get_scenario_detail(s["id"])
            if detail:
                summary = detail["scenario"].get("results_summary", {})
                if isinstance(summary, str):
                    import json
                    try:
                        summary = json.loads(summary)
                    except Exception:
                        summary = {}

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total ER", f"{summary.get('total_er', 0):,.0f} tCO2e")
                with col2:
                    st.metric("Annual ER", f"{summary.get('average_annual_er', 0):,.0f} tCO2e/yr")
                with col3:
                    if s.get("carbon_price_usd"):
                        st.metric("Carbon Price", f"${s['carbon_price_usd']:,.2f}")
                with col4:
                    st.metric("Purpose", purpose_label)

                if detail["years"]:
                    er_data = {
                        "Year": [y["calendar_year"] for y in detail["years"]],
                        "Net ER": [float(y["net_er"]) for y in detail["years"]],
                    }
                    st.bar_chart(data={"Net ER": er_data["Net ER"]}, use_container_width=True)

            action_cols = st.columns(4)
            with action_cols[0]:
                if is_selected:
                    if st.button("Deselect", key=f"deselect_{s['id']}"):
                        deselect_scenario(project_id)
                        st.success(f"'{s['name']}' deselected")
                        st.rerun()
                else:
                    if st.button("Select for PDD", key=f"select_{s['id']}"):
                        result = select_scenario_for_drafting(project_id, s["id"])
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.success(f"'{s['name']}' is now the selected scenario for PDD drafting")
                            st.rerun()
            with action_cols[1]:
                if purpose != "shortlisted" and not is_selected:
                    if st.button("Shortlist", key=f"shortlist_{s['id']}"):
                        update_scenario_purpose(project_id, s["id"], "shortlisted")
                        st.rerun()
            with action_cols[2]:
                if purpose != "archived":
                    if st.button("Archive", key=f"archive_{s['id']}"):
                        update_scenario_purpose(project_id, s["id"], "archived")
                        st.rerun()
            with action_cols[3]:
                if st.button("Delete", key=f"del_scenario_{s['id']}"):
                    delete_scenario(s["id"])
                    st.success("Scenario deleted")
                    st.rerun()


def _render_scenario_comparison(project_id):
    result = compare_scenarios(project_id)
    scenarios = result.get("scenarios", [])
    if len(scenarios) < 2:
        st.info("Save at least 2 scenarios to compare them.")
        return

    rows = []
    for s in scenarios:
        purpose_label = {
            "exploratory": "Exploratory",
            "comparison": "Comparison",
            "shortlisted": "Shortlisted",
            "selected_for_drafting": "SELECTED",
            "archived": "Archived",
        }.get(s.get("scenario_purpose", ""), s.get("scenario_purpose", ""))

        rows.append({
            "Scenario": s["name"],
            "Purpose": purpose_label,
            "Total ER (tCO2e)": f"{s.get('total_er', 0):,.0f}",
            "Annual ER (tCO2e/yr)": f"{s.get('average_annual_er', 0):,.0f}",
            "Years": s.get("crediting_years", 7),
            "Carbon Price": f"${s['carbon_price_usd']:,.2f}" if s.get("carbon_price_usd") else "--",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    overrides_rows = []
    all_override_keys = set()
    for s in scenarios:
        for k in (s.get("parameter_overrides") or {}).keys():
            all_override_keys.add(k)
    all_override_keys = sorted(all_override_keys)

    if all_override_keys:
        st.markdown("**Parameter Differences**")
        param_rows = []
        for s in scenarios:
            row = {"Scenario": s["name"]}
            ov = s.get("parameter_overrides") or {}
            for k in all_override_keys:
                row[k] = ov.get(k, "--")
            param_rows.append(row)
        df_params = pd.DataFrame(param_rows)
        st.dataframe(df_params, use_container_width=True, hide_index=True)


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


def _safe_status(params, key):
    if key in params:
        v = params[key]
        if isinstance(v, dict):
            return v.get("param_status", "default")
    return "default"


def _safe_source(params, key):
    if key in params:
        v = params[key]
        if isinstance(v, dict):
            return v.get("source_type", "default")
    return "default"
