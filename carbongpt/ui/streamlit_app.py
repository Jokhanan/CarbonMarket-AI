"""
streamlit_app.py — CarbonGPT Web UI

Provides a simple interface for uploading .docx monitoring reports,
selecting an internal template (Standard + Doc Type + Version), and
viewing compliance analysis results.
"""

import os
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
