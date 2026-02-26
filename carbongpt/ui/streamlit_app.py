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

st.set_page_config(page_title="CarbonGPT", page_icon="🌍", layout="wide")

st.title("CarbonGPT — Compliance Analyzer")
st.markdown("Upload a monitoring report and check it against Gold Standard templates and rules.")

STANDARDS = ["GoldStandard"]
DOC_TYPES = {"GoldStandard": ["MR", "PDD"]}
VERSIONS = {
    ("GoldStandard", "MR"): ["MR_v1_1"],
    ("GoldStandard", "PDD"): ["PDD_v1_0"],
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

    result = analyze_resp.json()

    st.divider()

    score = result["compliance_score"]
    compliant = result["compliant"]

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

        ai_result = None
        start_resp = requests.post(
            f"{API_BASE}/ai-review",
            json={
                "standard": standard,
                "doc_type": doc_type,
                "version": "PerfCert_v1_2",
                "doc_path": user_doc_path,
            },
            timeout=10,
        )

        if start_resp.status_code != 200:
            st.error(f"AI Review failed to start: {start_resp.text}")
        else:
            task_id = start_resp.json().get("task_id")
            if not task_id:
                st.error("AI Review failed: no task ID returned.")
            else:
                progress_bar = st.progress(0, text="Starting AI review...")
                poll_count = 0
                max_polls = 90
                not_found_count = 0

                while poll_count < max_polls:
                    time.sleep(2)
                    poll_count += 1
                    progress_bar.progress(
                        min(poll_count / max_polls, 0.95),
                        text=f"AI review in progress... ({poll_count * 2}s)",
                    )
                    try:
                        poll_resp = requests.get(
                            f"{API_BASE}/ai-review/{task_id}",
                            timeout=5,
                        )
                        if poll_resp.status_code == 404:
                            not_found_count += 1
                            if not_found_count > 5:
                                st.error("AI Review task lost. The server may have restarted. Please try again.")
                                progress_bar.empty()
                                break
                            continue
                        if poll_resp.status_code != 200:
                            continue
                        not_found_count = 0
                        poll_data = poll_resp.json()
                        if poll_data["status"] == "complete":
                            ai_result = poll_data["result"]
                            progress_bar.progress(1.0, text="AI review complete!")
                            break
                        elif poll_data["status"] == "failed":
                            st.error(f"AI Review failed: {poll_data.get('error', 'Unknown error')}")
                            progress_bar.empty()
                            break
                    except requests.exceptions.RequestException:
                        continue
                else:
                    st.warning("AI Review timed out after 3 minutes. Please try again.")
                    progress_bar.empty()

        if ai_result is not None:

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
