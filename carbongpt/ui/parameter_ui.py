import streamlit as st
from carbongpt.core.parameter_engine import (
    initialize_project_parameters,
    get_project_parameters,
    update_parameter,
    validate_all_parameters,
    get_parameter_summary,
)
from carbongpt.core.evidence_engine import get_evidence_links


def render_parameter_dashboard(project):
    project_id = project["id"]
    _param_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/></svg>'
    st.markdown(f"""
    <div class="section-header">
        <span class="section-header-icon section-header-icon-teal">{_param_icon}</span>
        <span class="section-header-text">Parameter Intelligence Dashboard</span>
    </div>
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
        valid_color = "normal" if summary["valid"] == summary["total"] else "off"
        st.metric("Valid", summary["valid"], delta=None if summary["valid"] == summary["total"] else f"{summary['pending']} pending", delta_color=valid_color)
    with col3:
        st.metric("Using Defaults", summary["defaults"])
    with col4:
        st.metric("Measured/Override", summary["measured"] + summary["overrides"])

    if summary["invalid"] > 0:
        st.warning(f"{summary['invalid']} parameter(s) have invalid values. Review and fix them below.")
    if summary["pending"] > 0:
        st.info(f"{summary['pending']} parameter(s) are still missing values.")

    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("Validate All", key="validate_all_params"):
            result = validate_all_parameters(project_id)
            if result["issues"]:
                st.warning(f"Found {len(result['issues'])} issue(s)")
            else:
                st.success("All parameters are valid")
    with action_col2:
        if st.button("Re-initialize from Methodology", key="reinit_params", help="Resets default values but preserves any measured or user-override values"):
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

    for cat in categories:
        cat_params = [p for p in all_params if p["category"] == cat]
        if not cat_params:
            continue

        with st.expander(f"{category_names.get(cat, cat)} ({len(cat_params)})", expanded=(cat in ("baseline", "emission_factor"))):
            for p in cat_params:
                _render_parameter_row(project_id, p, evidence_by_param)


def _render_parameter_row(project_id, param, evidence_by_param):
    param_key = param["param_key"]
    status = param["validation_status"]

    status_indicator = {
        "valid": "[OK]",
        "invalid": "[X]",
        "pending": "[?]",
        "warning": "[!]",
    }.get(status, "[ ]")

    status_color = {
        "valid": "green",
        "invalid": "red",
        "pending": "orange",
        "warning": "orange",
    }.get(status, "gray")

    has_evidence = param_key in evidence_by_param
    evidence_indicator = " [E]" if has_evidence else ""

    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        st.markdown(f"<span style='color:{status_color};font-weight:bold;'>{status_indicator}</span> **{param['param_name']}**{evidence_indicator}", unsafe_allow_html=True)
        source_label = param.get("source_type", "default")
        source_ref = param.get("source_reference", "")
        st.caption(f"Source: {source_label} | {source_ref}")

    with col2:
        current_val = param["value"] if param["value"] is not None else ""
        unit = param.get("unit", "")
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
