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
    normalize_fuel_type,
    PARAMETER_DEFINITIONS,
)
from carbongpt.core.evidence_engine import get_evidence_links, get_evidence_counts_by_param

DERIVED_PARAMS = {
    "num_beneficiaries",
    "num_households",
    "bl_consumption_wood_equiv",
    # When SFC is set (Method 1 KPT), these are derived (read-only) from SFC × 365 / 1000.
    # When no SFC (user enters directly), source_type stays 'default' → normal editable row.
    "baseline_fuel_consumption",
    "project_fuel_consumption",
}

CHARCOAL_ONLY_PARAMS = {"CF"}

METHOD3_ONLY_PARAMS = {"NCV_project", "EF_CO2_project", "EF_nonCO2_project"}

METHOD2_LOCKED_PARAMS = {"SFC_baseline"}


def _get_project_method_settings(project_id, all_params):
    """Return (baseline_fuel, project_fuel, method_id, methodology_settings)."""
    baseline_fuel = "wood"
    project_fuel = "wood"
    method_id = None
    settings = {}
    try:
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute("SELECT methodology_settings FROM user_projects WHERE id = %s", (project_id,))
            row = cur.fetchone()
            if row and row[0]:
                settings = row[0] if isinstance(row[0], dict) else {}
                if settings.get("baseline_fuel"):
                    baseline_fuel = normalize_fuel_type(str(settings["baseline_fuel"]))
                if settings.get("project_fuel"):
                    project_fuel = normalize_fuel_type(str(settings["project_fuel"]))
                method_id = settings.get("calculation_method") or settings.get("method_id")
    except Exception:
        pass
    for p in all_params:
        if p["param_key"] == "baseline_fuel" and p["value"]:
            baseline_fuel = normalize_fuel_type(str(p["value"]))
        if p["param_key"] == "project_fuel" and p["value"]:
            project_fuel = normalize_fuel_type(str(p["value"]))
    return baseline_fuel, project_fuel, method_id, settings


def _get_project_fuels(project_id, all_params):
    bl, pj, _, _ = _get_project_method_settings(project_id, all_params)
    return bl, pj


FNRB_GUIDANCE = (
    "fNRB must be country/region-specific. Default sources: "
    "CDM/GS approved country studies, IPCC default (0.73 for sub-Saharan Africa), "
    "or a project-specific survey following TPDDTEC Annex 2 / VM0050 §5.3. "
    "Using a conservative (higher) value increases ER credibility."
)


def _should_show_param(param_key, baseline_fuel, project_fuel, method_id=None):
    if param_key in CHARCOAL_ONLY_PARAMS:
        return baseline_fuel == "charcoal" or project_fuel == "charcoal"
    if method_id in ("method_1", "method_2") and param_key in METHOD3_ONLY_PARAMS:
        return False
    # Method 2: SFC_baseline is fixed by the methodology default — hide from editable list
    if method_id == "method_2" and param_key in METHOD2_LOCKED_PARAMS:
        return False
    return True


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
    baseline_fuel, project_fuel, method_id, meth_settings = _get_project_method_settings(project_id, all_params)

    if method_id:
        try:
            from carbongpt.core.methodology_rules import get_tpddtec_method_badge_info
            badge_info = get_tpddtec_method_badge_info(method_id)
            st.markdown(
                f'<span style="background:{badge_info["color"]};color:white;padding:3px 10px;border-radius:4px;'
                f'font-size:0.85em;font-weight:bold;">{badge_info["label"]}</span>'
                f' <span style="font-size:0.85em;color:#666;">{badge_info["description"]}</span>',
                unsafe_allow_html=True,
            )
        except Exception:
            pass

    if method_id == "method_2":
        hh_size = next((float(p["value"]) for p in all_params if p["param_key"] == "household_size" and p["value"]), 5.0)
        devices_per_hh = next((float(p["value"]) for p in all_params if p["param_key"] == "devices_per_household" and p["value"]), 1.0)
        sfc_b_locked = 0.5 * hh_size / devices_per_hh / 365.0 * 1000.0
        st.info(
            f"**Method 2 — Methodology-locked baseline:**  \n"
            f"SFC_baseline is fixed at the TPDDTEC/VM0050 default: "
            f"**{sfc_b_locked:.4f} kg/technology-day** "
            f"(= 0.5 t/capita/yr × {hh_size:.0f} persons ÷ {devices_per_hh:.0f} device ÷ 365 days).  \n"
            f"This value is not user-editable under Method 2. To use field-measured baseline consumption, "
            f"switch to **Method 1 (BFT)** in the Methodology wizard.",
            icon="🔒",
        )

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
        displayable = [p for p in cat_params
                       if p["param_key"] not in globally_rendered
                       and _should_show_param(p["param_key"], baseline_fuel, project_fuel, method_id)]
        if not displayable:
            continue

        with st.expander(f"{category_names.get(cat, cat)} ({len(displayable)})", expanded=(cat in ("baseline", "emission_factor"))):
            for p in displayable:
                key = p["param_key"]
                if key in globally_rendered:
                    continue
                if not _should_show_param(key, baseline_fuel, project_fuel, method_id):
                    globally_rendered.add(key)
                    continue

                is_derived = key in DERIVED_PARAMS and p.get("source_type") == "calculated"

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
                elif is_derived:
                    _render_derived_parameter(project_id, p, evidence_by_param)
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


def _render_derived_parameter(project_id, param, evidence_by_param):
    param_key = param["param_key"]
    status_label, status_color, p_status = _get_param_status_display(param)

    has_evidence = param_key in evidence_by_param
    ev_count = len(evidence_by_param.get(param_key, []))
    evidence_indicator = ""
    if ev_count > 0:
        evidence_indicator = f' <span style="color:#0d9488;font-size:0.85em;">[{ev_count} evidence]</span>'

    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        st.markdown(
            f"<span style='color:{status_color};font-weight:bold;'>{status_label}</span> "
            f"**{param['param_name']}**{evidence_indicator}",
            unsafe_allow_html=True,
        )
        source_ref = param.get("source_reference", "")
        st.caption(f"Source: {source_ref}")

    with col2:
        current_val = param["value"] if param["value"] is not None else ""
        unit = param.get("unit", "")
        if current_val:
            try:
                display_val = f"{float(current_val):,.4f}"
            except (ValueError, TypeError):
                display_val = str(current_val)
            st.markdown(f"**{display_val}** {unit}")
            if param_key in ("baseline_fuel_consumption", "project_fuel_consumption"):
                sfc_key = "SFC_baseline" if "baseline" in param_key else "SFC_project"
                st.caption(f"Auto-derived from {sfc_key} (kg/device/day × 365 / 1000). Override to use a direct field measurement.")
        else:
            if param_key in ("baseline_fuel_consumption", "project_fuel_consumption"):
                sfc_key = "SFC_baseline" if "baseline" in param_key else "SFC_project"
                st.caption(f"Will be auto-derived from {sfc_key} once set. Override below to enter a direct field measurement.")
            else:
                st.caption("Not yet computed (set primary inputs first)")

    with col3:
        override_key = f"override_derived_{param_key}_{project_id}"
        if st.button("Override", key=f"btn_override_{param_key}_{param['id']}", help="Manually set this value instead of using the computed one"):
            st.session_state[override_key] = True

    if st.session_state.get(f"override_derived_{param_key}_{project_id}"):
        oc1, oc2 = st.columns([3, 1])
        with oc1:
            override_val = st.text_input(
                f"Override value ({param.get('unit', '')})",
                value=str(current_val) if current_val else "",
                key=f"override_val_{param_key}_{param['id']}",
            )
        with oc2:
            if st.button("Save Override", key=f"save_override_{param_key}_{param['id']}"):
                update_parameter(
                    project_id, param_key,
                    value=override_val if override_val else None,
                    source_type="user_override",
                    source_reference="Manual override of derived value",
                )
                st.session_state.pop(f"override_derived_{param_key}_{project_id}", None)
                st.success(f"Updated {param['param_name']}")
                st.rerun()


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
    ev_count = len(evidence_by_param.get(param_key, []))
    evidence_indicator = ""
    if ev_count > 0:
        evidence_indicator = f' <span style="color:#0d9488;font-size:0.85em;">[{ev_count} evidence]</span>'

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
        if param_key == "fNRB":
            st.caption(f"ℹ️  {FNRB_GUIDANCE}")
        # Show extraction hint from PARAMETER_DEFINITIONS if available
        _param_def = PARAMETER_DEFINITIONS.get(param_key, {})
        _extraction_hint = _param_def.get("extraction_hint", "")
        if _extraction_hint:
            st.caption(f"Extraction hint: {_extraction_hint}")

    with col2:
        current_val = param["value"] if param["value"] is not None else ""
        unit = param.get("unit", "")

        if param_key in ("baseline_fuel", "project_fuel"):
            display_fuel = get_fuel_display_label(str(current_val)) if current_val else "wood"
            st.markdown(f"**{display_fuel}**", help="Set in Methodology Choices in the Setup tab")
            st.caption("Read-only — change fuel type in Setup tab (Methodology Choices)")
            new_val = current_val
        else:
            new_val = st.text_input(
                f"Value ({unit})",
                value=str(current_val),
                key=f"param_val_{param_key}_{param['id']}",
                label_visibility="collapsed",
                placeholder=f"Enter value ({unit})",
            )

    with col3:
        source_options = ["default", "measured", "calculated", "user_override", "national_inventory", "ipcc", "methodology", "document_extracted"]
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
