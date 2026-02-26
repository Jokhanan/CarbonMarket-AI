"""
streamlit_app.py — CarbonGPT Web UI

Provides a simple interface for uploading .docx monitoring reports,
selecting an internal template (Standard + Doc Type + Version), and
viewing compliance analysis results.
"""

import os
import time
import requests
import streamlit as st

API_BASE = os.getenv("CARBONGPT_API_URL", "http://localhost:3000")


def _render_ai_result(ai_result):
    global_summary = ai_result.get("global_summary", {})
    risk = global_summary.get("overall_risk", "UNKNOWN")
    risk_colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    risk_color = risk_colors.get(risk, "red")

    st.markdown(f"### Overall Risk: :{risk_color}[**{risk}**]")

    if global_summary.get("top_issues"):
        st.markdown("**Top Issues:**")
        for issue in global_summary["top_issues"]:
            st.markdown(f"- {issue}")

    if global_summary.get("top_actions"):
        st.markdown("**Priority Actions:**")
        for action in global_summary["top_actions"]:
            st.markdown(f"- {action}")

    if global_summary.get("coherence_flags"):
        st.markdown("**Coherence Flags:**")
        for flag in global_summary["coherence_flags"]:
            st.markdown(f"- {flag}")

    st.divider()
    st.markdown("### Section-by-Section Review")

    for review in ai_result.get("per_section_reviews", []):
        sec_id = review["section_id"]
        sec_title = review["section_title"]
        sec_score = review["completeness_score"]

        if sec_score >= 80:
            sec_icon = "🟢"
        elif sec_score >= 50:
            sec_icon = "🟡"
        else:
            sec_icon = "🔴"

        with st.expander(f"{sec_icon} {sec_id}: {sec_title} — Score: {sec_score}/100"):
            if review.get("issues"):
                st.markdown("**Issues:**")
                for issue in review["issues"]:
                    st.markdown(f"- {issue}")

            if review.get("suggested_fixes"):
                st.markdown("**Suggested Fixes:**")
                for fix in review["suggested_fixes"]:
                    st.markdown(f"- {fix}")

            if review.get("questions_for_user"):
                st.markdown("**Questions for You:**")
                for q in review["questions_for_user"]:
                    st.markdown(f"- {q}")

            if not review.get("issues") and not review.get("suggested_fixes") and not review.get("questions_for_user"):
                st.info("No issues found for this subsection.")


@st.fragment(run_every=5)
def _poll_ai_review():
    ai_task_id = st.session_state.get("ai_task_id")
    if not ai_task_id:
        return

    elapsed = time.time() - st.session_state.get("ai_task_start", time.time())
    if elapsed > 180:
        st.warning("AI Review timed out after 3 minutes. Please re-analyze to try again.")
        st.session_state.pop("ai_task_id", None)
        return

    progress = min(elapsed / 180, 0.95)
    st.progress(progress, text=f"AI review in progress... ({int(elapsed)}s)")

    try:
        poll_resp = requests.get(f"{API_BASE}/ai-review/{ai_task_id}", timeout=5)
        if poll_resp.status_code == 200:
            poll_data = poll_resp.json()
            if poll_data["status"] == "complete":
                st.session_state["ai_result"] = poll_data["result"]
                st.session_state.pop("ai_task_id", None)
                st.rerun()
            elif poll_data["status"] == "failed":
                st.error(f"AI Review failed: {poll_data.get('error', 'Unknown error')}")
                st.session_state.pop("ai_task_id", None)
    except requests.exceptions.RequestException:
        pass


st.set_page_config(page_title="CarbonGPT", page_icon="🌍", layout="wide")

st.title("CarbonGPT — Compliance Analyzer")
st.markdown("Upload a document and check it against Gold Standard templates and rules. Supports Monitoring Reports (MR), Project Design Documents (PDD), Programme of Activity DDs (PoA-DD), and VPA Design Documents (VPA-DD).")

STANDARDS = ["GoldStandard"]
DOC_TYPES = {"GoldStandard": ["MR", "PDD", "PoA-DD", "VPA-DD"]}
VERSIONS = {
    ("GoldStandard", "MR"): ["MR_v1_1"],
    ("GoldStandard", "PDD"): ["PDD_v1_5"],
    ("GoldStandard", "PoA-DD"): ["PoA-DD_v2_2"],
    ("GoldStandard", "VPA-DD"): ["VPA-DD_v2_3"],
}

col1, col2, col3 = st.columns(3)

with col1:
    standard = st.selectbox("Standard", STANDARDS, key="standard")

with col2:
    doc_type = st.selectbox("Document Type", DOC_TYPES.get(standard, []), key="doc_type")

with col3:
    version = st.selectbox("Version", VERSIONS.get((standard, doc_type), []), key="version")

ai_review_enabled = st.toggle("AI Review (beta)", value=False, key="ai_review_toggle")

uploaded_file = st.file_uploader("Upload your document (.docx)", type=["docx"])

analyze_btn = st.button("Analyze", type="primary", disabled=uploaded_file is None)

if analyze_btn and uploaded_file is not None:
    st.session_state.pop("ai_task_id", None)
    st.session_state.pop("ai_task_start", None)
    st.session_state.pop("ai_result", None)

    with st.spinner("Uploading document..."):
        upload_resp = requests.post(
            f"{API_BASE}/upload-document",
            files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            timeout=30,
        )

    if upload_resp.status_code != 200:
        st.error(f"Upload failed: {upload_resp.text}")
        st.stop()

    user_doc_path = upload_resp.json()["file_path"]
    st.session_state["user_doc_path"] = user_doc_path

    with st.spinner("Running compliance analysis..."):
        analyze_resp = requests.post(
            f"{API_BASE}/analyze-selected",
            json={
                "standard": standard,
                "doc_type": doc_type,
                "version": version,
                "user_doc_path": user_doc_path,
            },
            timeout=60,
        )

    if analyze_resp.status_code != 200:
        st.error(f"Analysis failed: {analyze_resp.text}")
        st.stop()

    st.session_state["analysis_result"] = analyze_resp.json()

    if ai_review_enabled:
        try:
            start_resp = requests.post(
                f"{API_BASE}/ai-review",
                json={
                    "standard": standard,
                    "doc_type": doc_type,
                    "version": version,
                    "doc_path": user_doc_path,
                },
                timeout=10,
            )
            if start_resp.status_code == 200:
                task_id = start_resp.json().get("task_id")
                if task_id:
                    st.session_state["ai_task_id"] = task_id
                    st.session_state["ai_task_start"] = time.time()
        except requests.exceptions.RequestException:
            pass

if "analysis_result" in st.session_state:
    result = st.session_state["analysis_result"]

    st.divider()

    score = result["compliance_score"]
    status = result.get("status", "REVIEW")
    status_label = result.get("status_label", "")

    score_col, status_col = st.columns(2)
    with score_col:
        if score >= 80:
            color = "green"
        elif score >= 50:
            color = "orange"
        else:
            color = "red"
        st.markdown(f"### Compliance Score: :{color}[**{score}/100**]")

    with status_col:
        if status == "PASS":
            st.success(status_label)
        elif status == "REVIEW":
            st.warning(status_label)
        else:
            st.error(status_label)

    findings = result.get("findings", [])

    if not findings:
        st.info("No findings — the document is fully compliant.")
    else:
        errors = [f for f in findings if f["severity"] == "ERROR"]
        warnings = [f for f in findings if f["severity"] == "WARNING"]
        infos = [f for f in findings if f["severity"] == "INFO"]

        if errors:
            st.markdown("#### Errors")
            for f in errors:
                st.markdown(f"- **[{f['rule_id']}]** {f['message']}")

        if warnings:
            st.markdown("#### Warnings")
            for f in warnings:
                st.markdown(f"- **[{f['rule_id']}]** {f['message']}")

        if infos:
            st.markdown("#### Info")
            for f in infos:
                st.markdown(f"- **[{f['rule_id']}]** {f['message']}")

    with st.expander("Sections found in your document"):
        for s in result.get("sections_found", []):
            st.markdown(f"- {s}")

    with st.expander("Template section matching"):
        for m in result.get("section_matches", []):
            expected = m["expected"]
            matched = m["matched"]
            if matched:
                st.markdown(f"- **{expected}** → {matched}")
            else:
                st.markdown(f"- **{expected}** → _not found_")

    if ai_review_enabled:
        st.divider()
        st.subheader("AI Review (beta)")

        ai_result = st.session_state.get("ai_result")

        if ai_result is not None:
            _render_ai_result(ai_result)
        elif st.session_state.get("ai_task_id"):
            _poll_ai_review()
        else:
            st.info("AI Review was not started. Re-analyze with the AI Review toggle enabled.")
