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


def _auto_refresh_null_defaults(project_id, all_params):
    """
    One-time per-session check that fires when key parameters still have null
    values — either because the engine defaults improved since initialization, or
    because the intake key-name mismatch (num_devices vs num_units) prevented the
    wizard-entered device count from seeding the parameter on project creation.

    Confirmed / measured / user_override values are always preserved by initialize.
    """
    from carbongpt.repository.store import get_user_project

    SENTINEL_PARAMS = {"SFC_project", "SFC_baseline"}
    needs_refresh = any(
        p["param_key"] in SENTINEL_PARAMS
        and p.get("value") is None
        and p.get("source_type") == "default"
        for p in all_params
    )

    # Also trigger if num_devices is missing but the project intake already has it
    # (happens on projects created before the num_devices/num_units key fix).
    if not needs_refresh:
        nd_param = next((p for p in all_params if p["param_key"] == "num_devices"), None)
        if nd_param and nd_param.get("value") is None and nd_param.get("source_type") == "default":
            project = get_user_project(project_id)
            if project:
                po = (project.get("project_intake") or {}).get("project_overview") or {}
                if po.get("num_devices") or po.get("num_units"):
                    needs_refresh = True

    if not needs_refresh:
        return False
    result = initialize_project_parameters(project_id)
    return "error" not in result


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

    # ── Technology profile loader
    try:
        from carbongpt.repository.profile_store import list_profiles
        tech_profiles = list_profiles("technology")
        if tech_profiles:
            _tech_load_key = f"load_tech_profile_{project_id}"
            tech_opts = ["— load from technology profile —"] + [p["name"] for p in tech_profiles]
            sel_tech = st.selectbox(
                "Import from technology profile",
                tech_opts,
                index=0,
                key=_tech_load_key,
                help="Pre-fill SFC, efficiency and emission factor parameters from a saved stove profile.",
            )
            if sel_tech != tech_opts[0]:
                chosen_tech = next((p for p in tech_profiles if p["name"] == sel_tech), None)
                if chosen_tech:
                    td = chosen_tech.get("data") or {}
                    _TECH_PARAM_MAP = {
                        "SFC_project": "sfc_project_kg_per_day",
                        "baseline_efficiency": "thermal_efficiency_baseline",
                        "project_efficiency": "thermal_efficiency_project",
                        "EF_CO2_baseline": "co_emission_factor",
                    }
                    imported = []
                    for param_key, profile_field in _TECH_PARAM_MAP.items():
                        raw_val = td.get(profile_field)
                        if raw_val:
                            try:
                                fval = float(str(raw_val).strip())
                                # Convert percentage to fraction for efficiency fields
                                if "efficiency" in profile_field and fval > 1:
                                    fval = round(fval / 100, 4)
                                update_parameter(
                                    project_id, param_key,
                                    value=str(fval),
                                    source_type="user_override",
                                    source_reference=f"Loaded from technology profile: {sel_tech}",
                                )
                                imported.append(param_key)
                            except (ValueError, TypeError):
                                pass
                    if imported:
                        st.success(f"Loaded {len(imported)} parameter(s) from '{sel_tech}'.")
                        import time; time.sleep(0.4); st.rerun()
    except Exception:
        pass

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

    # One-time auto-refresh: if key params (SFC_project etc.) have null defaults from
    # an old engine, re-initialize to pick up improved ex-ante defaults.
    _refresh_key = f"params_refreshed_{project_id}"
    if _refresh_key not in st.session_state:
        st.session_state[_refresh_key] = True
        if _auto_refresh_null_defaults(project_id, all_params):
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

                # num_households is normally derived from num_devices; but when num_devices
                # is not yet set the user should be able to enter it directly (reverse derivation
                # will then compute num_devices from it automatically on Save).
                if key == "num_households" and p.get("source_type") == "calculated":
                    _nd_param = next((q for q in all_params if q["param_key"] == "num_devices"), None)
                    _nd_missing = (not _nd_param) or (_nd_param.get("value") is None)
                    is_derived = not _nd_missing  # editable when num_devices is missing
                else:
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
                    # Guided entry panel for fuel consumption (below the standard row)
                    if key in ("baseline_fuel_consumption", "project_fuel_consumption"):
                        _render_fuel_consumption_guide(project_id, p, all_params)


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
            elif param_key == "num_beneficiaries":
                st.caption(
                    "Not yet computed — set **Number of devices deployed** or **Number of households served** "
                    "first; beneficiaries will be derived automatically (households x household size)."
                )
            elif param_key == "num_households":
                st.caption(
                    "Not yet computed — set **Number of devices deployed** and this will be derived "
                    "automatically (devices / devices per household)."
                )
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


def _render_fuel_consumption_guide(project_id, param, all_params):
    """
    Guided entry panel shown below the standard row for baseline/project fuel consumption.

    Baseline: when using a methodology default (per-capita reference), prompts for
    household_size and devices_per_household so the user can see and apply the
    per-household AND per-device conversion before saving.

    Project: offers a radio choice between "per capita", "per household", and
    "per device directly" so the user can enter whichever unit they have and the
    system converts to t/device/yr for storage.
    """
    import re

    param_key = param["param_key"]
    current_source = param.get("source_type", "default")

    # Do not show guide when the value is already field-measured or user-confirmed
    if current_source in ("calculated", "user_override", "measured", "confirmed"):
        return

    def _get_val(key):
        p = next((x for x in all_params if x["param_key"] == key), None)
        if p and p.get("value") is not None:
            try:
                return float(p["value"])
            except (ValueError, TypeError):
                pass
        return None

    hh_sz_db = _get_val("household_size") or 5.0
    dph_db   = _get_val("devices_per_household") or 1.0

    if param_key == "baseline_fuel_consumption":
        # Extract P_b from the source_reference generated by _resolve_parameter_value
        src_ref = param.get("source_reference", "")
        try:
            m = re.search(r"P_b\s*=\s*([\d.]+)\s*t/capita", src_ref)
            p_b = float(m.group(1)) if m else 0.4
        except Exception:
            p_b = 0.4

        with st.expander(
            f"Guided calculation — {p_b} t/capita/yr reference to t/device/yr",
            expanded=(param.get("value") is None),
        ):
            st.caption(
                f"The methodology reference is **{p_b} t/capita/yr** (per person per year). "
                f"Adjust household size and devices per household below to compute the "
                f"baseline consumption **per household** and **per device**."
            )
            gc1, gc2 = st.columns(2)
            with gc1:
                hh_sz_input = st.number_input(
                    "Persons per household",
                    min_value=1.0, max_value=20.0,
                    value=hh_sz_db, step=0.5,
                    key=f"bl_guide_hh_{project_id}",
                    help="Average household size — updates the household_size parameter when saved",
                )
            with gc2:
                dph_input = st.number_input(
                    "Devices per household",
                    min_value=1.0, max_value=10.0,
                    value=dph_db, step=1.0,
                    key=f"bl_guide_dph_{project_id}",
                    help="Number of project stoves/devices per household — updates devices_per_household",
                )

            per_hh  = round(p_b * hh_sz_input, 4)
            per_dev = round(per_hh / dph_input, 4)

            st.info(
                f"**{p_b} t/capita/yr × {hh_sz_input:.0f} persons = {per_hh} t/household/yr**  \n"
                f"÷ {dph_input:.0f} device/hh = **{per_dev} t/device/yr** ← value that will be saved"
            )

            if st.button("Apply and save", key=f"bl_guide_apply_{project_id}"):
                if abs(hh_sz_input - hh_sz_db) > 0.01:
                    update_parameter(
                        project_id, "household_size",
                        value=str(hh_sz_input), source_type="user_override",
                        source_reference=f"Set via guided entry ({hh_sz_input:.0f} persons/hh)",
                    )
                if abs(dph_input - dph_db) > 0.01:
                    update_parameter(
                        project_id, "devices_per_household",
                        value=str(dph_input), source_type="user_override",
                        source_reference=f"Set via guided entry ({dph_input:.0f} devices/hh)",
                    )
                update_parameter(
                    project_id, "baseline_fuel_consumption",
                    value=str(per_dev), source_type="methodology",
                    source_reference=(
                        f"Guided: P_b = {p_b} t/capita/yr × {hh_sz_input:.0f} persons/hh "
                        f"÷ {dph_input:.0f} device/hh = {per_dev} t/device/yr "
                        f"({per_hh} t/household/yr)"
                    ),
                )
                st.success(f"Saved: {per_dev} t/device/yr  ({per_hh} t/household/yr)")
                st.rerun()

    elif param_key == "project_fuel_consumption":
        mode_key = f"proj_fuel_mode_{project_id}"
        if mode_key not in st.session_state:
            st.session_state[mode_key] = "per_capita"

        with st.expander("Enter project fuel consumption", expanded=(param.get("value") is None)):
            entry_mode = st.radio(
                "Entry format",
                options=["per_capita", "per_household", "per_device"],
                format_func=lambda x: {
                    "per_capita":   f"Per capita  (t/capita/yr)  — uses {hh_sz_db:.0f} persons/hh from baseline",
                    "per_household": f"Per household  (t/household/yr)  — divide by {dph_db:.0f} device/hh",
                    "per_device":    "Per device directly  (t/device/yr)  — e.g. from KPT field measurement",
                }[x],
                index=["per_capita", "per_household", "per_device"].index(
                    st.session_state.get(mode_key, "per_capita")
                ),
                key=f"proj_fuel_mode_radio_{project_id}",
            )
            st.session_state[mode_key] = entry_mode

            val_in = st.number_input(
                {
                    "per_capita":    "Project consumption (t/capita/yr)",
                    "per_household": "Project consumption (t/household/yr)",
                    "per_device":    "Project consumption (t/device/yr)",
                }[entry_mode],
                min_value=0.0,
                max_value={"per_capita": 5.0, "per_household": 50.0, "per_device": 20.0}[entry_mode],
                value=0.0, step=0.01,
                key=f"proj_fuel_val_{project_id}",
            )

            if entry_mode == "per_capita":
                per_hh  = round(val_in * hh_sz_db, 4)
                per_dev = round(per_hh / dph_db, 4)
                st.caption(
                    f"{val_in} t/capita/yr × {hh_sz_db:.0f} persons/hh = **{per_hh} t/household/yr** "
                    f"÷ {dph_db:.0f} device/hh = **{per_dev} t/device/yr**"
                )
                src_ref = (
                    f"Entered per capita: {val_in} t/capita/yr × {hh_sz_db:.0f} persons/hh "
                    f"÷ {dph_db:.0f} device/hh = {per_dev} t/device/yr"
                )
            elif entry_mode == "per_household":
                per_dev = round(val_in / dph_db, 4)
                per_cap = round(val_in / hh_sz_db, 4) if hh_sz_db > 0 else None
                cap_str = f" (= {per_cap} t/capita/yr)" if per_cap else ""
                st.caption(
                    f"{val_in} t/household/yr ÷ {dph_db:.0f} device/hh = **{per_dev} t/device/yr**{cap_str}"
                )
                src_ref = (
                    f"Entered per household: {val_in} t/household/yr "
                    f"÷ {dph_db:.0f} device/hh = {per_dev} t/device/yr"
                )
            else:
                per_dev = round(val_in, 6)
                per_hh  = round(per_dev * dph_db, 4)
                per_cap = round(per_dev * dph_db / hh_sz_db, 4) if hh_sz_db > 0 else None
                cap_str = f" (= {per_cap} t/capita/yr)" if per_cap else ""
                st.caption(f"{per_dev} t/device/yr = {per_hh} t/household/yr{cap_str}")
                src_ref = f"Entered directly: {per_dev} t/device/yr"

            if st.button("Save project consumption", key=f"proj_fuel_save_{project_id}"):
                if per_dev > 0:
                    update_parameter(
                        project_id, "project_fuel_consumption",
                        value=str(round(per_dev, 6)),
                        source_type="user_override",
                        source_reference=src_ref,
                    )
                    st.success(f"Saved: {round(per_dev, 6)} t/device/yr")
                    st.rerun()
                else:
                    st.warning("Enter a value greater than 0 to save.")


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
        # num_households shown as editable because num_devices is not yet set
        if param_key == "num_households" and source_label == "calculated":
            st.caption(
                "Enter number of households directly — "
                "Number of devices deployed will be computed automatically on save "
                "(= households x devices per household). "
                "Alternatively, enter **Number of devices deployed** below and this will be derived from it."
            )
        else:
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
        # num_households shown as editable (num_devices missing): pre-select "user_override" so
        # that saving protects the user's direct entry from being overwritten by forward derivation.
        if param_key == "num_households" and current_source == "calculated":
            current_source = "user_override"
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
