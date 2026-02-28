import os
import time
import requests
import streamlit as st

API_BASE = os.getenv("CARBONGPT_API_URL", "http://localhost:3000")

st.set_page_config(page_title="CarbonGPT", layout="wide")

PAGES = ["Compliance Analyzer", "Document Repository"]

with st.sidebar:
    st.markdown("### CarbonGPT")
    page = st.radio("Navigation", PAGES, key="nav_page", label_visibility="collapsed")


def _render_ai_result(ai_result):
    global_summary = ai_result.get("global_summary", {})
    risk = global_summary.get("overall_risk", "UNKNOWN")
    risk_colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    risk_color = risk_colors.get(risk, "red")

    st.markdown(f"### Overall Risk: :{risk_color}[**{risk}**]")

    compliance_alerts = ai_result.get("compliance_alerts", [])
    if compliance_alerts:
        st.markdown("### Compliance Alerts")
        for alert in compliance_alerts:
            sev = alert.get("severity", "info")
            icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(sev, "⚪")
            meth = f" (methodology: {alert['methodology']})" if alert.get("methodology") else ""
            if sev == "error":
                st.error(f"{icon} **{alert['title']}**{meth}: {alert['description']}")
            elif sev == "warning":
                st.warning(f"{icon} **{alert['title']}**{meth}: {alert['description']}")
            else:
                st.info(f"{icon} {alert['title']}{meth}: {alert['description']}")
            if alert.get("source_url"):
                st.markdown(f"  Source: [{alert.get('source_description', 'Link')}]({alert['source_url']})")
        st.divider()

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


def _fetch(endpoint, method="GET", **kwargs):
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=10, **kwargs)
        elif method == "POST":
            resp = requests.post(url, timeout=120, **kwargs)
        elif method == "PATCH":
            resp = requests.patch(url, timeout=10, **kwargs)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=10, **kwargs)
        else:
            return None
        if resp.status_code >= 400:
            st.error(f"API Error: {resp.text}")
            return None
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


CATEGORY_LABELS = {
    "standard_text": "Standard Document",
    "methodology": "Methodology",
    "guidance": "Guidance Document",
    "tool": "Calculation Tool",
    "template": "Template",
    "example_pdd": "Example PDD",
    "example_mr": "Example Monitoring Report",
    "example_fvr": "Example Final Verification Report",
    "example_valver": "Example Validation/Verification Report",
    "example_other": "Example (Other)",
    "rule_update": "Rule Update",
    "other": "Other",
}
CATEGORY_OPTIONS = list(CATEGORY_LABELS.keys())


def render_analyzer():
    st.title("CarbonGPT — Compliance Analyzer")
    st.markdown(
        "Upload a document and check it against Gold Standard or Verra VCS templates and rules. "
        "Supports Gold Standard (MR, PDD, PoA-DD, VPA-DD) and Verra VCS "
        "(Project Description, Monitoring Report, Joint Validation & Verification Report)."
    )

    STANDARDS = ["GoldStandard", "Verra"]
    DOC_TYPES = {
        "GoldStandard": ["MR", "PDD", "PoA-DD", "VPA-DD"],
        "Verra": ["VCS-PD", "VCS-MR", "VCS-ValVer"],
    }
    VERSIONS = {
        ("GoldStandard", "MR"): ["MR_v1_1"],
        ("GoldStandard", "PDD"): ["PDD_v1_5"],
        ("GoldStandard", "PoA-DD"): ["PoA-DD_v2_2"],
        ("GoldStandard", "VPA-DD"): ["VPA-DD_v2_3"],
        ("Verra", "VCS-PD"): ["VCS-PD_v4_4"],
        ("Verra", "VCS-MR"): ["VCS-MR_v4_4"],
        ("Verra", "VCS-ValVer"): ["VCS-ValVer_v4_4"],
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
    analyze_btn = st.button("Analyze", type="primary", disabled=uploaded_file is None, key="analyze_btn")

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


def render_repository():
    st.title("CarbonGPT — Document Repository")
    st.markdown(
        "Manage your carbon standards library. Upload standards, methodologies, guidance documents, "
        "templates, and example project documentation. Documents are automatically parsed, indexed, "
        "and classified by AI."
    )

    stats = _fetch("/admin/stats")
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats.get("total_documents", 0), help="Total documents in the repository")
        with col2:
            st.metric("Ingested", stats.get("ingested", 0), help="Documents fully processed")
        with col3:
            st.metric("Total Words", f"{stats.get('total_words', 0):,}", help="Total words extracted")
        with col4:
            st.metric("Vector Chunks", stats.get("total_chunks", 0), help="Searchable text chunks with embeddings")

        pending = stats.get("pending", 0)
        processing = stats.get("processing", 0)
        failed = stats.get("failed", 0)
        if pending > 0 or processing > 0:
            st.info(f"Pending: {pending} | Processing: {processing}")
        if failed > 0:
            st.warning(f"Failed ingestions: {failed}")

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Upload Documents",
        "Document Library",
        "Semantic Search",
        "Compliance Rules",
        "Web Intelligence",
        "Methodology Sync",
        "Manage Standards",
    ])

    with tab1:
        _render_upload()
    with tab2:
        _render_library()
    with tab3:
        _render_search()
    with tab4:
        _render_compliance_rules()
    with tab5:
        _render_web_intelligence()
    with tab6:
        _render_methodology_sync()
    with tab7:
        _render_manage_standards()


def _render_upload():
    st.subheader("Upload Documents")
    st.markdown("Upload PDF, DOCX, XLSX, or CSV files. Documents are automatically parsed, classified, and indexed.")

    standards = _fetch("/admin/standards") or []
    versions = _fetch("/admin/standard-versions") or []

    version_options = {}
    for v in versions:
        label = f"{v['standard_name']} — {v['version']} ({v['status']})"
        version_options[label] = v["id"]

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "Document Category",
            CATEGORY_OPTIONS,
            format_func=lambda x: CATEGORY_LABELS[x],
            key="upload_category",
        )
    with col2:
        version_labels = ["Auto-detect / Not specified"] + list(version_options.keys())
        selected_version = st.selectbox("Standard & Version", version_labels, key="upload_version")

    col3, col4 = st.columns(2)
    with col3:
        reference_id = st.text_input("Reference ID (optional)", placeholder="e.g., VM0007, AMS-II.G", key="upload_ref_id")
    with col4:
        doc_version = st.text_input("Document Version (optional)", placeholder="e.g., v6.0, v09", key="upload_doc_version")

    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "docx", "xlsx", "csv"],
        accept_multiple_files=True,
        key="repo_upload_files",
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected**")

    upload_btn = st.button("Upload & Ingest", type="primary", disabled=not uploaded_files, key="repo_upload_btn")

    if upload_btn and uploaded_files:
        sv_id = version_options.get(selected_version) if selected_version != "Auto-detect / Not specified" else None
        progress = st.progress(0, text="Uploading...")

        for i, f in enumerate(uploaded_files):
            progress.progress((i + 1) / len(uploaded_files), text=f"Uploading {f.name}...")
            files_data = {"file": (f.name, f.getvalue(), "application/octet-stream")}
            form_data = {
                "category": category,
                "title": f.name.rsplit(".", 1)[0],
            }
            if sv_id:
                form_data["standard_version_id"] = str(sv_id)
            if reference_id:
                form_data["reference_id"] = reference_id
            if doc_version:
                form_data["doc_version"] = doc_version

            result = _fetch("/admin/documents/upload", method="POST", files=files_data, data=form_data)
            if result:
                st.success(f"Uploaded: {f.name} (ID: {result['id']})")
            else:
                st.error(f"Failed to upload: {f.name}")

        progress.empty()
        time.sleep(1)
        st.rerun()


def _render_library():
    st.subheader("Document Library")

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All"] + CATEGORY_OPTIONS,
            format_func=lambda x: "All Categories" if x == "All" else CATEGORY_LABELS.get(x, x),
            key="filter_category",
        )
    with col2:
        versions = _fetch("/admin/standard-versions") or []
        version_options = {"All": None}
        for v in versions:
            label = f"{v['standard_name']} — {v['version']}"
            version_options[label] = v["id"]
        filter_version = st.selectbox("Filter by Standard", list(version_options.keys()), key="filter_version")
    with col3:
        st.button("Refresh", key="refresh_library")

    params = {}
    if filter_category != "All":
        params["category"] = filter_category
    sv_id = version_options.get(filter_version)
    if sv_id:
        params["standard_version_id"] = sv_id

    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    endpoint = f"/admin/documents?{query_string}" if query_string else "/admin/documents"
    documents = _fetch(endpoint) or []

    if not documents:
        st.info("No documents found. Upload some documents to get started.")
        return

    for doc in documents:
        status_icons = {
            "completed": "white_check_mark",
            "processing": "hourglass_flowing_sand",
            "pending": "clock3",
            "failed": "x",
        }
        ing_status = doc.get("ingestion_status", "pending")
        icon = status_icons.get(ing_status, "question")

        standard_info = ""
        if doc.get("standard_name"):
            standard_info = f" | {doc['standard_name']} {doc.get('standard_version', '')}"

        title = doc.get("title", "Untitled")
        cat_label = CATEGORY_LABELS.get(doc.get("category", ""), doc.get("category", ""))
        size_kb = (doc.get("file_size_bytes") or 0) / 1024

        with st.expander(f":{icon}: **{title}** — {cat_label}{standard_info}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Category:** {cat_label}")
                st.markdown(f"**File Type:** {doc.get('file_type', '').upper()}")
                st.markdown(f"**Size:** {size_kb:.1f} KB")
                st.markdown(f"**Ingestion:** {ing_status}")
                if doc.get("word_count"):
                    st.markdown(f"**Words:** {doc['word_count']:,}")
                if doc.get("page_count"):
                    st.markdown(f"**Pages:** {doc['page_count']}")
            with col_b:
                if doc.get("auto_detected_standard"):
                    st.markdown(f"**Detected Standard:** {doc['auto_detected_standard']}")
                if doc.get("auto_detected_version"):
                    st.markdown(f"**Detected Version:** {doc['auto_detected_version']}")
                if doc.get("auto_detected_category"):
                    st.markdown(f"**Detected Type:** {doc['auto_detected_category']}")
                if doc.get("auto_detected_applicability"):
                    st.markdown(f"**Applicability:** {doc['auto_detected_applicability']}")
                if doc.get("reference_id"):
                    st.markdown(f"**Reference ID:** {doc['reference_id']}")

            btn_col1, _, btn_col3 = st.columns(3)
            with btn_col1:
                if ing_status in ("failed", "completed"):
                    if st.button("Re-ingest", key=f"reingest_{doc['id']}"):
                        result = _fetch(f"/admin/documents/{doc['id']}/reingest", method="POST")
                        if result:
                            st.success("Re-ingestion started.")
                            time.sleep(1)
                            st.rerun()
            with btn_col3:
                if st.button("Delete", key=f"delete_{doc['id']}", type="secondary"):
                    result = _fetch(f"/admin/documents/{doc['id']}", method="DELETE")
                    if result:
                        st.success("Document deleted.")
                        time.sleep(0.5)
                        st.rerun()


def _render_search():
    st.subheader("Semantic Search")
    st.markdown("Search across all ingested documents using natural language.")

    query = st.text_input(
        "Search query",
        placeholder="e.g., additionality requirements for REDD+ projects",
        key="search_query",
    )
    col1, col2 = st.columns(2)
    with col1:
        limit = st.slider("Results", 3, 20, 5, key="search_limit")
    with col2:
        search_btn = st.button("Search", type="primary", disabled=not query, key="search_btn")

    if search_btn and query:
        with st.spinner("Searching..."):
            results = _fetch(f"/admin/search?q={query}&limit={limit}")

        if results is None:
            return
        if not results:
            st.info("No results found. Make sure documents have been ingested with embeddings.")
            return

        st.markdown(f"**{len(results)} results found:**")
        for i, r in enumerate(results):
            distance = r.get("distance", 0)
            similarity = max(0, 1 - distance)
            doc_title = r.get("document_title", "Unknown")
            standard = r.get("standard_name", "")
            version = r.get("standard_version", "")
            category = r.get("document_category", "")

            with st.expander(
                f"**{i+1}.** {doc_title} ({category}) — "
                f"{standard} {version} — Relevance: {similarity:.0%}"
            ):
                st.markdown(r.get("content", ""))


RULE_TYPE_LABELS = {
    "methodology_status": "Methodology Status",
    "methodology_transition": "Methodology Transition",
    "crediting_period": "Crediting Period",
    "eligibility": "Eligibility Requirement",
    "regulatory": "Regulatory Change",
    "default_value": "Default Value Update",
    "fee_structure": "Fee Structure",
    "general": "General Rule",
}

SEVERITY_LABELS = {
    "error": "Critical",
    "warning": "Warning",
    "info": "Info",
}


def _render_compliance_rules():
    st.subheader("Compliance Rules")
    st.markdown(
        "Manage compliance intelligence rules. These rules are automatically checked "
        "during AI review to catch issues like deprecated methodologies, regulatory changes, "
        "and eligibility requirements. Rules can be added manually or proposed by the AI."
    )

    rules = _fetch("/admin/compliance-rules") or []
    standards = _fetch("/admin/standards") or []

    active_rules = [r for r in rules if r["status"] == "active"]
    proposed_rules = [r for r in rules if r["status"] == "proposed"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Rules", len(active_rules))
    with col2:
        st.metric("Pending Review", len(proposed_rules))
    with col3:
        st.metric("Total Rules", len(rules))

    if proposed_rules:
        st.divider()
        st.markdown("#### Proposed Rules (Pending Admin Review)")
        st.markdown("These rules were discovered by AI during reviews. Approve or reject them.")
        for rule in proposed_rules:
            severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(rule["severity"], "⚪")
            with st.expander(f"{severity_icon} {rule['title']} — {RULE_TYPE_LABELS.get(rule['rule_type'], rule['rule_type'])}"):
                st.markdown(f"**Description:** {rule['description']}")
                if rule.get("source_url"):
                    st.markdown(f"**Source:** [{rule['source_description'] or rule['source_url']}]({rule['source_url']})")
                if rule.get("conditions"):
                    st.json(rule["conditions"])
                st.markdown(f"**Discovered by:** {rule['discovered_by']}")

                acol1, acol2 = st.columns(2)
                with acol1:
                    if st.button("Approve", key=f"approve_{rule['id']}", type="primary"):
                        _fetch(f"/admin/compliance-rules/{rule['id']}", method="PATCH",
                               json={"status": "active"})
                        st.success("Rule approved!")
                        time.sleep(0.5)
                        st.rerun()
                with acol2:
                    if st.button("Reject", key=f"reject_{rule['id']}"):
                        _fetch(f"/admin/compliance-rules/{rule['id']}", method="PATCH",
                               json={"status": "rejected"})
                        st.info("Rule rejected.")
                        time.sleep(0.5)
                        st.rerun()

    st.divider()
    st.markdown("#### Active Rules")
    if not active_rules:
        st.info("No active compliance rules yet. Add rules below or let the AI discover them during reviews.")
    else:
        for rule in active_rules:
            severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(rule["severity"], "⚪")
            std_name = rule.get("standard_name") or "All Standards"
            with st.expander(f"{severity_icon} {rule['title']} — {std_name} — {RULE_TYPE_LABELS.get(rule['rule_type'], rule['rule_type'])}"):
                st.markdown(f"**Description:** {rule['description']}")
                st.markdown(f"**Severity:** {SEVERITY_LABELS.get(rule['severity'], rule['severity'])}")
                if rule.get("effective_date"):
                    st.markdown(f"**Effective:** {rule['effective_date']}")
                if rule.get("expiry_date"):
                    st.markdown(f"**Expires:** {rule['expiry_date']}")
                if rule.get("source_url"):
                    st.markdown(f"**Source:** [{rule.get('source_description') or 'Link'}]({rule['source_url']})")
                if rule.get("conditions"):
                    st.json(rule["conditions"])
                if st.button("Delete", key=f"del_rule_{rule['id']}"):
                    _fetch(f"/admin/compliance-rules/{rule['id']}", method="DELETE")
                    st.rerun()

    st.divider()
    with st.expander("Add New Compliance Rule"):
        std_options = {"All Standards": None}
        for s in standards:
            std_options[s["name"]] = s["id"]

        r_col1, r_col2 = st.columns(2)
        with r_col1:
            new_rule_type = st.selectbox(
                "Rule Type",
                list(RULE_TYPE_LABELS.keys()),
                format_func=lambda x: RULE_TYPE_LABELS[x],
                key="new_rule_type"
            )
        with r_col2:
            new_severity = st.selectbox(
                "Severity",
                list(SEVERITY_LABELS.keys()),
                format_func=lambda x: SEVERITY_LABELS[x],
                key="new_rule_severity"
            )

        new_rule_std = st.selectbox("Standard", list(std_options.keys()), key="new_rule_std")
        new_rule_title = st.text_input("Title", key="new_rule_title",
                                       placeholder="e.g., AMS-II.G deprecated for VCS projects")
        new_rule_desc = st.text_area("Description", key="new_rule_desc",
                                     placeholder="e.g., AMS-II.G is no longer accepted as a standalone methodology under VCS. Projects must use VMR0006 v1.2 instead.")
        new_rule_source = st.text_input("Source URL (optional)", key="new_rule_source",
                                        placeholder="e.g., https://verra.org/...")
        new_rule_source_desc = st.text_input("Source Description (optional)", key="new_rule_source_desc",
                                             placeholder="e.g., Verra announcement, July 2023")

        st.markdown("**Conditions (JSON)** — Define matching criteria:")
        st.markdown("- `affected_methodologies`: list of methodology IDs to match (e.g., `[\"AMS-II.G\", \"AMS-IIG\"]`)")
        st.markdown("- `keywords`: list of keywords to search in document text")
        st.markdown("- `check_in_document`: list of keywords that trigger this rule when found")
        new_rule_conditions = st.text_area(
            "Conditions JSON",
            value='{"affected_methodologies": [], "keywords": []}',
            key="new_rule_conditions"
        )

        r_col3, r_col4 = st.columns(2)
        with r_col3:
            new_rule_eff = st.text_input("Effective Date (YYYY-MM-DD, optional)", key="new_rule_eff")
        with r_col4:
            new_rule_exp = st.text_input("Expiry Date (YYYY-MM-DD, optional)", key="new_rule_exp")

        if st.button("Create Rule", key="create_rule_btn", type="primary"):
            if new_rule_title and new_rule_desc:
                import json as _json
                try:
                    conditions = _json.loads(new_rule_conditions)
                except Exception:
                    st.error("Invalid JSON in conditions field.")
                    conditions = None

                if conditions is not None:
                    result = _fetch("/admin/compliance-rules", method="POST",
                                    json={
                                        "standard_id": std_options[new_rule_std],
                                        "rule_type": new_rule_type,
                                        "severity": new_severity,
                                        "title": new_rule_title,
                                        "description": new_rule_desc,
                                        "conditions": conditions,
                                        "source_url": new_rule_source or None,
                                        "source_description": new_rule_source_desc or None,
                                        "effective_date": new_rule_eff or None,
                                        "expiry_date": new_rule_exp or None,
                                        "status": "active",
                                        "discovered_by": "admin",
                                    })
                    if result:
                        st.success("Compliance rule created!")
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.warning("Title and description are required.")


def _render_methodology_sync():
    st.subheader("Document Sync")
    st.markdown(
        "Download program standards, methodologies, guides, templates, and project "
        "documents from Verra, CDM/UNFCCC, and Gold Standard public catalogs and registries. "
        "Documents are stored in the repository, parsed, and embedded for AI-powered reviews."
    )

    status = _fetch("/admin/methodology-sync/status")
    if status:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Documents", status.get("total_documents", 0))
        with col2:
            by_source = status.get("by_source", {})
            st.metric("Verra", by_source.get("verra", 0))
        with col3:
            st.metric("CDM", by_source.get("cdm", 0))
        with col4:
            st.metric("Gold Standard", by_source.get("goldstandard", 0))
        with col5:
            st.metric("Manual", by_source.get("manual", 0))

        by_category = status.get("by_category", {})
        if by_category:
            cat_parts = []
            for cat, count in sorted(by_category.items()):
                cat_parts.append(f"{cat}: {count}")
            st.markdown(f"**By category:** {' | '.join(cat_parts)}")

        scheduler_status = "Active" if status.get("scheduler_active") else "Inactive"
        interval = status.get("sync_interval_hours", 168)
        st.markdown(
            f"**Auto-sync scheduler:** {scheduler_status} "
            f"(interval: {interval} hours / {interval // 24} days). "
            f"Set `CARBONGPT_AUTO_SYNC=true` to enable."
        )

    st.divider()

    col_sync, col_config = st.columns(2)

    with col_sync:
        st.markdown("#### Run Sync Now")

        source_options = {
            "Verra VCS": "verra",
            "CDM/UNFCCC": "cdm",
            "Gold Standard": "goldstandard",
        }
        selected_sources = st.multiselect(
            "Sources to sync",
            options=list(source_options.keys()),
            default=list(source_options.keys()),
            key="sync_sources",
        )

        max_per_source = st.slider(
            "Max documents per source",
            min_value=5,
            max_value=200,
            value=50,
            step=5,
            key="sync_max",
        )

        include_program = st.checkbox(
            "Include program standards, guides, and templates",
            value=True,
            key="sync_program_docs",
        )

        include_registry = st.checkbox(
            "Include real project documents from registries (PDs, MRs, validation/verification reports)",
            value=False,
            key="sync_registry",
        )

        if include_registry:
            max_projects = st.slider(
                "Max registry projects to scan",
                min_value=1,
                max_value=500,
                value=10,
                step=5,
                key="sync_max_projects",
            )
            discover_projects = st.checkbox(
                "Auto-discover projects (scan registries for new project IDs instead of using seed list)",
                value=max_projects > 10,
                key="sync_discover",
            )
            st.caption(
                "Verra: direct PDF download from registry. "
                "Gold Standard: document metadata scraped (downloads require auth -- metadata indexed for reference). "
                f"Scanning {max_projects} projects takes ~{max_projects * 3 // 60 + 1} minutes."
            )
        else:
            max_projects = 5
            discover_projects = False

        dry_run = st.checkbox("Dry run (preview only, no downloads)", value=True, key="sync_dry_run")

        if st.button("Start Sync", key="sync_start_btn"):
            sources = [source_options[s] for s in selected_sources]
            with st.spinner("Syncing documents (this may take several minutes)..."):
                result = _fetch(
                    "/admin/methodology-sync",
                    method="POST",
                    json={
                        "sources": sources,
                        "max_per_source": max_per_source,
                        "dry_run": dry_run,
                        "include_program_docs": include_program,
                        "include_registry_projects": include_registry,
                        "max_registry_projects": max_projects,
                        "discover_projects": discover_projects,
                    },
                )

            if result:
                skipped = result.get('skipped_no_download', 0)
                skipped_msg = f", {skipped} metadata-only" if skipped else ""
                st.success(
                    f"Sync complete: {result.get('total_found', 0)} found, "
                    f"{result.get('already_stored', 0)} already stored, "
                    f"{result.get('newly_downloaded', 0)} newly downloaded, "
                    f"{result.get('ingestion_started', 0)} ingestion started, "
                    f"{result.get('errors', 0)} errors{skipped_msg}"
                )

                details = result.get("details", [])
                if details:
                    status_counts = {}
                    category_counts = {}
                    for d in details:
                        s = d.get("status", "unknown")
                        status_counts[s] = status_counts.get(s, 0) + 1
                        cat = d.get("category", "unknown")
                        category_counts[cat] = category_counts.get(cat, 0) + 1

                    st.markdown("**By status:**")
                    for s, count in sorted(status_counts.items()):
                        st.markdown(f"- {s}: {count}")

                    st.markdown("**By type:**")
                    for cat, count in sorted(category_counts.items()):
                        st.markdown(f"- {cat}: {count}")

                    with st.expander("Details", expanded=False):
                        for d in details[:80]:
                            status_label = d.get("status", "unknown")
                            code = d.get("code", "?")
                            source = d.get("source", "?")
                            cat = d.get("category", "")
                            title = d.get("title", "")
                            line = f"[{source}/{cat}] {code}: {status_label}"
                            if title:
                                line += f" - {title[:60]}"
                            if d.get("doc_id"):
                                line += f" (doc #{d['doc_id']})"
                            st.text(line)
                        if len(details) > 80:
                            st.text(f"... and {len(details) - 80} more")
            else:
                st.error("Sync failed.")

    with col_config:
        st.markdown("#### What Gets Downloaded")
        st.markdown(
            "**Methodologies** - Active VM/VMR methodologies (Verra), CDM tools and "
            "methodology booklet, Gold Standard sector methodologies\n\n"
            "**Program Standards & Guides** - VCS Standard, Program Guide, Registration "
            "Process, Methodology Requirements, AFOLU Non-Permanence Risk Tool, "
            "GS Principles & Requirements, Safeguarding, Stakeholder Consultation, "
            "VVB Requirements, CDM Glossary, Validation Standard\n\n"
            "**Templates** - PD, MR, and ValVer report templates (Verra), "
            "MR/PDD/Validation/Verification guides (Gold Standard), CDM PDD form\n\n"
            "**Registry Projects** (optional) - Real project descriptions, monitoring reports, "
            "and validation/verification reports from the Verra public registry\n\n"
            "**Rate limiting:** 2-second delay between requests. "
            "Run dry-run first to preview."
        )


def _render_web_intelligence():
    st.subheader("Web Intelligence")
    st.markdown(
        "Search the web for methodology status updates, regulatory changes, "
        "and compliance-relevant information. Findings can be saved as proposed "
        "compliance rules for admin review."
    )

    col_verify, col_refresh = st.columns(2)

    with col_verify:
        st.markdown("#### Verify Methodology")
        meth_input = st.text_input(
            "Methodology ID",
            placeholder="e.g. AMS-II.G, VM0050, VMR0006",
            key="wi_meth_input",
        )
        standard_choice = st.selectbox(
            "Standard",
            ["Verra VCS", "Gold Standard", "CDM/UNFCCC"],
            key="wi_standard",
        )

        standards = _fetch("/admin/standards") or []
        std_id = None
        for s in standards:
            if standard_choice == "Verra VCS" and s.get("slug") == "verra":
                std_id = s["id"]
            elif standard_choice == "Gold Standard" and s.get("slug") == "goldstandard":
                std_id = s["id"]

        if st.button("Verify Status", key="wi_verify_btn", disabled=not meth_input):
            with st.spinner("Searching web and analyzing..."):
                result = _fetch(
                    "/admin/web-intelligence/verify-methodology",
                    method="POST",
                    json={"methodology": meth_input, "standard": standard_choice, "standard_id": std_id},
                )
            if result and result.get("result"):
                r = result["result"]
                status = r.get("status", "unknown")
                confidence = r.get("confidence", "unknown")

                status_colors = {
                    "approved": "green",
                    "deprecated": "red",
                    "transitioning": "orange",
                    "conditional": "yellow",
                    "unknown": "gray",
                }
                color = status_colors.get(status, "gray")
                st.markdown(f"**Status:** :{color}[{status.upper()}] (confidence: {confidence})")
                st.markdown(f"**Summary:** {r.get('summary', 'N/A')}")
                if r.get("replacement"):
                    st.info(f"Replacement: {r['replacement']}")
                if r.get("deadline"):
                    st.warning(f"Deadline: {r['deadline']}")
                if r.get("source_url"):
                    st.markdown(f"[Source]({r['source_url']})")

                if r.get("proposed_rule_title"):
                    st.divider()
                    st.markdown("**Proposed compliance rule:**")
                    st.markdown(f"- **{r['proposed_rule_title']}**")
                    st.markdown(f"  {r.get('proposed_rule_description', '')}")
                    if st.button("Save as Proposed Rule", key="wi_save_rule"):
                        save_result = _fetch(
                            "/admin/web-intelligence/propose-rule",
                            method="POST",
                            json={"methodology": meth_input, "standard": standard_choice, "standard_id": std_id},
                        )
                        if save_result and save_result.get("proposed_rule"):
                            rule_data = save_result["proposed_rule"]
                            create_result = _fetch("/admin/compliance-rules", method="POST", json=rule_data)
                            if create_result and create_result.get("id"):
                                st.success(f"Rule saved as proposed (ID: {create_result['id']}). Review it in the Compliance Rules tab.")
                            else:
                                st.error("Failed to save rule.")
                        else:
                            msg = save_result.get("message", "No rule to propose.") if save_result else "Request failed."
                            st.info(msg)
            else:
                st.error("Verification failed. Check that OPENAI_API_KEY is set.")

    with col_refresh:
        st.markdown("#### Knowledge Refresh")
        st.markdown(
            "Search for recent regulatory updates across a standard. "
            "Findings are saved as proposed rules for your review."
        )
        refresh_standard = st.selectbox(
            "Standard to research",
            ["Verra VCS", "Gold Standard", "CDM/UNFCCC"],
            key="wi_refresh_standard",
        )
        custom_topics = st.text_area(
            "Custom search topics (one per line, optional)",
            placeholder="e.g.\nVCS buffer pool update 2025\nNew cookstove methodology M0174",
            key="wi_custom_topics",
            height=100,
        )

        refresh_std_id = None
        for s in standards:
            if refresh_standard == "Verra VCS" and s.get("slug") == "verra":
                refresh_std_id = s["id"]
            elif refresh_standard == "Gold Standard" and s.get("slug") == "goldstandard":
                refresh_std_id = s["id"]

        auto_save = st.checkbox("Auto-save findings as proposed rules", value=True, key="wi_auto_save")

        if st.button("Run Knowledge Refresh", key="wi_refresh_btn"):
            topics = None
            if custom_topics.strip():
                topics = [t.strip() for t in custom_topics.strip().split("\n") if t.strip()]

            with st.spinner("Researching standard updates (this may take 30-60 seconds)..."):
                result = _fetch(
                    "/admin/web-intelligence/knowledge-refresh",
                    method="POST",
                    json={
                        "standard": refresh_standard,
                        "standard_id": refresh_std_id,
                        "topics": topics,
                        "auto_save": auto_save,
                    },
                )

            if result:
                total = result.get("total_found", 0)
                saved = result.get("saved_count", 0)

                if total == 0:
                    st.info("No new compliance-relevant findings discovered.")
                else:
                    st.success(f"Found {total} potential update(s). {saved} saved as proposed rules.")
                    for i, rule in enumerate(result.get("proposed_rules", [])):
                        sev = rule.get("severity", "info").upper()
                        with st.expander(f"[{sev}] {rule.get('title', 'Untitled')}", expanded=(i < 3)):
                            st.markdown(f"**Type:** {rule.get('rule_type', 'general')}")
                            st.markdown(f"**Description:** {rule.get('description', 'N/A')}")
                            if rule.get("source_url"):
                                st.markdown(f"**Source:** [{rule['source_url']}]({rule['source_url']})")
                            if rule.get("source_description"):
                                st.markdown(f"**Source info:** {rule['source_description']}")
            else:
                st.error("Knowledge refresh failed. Check that OPENAI_API_KEY is set.")

    st.divider()
    st.markdown("#### Web Search Configuration")
    serper_status = "Configured" if os.environ.get("SERPER_API_KEY") else "Not configured"
    openai_status = "Configured" if os.environ.get("OPENAI_API_KEY") else "Not configured"
    web_search_enabled = os.environ.get("CARBONGPT_WEB_SEARCH", "").lower() in ("1", "true", "yes")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("OpenAI API", openai_status)
    with col2:
        st.metric("Serper Search API", serper_status)
    with col3:
        st.metric("Auto Web Search in Reviews", "Enabled" if web_search_enabled else "Disabled")

    st.markdown(
        "**Setup:** Set `SERPER_API_KEY` for web search (get one at [serper.dev](https://serper.dev)). "
        "Set `CARBONGPT_WEB_SEARCH=true` to enable automatic web search during AI reviews for "
        "methodologies not found in the compliance rules database."
    )


def _render_manage_standards():
    st.subheader("Manage Standards & Versions")

    standards = _fetch("/admin/standards") or []
    versions = _fetch("/admin/standard-versions") or []

    st.markdown("**Existing Standards:**")
    for s in standards:
        s_versions = [v for v in versions if v["standard_id"] == s["id"]]
        version_str = ", ".join(f"{v['version']} ({v['status']})" for v in s_versions) or "No versions"
        st.markdown(f"- **{s['name']}** (`{s['slug']}`) — Versions: {version_str}")

    st.divider()

    with st.expander("Add New Standard"):
        new_name = st.text_input("Standard Name", key="new_std_name")
        new_slug = st.text_input("Slug", key="new_std_slug")
        new_desc = st.text_area("Description", key="new_std_desc")
        if st.button("Create Standard", key="create_std_btn"):
            if new_name and new_slug:
                result = _fetch("/admin/standards", method="POST",
                                json={"name": new_name, "slug": new_slug, "description": new_desc})
                if result:
                    st.success(f"Standard '{new_name}' created.")
                    time.sleep(0.5)
                    st.rerun()

    with st.expander("Add New Version"):
        std_options = {s["name"]: s["id"] for s in standards}
        if std_options:
            selected_std = st.selectbox("Standard", list(std_options.keys()), key="new_ver_std")
            new_ver = st.text_input("Version", key="new_ver_version")
            new_date = st.text_input("Effective Date (YYYY-MM-DD)", key="new_ver_date")
            new_status = st.selectbox("Status", ["active", "superseded", "draft"], key="new_ver_status")
            if st.button("Create Version", key="create_ver_btn"):
                if new_ver:
                    result = _fetch("/admin/standard-versions", method="POST",
                                    json={
                                        "standard_id": std_options[selected_std],
                                        "version": new_ver,
                                        "effective_date": new_date or None,
                                        "status": new_status,
                                    })
                    if result:
                        st.success(f"Version '{new_ver}' created.")
                        time.sleep(0.5)
                        st.rerun()
        else:
            st.info("Create a standard first.")


if page == "Compliance Analyzer":
    render_analyzer()
elif page == "Document Repository":
    render_repository()
