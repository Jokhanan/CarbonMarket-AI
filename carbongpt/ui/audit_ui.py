import streamlit as st
from carbongpt.core.audit_simulator import (
    run_audit_simulation,
    get_simulation_history,
    get_simulation_detail,
)


def render_audit_simulation(project):
    project_id = project["id"]
    _audit_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>'
    st.markdown(f"""
    <div class="section-header">
        <span class="section-header-icon section-header-icon-amber">{_audit_icon}</span>
        <span class="section-header-text">Audit Simulation</span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Simulate a VVB audit to identify potential findings before submission")

    has_sim = f"sim_result_{project_id}" in st.session_state and bool(st.session_state.get(f"sim_result_{project_id}"))
    doc_count = len(project.get("documents", []))
    if has_sim and doc_count > 0:
        st.markdown(
            '<span class="readiness-banner readiness-banner-ready">'
            '<span class="readiness-banner-icon">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>'
            '</span>'
            'ER simulation and documents available. The audit will have full context for a thorough review.'
            '</span>',
            unsafe_allow_html=True,
        )
    elif not has_sim and doc_count == 0:
        st.markdown(
            '<span class="readiness-banner readiness-banner-warning">'
            '<span class="readiness-banner-icon">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>'
            '</span>'
            'For a meaningful audit, run the ER Simulator and upload supporting documents first.'
            '</span>',
            unsafe_allow_html=True,
        )
    else:
        tips = []
        if not has_sim:
            tips.append("running the ER Simulator")
        if doc_count == 0:
            tips.append("uploading supporting documents")
        st.markdown(
            f'<span class="readiness-banner readiness-banner-info">'
            f'<span class="readiness-banner-icon">'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>'
            f'</span>'
            f'Tip: You can improve audit accuracy by {" and ".join(tips)} first.'
            f'</span>',
            unsafe_allow_html=True,
        )

    audit_tabs = st.tabs(["Run Simulation", "History"])

    with audit_tabs[0]:
        _render_run_simulation(project_id)

    with audit_tabs[1]:
        _render_history(project_id)


def _render_run_simulation(project_id):
    if st.button("Run Full Audit Simulation", key="run_audit", type="primary"):
        with st.spinner("Running audit simulation... This checks parameters, evidence, consistency, and compliance."):
            result = run_audit_simulation(project_id)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state[f"audit_result_{project_id}"] = result

    result = st.session_state.get(f"audit_result_{project_id}")
    if result:
        _render_audit_results(result)
        score = result.get("overall_score", 0)
        if score >= 80:
            st.markdown(
                '<span class="readiness-banner readiness-banner-ready">'
                '<span class="readiness-banner-icon">'
                '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>'
                '</span>'
                'Strong audit score. Consider exporting your document or advancing the project lifecycle status.'
                '</span>',
                unsafe_allow_html=True,
            )
        elif score >= 50:
            st.markdown(
                '<span class="readiness-banner readiness-banner-warning">'
                '<span class="readiness-banner-icon">'
                '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>'
                '</span>'
                'Review the findings above. Address critical and major issues, then re-run the audit to improve your score.'
                '</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="readiness-banner readiness-banner-warning">'
                '<span class="readiness-banner-icon">'
                '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>'
                '</span>'
                'Significant gaps found. Focus on configuring parameters and uploading evidence documents before re-running.'
                '</span>',
                unsafe_allow_html=True,
            )


def _render_audit_results(result):
    risk_level = result.get("risk_level", "UNKNOWN")
    score = result.get("overall_score", 0)
    counts = result.get("counts", {})

    risk_color = {
        "LOW": "green", "MEDIUM": "orange", "HIGH": "red", "CRITICAL": "darkred", "UNKNOWN": "gray"
    }.get(risk_level, "gray")

    st.markdown(f"<span style='font-size:1.5em;font-weight:bold;color:{risk_color};'>Risk Level: {risk_level}</span>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Score", f"{score}/100")
    with col2:
        st.metric("Critical", counts.get("critical", 0))
    with col3:
        st.metric("High", counts.get("high", 0))
    with col4:
        st.metric("Medium", counts.get("medium", 0))
    with col5:
        st.metric("Low", counts.get("low", 0))

    st.markdown(result.get("summary", ""))

    findings = result.get("findings", [])
    if findings:
        st.markdown("---")
        st.markdown("**Simulated Findings**")

        for i, f in enumerate(findings):
            severity = f.get("severity", "medium")
            finding_type = f.get("type", "observation")
            severity_color = {"critical": "darkred", "high": "red", "medium": "orange", "low": "gray"}.get(severity, "gray")

            with st.expander(f"[{finding_type.upper()}] {f.get('title', 'Finding')} -- Severity: {severity}"):
                st.markdown(f"<span style='color:{severity_color};font-weight:bold;'>{severity.upper()}</span> | Category: {f.get('category', 'general')}", unsafe_allow_html=True)
                st.write(f.get("description", ""))

    parameter_issues = result.get("parameter_issues", [])
    if parameter_issues:
        with st.expander(f"Parameter Issues ({len(parameter_issues)})"):
            for pi in parameter_issues:
                st.write(f"- **{pi['param_key']}**: {pi.get('message', pi.get('status', ''))}")

    evidence_gaps = result.get("evidence_gaps", [])
    if evidence_gaps:
        with st.expander(f"Evidence Gaps ({len(evidence_gaps)})"):
            for eg in evidence_gaps:
                st.write(f"- **{eg['param_name']}** ({eg['param_key']}): No supporting evidence linked. Source: {eg.get('source_type', 'N/A')}")

    recommendations = result.get("recommendations", [])
    if recommendations:
        st.markdown("---")
        st.markdown("**Recommendations**")
        for r in recommendations:
            st.write(f"- {r}")


def _render_history(project_id):
    history = get_simulation_history(project_id)
    if not history:
        st.info("No audit simulations have been run yet.")
        return

    for sim in history:
        risk_color = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red", "CRITICAL": "darkred"}.get(sim.get("risk_level", ""), "gray")
        with st.expander(f"Simulation {sim['id']} -- {sim.get('risk_level', 'N/A')} (Score: {sim.get('overall_score', 0)}) -- {sim.get('simulated_at', '')}"):
            st.markdown(f"<span style='color:{risk_color};font-weight:bold;'>Risk: {sim.get('risk_level', 'N/A')}</span> | Score: {sim.get('overall_score', 0)}/100", unsafe_allow_html=True)
            st.write(sim.get("summary", ""))

            if st.button("View Full Details", key=f"view_sim_{sim['id']}"):
                detail = get_simulation_detail(sim["id"])
                if detail:
                    findings = detail.get("findings", [])
                    if isinstance(findings, str):
                        import json
                        try:
                            findings = json.loads(findings)
                        except Exception:
                            findings = []
                    for f in findings:
                        st.write(f"- [{f.get('type', '')}] {f.get('title', '')}: {f.get('description', '')}")
