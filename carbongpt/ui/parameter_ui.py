import streamlit as st
from carbongpt.core.parameter_engine import (
    initialize_project_parameters,
    get_project_parameters,
    update_parameter,
    validate_all_parameters,
    get_parameter_summary,
    confirm_parameter,
    FUEL_CANONICAL_OPTIONS,
    get_fuel_display_label,
)
from carbongpt.core.evidence_engine import get_evidence_links


def render_parameter_dashboard(project):
    project_id = project["id"]
    _param_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/></svg>'
    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-teal">{_param_icon}</span>
        <span class="section-header-text">Parameter Intelligence Dashboard</span>
    </span>
    """, unsafe_allow_html=True)

    summary = get_parameter_summary(project_id)
    if not summary or summary["total"] == 0:
        st.info("Parameters have not been initialized for this project yet.")
        if st.button("Initialize Parameters from Methodology", key="init_params"):
            with st.spinner("Initializing parameters..."):
                result = initialize_project_parameters(project_id)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"Initialized {result['inserted']} parameters for {result['methodology']}")
                    st.rerun()
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Parameters", summary["total"])
    with col2:
        confirmed = summary.get("confirmed", 0)
        st.metric("Confirmed", confirmed, delta=None if confirmed == summary["total"] else f"{summary['total'] - confirmed} remaining")
    with col3:
        st.metric("Using Defaults", summary.get("status_default", summary["defaults"]))
    with col4:
        missing = summary.get("missing", summary["pending"])
        st.metric("Missing", missing, delta=None if missing == 0 else f"{missing} need values", delta_color="inverse" if missing > 0 else "normal")

    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    with status_col1:
        st.caption(f"Confirmed: {summary.get('confirmed', 0)}")
    with status_col2:
        st.caption(f"Default: {summary.get('status_default', 0)}")
    with status_col3:
        st.caption(f"Estimated: {summary.get('estimated', 0)}")
    with status_col4:
        st.caption(f"Missing: {summary.get('missing', 0)}")

    if summary["invalid"] > 0:
        st.warning(f"{summary['invalid']} parameter(s) have invalid values. Review and fix them below.")
    if summary.get("missing", summary["pending"]) > 0:
        st.info(f"{summary.get('missing', summary['pending'])} parameter(s) are still missing values.")

    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("Validate All", key="validate_all_params"):
            result = validate_all_parameters(project_id)
            if result["issues"]:
                st.warning(f"Found {len(result['issues'])} issue(s)")
            else:
                st.success("All parameters are valid")
    with action_col2:
        if st.button("Re-initialize from Methodology", key="reinit_params", help="Resets default values but preserves any measured, user-override, or confirmed values"):
            result = initialize_project_parameters(project_id)
            if "error" in result:
                st.error(result["error"])
            else:
                preserved = result.get("preserved", 0)
                msg = f"Re-initialized {result['inserted']} parameters"
                if preserved > 0:
                    msg += f" ({preserved} user values preserved)"
                st.success(msg)
                st.rerun()

    st.markdown("---")

    categories = ["baseline", "project", "emission_factor", "fuel_property", "activity_data", "monitoring", "leakage", "calculated", "financial", "other"]
    category_names = {
        "baseline": "Baseline Parameters",
        "project": "Project Parameters",
        "emission_factor": "Emission Factors",
        "fuel_property": "Fuel Properties",
        "activity_data": "Activity Data",
        "monitoring": "Monitoring Parameters",
        "leakage": "Leakage",
        "calculated": "Calculated Values",
        "financial": "Financial",
        "other": "Other",
    }

    all_params = get_project_parameters(project_id)
    evidence = get_evidence_links(project_id, target_type="parameter")
    evidence_by_param = {}
    for e in evidence:
        evidence_by_param.setdefault(e["target_id"], []).append(e)

    pair_map = {}
    for p in all_params:
        key = p["param_key"]
        base_key = key.replace("_baseline", "").replace("_project", "")
        if key.endswith("_baseline") or key.endswith("_project"):
            pair_map.setdefault(base_key, {})[key] = p

    globally_rendered = set()

    for cat in categories:
        cat_params = [p for p in all_params if p["category"] == cat]
        displayable = [p for p in cat_params if p["param_key"] not in globally_rendered]
        if not displayable:
            continue

        with st.expander(f"{category_names.get(cat, cat)} ({len(displayable)})", expanded=(cat in ("baseline", "emission_factor"))):
            for p in displayable:
                key = p["param_key"]
                if key in globally_rendered:
                    continue
                base_key = key.replace("_baseline", "").replace("_project", "")
                pair = pair_map.get(base_key, {})
                bl = pair.get(f"{base_key}_baseline")
                pr = pair.get(f"{base_key}_project")
                if bl and pr:
                    bl_val = bl["value"] if bl["value"] is not None else ""
                    pr_val = pr["value"] if pr["value"] is not None else ""
                    same_value = str(bl_val) == str(pr_val) and bl_val != ""
                    if same_value:
                        clean_name = bl["param_name"].replace("(baseline fuel)", "").replace("(baseline)", "").strip()
                        st.markdown(f"**{clean_name}** -- Baseline and Project use the same value")
                        combined_evidence = dict(evidence_by_param)
                        pr_evidence = evidence_by_param.get(pr["param_key"], [])
                        if pr_evidence:
                            combined_evidence.setdefault(bl["param_key"], []).extend(pr_evidence)
                        _render_parameter_row(project_id, bl, combined_evidence)
                        globally_rendered.add(bl["param_key"])
                        globally_rendered.add(pr["param_key"])
                    else:
                        _render_parameter_row(project_id, p, evidence_by_param)
                        globally_rendered.add(key)
                else:
                    _render_parameter_row(project_id, p, evidence_by_param)
                    globally_rendered.add(key)


def _get_param_status_display(param):
    p_status = param.get("param_status", "default")
    status_map = {
        "confirmed": ("[OK]", "green"),
        "default": ("[DEF]", "gray"),
        "estimated": ("[EST]", "orange"),
        "missing": ("[--]", "red"),
    }
    label, color = status_map.get(p_status, ("[?]", "gray"))
    return label, color, p_status


def _render_parameter_row(project_id, param, evidence_by_param):
    param_key = param["param_key"]
    status_label, status_color, p_status = _get_param_status_display(param)

    v_status = param.get("validation_status", "pending")
    v_indicator = ""
    if v_status == "invalid":
        v_indicator = ' <span style="color:red;font-size:0.85em;">[invalid]</span>'
    elif v_status == "warning":
        v_indicator = ' <span style="color:orange;font-size:0.85em;">[warning]</span>'

    has_evidence = param_key in evidence_by_param
    evidence_indicator = " [E]" if has_evidence else ""

    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

    with col1:
        st.markdown(
            f"<span style='color:{status_color};font-weight:bold;'>{status_label}</span> "
            f"**{param['param_name']}**{v_indicator}{evidence_indicator}",
            unsafe_allow_html=True,
        )
        source_label = param.get("source_type", "default")
        source_ref = param.get("source_reference", "")
        st.caption(f"Status: {p_status} | Source: {source_label} | {source_ref}")

    with col2:
        current_val = param["value"] if param["value"] is not None else ""
        unit = param.get("unit", "")

        if param_key == "baseline_fuel":
            fuel_options = FUEL_CANONICAL_OPTIONS
            current_fuel = str(current_val) if current_val else "wood"
            fuel_idx = fuel_options.index(current_fuel) if current_fuel in fuel_options else 0
            new_val = st.selectbox(
                f"Fuel Type",
                fuel_options,
                index=fuel_idx,
                key=f"param_val_{param_key}_{param['id']}",
                label_visibility="collapsed",
                format_func=get_fuel_display_label,
            )
        else:
            new_val = st.text_input(
                f"Value ({unit})",
                value=str(current_val),
                key=f"param_val_{param_key}_{param['id']}",
                label_visibility="collapsed",
                placeholder=f"Enter value ({unit})",
            )

    with col3:
        source_options = ["default", "measured", "calculated", "user_override", "national_inventory", "ipcc", "methodology"]
        current_source = param.get("source_type", "default")
        source_idx = source_options.index(current_source) if current_source in source_options else 0
        new_source = st.selectbox(
            "Source",
            source_options,
            index=source_idx,
            key=f"param_src_{param_key}_{param['id']}",
            label_visibility="collapsed",
        )

    with col4:
        if p_status in ("default", "estimated") and current_val and str(current_val).strip():
            if st.button("Confirm", key=f"confirm_{param_key}_{param['id']}", help="Accept this value as confirmed for your project"):
                result = confirm_parameter(project_id, param_key)
                if result and result.get("param_status") == "confirmed":
                    st.success("Confirmed")
                    st.rerun()
                else:
                    st.warning("Cannot confirm: value may be invalid or missing")

    if str(new_val) != str(current_val) or new_source != current_source:
        if st.button("Save", key=f"save_param_{param_key}_{param['id']}"):
            update_parameter(
                project_id, param_key,
                value=new_val if new_val != "" else None,
                source_type=new_source,
            )
            st.success(f"Updated {param['param_name']}")
            st.rerun()

    if param.get("validation_message"):
        st.caption(f"Validation: {param['validation_message']}")
