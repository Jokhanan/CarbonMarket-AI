import streamlit as st
from carbongpt.core.lifecycle_manager import (
    initialize_lifecycle,
    get_lifecycle,
    advance_stage,
    get_tasks,
    update_task,
    add_task,
    delete_task,
    get_issuances,
    add_issuance,
    update_issuance,
    get_monitoring_tasks,
    initialize_monitoring_tasks,
    LIFECYCLE_STAGES,
)


def render_lifecycle_dashboard(project):
    project_id = project["id"]
    _lifecycle_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-blue">{_lifecycle_icon}</span>
        <span class="section-header-text">Project Lifecycle</span>
    </span>
    """, unsafe_allow_html=True)

    lifecycle = get_lifecycle(project_id)
    if not lifecycle.get("stages") or not any(s["status"] != "upcoming" for s in lifecycle.get("stages", [])):
        st.info("Project lifecycle has not been initialized yet.")
        if st.button("Initialize Lifecycle", key="init_lifecycle"):
            with st.spinner("Setting up lifecycle stages and tasks..."):
                initialize_lifecycle(project_id)
                st.success("Lifecycle initialized with default tasks for each stage")
                st.rerun()
        return

    lifecycle = get_lifecycle(project_id)
    current = lifecycle.get("current_stage", "feasibility")

    _render_stage_progress(lifecycle)

    lc_tabs = st.tabs(["Tasks", "Stage Management", "Issuance Tracking"])

    with lc_tabs[0]:
        _render_tasks(project_id, lifecycle, current)

    with lc_tabs[1]:
        _render_stage_management(project_id, lifecycle, current)

    with lc_tabs[2]:
        _render_issuance_tracking(project_id)


def _render_stage_progress(lifecycle):
    stages = lifecycle.get("stages", [])
    cols = st.columns(len(stages))
    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            status = stage["status"]
            if status == "completed":
                indicator = "[Done]"
                color = "green"
            elif status == "active":
                indicator = "[Active]"
                color = "#2196F3"
            else:
                indicator = "[ ]"
                color = "gray"

            progress = ""
            if stage["tasks_total"] > 0:
                progress = f" {stage['tasks_completed']}/{stage['tasks_total']}"

            st.markdown(
                f"<div style='text-align:center;'>"
                f"<span style='color:{color};font-weight:bold;font-size:0.75em;'>{indicator}</span><br>"
                f"<span style='font-size:0.7em;'>{stage['name']}{progress}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


def _render_tasks(project_id, lifecycle, current_stage):
    stage_filter = st.selectbox(
        "Filter by Stage",
        ["All Stages", "Current Stage Only"] + [s["name"] for s in LIFECYCLE_STAGES],
        key="task_stage_filter",
    )

    if stage_filter == "Current Stage Only":
        tasks = get_tasks(project_id, stage=current_stage)
    elif stage_filter != "All Stages":
        stage_key = next((s["key"] for s in LIFECYCLE_STAGES if s["name"] == stage_filter), None)
        tasks = get_tasks(project_id, stage=stage_key)
    else:
        tasks = get_tasks(project_id)

    if not tasks:
        st.info("No tasks found for the selected filter.")
    else:
        for task in tasks:
            _render_task_row(task)

    st.markdown("---")
    st.markdown("**Add New Task**")
    new_col1, new_col2, new_col3 = st.columns([3, 1, 1])
    with new_col1:
        new_title = st.text_input("Task Title", key="new_task_title", placeholder="Enter task description")
    with new_col2:
        stage_options = [s["key"] for s in LIFECYCLE_STAGES]
        stage_names = [s["name"] for s in LIFECYCLE_STAGES]
        default_idx = stage_options.index(current_stage) if current_stage in stage_options else 0
        new_stage = st.selectbox("Stage", stage_options, index=default_idx, format_func=lambda x: next((s["name"] for s in LIFECYCLE_STAGES if s["key"] == x), x), key="new_task_stage")
    with new_col3:
        new_priority = st.selectbox("Priority", ["low", "medium", "high", "critical"], index=1, key="new_task_priority")

    if st.button("Add Task", key="add_task_btn"):
        if new_title:
            add_task(project_id, new_title, stage=new_stage, priority=new_priority)
            st.success("Task added")
            st.rerun()
        else:
            st.warning("Enter a task title")


def _render_task_row(task):
    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
    with col1:
        done = task["status"] == "completed"
        title = task["title"]
        stage_label = task.get("lifecycle_stage", "")
        priority = task.get("priority", "medium")
        priority_indicator = {"critical": "[!!]", "high": "[!]", "medium": "", "low": ""}.get(priority, "")
        if done:
            st.markdown(f"~~{title}~~ {priority_indicator} _({stage_label})_")
        else:
            st.markdown(f"**{title}** {priority_indicator} _({stage_label})_")

    with col2:
        due = task.get("due_date")
        if due:
            st.caption(f"Due: {due}")

    with col3:
        status_options = ["pending", "in_progress", "completed", "blocked", "cancelled"]
        current_idx = status_options.index(task["status"]) if task["status"] in status_options else 0
        new_status = st.selectbox("Status", status_options, index=current_idx, key=f"task_status_{task['id']}", label_visibility="collapsed")
        if new_status != task["status"]:
            update_task(task["id"], status=new_status)
            st.rerun()

    with col4:
        if st.button("X", key=f"del_task_{task['id']}"):
            delete_task(task["id"])
            st.rerun()


def _render_stage_management(project_id, lifecycle, current_stage):
    st.markdown(f"**Current Stage:** {current_stage}")

    current_tasks = get_tasks(project_id, stage=current_stage)
    total = len(current_tasks)
    completed = len([t for t in current_tasks if t["status"] == "completed"])

    if total > 0:
        st.progress(completed / total, text=f"{completed}/{total} tasks completed")

    stage_keys = [s["key"] for s in LIFECYCLE_STAGES]
    current_idx = stage_keys.index(current_stage) if current_stage in stage_keys else 0

    if current_idx < len(stage_keys) - 1:
        next_stage = stage_keys[current_idx + 1]
        next_name = LIFECYCLE_STAGES[current_idx + 1]["name"]

        incomplete = total - completed
        if incomplete > 0:
            st.warning(f"{incomplete} task(s) are not yet completed in the current stage.")

        if st.button(f"Advance to: {next_name}", key="advance_stage", type="primary"):
            result = advance_stage(project_id)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success(f"Advanced to {next_name}")
                st.rerun()
    else:
        st.success("Project is at the final lifecycle stage.")


def _render_issuance_tracking(project_id):
    issuances = get_issuances(project_id)

    if issuances:
        total_issued = sum(i.get("credits_issued") or 0 for i in issuances)
        total_requested = sum(i.get("credits_requested") or 0 for i in issuances)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Issued", f"{total_issued:,.0f} tCO2e")
        with col2:
            st.metric("Total Requested", f"{total_requested:,.0f} tCO2e")
        with col3:
            st.metric("Vintages", len(issuances))

        for iss in issuances:
            with st.expander(f"Vintage {iss['vintage_year']} - {iss.get('registry_status', 'planned')}"):
                ic1, ic2, ic3 = st.columns(3)
                with ic1:
                    st.write(f"Credits Requested: {iss.get('credits_requested', 'N/A')}")
                    st.write(f"Credits Issued: {iss.get('credits_issued', 'N/A')}")
                with ic2:
                    st.write(f"Monitoring: {iss.get('monitoring_period_start', 'N/A')} to {iss.get('monitoring_period_end', 'N/A')}")
                    st.write(f"VVB: {iss.get('vvb_name', 'N/A')}")
                with ic3:
                    st.write(f"Status: {iss.get('registry_status', 'planned')}")
                    st.write(f"Verification: {iss.get('verification_date', 'N/A')}")

                new_status = st.selectbox(
                    "Update Status",
                    ["planned", "monitoring", "under_verification", "verified", "issued", "retired", "cancelled"],
                    index=["planned", "monitoring", "under_verification", "verified", "issued", "retired", "cancelled"].index(iss.get("registry_status", "planned")),
                    key=f"iss_status_{iss['id']}",
                )
                if new_status != iss.get("registry_status"):
                    if st.button("Update", key=f"iss_update_{iss['id']}"):
                        update_issuance(iss["id"], registry_status=new_status)
                        st.success("Updated")
                        st.rerun()

    st.markdown("---")
    st.markdown("**Add Issuance Record**")
    add_col1, add_col2, add_col3 = st.columns(3)
    with add_col1:
        vintage = st.number_input("Vintage Year", min_value=2000, max_value=2050, value=2025, key="new_vintage")
        credits_req = st.number_input("Credits Requested (tCO2e)", min_value=0.0, value=0.0, step=100.0, key="new_credits_req")
    with add_col2:
        credits_iss = st.number_input("Credits Issued (tCO2e)", min_value=0.0, value=0.0, step=100.0, key="new_credits_iss")
        vvb = st.text_input("VVB Name", key="new_vvb", placeholder="e.g. SCS Global Services")
    with add_col3:
        reg_status = st.selectbox("Status", ["planned", "monitoring", "under_verification", "verified", "issued"], key="new_iss_status")

    if st.button("Add Issuance Record", key="add_issuance"):
        add_issuance(
            project_id, vintage,
            credits_requested=credits_req if credits_req > 0 else None,
            credits_issued=credits_iss if credits_iss > 0 else None,
            vvb_name=vvb if vvb else None,
            registry_status=reg_status,
        )
        st.success("Issuance record added")
        st.rerun()


def render_monitoring_dashboard(project):
    project_id = project["id"]
    methodology = (project.get("methodology") or "").upper().replace("GS-", "")

    _mon_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>'
    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-green">{_mon_icon}</span>
        <span class="section-header-text">Monitoring Management</span>
    </span>
    """, unsafe_allow_html=True)

    selected_scenario_id = project.get("selected_scenario_id")
    if selected_scenario_id:
        try:
            from carbongpt.core.er_simulator import get_selected_scenario
            sel = get_selected_scenario(project_id)
            if sel:
                sc = sel["scenario"]
                summary = sc.get("results_summary") or {}
                if isinstance(summary, str):
                    import json
                    try:
                        summary = json.loads(summary)
                    except Exception:
                        summary = {}
                total_er = summary.get("total_er", 0)
                annual_er = summary.get("average_annual_er", 0)
                st.info(
                    f"Benchmark Scenario: {sc.get('name', 'Unknown')} "
                    f"-- {total_er:,.0f} tCO2e total, {annual_er:,.0f} tCO2e/yr. "
                    f"Monitoring targets are based on this scenario."
                )
        except Exception:
            pass

    tasks = get_monitoring_tasks(project_id)
    if not tasks:
        st.info("Monitoring tasks have not been set up yet.")
        if st.button("Initialize Monitoring Tasks", key="init_monitoring"):
            with st.spinner("Setting up monitoring tasks from methodology requirements..."):
                tasks = initialize_monitoring_tasks(project_id, methodology)
                st.success(f"Initialized {len(tasks)} monitoring tasks")
                st.rerun()
        return

    active = [t for t in tasks if t["status"] not in ("completed",)]
    completed = [t for t in tasks if t["status"] == "completed"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tasks", len(tasks))
    with col2:
        st.metric("Active", len(active))
    with col3:
        st.metric("Completed", len(completed))

    for task in tasks:
        _render_monitoring_task(task)


def _render_monitoring_task(task):
    status_color = {
        "pending": "orange",
        "scheduled": "blue",
        "in_progress": "#2196F3",
        "completed": "green",
        "overdue": "red",
    }.get(task["status"], "gray")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"<span style='color:{status_color};'>**{task['task_name']}**</span>", unsafe_allow_html=True)
        st.caption(f"Parameter: {task.get('param_key', 'N/A')} | Frequency: {task.get('frequency', 'N/A')} | Method: {task.get('method', 'N/A')}")
    with col2:
        due = task.get("next_due_date")
        if due:
            st.caption(f"Next Due: {due}")
    with col3:
        status_options = ["pending", "scheduled", "in_progress", "completed", "overdue"]
        current_idx = status_options.index(task["status"]) if task["status"] in status_options else 0
        new_status = st.selectbox("Status", status_options, index=current_idx, key=f"mon_status_{task['id']}", label_visibility="collapsed")
        if new_status != task["status"]:
            from carbongpt.repository.db import get_cursor
            with get_cursor() as cur:
                cur.execute("UPDATE monitoring_tasks SET status = %s, updated_at = NOW() WHERE id = %s", (new_status, task["id"]))
            st.rerun()
