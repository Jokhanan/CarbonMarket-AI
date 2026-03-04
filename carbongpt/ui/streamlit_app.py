import os
import time
import requests
import streamlit as st

API_BASE = os.getenv("CARBONGPT_API_URL", "http://localhost:3000")

st.set_page_config(page_title="CarbonGPT", layout="wide", page_icon="C")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(180deg, #f8f9fb 0%, #f0f2f5 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1821 0%, #162837 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e8edf2;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #c0cad8 !important;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08);
    }

    .brand-header {
        padding: 0.5rem 0 1.2rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }
    .brand-header h2 {
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        background: linear-gradient(135deg, #4ecdc4, #45b7d1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .brand-tagline {
        font-size: 0.72rem;
        color: #7a8a9e;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 2px;
    }

    .page-header {
        padding: 0 0 1.5rem 0;
        margin-bottom: 0.5rem;
    }
    .page-header h1 {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #1a1a2e;
        margin-bottom: 0.25rem;
    }
    .page-subtitle {
        font-size: 0.92rem;
        color: #64748b;
        line-height: 1.5;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetric"] label {
        color: #64748b;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1e293b;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px;
        border-color: #e2e8f0;
        background: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: all 0.2s ease;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4ecdc4, #44a8b3);
        border: none;
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: 0.01em;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(78,205,196,0.2);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #44b8b0, #3d9aa5);
        box-shadow: 0 4px 12px rgba(78,205,196,0.35);
        transform: translateY(-1px);
    }
    .stButton > button[kind="secondary"] {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="secondary"]:hover {
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 2px solid #e2e8f0;
        background: transparent;
        padding: 0 0 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        font-size: 0.88rem;
        padding: 0.7rem 1.4rem;
        border-radius: 10px 10px 0 0;
        color: #64748b;
        transition: all 0.2s ease;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #334155;
        background: rgba(78,205,196,0.06);
    }
    .stTabs [aria-selected="true"] {
        color: #1e293b !important;
        font-weight: 600 !important;
        border-bottom: 3px solid #4ecdc4 !important;
        background: rgba(78,205,196,0.04) !important;
    }

    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 0.9rem;
    }

    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.73rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    .status-draft { background: #f1f5f9; color: #64748b; }
    .status-active { background: #ecfdf5; color: #059669; }
    .status-review { background: #eff6ff; color: #2563eb; }
    .status-complete { background: #f0fdf4; color: #16a34a; }

    .project-type-badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-pdd { background: #dbeafe; color: #1d4ed8; }
    .badge-mr { background: #fef3c7; color: #b45309; }
    .badge-poa { background: #ede9fe; color: #7c3aed; }
    .badge-vpa { background: #e0e7ff; color: #4338ca; }
    .badge-valver { background: #fce7f3; color: #be185d; }

    .project-card-gs {
        border-left: 4px solid #d4a843 !important;
    }
    .project-card-verra {
        border-left: 4px solid #3b82f6 !important;
    }

    .section-card-drafted {
        border-left: 4px solid #22c55e !important;
    }
    .section-card-empty {
        border-left: 4px solid #e2e8f0 !important;
    }
    .section-card-revision {
        border-left: 4px solid #f59e0b !important;
    }

    .step-indicator {
        display: flex;
        gap: 0;
        align-items: center;
        padding: 0.6rem 0;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 0.3rem 0.8rem;
        font-size: 0.75rem;
        font-weight: 500;
        color: #94a3b8;
        border-radius: 20px;
    }
    .step-item.active {
        background: rgba(78,205,196,0.1);
        color: #0f766e;
        font-weight: 600;
    }
    .step-item.done {
        color: #22c55e;
    }
    .step-arrow {
        color: #cbd5e1;
        font-size: 0.75rem;
        margin: 0 2px;
    }

    .doc-toggle-card {
        display: flex;
        align-items: center;
        padding: 0.8rem 1rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        margin-bottom: 0.5rem;
        transition: all 0.15s ease;
    }
    .doc-toggle-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }

    .type-selector-card {
        padding: 1.2rem 1rem;
        border: 2px solid #e2e8f0;
        border-radius: 14px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        background: #ffffff;
    }
    .type-selector-card:hover {
        border-color: #4ecdc4;
        box-shadow: 0 4px 12px rgba(78,205,196,0.15);
        transform: translateY(-2px);
    }
    .type-selector-card.selected {
        border-color: #4ecdc4;
        background: rgba(78,205,196,0.04);
        box-shadow: 0 4px 12px rgba(78,205,196,0.15);
    }

    .stButton > button, .stSelectbox, .stTextInput input {
        transition: all 0.15s ease;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        border-radius: 10px !important;
    }

    hr {
        border-color: #e2e8f0 !important;
        margin: 1rem 0 !important;
    }

    div[data-testid="stMetric"] button[title="View fullscreen"] {
        display: none;
    }

    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        border-radius: 16px;
        border: 1px dashed #cbd5e1;
        margin: 1rem 0;
    }
    .empty-state-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .empty-state-desc {
        font-size: 0.88rem;
        color: #64748b;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

PAGES = ["Workspace", "Admin"]

with st.sidebar:
    st.markdown("""
    <div class="brand-header">
        <h2>CarbonGPT</h2>
        <div class="brand-tagline">AI Carbon Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
    page = st.radio("Navigation", PAGES, key="nav_page", label_visibility="collapsed")
    st.divider()
    st.caption("CarbonGPT v1.0")


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
            meth = f" (methodology: {alert['methodology']})" if alert.get("methodology") else ""
            if sev == "error":
                st.error(f"**{alert['title']}**{meth}: {alert['description']}")
            elif sev == "warning":
                st.warning(f"**{alert['title']}**{meth}: {alert['description']}")
            else:
                st.info(f"{alert['title']}{meth}: {alert['description']}")
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
            sec_label = "PASS"
        elif sec_score >= 50:
            sec_label = "REVIEW"
        else:
            sec_label = "FAIL"

        with st.expander(f"[{sec_label}] {sec_id}: {sec_title} -- Score: {sec_score}/100"):
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


def _fetch(endpoint, method="GET", timeout=None, **kwargs):
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=timeout or 10, **kwargs)
        elif method == "POST":
            resp = requests.post(url, timeout=timeout or 120, **kwargs)
        elif method == "PATCH":
            resp = requests.patch(url, timeout=timeout or 10, **kwargs)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=timeout or 10, **kwargs)
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


def render_repository():
    st.markdown("""
    <div class="page-header">
        <h1>Admin</h1>
        <div class="page-subtitle">Document repository, compliance rules, knowledge base, and sync tools</div>
    </div>
    """, unsafe_allow_html=True)
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
                "Auto-discover projects (search Verra registry API for all VCS projects instead of using seed list)",
                value=max_projects > 10,
                key="sync_discover",
            )
            st.caption(
                "Verra: direct PDF download via registry API (PDs, MRs, validation/verification reports, ~30-80 docs/project). "
                "Gold Standard: project metadata via public API (document downloads require auth). "
                "CDM/UNFCCC: project documents not available (bot protection)."
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


def render_intelligence():
    analytics = _fetch("/admin/projects/analytics")
    if not analytics or not analytics.get("summary"):
        st.warning("No project data available. Use the Sync tab to import projects from registries.")
        if st.button("Sync Projects Now", key="sync_empty_btn", type="primary"):
            with st.spinner("Syncing projects from registries..."):
                result = _fetch("/admin/sync-projects", method="POST")
                if result:
                    total = result.get("total_synced", 0)
                    st.success(f"Synced {total:,} projects.")
                    time.sleep(1)
                    st.rerun()
        return

    summary = analytics["summary"]

    tabs = st.tabs(["Global Overview", "Country Explorer", "Methodology Analysis",
                     "Project Browser", "Sync"])

    with tabs[0]:
        _render_global_overview(analytics, summary)

    with tabs[1]:
        _render_country_explorer(analytics)

    with tabs[2]:
        _render_methodology_analysis()

    with tabs[3]:
        _render_project_browser()

    with tabs[4]:
        _render_sync_controls(summary)


def _render_global_overview(analytics, summary):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Projects", f"{summary['total_projects']:,}",
                   help="Total carbon projects across all registries")
    with col2:
        credits = summary.get("total_estimated_credits", 0) or 0
        if credits >= 1_000_000_000:
            credits_str = f"{credits / 1_000_000_000:.1f}B"
        elif credits >= 1_000_000:
            credits_str = f"{credits / 1_000_000:.0f}M"
        else:
            credits_str = f"{credits:,}"
        st.metric("Est. Annual Credits", credits_str,
                   help="Total estimated annual emission reductions (tCO2e)")
    with col3:
        st.metric("Countries", f"{summary['total_countries']}")
    with col4:
        st.metric("Registries", f"{summary['total_registries']}")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Top 15 Countries by Project Count")
        countries = analytics.get("by_country", [])[:15]
        if countries:
            import pandas as pd
            df = pd.DataFrame(countries)
            df = df.rename(columns={"country": "Country", "project_count": "Projects", "total_credits": "Est. Credits"})
            st.bar_chart(df.set_index("Country")["Projects"])

    with col_right:
        st.subheader("Projects by Region")
        regions = analytics.get("by_region", [])
        if regions:
            import pandas as pd
            df = pd.DataFrame(regions)
            df = df.rename(columns={"region": "Region", "project_count": "Projects", "total_credits": "Est. Credits"})
            st.bar_chart(df.set_index("Region")["Projects"])

    st.divider()

    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.subheader("Project Status Distribution")
        statuses = analytics.get("by_status", [])
        if statuses:
            import pandas as pd
            df = pd.DataFrame(statuses)
            df = df.rename(columns={"status": "Status", "project_count": "Projects"})
            st.bar_chart(df.set_index("Status")["Projects"])

    with col_right2:
        st.subheader("Project Types")
        types = analytics.get("by_project_type", [])[:10]
        if types:
            import pandas as pd
            df = pd.DataFrame(types)
            df["project_type"] = df["project_type"].str[:40]
            df = df.rename(columns={"project_type": "Type", "project_count": "Projects", "total_credits": "Est. Credits"})
            st.bar_chart(df.set_index("Type")["Projects"])

    by_registry = analytics.get("by_registry", [])
    if by_registry:
        st.divider()
        st.subheader("By Registry")
        cols = st.columns(len(by_registry))
        for i, reg in enumerate(by_registry):
            with cols[i]:
                label = "Verra VCS" if reg["registry"] == "verra" else "Gold Standard"
                st.metric(label, f"{reg['project_count']:,} projects")


def _render_country_explorer(analytics):
    countries = analytics.get("by_country", [])
    if not countries:
        st.info("No country data available.")
        return

    country_names = [c["country"] for c in countries]
    selected = st.selectbox("Select a country", country_names,
                            key="country_select",
                            help="Choose a country to explore its carbon projects")

    if selected:
        detail = _fetch(f"/admin/projects/country/{selected}")
        if not detail:
            st.warning("Could not load country details.")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Projects", f"{detail['total']}")
        with col2:
            total_credits = sum(
                (p.get("estimated_annual_credits") or 0) for p in detail.get("projects", [])
            )
            st.metric("Est. Annual Credits", f"{total_credits:,}")
        with col3:
            st.metric("Developers", f"{len(detail.get('developers', []))}")

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Methodologies")
            meths = detail.get("methodologies", [])
            if meths:
                import pandas as pd
                df = pd.DataFrame(meths)
                df = df.rename(columns={"methodology": "Methodology", "count": "Projects", "credits": "Est. Credits"})
                st.dataframe(df, width="stretch", hide_index=True)

        with col_right:
            st.subheader("Top Developers")
            devs = detail.get("developers", [])
            if devs:
                import pandas as pd
                df = pd.DataFrame(devs)
                df = df.rename(columns={"proponent": "Developer", "count": "Projects"})
                st.dataframe(df, width="stretch", hide_index=True)

        statuses = detail.get("statuses", [])
        if statuses:
            st.subheader("Status Breakdown")
            import pandas as pd
            df = pd.DataFrame(statuses)
            df = df.rename(columns={"status": "Status", "count": "Projects"})
            st.bar_chart(df.set_index("Status")["Projects"])

        st.subheader(f"All Projects in {selected}")
        projects = detail.get("projects", [])
        if projects:
            import pandas as pd
            df = pd.DataFrame(projects)
            display_cols = ["name", "status", "methodology", "proponent", "estimated_annual_credits", "registry"]
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()
            df_display.columns = [c.replace("_", " ").title() for c in display_cols]
            st.dataframe(df_display, width="stretch", hide_index=True)


def _render_methodology_analysis():
    st.subheader("Top Methodologies")
    meths = _fetch("/admin/projects/methodologies?limit=30")
    if not meths:
        st.info("No methodology data available.")
        return

    import pandas as pd
    df = pd.DataFrame(meths)
    df = df.rename(columns={
        "methodology": "Methodology",
        "project_count": "Projects",
        "total_credits": "Est. Annual Credits"
    })

    st.dataframe(df, width="stretch", hide_index=True)

    st.subheader("Projects per Methodology")
    top_10 = df.head(15)
    st.bar_chart(top_10.set_index("Methodology")["Projects"])

    st.subheader("Credits per Methodology")
    top_credits = df.sort_values("Est. Annual Credits", ascending=False).head(15)
    st.bar_chart(top_credits.set_index("Methodology")["Est. Annual Credits"])


def _render_project_browser():
    col1, col2, col3 = st.columns(3)
    with col1:
        search_q = st.text_input("Search projects", key="proj_search",
                                  placeholder="Project name, country, methodology...")
    with col2:
        registry_filter = st.selectbox("Registry", ["All", "verra", "goldstandard"],
                                        key="proj_registry")
    with col3:
        status_filter = st.selectbox("Status", ["All", "Registered", "Under development",
                                                  "Under validation", "Late to verify"],
                                      key="proj_status")

    if search_q:
        projects = _fetch(f"/admin/projects/search?q={search_q}&limit=100")
    else:
        params = []
        if registry_filter != "All":
            params.append(f"registry={registry_filter}")
        if status_filter != "All":
            params.append(f"status={status_filter}")
        params.append("limit=100")
        query_str = "&".join(params)
        projects = _fetch(f"/admin/projects?{query_str}")

    if not projects:
        st.info("No projects found matching your criteria.")
        return

    st.write(f"Showing {len(projects)} projects")

    import pandas as pd
    df = pd.DataFrame(projects)
    display_cols = ["registry", "registry_id", "name", "country", "status", "methodology",
                    "project_type", "proponent", "estimated_annual_credits"]
    display_cols = [c for c in display_cols if c in df.columns]
    df_display = df[display_cols].copy()
    df_display.columns = [c.replace("_", " ").title() for c in display_cols]
    st.dataframe(df_display, width="stretch", hide_index=True)


def _render_sync_controls(summary):
    st.subheader("Project Data Sync")

    sync_status = _fetch("/admin/sync-projects/status")

    st.write(f"Total projects in database: {summary.get('total_projects', 0):,}")
    st.write(f"Countries covered: {summary.get('total_countries', 0)}")

    if sync_status and sync_status.get("running"):
        st.info("A sync is currently running in the background. Refresh this page to check progress.")
        current_count = sync_status.get("total_projects_in_db", 0)
        st.write(f"Current project count: {current_count:,}")
    else:
        last_result = sync_status.get("last_result") if sync_status else None
        if last_result and not last_result.get("error"):
            verra = last_result.get("verra", {})
            gs = last_result.get("goldstandard", {})
            st.write(
                f"Last sync: Verra {verra.get('synced', 0):,} projects, "
                f"Gold Standard {gs.get('synced', 0):,} projects"
            )

    st.divider()

    if st.button("Sync All Projects", key="sync_all_btn", type="primary",
                  help="Fetch latest project data from Verra and Gold Standard registries"):
        result = _fetch("/admin/sync-projects", method="POST")
        if result:
            status = result.get("status", "")
            if status == "started":
                st.success("Sync started in the background. Refresh this page in a few minutes to see results.")
            elif status == "already_running":
                st.warning("A sync is already running. Please wait for it to finish.")
            else:
                verra = result.get("verra", {})
                gs = result.get("goldstandard", {})
                st.success(
                    f"Sync complete. "
                    f"Verra: {verra.get('synced', 0):,} projects. "
                    f"Gold Standard: {gs.get('synced', 0):,} projects."
                )
                time.sleep(1)
                st.rerun()


@st.cache_data(ttl=300)
def _load_methodologies(standard=None):
    params = f"?limit=300"
    if standard:
        std_map = {"GoldStandard": "GoldStandard", "Verra": "Verra"}
        mapped = std_map.get(standard)
        if mapped:
            params += f"&standard={mapped}"
    result = _fetch(f"/projects/methodologies{params}")
    return result or []


def _methodology_selector(key_prefix, standard=None, current_value=None):
    meths = _load_methodologies()
    search = st.text_input("Search methodology", key=f"{key_prefix}_meth_search",
                            placeholder="Type to search (e.g., AMS-II.G, cookstove, REDD)...")
    if search:
        search_lower = search.lower()
        filtered = [m for m in meths if
                    search_lower in (m.get("code") or "").lower() or
                    search_lower in (m.get("name") or "").lower() or
                    search_lower in (m.get("sector") or "").lower()]
    else:
        filtered = meths

    if standard and not search:
        allowed_standards = {"CDM"}
        if standard == "GoldStandard":
            allowed_standards.add("GoldStandard")
        elif standard == "Verra":
            allowed_standards.add("Verra")
        std_filtered = [m for m in filtered if m.get("standard") in allowed_standards]
        if std_filtered:
            filtered = std_filtered

    if not search:
        filtered = [m for m in filtered if (m.get("name") or "").strip()]

    if standard and not search:
        def _sort_key(m):
            ms = m.get("standard", "")
            if standard == "GoldStandard" and ms == "GoldStandard":
                return (0, m.get("code", ""))
            elif standard == "Verra" and ms == "Verra":
                return (0, m.get("code", ""))
            else:
                return (1, m.get("code", ""))
        filtered = sorted(filtered, key=_sort_key)

    shown = filtered[:80]
    shown_codes = {m["code"] for m in shown}
    if current_value and current_value not in shown_codes:
        current_meth = next((m for m in meths if m["code"] == current_value), None)
        if current_meth:
            shown.insert(0, current_meth)
        else:
            shown.insert(0, {"code": current_value, "name": current_value, "project_count": 0})

    options = ["(none)"] + [m["code"] for m in shown]
    labels = {
        "(none)": "-- Select methodology --",
    }
    std_short = {"CDM": "CDM", "Verra": "VCS", "GoldStandard": "GS"}
    for m in shown:
        name = (m.get("name") or "").strip()
        version = (m.get("version") or "").strip()
        ms = std_short.get(m.get("standard", ""), "")
        label = f"[{ms}] {m['code']}" if ms else m["code"]
        if version:
            label += f" v{version}"
        if name:
            label += f" - {name[:60]}"
        labels[m["code"]] = label

    default_idx = 0
    if current_value and current_value in options:
        default_idx = options.index(current_value)

    selected = st.selectbox(
        "Methodology",
        options,
        index=default_idx,
        format_func=lambda x: labels.get(x, x),
        key=f"{key_prefix}_meth_select",
    )
    return selected if selected != "(none)" else None


STANDARD_OPTIONS = ["GoldStandard", "Verra"]
DOC_TYPES_FOR_STANDARD = {
    "GoldStandard": {"pdd": "PDD", "mr": "Monitoring Report", "poa_dd": "PoA-DD", "vpa_dd": "VPA-DD"},
    "Verra": {"pdd": "Project Description (VCS-PD)", "mr": "Monitoring Report (VCS-MR)", "valver": "Validation/Verification Report"},
}
PROJECT_DOC_TYPES = {
    "pdd": "Project Description (PDD)",
    "mr": "Monitoring Report (MR)",
    "valver": "Validation/Verification Report",
    "poa_dd": "PoA-DD",
    "vpa_dd": "VPA-DD",
    "reference": "Reference Document",
    "research": "Research / Study",
    "field_data": "Field Data / Test Results",
    "template": "Template",
    "other": "Other",
}
PROJECT_TYPE_INFO = {
    "standalone_pdd": {
        "label": "Standalone PDD",
        "short": "PDD",
        "badge_class": "badge-pdd",
        "description": "Write a new Project Design Document for a single project activity",
        "default_doc_type": "pdd",
        "standards": ["GoldStandard", "Verra"],
    },
    "poa_programme": {
        "label": "Programme of Activities (PoA-DD)",
        "short": "PoA-DD",
        "badge_class": "badge-poa",
        "description": "Create a PoA-DD programme envelope. You can add VPA-DDs under it later.",
        "default_doc_type": "poa_dd",
        "standards": ["GoldStandard"],
    },
    "vpa_component": {
        "label": "VPA Design Document",
        "short": "VPA-DD",
        "badge_class": "badge-vpa",
        "description": "Write a VPA-DD component linked to an existing PoA-DD programme",
        "default_doc_type": "vpa_dd",
        "standards": ["GoldStandard"],
        "needs_parent": True,
        "parent_type": "poa_programme",
    },
    "monitoring_report": {
        "label": "Monitoring Report",
        "short": "MR",
        "badge_class": "badge-mr",
        "description": "Write a Monitoring Report for an existing project",
        "default_doc_type": "mr",
        "standards": ["GoldStandard", "Verra"],
        "needs_parent": True,
        "parent_type": None,
    },
    "valver_report": {
        "label": "Validation / Verification Report",
        "short": "ValVer",
        "badge_class": "badge-valver",
        "description": "Write a Validation or Verification Report",
        "default_doc_type": "valver",
        "standards": ["Verra"],
    },
}
STATUS_LABELS = {
    "draft": "Draft",
    "in_progress": "In Progress",
    "under_review": "Under Review",
    "submitted": "Submitted",
    "registered": "Registered",
    "archived": "Archived",
}
STATUS_COLORS = {
    "draft": "gray",
    "in_progress": "blue",
    "under_review": "orange",
    "submitted": "violet",
    "registered": "green",
    "archived": "red",
}


def _render_home():
    st.markdown("""
    <div class="page-header">
        <h1>Workspace</h1>
        <div class="page-subtitle">Manage your carbon projects and explore market intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    home_tabs = st.tabs(["My Projects", "Carbon Intelligence"])
    with home_tabs[0]:
        _render_project_list()
    with home_tabs[1]:
        render_intelligence()


def _render_project_list():

    projects = _fetch("/projects") or []

    col_left, col_right = st.columns([4, 1])
    with col_left:
        if projects:
            st.caption(f"{len(projects)} project{'s' if len(projects) != 1 else ''}")
    with col_right:
        if st.button("+ New Project", key="new_proj_btn", type="primary"):
            st.session_state["show_new_project"] = True

    if st.session_state.get("show_new_project"):
        _render_new_project_wizard(projects)
        return

    if not projects:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-title">No projects yet</div>
            <div class="empty-state-desc">Create your first carbon project to start drafting PDDs, Monitoring Reports, and other documents with AI assistance.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    proj_by_parent = {}
    top_level = []
    for proj in projects:
        parent_id = proj.get("parent_project_id")
        if parent_id:
            proj_by_parent.setdefault(parent_id, []).append(proj)
        else:
            top_level.append(proj)

    for proj in top_level:
        children = proj_by_parent.get(proj["id"], [])
        _render_project_card(proj, child_count=len(children))
        if children:
            for child in children:
                _render_project_card(child, indent=True)

    orphaned_parents = set(proj_by_parent.keys()) - {p["id"] for p in top_level}
    for parent_id in orphaned_parents:
        for child in proj_by_parent[parent_id]:
            _render_project_card(child)


def _render_project_card(proj, indent=False, child_count=0):
    pid = proj["id"]
    status = proj.get("status", "draft")
    status_label = STATUS_LABELS.get(status, status)
    status_color = STATUS_COLORS.get(status, "gray")
    doc_count = proj.get("doc_count", 0)
    project_type = proj.get("project_type", "standalone_pdd")
    type_info = PROJECT_TYPE_INFO.get(project_type, PROJECT_TYPE_INFO["standalone_pdd"])
    badge_class = type_info.get("badge_class", "badge-pdd")

    with st.container(border=True):
        if indent:
            c0, c1, c2, c3, c4 = st.columns([0.3, 3.2, 1.2, 0.8, 0.8])
            with c0:
                st.markdown("<span style='color:#cbd5e1;'>|--</span>", unsafe_allow_html=True)
        else:
            c1, c2, c3, c4 = st.columns([3.5, 1.2, 0.8, 0.8])

        with c1:
            type_badge = f"<span class='project-type-badge {badge_class}'>{type_info['short']}</span>"
            st.markdown(f"{type_badge} **{proj['name']}**", unsafe_allow_html=True)
            details = []
            if proj.get("standard"):
                std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(proj["standard"], proj["standard"])
                details.append(std_display)
            if proj.get("methodology"):
                details.append(proj["methodology"])
            if proj.get("country"):
                details.append(proj["country"])
            if details:
                st.caption(" / ".join(details))
            if child_count > 0:
                st.caption(f"{child_count} VPA{'s' if child_count != 1 else ''}")

        with c2:
            st.markdown(f":{status_color}[{status_label}]")
        with c3:
            st.caption(f"{doc_count} doc{'s' if doc_count != 1 else ''}")
        with c4:
            if st.button("Open", key=f"open_proj_{pid}", type="primary", use_container_width=True):
                st.session_state.selected_project_id = pid
                st.rerun()


def _render_new_project_wizard(existing_projects):
    st.markdown("### Create New Project")

    if st.button("Cancel", key="cancel_new_proj"):
        st.session_state["show_new_project"] = False
        st.session_state.pop("new_proj_step", None)
        st.session_state.pop("new_proj_type", None)
        st.rerun()

    step_key = "new_proj_step"
    if step_key not in st.session_state:
        st.session_state[step_key] = 1

    step = st.session_state[step_key]

    if step == 1:
        st.markdown("**Step 1: What are you working on?**")
        type_cols = st.columns(len(PROJECT_TYPE_INFO))
        for i, (ptype, info) in enumerate(PROJECT_TYPE_INFO.items()):
            with type_cols[i]:
                with st.container(border=True):
                    badge_class = info.get("badge_class", "badge-pdd")
                    st.markdown(
                        f"<span class='project-type-badge {badge_class}'>{info['short']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{info['label']}**")
                    st.caption(info["description"])
                    standards_str = ", ".join(
                        {"GoldStandard": "GS", "Verra": "Verra"}.get(s, s) for s in info["standards"]
                    )
                    st.caption(f"Standards: {standards_str}")
                    if st.button("Select", key=f"select_type_{ptype}", use_container_width=True):
                        st.session_state["new_proj_type"] = ptype
                        st.session_state[step_key] = 2
                        st.rerun()

    elif step == 2:
        selected_type = st.session_state.get("new_proj_type", "standalone_pdd")
        type_info = PROJECT_TYPE_INFO[selected_type]
        badge_class = type_info.get("badge_class", "badge-pdd")
        st.markdown(
            f"<span class='project-type-badge {badge_class}'>{type_info['short']}</span> "
            f"**{type_info['label']}**",
            unsafe_allow_html=True,
        )

        available_standards = type_info.get("standards", STANDARD_OPTIONS)
        if len(available_standards) == 1:
            new_standard = available_standards[0]
            std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(new_standard, new_standard)
            st.info(f"Standard: {std_display}")
        else:
            new_standard = st.selectbox("Standard", available_standards, key="wizard_standard",
                                         format_func=lambda x: {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(x, x))

        needs_parent = type_info.get("needs_parent", False)
        parent_id = None
        if needs_parent:
            parent_filter_type = type_info.get("parent_type")
            if parent_filter_type:
                linkable = [p for p in existing_projects
                            if p.get("project_type") == parent_filter_type
                            and p.get("standard") == new_standard]
                parent_label = "Select parent PoA-DD programme"
            else:
                linkable = [p for p in existing_projects
                            if p.get("project_type") in ("standalone_pdd", "vpa_component", "poa_programme")
                            and p.get("standard") == new_standard]
                parent_label = "Link to existing project (optional)"

            if linkable:
                parent_options = {p["id"]: f"{p['name']} ({p.get('methodology', 'N/A')})" for p in linkable}
                parent_id = st.selectbox(
                    parent_label,
                    [None] + list(parent_options.keys()),
                    format_func=lambda x: parent_options[x] if x else "(none)",
                    key="wizard_parent",
                )
            else:
                if parent_filter_type == "poa_programme":
                    st.warning("No PoA-DD programmes found. Create a PoA-DD first, or proceed without linking.")
                else:
                    st.info("No existing projects to link. You can proceed without linking.")

        new_name = st.text_input("Project name", key="wizard_name",
                                  placeholder="e.g., Ghana Improved Cookstoves")
        new_methodology = _methodology_selector("wizard", standard=new_standard)
        c1, c2 = st.columns(2)
        with c1:
            new_country = st.text_input("Country", key="wizard_country", placeholder="e.g., Ghana")
        with c2:
            new_desc = st.text_area("Description (optional)", key="wizard_desc",
                                     placeholder="Brief description...", height=68)

        monitoring_start = None
        monitoring_end = None
        if selected_type == "monitoring_report":
            st.markdown("**Monitoring Period**")
            mc1, mc2 = st.columns(2)
            with mc1:
                monitoring_start = st.date_input("Period start", key="wizard_mon_start", value=None, format="YYYY-MM-DD")
            with mc2:
                monitoring_end = st.date_input("Period end", key="wizard_mon_end", value=None, format="YYYY-MM-DD")
            if monitoring_start and monitoring_end and monitoring_end <= monitoring_start:
                st.warning("Monitoring period end date must be after the start date.")

        if parent_id:
            parent_proj = next((p for p in existing_projects if p["id"] == parent_id), None)
            if parent_proj:
                inherited = []
                if parent_proj.get("methodology") and not new_methodology:
                    inherited.append(f"Methodology: {parent_proj['methodology']}")
                if parent_proj.get("country") and not new_country:
                    inherited.append(f"Country: {parent_proj['country']}")
                if inherited:
                    st.info(f"Inherited from parent: {', '.join(inherited)}")

        bc1, bc2 = st.columns([1, 3])
        with bc1:
            if st.button("Back", key="wizard_back"):
                st.session_state[step_key] = 1
                st.rerun()
        with bc2:
            if st.button("Create Project", key="wizard_create", type="primary"):
                if not new_name:
                    st.warning("Please enter a project name.")
                else:
                    final_methodology = new_methodology
                    final_country = new_country
                    if parent_id:
                        parent_proj = next((p for p in existing_projects if p["id"] == parent_id), None)
                        if parent_proj:
                            if not final_methodology:
                                final_methodology = parent_proj.get("methodology")
                            if not final_country:
                                final_country = parent_proj.get("country")

                    payload = {
                        "name": new_name,
                        "standard": new_standard,
                        "methodology": final_methodology,
                        "country": final_country or None,
                        "description": new_desc or None,
                        "project_type": selected_type,
                        "parent_project_id": parent_id,
                    }
                    if monitoring_start:
                        payload["monitoring_period_start"] = monitoring_start.isoformat()
                    if monitoring_end:
                        payload["monitoring_period_end"] = monitoring_end.isoformat()

                    result = _fetch("/projects", method="POST", json=payload)
                    if result:
                        st.success("Project created!")
                        st.session_state["show_new_project"] = False
                        st.session_state.pop(step_key, None)
                        time.sleep(0.5)
                        st.session_state.selected_project_id = result["id"]
                        st.rerun()


def _render_project_workspace(project_id):
    project = _fetch(f"/projects/{project_id}")
    if not project:
        st.error("Project not found.")
        st.session_state.selected_project_id = None
        st.rerun()
        return

    if st.button("< Back to Projects", key="back_to_projects"):
        st.session_state.selected_project_id = None
        st.rerun()

    status = project.get("status", "draft")
    status_label = STATUS_LABELS.get(status, status)
    status_color = STATUS_COLORS.get(status, "gray")
    project_type = project.get("project_type", "standalone_pdd")
    type_info = PROJECT_TYPE_INFO.get(project_type, PROJECT_TYPE_INFO["standalone_pdd"])
    badge_class = type_info.get("badge_class", "badge-pdd")

    std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(project.get("standard", ""), project.get("standard", ""))

    st.markdown(f"""
    <div class="page-header">
        <h1>
            <span class="project-type-badge {badge_class}">{type_info['short']}</span>
            {project['name']}
        </h1>
        <div class="page-subtitle">
            {std_display}
            {(' / ' + project['methodology']) if project.get('methodology') else ''}
            {(' / ' + project['country']) if project.get('country') else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if project.get("parent_project_id"):
        parent = _fetch(f"/projects/{project['parent_project_id']}")
        if parent:
            parent_type_info = PROJECT_TYPE_INFO.get(parent.get("project_type", ""), {})
            parent_short = parent_type_info.get("short", "Project")
            st.caption(f"Linked to: {parent_short} - {parent['name']}")

    if project.get("description"):
        st.caption(project["description"])

    if project_type == "poa_programme":
        children = _fetch(f"/projects/{project_id}/children") or []
        if children:
            with st.expander(f"{len(children)} VPA{'s' if len(children) != 1 else ''} in this programme"):
                for child in children:
                    child_type_info = PROJECT_TYPE_INFO.get(child.get("project_type", ""), {})
                    child_badge = child_type_info.get("badge_class", "badge-vpa")
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        st.markdown(
                            f"<span class='project-type-badge {child_badge}'>{child_type_info.get('short', 'VPA')}</span> "
                            f"**{child['name']}**",
                            unsafe_allow_html=True,
                        )
                    with cc2:
                        if st.button("Open", key=f"open_child_{child['id']}", use_container_width=True):
                            st.session_state.selected_project_id = child["id"]
                            st.rerun()
        if st.button("+ Add VPA", key=f"add_vpa_{project_id}"):
            st.session_state["show_new_project"] = True
            st.session_state["new_proj_type"] = "vpa_component"
            st.session_state["new_proj_step"] = 2
            st.session_state.selected_project_id = None
            st.rerun()

    tabs = st.tabs(["Project Setup", "Documents", "Write / Draft", "Review", "Export"])

    with tabs[0]:
        _render_project_settings(project)
    with tabs[1]:
        _render_documents_tab(project)
    with tabs[2]:
        _render_write_tab(project)
    with tabs[3]:
        _render_review_tab(project)
    with tabs[4]:
        _render_export_tab(project)


def _render_calculations_tab(project):
    project_id = project["id"]
    methodology = project.get("methodology")

    st.subheader("Emission Reduction Calculations")

    if not methodology:
        st.warning("Assign a methodology to this project in Project Settings before running calculations.")
        return

    st.write(f"Methodology: **{methodology}**")

    parse_key = f"parsed_methodology_{project_id}"
    calc_key = f"calc_result_{project_id}"

    if parse_key not in st.session_state:
        st.session_state[parse_key] = None
    if calc_key not in st.session_state:
        st.session_state[calc_key] = None

    if st.session_state[parse_key] is None:
        meth_data = _fetch(f"/projects/{project_id}/methodology-data")
        if meth_data and meth_data.get("status") == "ready":
            st.session_state[parse_key] = meth_data["parsed"]
            parsed_at = meth_data.get("parsed_at", "")
            if parsed_at:
                st.caption(f"Methodology pre-analyzed: {parsed_at[:19]}")

    parsed = st.session_state.get(parse_key)

    if not parsed:
        st.info("This methodology has not been analyzed yet. Click below to extract its calculation framework.")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Analyze Methodology", key=f"parse_meth_{project_id}",
                          type="primary"):
                with st.spinner("Analyzing methodology (this may take 30-60 seconds)..."):
                    result = _fetch(
                        f"/projects/{project_id}/parse-methodology",
                        method="POST",
                        json={"methodology_code": methodology},
                    )
                    if result and not result.get("error"):
                        st.session_state[parse_key] = result
                        st.rerun()
                    else:
                        err = (result or {}).get("error", "Unknown error")
                        st.error(f"Failed to analyze methodology: {err}")
        return

    st.divider()

    methods = parsed.get("calculation_methods", [])
    if methods:
        st.markdown("**Calculation Methods Available:**")
        method_labels = []
        for m in methods:
            mid = m.get("method_id", "")
            mname = m.get("method_name", mid)
            label = mname if mname.lower().startswith("method") else f"{mid}: {mname}"
            method_labels.append(label)
        selected_method_idx = st.selectbox(
            "Select calculation method",
            range(len(method_labels)),
            format_func=lambda i: method_labels[i],
            key=f"calc_method_{project_id}",
        )
        selected_method = methods[selected_method_idx]

        if selected_method.get("applicability"):
            st.caption(f"Applicability: {selected_method['applicability']}")
        elif selected_method.get("description"):
            st.caption(selected_method["description"])

        if selected_method.get("scale_restrictions"):
            st.caption(f"Scale: {selected_method['scale_restrictions']}")

        if selected_method.get("equations"):
            with st.expander("View Equations", expanded=True):
                for eq in selected_method["equations"]:
                    eq_id = eq.get("equation_id", "")
                    eq_label = eq.get("equation_label", "")
                    header = f"**{eq_id}**" if eq_id else ""
                    if eq_label:
                        header += f" - {eq_label}" if header else f"**{eq_label}**"
                    if header:
                        st.markdown(header)
                    st.code(eq.get("formula_text", ""), language=None)
                    if eq.get("formula_description"):
                        st.caption(eq["formula_description"])
                    if eq.get("variables"):
                        var_text = ", ".join(
                            f"{v['symbol']} ({v.get('name', '')})"
                            for v in eq["variables"]
                        )
                        st.caption(f"Variables: {var_text}")
                    st.markdown("---")
    else:
        selected_method = None

    st.divider()

    all_params = parsed.get("parameters", [])
    method_id = selected_method["method_id"] if selected_method else None

    eq_var_symbols = set()
    if selected_method:
        for eq in selected_method.get("equations", []):
            for var in eq.get("variables", []):
                s = var.get("symbol") or ""
                if s:
                    eq_var_symbols.add(s)

    def _param_relevant(p):
        cat = p.get("category", "")
        if cat == "qualitative":
            return False
        role = p.get("equation_role", "")
        if role == "output":
            return False
        sym = p.get("symbol") or ""
        sym_base = sym.split("_")[0] if sym and "_" in sym else sym
        if sym and (sym in eq_var_symbols or sym_base in {s.split("_")[0] for s in eq_var_symbols if s}):
            return True
        applicable = p.get("applicable_methods", [])
        if not applicable or "all" in applicable:
            if role in ("input", "intermediate") or cat in ("monitored", "methodology_default", "project_input"):
                return True
        if applicable and method_id and method_id in applicable:
            return True
        return False

    relevant_params = [p for p in all_params if _param_relevant(p)]

    proj_settings = project.get("project_settings") or {}
    context_dims = parsed.get("context_dimensions", []) if parsed else []
    dim_keys = [d["dimension_key"] for d in context_dims]

    import hashlib as _hashlib
    import json as _json_mod
    settings_hash = _hashlib.md5(_json_mod.dumps(proj_settings, sort_keys=True).encode()).hexdigest()[:8]

    def _resolve_default(param):
        dbc = param.get("defaults_by_context", [])
        if not dbc:
            dn = param.get("default_numeric")
            if dn is not None:
                return str(dn)
            return ""
        selected_values = []
        for dk in dim_keys:
            val = proj_settings.get(dk, "")
            if val:
                selected_values.append(val.lower())
        if not selected_values:
            return str(dbc[0]["value"])
        best_match = None
        best_score = -1
        for entry in dbc:
            ck = entry.get("context_key", "").lower()
            score = sum(1 for sv in selected_values if sv in ck)
            if score > best_score:
                best_score = score
                best_match = entry
        if best_match and best_score > 0:
            return str(best_match["value"])
        return str(dbc[0]["value"])

    def _display_group(p):
        cat = p.get("category", "")
        dbc = p.get("defaults_by_context", [])
        dn = p.get("default_numeric")
        if cat == "methodology_default" or dbc or dn is not None:
            return "methodology_default"
        if cat in ("monitored", "calculated"):
            return "monitored"
        if cat == "project_input":
            return "project_input"
        return "monitored"

    group_order = ["methodology_default", "monitored", "project_input"]
    group_labels = {
        "methodology_default": "Methodology Defaults",
        "monitored": "Monitored / Field Data",
        "project_input": "Project-Specific Inputs",
    }
    group_captions = {
        "methodology_default": "Pre-filled from methodology based on your project settings. You can override any value.",
        "monitored": "Values from field surveys, monitoring, or project records. Enter your project data.",
        "project_input": "Project-specific values defined by the developer.",
    }

    user_inputs = {}

    for grp in group_order:
        grp_params = [p for p in relevant_params if _display_group(p) == grp]
        if not grp_params:
            continue

        st.markdown(f"**{group_labels.get(grp, grp)}:**")
        cap = group_captions.get(grp)
        if cap:
            st.caption(cap)

        for i, param in enumerate(grp_params):
            default_resolved = _resolve_default(param)
            sym = param.get("symbol") or ""
            unit = param.get("unit") or ""
            param_name = param.get("name") or param.get("parameter_id") or f"Parameter {i+1}"

            label = f"{sym} - {param_name}" if sym else param_name
            if unit and unit != "NA":
                label += f" [{unit}]"

            help_parts = []
            if param.get("source"):
                help_parts.append(f"Source: {param['source']}")
            dbc = param.get("defaults_by_context", [])
            if dbc:
                defaults_text = "; ".join(f"{d['context_key']}: {d['value']} {d.get('unit','')}" for d in dbc[:6])
                help_parts.append(f"Available defaults: {defaults_text}")
            elif param.get("default_value"):
                help_parts.append(f"Default: {param['default_value']}")
            if param.get("monitoring_frequency"):
                help_parts.append(f"Monitoring: {param['monitoring_frequency']}")
            help_text = " | ".join(help_parts) if help_parts else None

            param_key = param.get("parameter_id", f"p{i}").replace(" ", "_").replace(".", "_")
            widget_key = f"param_{project_id}_{settings_hash}_{param_key}"

            val = st.text_input(
                label,
                value=default_resolved,
                key=widget_key,
                help=help_text,
            )
            if val:
                user_inputs[sym] = val

        st.markdown("---")

    st.divider()

    crediting_years = project.get("crediting_period_years") or 7
    cp_start = project.get("crediting_period_start")
    if cp_start:
        st.caption(f"Crediting period: {str(cp_start)[:10]}, {crediting_years} years (set in Project Settings)")
    else:
        st.caption(f"Crediting period: {crediting_years} years (set start date in Project Settings for vintage labels)")

    if st.button("Run Calculation", key=f"run_calc_{project_id}",
                  type="primary"):
        if not user_inputs:
            st.warning("Please fill in at least some parameter values.")
            return

        with st.spinner("Running emission reduction calculation..."):
            result = _fetch(
                f"/projects/{project_id}/calculate",
                method="POST",
                json={
                    "method_id": method_id,
                    "crediting_years": crediting_years,
                    "user_inputs": user_inputs,
                },
            )
            if result and not result.get("error"):
                st.session_state[calc_key] = result
            else:
                err = (result or {}).get("error", "Calculation failed")
                st.error(f"Calculation failed: {err}")

    calc_result = st.session_state.get(calc_key)
    if calc_result and not calc_result.get("error"):
        st.divider()
        _render_calc_results(project, calc_result)


def _render_calc_results(project, calc_result):
    import pandas as pd

    project_id = project["id"]

    st.markdown("### Calculation Results")

    if calc_result.get("narrative_explanation"):
        with st.expander("Narrative Explanation", expanded=True):
            st.write(calc_result["narrative_explanation"])

    annual = calc_result.get("annual_calculations", [])
    if annual:
        df = pd.DataFrame(annual)
        display_cols = {
            "year": "Year",
            "baseline_emissions_tco2e": "Baseline (tCO2e)",
            "project_emissions_tco2e": "Project (tCO2e)",
            "leakage_tco2e": "Leakage (tCO2e)",
            "net_emission_reductions_tco2e": "Net ER (tCO2e)",
        }
        available = [c for c in display_cols if c in df.columns]
        df_display = df[available].rename(columns=display_cols)
        st.dataframe(df_display, width="stretch", hide_index=True)

        total = calc_result.get("total_emission_reductions_tco2e", 0)
        avg = calc_result.get("average_annual_reductions_tco2e", 0)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Emission Reductions",
                       f"{total:,.0f} tCO2e")
        with col2:
            st.metric("Avg. Annual Reductions",
                       f"{avg:,.0f} tCO2e/yr")

        st.subheader("Emission Reductions by Year")
        chart_df = df_display.set_index("Year")[["Net ER (tCO2e)"]] if "Year" in df_display.columns else None
        if chart_df is not None:
            st.bar_chart(chart_df)

    if calc_result.get("parameters_used"):
        with st.expander("Parameters Used"):
            params_df = pd.DataFrame(calc_result["parameters_used"])
            st.dataframe(params_df, width="stretch", hide_index=True)

    if calc_result.get("assumptions"):
        with st.expander("Assumptions"):
            for a in calc_result["assumptions"]:
                st.write(f"- {a}")

    if calc_result.get("monitoring_parameters"):
        with st.expander("Monitoring Parameters"):
            mon_df = pd.DataFrame(calc_result["monitoring_parameters"])
            st.dataframe(mon_df, width="stretch", hide_index=True)

    st.divider()
    if st.button("Download Calculation Spreadsheet (Excel)",
                  key=f"download_calc_{project_id}",
                  type="primary"):
        with st.spinner("Generating Excel file..."):
            import io
            resp = requests.post(
                f"{API_BASE}/projects/{project_id}/export-calculation",
                json={"calculation_result": calc_result},
                timeout=30,
            )
            if resp.status_code == 200:
                st.download_button(
                    label="Save Excel File",
                    data=resp.content,
                    file_name=f"{project['name'][:30]}_calculations.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"save_calc_excel_{project_id}",
                )
            else:
                st.error("Failed to generate Excel file.")


def _render_export_tab(project):
    project_id = project["id"]
    standard = project.get("standard", "GoldStandard")
    methodology = project.get("methodology")

    st.subheader("Export Documents")
    st.write("Generate filled templates with your drafted content, or download calculation spreadsheets.")

    st.markdown("### Template Export")
    st.write("Export a Word document with all your drafted sections filled into the standard template structure.")

    project_type = project.get("project_type", "standalone_pdd")
    available_types = DOC_TYPES_FOR_STANDARD.get(standard, {"pdd": "PDD", "mr": "MR"})

    default_dt = PROJECT_TYPE_INFO.get(project_type, {}).get("default_doc_type", "pdd")
    type_keys = list(available_types.keys())
    default_idx = type_keys.index(default_dt) if default_dt in type_keys else 0

    selected_doc_type = st.selectbox(
        "Document type to export",
        type_keys,
        index=default_idx,
        format_func=lambda x: available_types[x],
        key=f"export_doc_type_{project_id}",
    )

    write_sessions = _fetch(f"/projects/{project_id}/write-sessions?doc_type={selected_doc_type}")
    session_count = len(write_sessions) if write_sessions else 0

    if session_count > 0:
        st.info(f"{session_count} section(s) have been drafted using the AI Writer. These will be included in the template.")
    else:
        st.warning("No sections have been drafted yet. Use the Write / Draft tab to generate content before exporting.")

    calc_key = f"calc_result_{project_id}"
    has_calc = calc_key in st.session_state and st.session_state[calc_key] is not None
    include_calc = False
    if has_calc:
        include_calc = st.checkbox(
            "Include calculation results in the document",
            value=True,
            key=f"include_calc_{project_id}",
        )

    if st.button("Generate Template Document",
                  key=f"gen_template_{project_id}",
                  type="primary"):
        with st.spinner("Generating filled template document..."):
            payload = {
                "doc_type": selected_doc_type,
                "include_calculations": include_calc,
            }
            if include_calc and has_calc:
                payload["calculation_result"] = st.session_state[calc_key]
            resp = requests.post(
                f"{API_BASE}/projects/{project_id}/generate-template",
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                doc_label = available_types.get(selected_doc_type, selected_doc_type)
                safe_name = project["name"].replace(" ", "_")[:30]
                filename = f"{safe_name}_{selected_doc_type.upper()}.docx"
                st.download_button(
                    label=f"Save {doc_label}",
                    data=resp.content,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"save_template_{project_id}",
                )
                st.success("Template generated successfully.")
            else:
                detail = ""
                try:
                    detail = resp.json().get("detail", "")
                except Exception:
                    pass
                st.error(f"Failed to generate template. {detail}")

    st.divider()
    st.markdown("### Calculation Spreadsheet")

    if has_calc:
        calc_result = st.session_state[calc_key]
        total_er = calc_result.get("total_emission_reductions_tco2e", 0)
        st.write(f"Calculation available: {total_er:,.0f} tCO2e total emission reductions")
        if st.button("Download Excel Spreadsheet",
                      key=f"export_calc_excel_{project_id}",
                      type="primary"):
            with st.spinner("Generating spreadsheet..."):
                resp = requests.post(
                    f"{API_BASE}/projects/{project_id}/export-calculation",
                    json={"calculation_result": calc_result},
                    timeout=30,
                )
                if resp.status_code == 200:
                    safe_name = project["name"].replace(" ", "_")[:30]
                    st.download_button(
                        label="Save Excel File",
                        data=resp.content,
                        file_name=f"{safe_name}_calculations.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"save_export_excel_{project_id}",
                    )
                else:
                    st.error("Failed to generate spreadsheet.")
    else:
        st.info("No calculations available yet. Emission reduction calculations will be available in a future update.")

    st.divider()
    st.markdown("### Methodology Reference")
    if methodology:
        meth_detail = _fetch(f"/projects/methodologies/{methodology}")
        if meth_detail:
            with st.container(border=True):
                st.markdown(f"**{meth_detail.get('code', '')}** - {meth_detail.get('name', '')}")
                if meth_detail.get("standard"):
                    st.caption(f"Standard: {meth_detail['standard']}")
                if meth_detail.get("applicability"):
                    st.caption(f"Applicability: {meth_detail['applicability'][:300]}")
    else:
        st.caption("No methodology assigned to this project.")


def _render_documents_tab(project):
    project_id = project["id"]
    project_type = project.get("project_type", "standalone_pdd")

    st.subheader("Documents & Knowledge Base")
    st.write("Upload project documents. Toggle which ones the AI uses when writing and reviewing your documents.")

    documents = project.get("documents", [])

    if not documents:
        _render_document_prompts(project_type)

    standard = project.get("standard", "GoldStandard")
    available_doc_types = list(DOC_TYPES_FOR_STANDARD.get(standard, {}).keys())
    upload_types = available_doc_types + ["reference", "research", "field_data", "other"]

    with st.container(border=True):
        st.markdown("#### Upload Document")
        upload_col1, upload_col2 = st.columns(2)
        with upload_col1:
            upload_file = st.file_uploader("Choose a file", type=["docx", "pdf"], key=f"upload_{project_id}")
        with upload_col2:
            doc_type = st.selectbox(
                "Document type",
                upload_types,
                format_func=lambda x: PROJECT_DOC_TYPES.get(x, x),
                key=f"upload_type_{project_id}",
            )
            upload_notes = st.text_input("Notes (optional)", key=f"upload_notes_{project_id}")

        if st.button("Upload", key=f"upload_btn_{project_id}", type="primary", disabled=not upload_file):
            if upload_file:
                files = {"file": (upload_file.name, upload_file.getvalue())}
                data = {"doc_type": doc_type}
                if upload_notes:
                    data["notes"] = upload_notes
                result = _fetch(
                    f"/projects/{project_id}/documents",
                    method="POST",
                    files=files,
                    data=data,
                )
                if result:
                    parsed = "parsed" if result.get("parsed") else "uploaded"
                    st.success(f"Document uploaded and {parsed} successfully.")
                    time.sleep(0.5)
                    st.rerun()

    if project.get("parent_project_id"):
        parent = _fetch(f"/projects/{project['parent_project_id']}")
        if parent and parent.get("documents"):
            parent_type_info = PROJECT_TYPE_INFO.get(parent.get("project_type", ""), {})
            parent_label = parent_type_info.get("short", "Parent")
            with st.container(border=True):
                st.markdown(f"#### Documents from {parent_label}: {parent['name']}")
                st.caption("These documents are automatically available as AI context.")
                for pdoc in parent.get("documents", []):
                    if pdoc.get("parsed_text"):
                        doc_type_label = PROJECT_DOC_TYPES.get(pdoc["doc_type"], pdoc["doc_type"])
                        st.markdown(f"- **{pdoc['file_name']}** ({doc_type_label})")

    if documents:
        core_docs = [d for d in documents if d.get("doc_type") in ("pdd", "mr", "valver", "poa_dd", "vpa_dd")]
        support_docs = [d for d in documents if d.get("doc_type") in ("reference", "research", "field_data")]
        other_docs = [d for d in documents if d.get("doc_type") in ("template", "other")]

        if core_docs:
            st.markdown("#### Core Documents")
            for doc in core_docs:
                _render_document_card(project_id, doc)

        if support_docs:
            st.markdown("#### Supporting Evidence")
            st.caption("KPT reports, field data, feasibility studies, and other supporting materials")
            for doc in support_docs:
                _render_document_card(project_id, doc)

        if other_docs:
            st.markdown("#### Other Documents")
            for doc in other_docs:
                _render_document_card(project_id, doc)

        ai_context_count = sum(1 for d in documents if d.get("use_as_ai_context", True) and d.get("parsed_text"))
        if ai_context_count > 0:
            st.info(f"{ai_context_count} document{'s' if ai_context_count != 1 else ''} active as AI context")
    elif not documents:
        pass


def _render_document_card(project_id, doc):
    doc_type_label = PROJECT_DOC_TYPES.get(doc["doc_type"], doc["doc_type"])
    status_label = doc.get("status", "uploaded")
    use_ai = doc.get("use_as_ai_context", True)
    has_parsed = bool(doc.get("parsed_text"))

    with st.container(border=True):
        dc1, dc2, dc3, dc4, dc5 = st.columns([3, 1.2, 0.8, 0.8, 0.5])
        with dc1:
            st.markdown(f"**{doc['file_name']}**")
            st.caption(f"{doc_type_label}")
        with dc2:
            status_display = {"parsed": "Parsed", "reviewed": "Reviewed", "uploaded": "Uploaded", "draft_generated": "Generated"}.get(status_label, status_label)
            st.caption(f"Status: {status_display}")
            if doc.get("notes"):
                st.caption(f"Notes: {doc['notes']}")
        with dc3:
            size = doc.get("file_size_bytes", 0) or 0
            if size > 1024 * 1024:
                st.caption(f"{size / 1024 / 1024:.1f} MB")
            elif size > 1024:
                st.caption(f"{size / 1024:.0f} KB")
        with dc4:
            toggle_label = "AI Context" if has_parsed else "Not parsed"
            new_val = st.checkbox(
                toggle_label,
                value=use_ai and has_parsed,
                key=f"ai_ctx_{doc['id']}",
                disabled=not has_parsed,
                help="Toggle whether the AI writer/reviewer uses this document as context",
            )
            if new_val != use_ai and has_parsed:
                _fetch(
                    f"/projects/{project_id}/documents/{doc['id']}/ai-context?use_as_ai_context={str(new_val).lower()}",
                    method="PATCH",
                )
                st.rerun()
        with dc5:
            if st.button("X", key=f"del_doc_{doc['id']}", help="Delete document"):
                _fetch(f"/projects/{project_id}/documents/{doc['id']}", method="DELETE")
                time.sleep(0.3)
                st.rerun()


def _render_document_prompts(project_type):
    prompts = {
        "standalone_pdd": {
            "title": "Recommended documents for your PDD",
            "items": [
                "KPT (Kitchen Performance Test) report",
                "Baseline study or survey data",
                "Feasibility study",
                "Stakeholder consultation report",
                "Technical specifications / test certificates",
            ],
        },
        "poa_programme": {
            "title": "Recommended documents for your PoA-DD",
            "items": [
                "Programme concept document",
                "CME organizational details",
                "Eligibility criteria documentation",
                "Methodology document",
            ],
        },
        "vpa_component": {
            "title": "Recommended documents for your VPA-DD",
            "items": [
                "Parent PoA-DD document (will be used for eligibility criteria context)",
                "VPA-specific KPT or field test reports",
                "Local baseline data",
                "VPA location documentation",
            ],
        },
        "monitoring_report": {
            "title": "Recommended documents for your Monitoring Report",
            "items": [
                "PDD (critical - the AI will reference your baseline, methodology, and monitoring plan)",
                "Previous Monitoring Reports (for consistency)",
                "Monitoring data spreadsheets",
                "Field visit reports",
                "Survey or sampling data",
            ],
        },
        "valver_report": {
            "title": "Recommended documents for your ValVer Report",
            "items": [
                "PDD or Project Description being validated/verified",
                "Monitoring Report (if verification)",
                "Field visit notes",
                "Interview records",
            ],
        },
    }
    prompt_data = prompts.get(project_type, prompts["standalone_pdd"])
    with st.container(border=True):
        st.markdown(f"#### {prompt_data['title']}")
        st.caption("Upload these documents to give the AI better context for writing and reviewing.")
        for item in prompt_data["items"]:
            st.markdown(f"- {item}")


def _render_review_tab(project):
    project_id = project["id"]
    standard = project.get("standard", "GoldStandard")
    project_type = project.get("project_type", "standalone_pdd")

    st.subheader("Review")

    review_tabs = st.tabs(["Review Your Draft", "Review Uploaded Document"])

    with review_tabs[0]:
        st.markdown("#### Review Your Draft")
        st.write("The AI will assemble all your drafted sections and review them against the standard's requirements.")

        available_doc_types = DOC_TYPES_FOR_STANDARD.get(standard, {})
        default_dt = PROJECT_TYPE_INFO.get(project_type, {}).get("default_doc_type", "pdd")
        doc_type_keys = list(available_doc_types.keys())
        default_idx = doc_type_keys.index(default_dt) if default_dt in doc_type_keys else 0

        draft_doc_type = st.selectbox(
            "Document type to review",
            doc_type_keys,
            index=default_idx,
            format_func=lambda x: available_doc_types[x],
            key=f"draft_review_dt_{project_id}",
        )

        write_sessions = _fetch(f"/projects/{project_id}/write-sessions?doc_type={draft_doc_type}")
        drafted_count = sum(1 for s in (write_sessions or []) if (s.get("user_text") or s.get("generated_text", "")).strip())

        if drafted_count > 0:
            st.info(f"{drafted_count} section{'s' if drafted_count != 1 else ''} drafted. Ready for review.")

            if st.button("Start Draft Review", key=f"draft_review_btn_{project_id}", type="primary"):
                with st.spinner("AI is reviewing your draft... This may take a minute."):
                    result = _fetch(
                        f"/projects/{project_id}/review-draft?doc_type={draft_doc_type}",
                        method="POST",
                    )
                    if result:
                        st.session_state[f"draft_review_result_{project_id}_{draft_doc_type}"] = result
                        st.rerun()

            draft_result = st.session_state.get(f"draft_review_result_{project_id}_{draft_doc_type}")
            if draft_result:
                _render_review_result(draft_result)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-title">No drafted sections yet</div>
                <div class="empty-state-desc">Use the Write / Draft tab to generate content, then come back here to review it.</div>
            </div>
            """, unsafe_allow_html=True)

    with review_tabs[1]:
        st.markdown("#### Review Uploaded Document")
        st.write("Select an uploaded document to review against the standard's requirements.")

        documents = project.get("documents", [])
        reviewable = [d for d in documents if d.get("status") in ("parsed", "reviewed") and d.get("doc_type") in ("pdd", "mr", "valver", "poa_dd", "vpa_dd")]

        if not reviewable:
            st.info("Upload a PDD, MR, or other reviewable document first (DOCX or PDF format).")
        else:
            doc_options = {d["id"]: f"{d['file_name']} ({PROJECT_DOC_TYPES.get(d['doc_type'], d['doc_type'])})" for d in reviewable}
            selected_doc_id = st.selectbox(
                "Select document to review",
                list(doc_options.keys()),
                format_func=lambda x: doc_options[x],
                key=f"review_doc_select_{project_id}",
            )

            selected_doc = next((d for d in reviewable if d["id"] == selected_doc_id), None)

            if selected_doc and selected_doc.get("doc_type") == "mr":
                pdd_docs = [d for d in documents if d["doc_type"] == "pdd" and d.get("parsed_text")]
                if pdd_docs:
                    st.info(f"PDD found in project: {pdd_docs[0]['file_name']}. The AI will cross-reference your MR against the PDD for consistency.")
                else:
                    st.warning("No PDD found in this project. For the best MR review, upload your PDD first so the AI can check consistency.")

            if st.button("Start Review", key=f"review_btn_{project_id}", type="primary"):
                with st.spinner("AI is reviewing your document... This may take a minute."):
                    result = _fetch(f"/projects/{project_id}/review/{selected_doc_id}", method="POST")
                    if result:
                        st.session_state[f"review_result_{selected_doc_id}"] = result
                        st.rerun()

            result = st.session_state.get(f"review_result_{selected_doc_id}")
            if not result:
                if selected_doc and selected_doc.get("review_result"):
                    import json
                    try:
                        result = json.loads(selected_doc["review_result"]) if isinstance(selected_doc["review_result"], str) else selected_doc["review_result"]
                    except (json.JSONDecodeError, TypeError):
                        result = None

            if result:
                _render_review_result(result)


def _render_review_result(result):
    risk = result.get("overall_risk", "UNKNOWN")
    risk_colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    risk_color = risk_colors.get(risk, "red")
    score = result.get("overall_score", "N/A")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall Risk", risk)
    with col2:
        st.metric("Overall Score", f"{score}/100" if isinstance(score, int) else score)

    pdd_consistency = result.get("pdd_consistency", [])
    if pdd_consistency:
        st.warning("**PDD Consistency Issues:**")
        for issue in pdd_consistency:
            st.write(f"- {issue}")

    priority = result.get("priority_actions", [])
    if priority:
        st.subheader("Priority Actions")
        for i, action in enumerate(priority, 1):
            st.write(f"{i}. {action}")

    sections = result.get("sections", [])
    if sections:
        st.subheader("Section-by-Section Review")
        for sec in sections:
            sec_name = sec.get("section", "Unknown")
            sec_score = sec.get("score", "N/A")
            with st.expander(f"{sec_name} (Score: {sec_score}/100)"):
                issues = sec.get("issues", [])
                if issues:
                    st.markdown("**Issues:**")
                    for iss in issues:
                        st.write(f"- {iss}")
                fixes = sec.get("fixes", [])
                if fixes:
                    st.markdown("**Suggested Fixes:**")
                    for fix in fixes:
                        st.write(f"- {fix}")
                questions = sec.get("questions", [])
                if questions:
                    st.markdown("**Questions for You:**")
                    for q in questions:
                        st.write(f"- {q}")

    raw = result.get("raw_review")
    if raw:
        with st.expander("Full Review Text"):
            st.write(raw)


def _render_write_tab(project):
    project_id = project["id"]
    standard = project.get("standard", "GoldStandard")
    project_type = project.get("project_type", "standalone_pdd")

    st.subheader("AI Writing Assistant")
    st.write("Draft your document section by section or generate the full document at once.")

    available_doc_types = DOC_TYPES_FOR_STANDARD.get(standard, {})
    if not available_doc_types:
        st.error("No document templates available for this standard.")
        return

    default_dt = PROJECT_TYPE_INFO.get(project_type, {}).get("default_doc_type", "pdd")
    doc_type_keys = list(available_doc_types.keys())
    default_idx = doc_type_keys.index(default_dt) if default_dt in doc_type_keys else 0

    col_dt, col_actions = st.columns([1, 2])
    with col_dt:
        selected_write_dt = st.selectbox(
            "Document type",
            doc_type_keys,
            index=default_idx,
            format_func=lambda x: available_doc_types[x],
            key=f"write_dt_{project_id}",
        )

    sections = _fetch(f"/projects/{project_id}/sections?doc_type={selected_write_dt}")
    if not sections:
        st.warning("Could not load sections for this document type.")
        return

    existing_sessions = _fetch(f"/projects/{project_id}/write-sessions?doc_type={selected_write_dt}")
    session_map = {}
    if existing_sessions:
        for sess in existing_sessions:
            session_map[sess["section_id"]] = sess

    drafted_count = sum(1 for s in sections if s["id"] in session_map)
    total_count = len(sections)

    with col_actions:
        st.caption(f"{drafted_count} of {total_count} sections drafted")
        if drafted_count > 0:
            st.progress(drafted_count / total_count)

    user_instructions = st.text_area(
        "Instructions for the AI (applies to all generation)",
        key=f"write_instr_{project_id}",
        placeholder="e.g., 'Focus on cookstove distribution in rural areas', 'Use conservative emission factors'...",
        height=60,
    )

    gen_col1, gen_col2, gen_col3 = st.columns([1, 1, 1])
    with gen_col1:
        generate_all = st.button(
            "Generate Full Document",
            key=f"generate_all_btn_{project_id}",
            type="primary",
            help="Generate all sections at once. This may take several minutes.",
        )
    with gen_col2:
        if drafted_count > 0:
            regenerate_all = st.button(
                "Regenerate All",
                key=f"regenerate_all_btn_{project_id}",
                help="Regenerate all sections, replacing existing drafts.",
            )
        else:
            regenerate_all = False

    if generate_all or regenerate_all:
        progress_bar = st.progress(0, text="Starting full document generation...")
        status_text = st.empty()

        result = None
        with st.spinner(""):
            import time as _time
            progress_bar.progress(0.02, text=f"Generating {total_count} sections...")
            result = _fetch(
                f"/projects/{project_id}/write-all?doc_type={selected_write_dt}",
                method="POST",
                json={"user_instructions": user_instructions or None},
                timeout=600,
            )

        if result:
            success_count = result.get("success_count", 0)
            total = result.get("total", 0)
            progress_bar.progress(1.0, text=f"Done: {success_count}/{total} sections generated")
            st.success(f"Generated {success_count} of {total} sections successfully.")
            _time.sleep(1)
            st.rerun()
        else:
            progress_bar.empty()
            st.error("Full document generation failed. Try generating sections individually.")

    st.divider()

    std_label = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(standard, standard)
    doc_label = available_doc_types.get(selected_write_dt, selected_write_dt)

    with st.container(border=True):
        st.markdown(
            f"<div style='text-align:center; padding: 12px 0 4px 0;'>"
            f"<span style='font-size:1.4em; font-weight:700;'>{doc_label}</span><br/>"
            f"<span style='color:#666;'>{std_label}</span><br/>"
            f"<span style='font-size:0.95em;'>{project.get('name', '')}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    current_parent = None
    for sec in sections:
        sec_id = sec["id"]
        sec_title = sec["title"]
        parent = sec.get("parent_section", "")

        if parent and parent != current_parent:
            current_parent = parent
            st.markdown(f"#### {parent}")

        has_draft = sec_id in session_map
        sess = session_map.get(sec_id, {})
        draft_text = sess.get("user_text") or sess.get("generated_text") or ""

        if has_draft and draft_text.strip():
            stripe_class = "section-card-drafted"
            status_text = "Drafted"
        else:
            stripe_class = "section-card-empty"
            status_text = "Not started"

        with st.container(border=True):
            st.markdown(
                f"<div class='{stripe_class}' style='margin:-1rem -1rem 0.5rem -1rem; padding:0;'></div>",
                unsafe_allow_html=True,
            )
            header_col, status_col, action_col1, action_col2 = st.columns([3.5, 0.8, 1, 1])
            with header_col:
                st.markdown(f"**{sec_id} &mdash; {sec_title}**")
            with status_col:
                if has_draft and draft_text.strip():
                    wc = len(draft_text.split())
                    st.markdown(
                        f"<span class='status-badge status-active'>{status_text}</span>"
                        f"<br/><span style='font-size:0.7rem;color:#94a3b8;'>{wc} words</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<span class='status-badge status-draft'>{status_text}</span>",
                        unsafe_allow_html=True,
                    )
            with action_col1:
                btn_label = "Regenerate" if has_draft else "Generate"
                if st.button(btn_label, key=f"gen_sec_{project_id}_{selected_write_dt}_{sec_id}", use_container_width=True):
                    with st.spinner(f"Generating {sec_id}..."):
                        result = _fetch(
                            f"/projects/{project_id}/write?doc_type={selected_write_dt}",
                            method="POST",
                            json={
                                "section_id": sec_id,
                                "user_instructions": user_instructions or None,
                            },
                        )
                        if result:
                            st.rerun()
            with action_col2:
                with st.popover("Info"):
                    st.markdown(f"**Requirements for {sec_id}:**")
                    for req in sec.get("must_include", []):
                        st.write(f"- {req}")
                    explain_key = f"explain_{project_id}_{selected_write_dt}_{sec_id}"
                    if st.button("Explain", key=f"explain_btn_{project_id}_{selected_write_dt}_{sec_id}"):
                        with st.spinner("..."):
                            expl_result = _fetch(
                                f"/projects/{project_id}/explain?doc_type={selected_write_dt}",
                                method="POST",
                                json={"section_id": sec_id},
                            )
                            if expl_result:
                                st.session_state[explain_key] = expl_result.get("explanation", "")
                    explanation = st.session_state.get(explain_key)
                    if explanation:
                        st.info(explanation)

            edit_key = f"edit_{project_id}_{selected_write_dt}_{sec_id}"
            editing = st.session_state.get(edit_key, False)

            if has_draft and draft_text:
                if editing:
                    edited_text = st.text_area(
                        f"Edit {sec_id}",
                        value=draft_text,
                        height=300,
                        key=f"textarea_{project_id}_{selected_write_dt}_{sec_id}",
                        label_visibility="collapsed",
                    )
                    save_col, cancel_col, _ = st.columns([1, 1, 4])
                    with save_col:
                        if st.button("Save", key=f"save_sec_{project_id}_{selected_write_dt}_{sec_id}", type="primary", use_container_width=True):
                            _fetch(
                                f"/projects/{project_id}/section-text",
                                method="PATCH",
                                json={
                                    "section_id": sec_id,
                                    "doc_type": selected_write_dt,
                                    "text": edited_text,
                                },
                            )
                            st.session_state[edit_key] = False
                            st.rerun()
                    with cancel_col:
                        if st.button("Cancel", key=f"cancel_sec_{project_id}_{selected_write_dt}_{sec_id}", use_container_width=True):
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    st.markdown(draft_text)
                    if st.button("Edit", key=f"edit_btn_{project_id}_{selected_write_dt}_{sec_id}"):
                        st.session_state[edit_key] = True
                        st.rerun()
            else:
                st.markdown(
                    "<span style='color:#999; font-style:italic;'>"
                    "[This section has not been drafted yet]</span>",
                    unsafe_allow_html=True,
                )


def _render_intake_by_type(project_id, project_type, intake):
    if project_type in ("standalone_pdd", ""):
        return _render_intake_pdd(project_id, intake)
    elif project_type == "poa_programme":
        return _render_intake_poa(project_id, intake)
    elif project_type == "vpa_component":
        return _render_intake_vpa(project_id, intake)
    elif project_type == "monitoring_report":
        return _render_intake_mr(project_id, intake)
    elif project_type == "valver_report":
        return _render_intake_valver(project_id, intake)
    else:
        return _render_intake_pdd(project_id, intake)


def _render_intake_pdd(project_id, intake):
    po = intake.get("project_overview", {})
    tech = intake.get("technology", {})
    loc = intake.get("location", {})
    ba = intake.get("baseline_additionality", {})
    mon = intake.get("monitoring", {})
    er = intake.get("emission_reductions", {})
    sdgs_data = intake.get("sdgs", {})
    stk = intake.get("stakeholders", {})
    safeg = intake.get("safeguards", {})

    with st.container(border=True):
        st.markdown("#### Project Overview")
        po_objective = st.text_area("Detailed objective", value=po.get("objective", ""),
                                     key=f"setup_po_objective_{project_id}",
                                     placeholder="What is the primary goal of this project?",
                                     height=80)
        po_summary = st.text_area("Project summary", value=po.get("summary", ""),
                                   key=f"setup_po_summary_{project_id}",
                                   placeholder="Provide a short summary suitable for a PDD introduction...",
                                   height=80)
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            po_start_date = st.text_input("Project start date", value=po.get("start_date", ""),
                                           key=f"setup_po_start_{project_id}",
                                           placeholder="YYYY-MM-DD")
        with pc2:
            po_scale = st.text_input("Project scale", value=po.get("scale", ""),
                                      key=f"setup_po_scale_{project_id}",
                                      placeholder="e.g., Small-scale, Large-scale")
        with pc3:
            po_num_units = st.text_input("Number of units", value=po.get("num_units", ""),
                                          key=f"setup_po_num_units_{project_id}",
                                          placeholder="e.g., 50,000 stoves")

    with st.container(border=True):
        st.markdown("#### Technology & Approach")
        tech_desc = st.text_area("Technology / intervention description", value=tech.get("description", ""),
                                  key=f"setup_tech_desc_{project_id}",
                                  placeholder="Describe the technology, intervention, or approach used (e.g., improved cookstoves, solar panels, EV fleet, grid connection, afforestation)...",
                                  height=80)
        tc1, tc2 = st.columns(2)
        with tc1:
            tech_manufacturer = st.text_input("Equipment manufacturer / supplier (if applicable)", value=tech.get("manufacturer", ""),
                                               key=f"setup_tech_mfr_{project_id}",
                                               placeholder="e.g., BioLite, Tesla, Vestas")
            tech_baseline_scenario = st.text_input("Baseline energy source / practice", value=tech.get("fuel_baseline", tech.get("baseline_scenario", "")),
                                                key=f"setup_tech_fuel_bl_{project_id}",
                                                placeholder="e.g., Wood, Diesel generators, Grid electricity, Open burning")
        with tc2:
            tech_model = st.text_input("Model / specification", value=tech.get("model", ""),
                                        key=f"setup_tech_model_{project_id}",
                                        placeholder="e.g., HomeStove 2, Model 3, V150-4.2MW")
            tech_project_scenario = st.text_input("Project energy source / practice", value=tech.get("fuel_project", tech.get("project_scenario", "")),
                                               key=f"setup_tech_fuel_pj_{project_id}",
                                               placeholder="e.g., LPG, Solar PV, Grid-connected wind, Improved cookstove")
        tech_distribution = st.text_input("Distribution / implementation method", value=tech.get("distribution_method", ""),
                                           key=f"setup_tech_dist_{project_id}",
                                           placeholder="e.g., Direct sales, Lease model, Government programme, Grid connection")

    with st.container(border=True):
        st.markdown("#### Location & Beneficiaries")
        loc_regions = st.text_input("Regions / provinces", value=loc.get("regions", ""),
                                     key=f"setup_loc_regions_{project_id}",
                                     placeholder="e.g., Northern Region, Ashanti Region")
        loc_coords = st.text_input("Coordinates (lat, lon)", value=loc.get("coordinates", ""),
                                    key=f"setup_loc_coords_{project_id}",
                                    placeholder="e.g., 7.9465, -1.0232")
        lc1, lc2 = st.columns(2)
        with lc1:
            loc_target = st.text_input("Target population", value=loc.get("target_population", ""),
                                        key=f"setup_loc_target_{project_id}",
                                        placeholder="e.g., Rural households")
        with lc2:
            loc_beneficiaries = st.text_input("Number of beneficiaries", value=loc.get("beneficiaries", ""),
                                               key=f"setup_loc_bene_{project_id}",
                                               placeholder="e.g., 250,000 people")

    with st.container(border=True):
        st.markdown("#### Baseline & Additionality")
        ba_baseline = st.text_area("Baseline scenario", value=ba.get("baseline_scenario", ""),
                                    key=f"setup_ba_baseline_{project_id}",
                                    placeholder="Describe what would happen without the project...",
                                    height=80)
        ba_additionality = st.text_area("Additionality justification", value=ba.get("additionality_justification", ""),
                                         key=f"setup_ba_add_{project_id}",
                                         placeholder="Why would this project not happen without carbon finance?",
                                         height=80)
        ba_barriers = st.text_area("Barriers", value=ba.get("barriers", ""),
                                    key=f"setup_ba_barriers_{project_id}",
                                    placeholder="Investment barriers, technological barriers, institutional barriers...",
                                    height=80)
        ba_common = st.text_area("Common practice analysis", value=ba.get("common_practice", ""),
                                  key=f"setup_ba_common_{project_id}",
                                  placeholder="Is this technology/practice common in the region?",
                                  height=80)

    with st.container(border=True):
        st.markdown("#### Monitoring Plan")
        mon_approach = st.text_area("Monitoring approach", value=mon.get("monitoring_approach", ""),
                                     key=f"setup_mon_approach_{project_id}",
                                     placeholder="Describe how the project will be monitored...",
                                     height=80)
        mon_params = st.text_area("Key parameters to monitor", value=mon.get("key_parameters", ""),
                                   key=f"setup_mon_params_{project_id}",
                                   placeholder="List the key monitoring parameters...",
                                   height=80)
        mon_sampling = st.text_area("Sampling approach", value=mon.get("sampling_approach", ""),
                                     key=f"setup_mon_sampling_{project_id}",
                                     placeholder="Describe the sampling methodology if applicable...",
                                     height=80)
        mon_qaqc = st.text_area("QA/QC procedures", value=mon.get("qa_qc", ""),
                                  key=f"setup_mon_qaqc_{project_id}",
                                  placeholder="Describe quality assurance / quality control procedures...",
                                  height=80)

    with st.container(border=True):
        st.markdown("#### Emission Reductions")
        ec1, ec2 = st.columns(2)
        with ec1:
            er_annual = st.text_input("Annual ER estimate (tCO2e)", value=er.get("annual_er_estimate", ""),
                                       key=f"setup_er_annual_{project_id}",
                                       placeholder="e.g., 150,000")
        with ec2:
            er_total = st.text_input("Total ER estimate (tCO2e)", value=er.get("total_er_estimate", ""),
                                      key=f"setup_er_total_{project_id}",
                                      placeholder="e.g., 1,050,000")
        er_calc_approach = st.text_area("Calculation approach", value=er.get("calculation_approach", ""),
                                         key=f"setup_er_calc_{project_id}",
                                         placeholder="Describe how emission reductions are calculated...",
                                         height=80)
        er_summary = st.text_area("ER summary", value=er.get("er_summary", ""),
                                   key=f"setup_er_summary_{project_id}",
                                   placeholder="Brief summary of the emission reduction claim...",
                                   height=80)

    sdg_list = _render_sdg_section(project_id, sdgs_data)

    with st.container(border=True):
        st.markdown("#### Stakeholder Engagement")
        stk_consultation = st.text_area("Consultation summary", value=stk.get("consultation_summary", ""),
                                         key=f"setup_stk_consult_{project_id}",
                                         placeholder="Describe the stakeholder consultation process and outcomes...",
                                         height=80)
        stk_grievance = st.text_area("Grievance mechanism", value=stk.get("grievance_mechanism", ""),
                                      key=f"setup_stk_grievance_{project_id}",
                                      placeholder="Describe the grievance redress mechanism...",
                                      height=80)
        stk_gender = st.text_area("Gender assessment", value=stk.get("gender_assessment", ""),
                                   key=f"setup_stk_gender_{project_id}",
                                   placeholder="Describe gender considerations and impact...",
                                   height=80)

    with st.container(border=True):
        st.markdown("#### Safeguards")
        safeg_env = st.text_area("Environmental safeguards", value=safeg.get("environmental_safeguards", ""),
                                  key=f"setup_safeg_env_{project_id}",
                                  placeholder="Describe environmental safeguards and mitigation measures...",
                                  height=80)
        safeg_social = st.text_area("Social safeguards", value=safeg.get("social_safeguards", ""),
                                     key=f"setup_safeg_social_{project_id}",
                                     placeholder="Describe social safeguards...",
                                     height=80)
        safeg_dnh = st.text_area("Do no harm assessment", value=safeg.get("do_no_harm", ""),
                                  key=f"setup_safeg_dnh_{project_id}",
                                  placeholder="Describe the do-no-harm assessment...",
                                  height=80)

    return {
        "project_overview": {
            "objective": po_objective, "summary": po_summary,
            "start_date": po_start_date, "scale": po_scale, "num_units": po_num_units,
        },
        "technology": {
            "description": tech_desc, "manufacturer": tech_manufacturer, "model": tech_model,
            "fuel_baseline": tech_baseline_scenario, "fuel_project": tech_project_scenario,
            "baseline_scenario": tech_baseline_scenario, "project_scenario": tech_project_scenario,
            "distribution_method": tech_distribution,
        },
        "location": {
            "regions": loc_regions, "coordinates": loc_coords,
            "target_population": loc_target, "beneficiaries": loc_beneficiaries,
        },
        "baseline_additionality": {
            "baseline_scenario": ba_baseline, "additionality_justification": ba_additionality,
            "barriers": ba_barriers, "common_practice": ba_common,
        },
        "monitoring": {
            "monitoring_approach": mon_approach, "key_parameters": mon_params,
            "sampling_approach": mon_sampling, "qa_qc": mon_qaqc,
        },
        "emission_reductions": {
            "annual_er_estimate": er_annual, "total_er_estimate": er_total,
            "calculation_approach": er_calc_approach, "er_summary": er_summary,
        },
        "sdgs": {"selected_sdgs": sdg_list},
        "stakeholders": {
            "consultation_summary": stk_consultation, "grievance_mechanism": stk_grievance,
            "gender_assessment": stk_gender,
        },
        "safeguards": {
            "environmental_safeguards": safeg_env, "social_safeguards": safeg_social,
            "do_no_harm": safeg_dnh,
        },
    }


def _render_intake_poa(project_id, intake):
    prog = intake.get("programme", {})
    elig = intake.get("eligibility", {})
    mon = intake.get("monitoring", {})
    er = intake.get("emission_reductions", {})
    sdgs_data = intake.get("sdgs", {})
    stk = intake.get("stakeholders", {})
    safeg = intake.get("safeguards", {})

    with st.container(border=True):
        st.markdown("#### Programme Description")
        prog_objective = st.text_area("Programme objective", value=prog.get("objective", ""),
                                       key=f"setup_poa_objective_{project_id}",
                                       placeholder="What is the overall objective of this Programme of Activities?",
                                       height=80)
        prog_scope = st.text_area("Geographic scope", value=prog.get("geographic_scope", ""),
                                   key=f"setup_poa_scope_{project_id}",
                                   placeholder="Countries/regions covered by the programme...",
                                   height=80)
        pc1, pc2 = st.columns(2)
        with pc1:
            prog_cme = st.text_input("Coordinating/Managing Entity (CME)", value=prog.get("cme_name", ""),
                                      key=f"setup_poa_cme_{project_id}",
                                      placeholder="Name of the CME organization")
        with pc2:
            prog_target_vpas = st.text_input("Target number of VPAs", value=prog.get("target_vpas", ""),
                                              key=f"setup_poa_target_vpas_{project_id}",
                                              placeholder="e.g., 15")
        prog_cme_details = st.text_area("CME organizational details", value=prog.get("cme_details", ""),
                                         key=f"setup_poa_cme_details_{project_id}",
                                         placeholder="Describe the CME's role, experience, and organizational structure...",
                                         height=80)

    with st.container(border=True):
        st.markdown("#### Eligibility & Inclusion")
        elig_criteria = st.text_area("VPA eligibility criteria", value=elig.get("criteria", ""),
                                      key=f"setup_poa_elig_{project_id}",
                                      placeholder="What criteria must a VPA meet to be included in this programme?",
                                      height=100)
        elig_process = st.text_area("VPA inclusion process", value=elig.get("inclusion_process", ""),
                                     key=f"setup_poa_inclusion_{project_id}",
                                     placeholder="Describe the process for adding new VPAs to the programme...",
                                     height=80)
        elig_approval = st.text_area("VPA approval mechanism", value=elig.get("approval_mechanism", ""),
                                      key=f"setup_poa_approval_{project_id}",
                                      placeholder="How are VPAs approved and validated?",
                                      height=80)

    with st.container(border=True):
        st.markdown("#### Monitoring & Emission Reductions")
        mon_approach = st.text_area("Programme-level monitoring approach", value=mon.get("monitoring_approach", ""),
                                     key=f"setup_poa_mon_{project_id}",
                                     placeholder="Describe the overall monitoring framework for the programme...",
                                     height=80)
        ec1, ec2 = st.columns(2)
        with ec1:
            er_annual = st.text_input("Estimated annual ERs (tCO2e)", value=er.get("annual_er_estimate", ""),
                                       key=f"setup_poa_er_annual_{project_id}")
        with ec2:
            er_total = st.text_input("Total estimated ERs (tCO2e)", value=er.get("total_er_estimate", ""),
                                      key=f"setup_poa_er_total_{project_id}")

    sdg_list = _render_sdg_section(project_id, sdgs_data)

    with st.container(border=True):
        st.markdown("#### Stakeholder Engagement")
        stk_consultation = st.text_area("Consultation summary", value=stk.get("consultation_summary", ""),
                                         key=f"setup_poa_stk_{project_id}",
                                         placeholder="Describe the stakeholder consultation process...",
                                         height=80)
        stk_grievance = st.text_area("Grievance mechanism", value=stk.get("grievance_mechanism", ""),
                                      key=f"setup_poa_grievance_{project_id}",
                                      placeholder="Describe the grievance redress mechanism...",
                                      height=80)

    with st.container(border=True):
        st.markdown("#### Safeguards")
        safeg_env = st.text_area("Environmental safeguards", value=safeg.get("environmental_safeguards", ""),
                                  key=f"setup_poa_safeg_env_{project_id}", height=80)
        safeg_social = st.text_area("Social safeguards", value=safeg.get("social_safeguards", ""),
                                     key=f"setup_poa_safeg_social_{project_id}", height=80)

    return {
        "programme": {
            "objective": prog_objective, "geographic_scope": prog_scope,
            "cme_name": prog_cme, "cme_details": prog_cme_details,
            "target_vpas": prog_target_vpas,
        },
        "eligibility": {
            "criteria": elig_criteria, "inclusion_process": elig_process,
            "approval_mechanism": elig_approval,
        },
        "monitoring": {"monitoring_approach": mon_approach},
        "emission_reductions": {"annual_er_estimate": er_annual, "total_er_estimate": er_total},
        "sdgs": {"selected_sdgs": sdg_list},
        "stakeholders": {"consultation_summary": stk_consultation, "grievance_mechanism": stk_grievance},
        "safeguards": {"environmental_safeguards": safeg_env, "social_safeguards": safeg_social},
    }


def _render_intake_vpa(project_id, intake):
    vpa = intake.get("vpa_details", {})
    tech = intake.get("technology", {})
    loc = intake.get("location", {})
    mon = intake.get("monitoring", {})
    er = intake.get("emission_reductions", {})

    with st.container(border=True):
        st.markdown("#### VPA Details")
        vpa_elig = st.text_area("How this VPA meets PoA eligibility criteria", value=vpa.get("eligibility_justification", ""),
                                 key=f"setup_vpa_elig_{project_id}",
                                 placeholder="Explain how this VPA satisfies the eligibility criteria defined in the parent PoA-DD...",
                                 height=100)
        vpa_start = st.text_input("VPA start date", value=vpa.get("start_date", ""),
                                   key=f"setup_vpa_start_{project_id}",
                                   placeholder="YYYY-MM-DD")

    with st.container(border=True):
        st.markdown("#### Technology & Approach")
        tech_desc = st.text_area("VPA-specific technology/approach", value=tech.get("description", ""),
                                  key=f"setup_vpa_tech_{project_id}",
                                  placeholder="Describe the technology or approach specific to this VPA...",
                                  height=80)
        tc1, tc2 = st.columns(2)
        with tc1:
            tech_manufacturer = st.text_input("Manufacturer", value=tech.get("manufacturer", ""),
                                               key=f"setup_vpa_mfr_{project_id}")
        with tc2:
            tech_model = st.text_input("Model", value=tech.get("model", ""),
                                        key=f"setup_vpa_model_{project_id}")

    with st.container(border=True):
        st.markdown("#### Location & Geography")
        loc_regions = st.text_input("VPA location / regions", value=loc.get("regions", ""),
                                     key=f"setup_vpa_regions_{project_id}",
                                     placeholder="Specific regions or districts for this VPA")
        loc_coords = st.text_input("Coordinates", value=loc.get("coordinates", ""),
                                    key=f"setup_vpa_coords_{project_id}",
                                    placeholder="e.g., 7.9465, -1.0232")
        lc1, lc2 = st.columns(2)
        with lc1:
            loc_target = st.text_input("Target population", value=loc.get("target_population", ""),
                                        key=f"setup_vpa_target_{project_id}")
        with lc2:
            loc_beneficiaries = st.text_input("Number of beneficiaries", value=loc.get("beneficiaries", ""),
                                               key=f"setup_vpa_bene_{project_id}")

    with st.container(border=True):
        st.markdown("#### Monitoring & Emission Reductions")
        mon_approach = st.text_area("VPA-specific monitoring arrangements", value=mon.get("monitoring_approach", ""),
                                     key=f"setup_vpa_mon_{project_id}",
                                     placeholder="Any VPA-specific monitoring requirements beyond the PoA-level plan...",
                                     height=80)
        ec1, ec2 = st.columns(2)
        with ec1:
            er_annual = st.text_input("Expected annual ERs (tCO2e)", value=er.get("annual_er_estimate", ""),
                                       key=f"setup_vpa_er_annual_{project_id}")
        with ec2:
            er_total = st.text_input("Expected total ERs (tCO2e)", value=er.get("total_er_estimate", ""),
                                      key=f"setup_vpa_er_total_{project_id}")

    return {
        "vpa_details": {
            "eligibility_justification": vpa_elig, "start_date": vpa_start,
        },
        "technology": {
            "description": tech_desc, "manufacturer": tech_manufacturer, "model": tech_model,
        },
        "location": {
            "regions": loc_regions, "coordinates": loc_coords,
            "target_population": loc_target, "beneficiaries": loc_beneficiaries,
        },
        "monitoring": {"monitoring_approach": mon_approach},
        "emission_reductions": {"annual_er_estimate": er_annual, "total_er_estimate": er_total},
    }


def _render_intake_mr(project_id, intake):
    period = intake.get("monitoring_period", {})
    data = intake.get("data_collection", {})
    deviations = intake.get("deviations", {})
    results = intake.get("results", {})

    with st.container(border=True):
        st.markdown("#### Monitoring Period")
        mp1, mp2 = st.columns(2)
        with mp1:
            period_start = st.text_input("Monitoring period start", value=period.get("start_date", ""),
                                          key=f"setup_mr_period_start_{project_id}",
                                          placeholder="YYYY-MM-DD")
        with mp2:
            period_end = st.text_input("Monitoring period end", value=period.get("end_date", ""),
                                        key=f"setup_mr_period_end_{project_id}",
                                        placeholder="YYYY-MM-DD")
        period_number = st.text_input("Monitoring period number", value=period.get("period_number", ""),
                                       key=f"setup_mr_period_num_{project_id}",
                                       placeholder="e.g., 1, 2, 3...")

    with st.container(border=True):
        st.markdown("#### Data Collection")
        data_units = st.text_input("Number of devices/installations in this period",
                                    value=data.get("num_units", ""),
                                    key=f"setup_mr_units_{project_id}",
                                    placeholder="e.g., 25,000 stoves distributed")
        data_summary = st.text_area("Data collection summary", value=data.get("collection_summary", ""),
                                     key=f"setup_mr_data_summary_{project_id}",
                                     placeholder="Summarize the monitoring data collected during this period...",
                                     height=100)
        data_highlights = st.text_area("Key monitoring data highlights", value=data.get("data_highlights", ""),
                                        key=f"setup_mr_highlights_{project_id}",
                                        placeholder="Notable findings, trends, or data points...",
                                        height=80)

    with st.container(border=True):
        st.markdown("#### Deviations & Changes")
        dev_methodology = st.text_area("Deviations from PDD methodology", value=deviations.get("methodology_deviations", ""),
                                        key=f"setup_mr_dev_meth_{project_id}",
                                        placeholder="Describe any deviations from the applied methodology...",
                                        height=80)
        dev_changes = st.text_area("Changes since last monitoring period", value=deviations.get("period_changes", ""),
                                    key=f"setup_mr_dev_changes_{project_id}",
                                    placeholder="Describe any changes compared to the previous monitoring period...",
                                    height=80)

    with st.container(border=True):
        st.markdown("#### Emission Reduction Results")
        rc1, rc2 = st.columns(2)
        with rc1:
            res_baseline = st.text_input("Baseline emissions (tCO2e)", value=results.get("baseline_emissions", ""),
                                          key=f"setup_mr_res_bl_{project_id}")
        with rc2:
            res_project = st.text_input("Project emissions (tCO2e)", value=results.get("project_emissions", ""),
                                         key=f"setup_mr_res_pj_{project_id}")
        rc3, rc4 = st.columns(2)
        with rc3:
            res_leakage = st.text_input("Leakage (tCO2e)", value=results.get("leakage", ""),
                                         key=f"setup_mr_res_leak_{project_id}")
        with rc4:
            res_net = st.text_input("Net emission reductions (tCO2e)", value=results.get("net_er", ""),
                                     key=f"setup_mr_res_net_{project_id}")

    return {
        "monitoring_period": {
            "start_date": period_start, "end_date": period_end,
            "period_number": period_number,
        },
        "data_collection": {
            "num_units": data_units, "collection_summary": data_summary,
            "data_highlights": data_highlights,
        },
        "deviations": {
            "methodology_deviations": dev_methodology, "period_changes": dev_changes,
        },
        "results": {
            "baseline_emissions": res_baseline, "project_emissions": res_project,
            "leakage": res_leakage, "net_er": res_net,
        },
    }


def _render_intake_valver(project_id, intake):
    scope = intake.get("scope", {})
    assessment = intake.get("assessment", {})
    findings = intake.get("findings", {})

    with st.container(border=True):
        st.markdown("#### Assessment Scope")
        scope_type = st.selectbox("Assessment type",
                                   ["Validation", "Verification", "Combined"],
                                   index=["Validation", "Verification", "Combined"].index(scope.get("assessment_type", "Validation"))
                                   if scope.get("assessment_type") in ["Validation", "Verification", "Combined"] else 0,
                                   key=f"setup_vv_type_{project_id}")
        scope_desc = st.text_area("Scope description", value=scope.get("scope_description", ""),
                                   key=f"setup_vv_scope_{project_id}",
                                   placeholder="Describe the scope of this validation/verification...",
                                   height=80)

    with st.container(border=True):
        st.markdown("#### Assessment Methodology")
        assess_method = st.text_area("Assessment methodology", value=assessment.get("methodology", ""),
                                      key=f"setup_vv_method_{project_id}",
                                      placeholder="Describe the assessment methodology used...",
                                      height=80)
        assess_site = st.text_area("Site visit details", value=assessment.get("site_visit", ""),
                                    key=f"setup_vv_site_{project_id}",
                                    placeholder="Details of site visits conducted...",
                                    height=80)
        assess_interviews = st.text_area("Interview records", value=assessment.get("interviews", ""),
                                          key=f"setup_vv_interviews_{project_id}",
                                          placeholder="Summary of interviews conducted...",
                                          height=80)

    with st.container(border=True):
        st.markdown("#### Key Findings")
        findings_summary = st.text_area("Findings summary", value=findings.get("summary", ""),
                                         key=f"setup_vv_findings_{project_id}",
                                         placeholder="Summary of key findings from the assessment...",
                                         height=100)
        findings_cars = st.text_area("CARs (Corrective Action Requests)", value=findings.get("cars", ""),
                                      key=f"setup_vv_cars_{project_id}",
                                      placeholder="List any Corrective Action Requests raised...",
                                      height=80)
        findings_cls = st.text_area("CLs (Clarification Requests)", value=findings.get("cls", ""),
                                     key=f"setup_vv_cls_{project_id}",
                                     placeholder="List any Clarification Requests raised...",
                                     height=80)

    return {
        "scope": {
            "assessment_type": scope_type, "scope_description": scope_desc,
        },
        "assessment": {
            "methodology": assess_method, "site_visit": assess_site,
            "interviews": assess_interviews,
        },
        "findings": {
            "summary": findings_summary, "cars": findings_cars, "cls": findings_cls,
        },
    }


def _render_sdg_section(project_id, sdgs_data):
    with st.container(border=True):
        st.markdown("#### SDGs & Co-benefits")
        st.caption("Select the Sustainable Development Goals this project contributes to.")
        existing_sdgs = sdgs_data.get("selected_sdgs", [])
        sdg_list = []
        sdg_goals = [
            "1 - No Poverty", "2 - Zero Hunger", "3 - Good Health and Well-being",
            "4 - Quality Education", "5 - Gender Equality", "6 - Clean Water and Sanitation",
            "7 - Affordable and Clean Energy", "8 - Decent Work and Economic Growth",
            "9 - Industry, Innovation and Infrastructure", "10 - Reduced Inequalities",
            "11 - Sustainable Cities and Communities", "12 - Responsible Consumption and Production",
            "13 - Climate Action", "14 - Life Below Water", "15 - Life on Land",
            "16 - Peace, Justice and Strong Institutions", "17 - Partnerships for the Goals",
        ]
        existing_map = {str(s.get("goal_number", "")): s.get("contribution_description", "") for s in existing_sdgs}
        for goal in sdg_goals:
            goal_num = goal.split(" - ")[0].strip()
            is_selected = st.checkbox(goal, value=goal_num in existing_map,
                                       key=f"setup_sdg_{project_id}_{goal_num}")
            if is_selected:
                contrib = st.text_input(
                    f"SDG {goal_num} contribution",
                    value=existing_map.get(goal_num, ""),
                    key=f"setup_sdg_contrib_{project_id}_{goal_num}",
                    placeholder=f"How does the project contribute to SDG {goal_num}?",
                )
                sdg_list.append({"goal_number": goal_num, "contribution_description": contrib})
    return sdg_list


def _render_project_settings(project):
    project_id = project["id"]
    project_type = project.get("project_type", "standalone_pdd")
    intake = project.get("project_intake") or {}
    if isinstance(intake, str):
        import json as _json
        intake = _json.loads(intake)

    st.subheader("Project Setup")
    st.caption("Fill in the details below. This data will be used by the AI when drafting and reviewing your documents.")

    with st.container(border=True):
        st.markdown("#### About Your Project")
        new_name = st.text_input("Project name", value=project.get("name", ""),
                                  key=f"setup_name_{project_id}")
        c1, c2 = st.columns(2)
        with c1:
            new_standard = st.selectbox("Standard", STANDARD_OPTIONS,
                                         index=STANDARD_OPTIONS.index(project.get("standard", "GoldStandard"))
                                         if project.get("standard") in STANDARD_OPTIONS else 0,
                                         key=f"setup_standard_{project_id}")
        with c2:
            new_country = st.text_input("Country", value=project.get("country", "") or "",
                                         key=f"setup_country_{project_id}")
        new_methodology = _methodology_selector(
            f"setup_{project_id}", standard=new_standard,
            current_value=project.get("methodology"))

        meth_detail = None
        if new_methodology:
            meth_detail = _fetch(f"/projects/methodologies/{new_methodology}")
        if meth_detail:
            with st.container(border=True):
                st.caption("Selected methodology")
                meth_name = meth_detail.get("name") or ""
                meth_code = meth_detail.get("code", "")
                meth_version = meth_detail.get("version") or ""
                header = f"**{meth_code}**"
                if meth_version:
                    header += f" v{meth_version}"
                if meth_name:
                    header += f" - {meth_name}"
                st.markdown(header)
                detail_parts = []
                if meth_detail.get("standard"):
                    std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS", "CDM": "CDM"}.get(meth_detail["standard"], meth_detail["standard"])
                    detail_parts.append(f"Standard: {std_display}")
                if meth_detail.get("sector"):
                    detail_parts.append(f"Sector: {meth_detail['sector']}")
                if meth_detail.get("category"):
                    detail_parts.append(f"Category: {meth_detail['category']}")
                if detail_parts:
                    st.markdown(" | ".join(detail_parts))
                if meth_detail.get("applicability"):
                    st.markdown(f"Applicability: {meth_detail['applicability']}")
                if meth_detail.get("status") == "deprecated":
                    st.warning(f"This methodology is deprecated. Superseded by: {meth_detail.get('superseded_by', 'N/A')}")

        new_desc = st.text_area("Project description / objective", value=project.get("description", "") or "",
                                 key=f"setup_desc_{project_id}",
                                 placeholder="Briefly describe the project activity and its objective...")
        new_status = st.selectbox("Project status", list(STATUS_LABELS.keys()),
                                   format_func=lambda x: STATUS_LABELS[x],
                                   index=list(STATUS_LABELS.keys()).index(project.get("status", "draft"))
                                   if project.get("status") in STATUS_LABELS else 0,
                                   key=f"setup_status_{project_id}")

    intake_data = _render_intake_by_type(project_id, project_type, intake)

    st.divider()
    st.subheader("Crediting Period")

    from datetime import date as _date

    cp_start_raw = project.get("crediting_period_start")
    cp_start_val = None
    if cp_start_raw:
        try:
            if isinstance(cp_start_raw, str):
                cp_start_val = _date.fromisoformat(cp_start_raw[:10])
            else:
                cp_start_val = cp_start_raw
        except Exception:
            pass
    cp_start = st.date_input(
        "Crediting period start date",
        value=cp_start_val,
        key=f"setup_cp_start_{project_id}",
    )
    cp_years = st.number_input(
        "Crediting period (years)",
        min_value=1, max_value=30,
        value=project.get("crediting_period_years") or 7,
        key=f"setup_cp_years_{project_id}",
    )
    if cp_start:
        cp_end = _date(cp_start.year + cp_years, cp_start.month, cp_start.day) if cp_start else None
        if cp_end:
            st.caption(f"Crediting period: {cp_start.isoformat()} to {cp_end.isoformat()} ({cp_years} years)")
            vintages = [str(cp_start.year + i) for i in range(cp_years)]
            st.caption(f"Vintages: {', '.join(vintages)}")

    existing_settings = project.get("project_settings") or {}

    meth_parsed = None
    methodology = project.get("methodology")
    if methodology:
        meth_data = _fetch(f"/projects/{project_id}/methodology-data")
        if meth_data and meth_data.get("status") == "ready":
            meth_parsed = meth_data.get("parsed")

    new_settings = dict(existing_settings)
    context_dims = []
    if meth_parsed:
        context_dims = meth_parsed.get("context_dimensions", [])

    if context_dims:
        st.divider()
        st.subheader("Methodology Parameters")
        st.caption("These settings determine which default values are used in calculations.")

        for dim in context_dims:
            dim_key = dim["dimension_key"]
            options = dim["options"]
            current_val = existing_settings.get(dim_key, "")
            idx = 0
            if current_val in options:
                idx = options.index(current_val)
            selected = st.selectbox(
                dim["label"],
                options,
                index=idx,
                key=f"setup_dim_{project_id}_{dim_key}",
                help=dim.get("description", ""),
            )
            new_settings[dim_key] = selected

    st.divider()

    if st.button("Save All Changes", key=f"save_setup_{project_id}", type="primary"):
        update_payload = {
            "name": new_name,
            "standard": new_standard,
            "methodology": new_methodology,
            "country": new_country or None,
            "description": new_desc or None,
            "status": new_status,
            "crediting_period_years": cp_years,
            "project_settings": new_settings,
            "project_intake": intake_data,
        }
        if cp_start:
            update_payload["crediting_period_start"] = cp_start.isoformat()
        _fetch(f"/projects/{project_id}", method="PATCH", json=update_payload)
        st.success("Project updated.")
        time.sleep(0.5)
        st.rerun()

    st.divider()
    st.subheader("Danger Zone")
    if st.button("Delete Project", key=f"delete_proj_{project_id}", type="secondary"):
        st.session_state[f"confirm_delete_{project_id}"] = True

    if st.session_state.get(f"confirm_delete_{project_id}"):
        st.warning("Are you sure? This will delete the project and all its documents.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete", key=f"confirm_del_yes_{project_id}"):
                _fetch(f"/projects/{project_id}", method="DELETE")
                st.session_state.selected_project_id = None
                st.session_state.pop(f"confirm_delete_{project_id}", None)
                st.rerun()
        with col2:
            if st.button("Cancel", key=f"confirm_del_no_{project_id}"):
                st.session_state.pop(f"confirm_delete_{project_id}", None)
                st.rerun()


def _render_project_settings_legacy(project):
    project_id = project["id"]
    st.subheader("Project Settings")

    new_name = st.text_input("Project name", value=project.get("name", ""),
                              key=f"settings_name_{project_id}")
    new_standard = st.selectbox("Standard", STANDARD_OPTIONS,
                                 index=STANDARD_OPTIONS.index(project.get("standard", "GoldStandard"))
                                 if project.get("standard") in STANDARD_OPTIONS else 0,
                                 key=f"settings_standard_{project_id}")
    new_methodology = _methodology_selector(
        f"settings_{project_id}", standard=new_standard,
        current_value=project.get("methodology"))

    meth_detail = None
    if new_methodology:
        meth_detail = _fetch(f"/projects/methodologies/{new_methodology}")
    if meth_detail:
        with st.container(border=True):
            st.caption("Selected methodology")
            meth_name = meth_detail.get("name") or ""
            meth_code = meth_detail.get("code", "")
            meth_version = meth_detail.get("version") or ""
            header = f"**{meth_code}**"
            if meth_version:
                header += f" v{meth_version}"
            if meth_name:
                header += f" - {meth_name}"
            st.markdown(header)
            detail_parts = []
            if meth_detail.get("standard"):
                std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS", "CDM": "CDM"}.get(meth_detail["standard"], meth_detail["standard"])
                detail_parts.append(f"Standard: {std_display}")
            if meth_detail.get("sector"):
                detail_parts.append(f"Sector: {meth_detail['sector']}")
            if meth_detail.get("category"):
                detail_parts.append(f"Category: {meth_detail['category']}")
            if detail_parts:
                st.markdown(" | ".join(detail_parts))
            if meth_detail.get("applicability"):
                st.markdown(f"Applicability: {meth_detail['applicability']}")
            if meth_detail.get("status") == "deprecated":
                st.warning(f"This methodology is deprecated. Superseded by: {meth_detail.get('superseded_by', 'N/A')}")

    new_country = st.text_input("Country", value=project.get("country", "") or "",
                                 key=f"settings_country_{project_id}")
    new_desc = st.text_area("Description", value=project.get("description", "") or "",
                             key=f"settings_desc_{project_id}")
    new_status = st.selectbox("Status", list(STATUS_LABELS.keys()),
                               format_func=lambda x: STATUS_LABELS[x],
                               index=list(STATUS_LABELS.keys()).index(project.get("status", "draft"))
                               if project.get("status") in STATUS_LABELS else 0,
                               key=f"settings_status_{project_id}")

    st.divider()
    st.subheader("Crediting Period")

    from datetime import date as _date

    cp_start_raw = project.get("crediting_period_start")
    cp_start_val = None
    if cp_start_raw:
        try:
            if isinstance(cp_start_raw, str):
                cp_start_val = _date.fromisoformat(cp_start_raw[:10])
            else:
                cp_start_val = cp_start_raw
        except Exception:
            pass
    cp_start = st.date_input(
        "Crediting period start date",
        value=cp_start_val,
        key=f"settings_cp_start_{project_id}",
    )
    cp_years = st.number_input(
        "Crediting period (years)",
        min_value=1, max_value=30,
        value=project.get("crediting_period_years") or 7,
        key=f"settings_cp_years_{project_id}",
    )
    if cp_start:
        from datetime import timedelta
        cp_end = _date(cp_start.year + cp_years, cp_start.month, cp_start.day) if cp_start else None
        if cp_end:
            st.caption(f"Crediting period: {cp_start.isoformat()} to {cp_end.isoformat()} ({cp_years} years)")
            vintages = [str(cp_start.year + i) for i in range(cp_years)]
            st.caption(f"Vintages: {', '.join(vintages)}")

    existing_settings = project.get("project_settings") or {}

    meth_parsed = None
    methodology = project.get("methodology")
    if methodology:
        meth_data = _fetch(f"/projects/{project_id}/methodology-data")
        if meth_data and meth_data.get("status") == "ready":
            meth_parsed = meth_data.get("parsed")

    new_settings = dict(existing_settings)
    context_dims = []
    if meth_parsed:
        context_dims = meth_parsed.get("context_dimensions", [])

    if context_dims:
        st.divider()
        st.subheader("Methodology Parameters")
        st.caption("These settings determine which default values are used in calculations.")

        for dim in context_dims:
            dim_key = dim["dimension_key"]
            options = dim["options"]
            current_val = existing_settings.get(dim_key, "")
            idx = 0
            if current_val in options:
                idx = options.index(current_val)
            selected = st.selectbox(
                dim["label"],
                options,
                index=idx,
                key=f"settings_dim_{project_id}_{dim_key}",
                help=dim.get("description", ""),
            )
            new_settings[dim_key] = selected

    st.divider()

    if st.button("Save Changes", key=f"save_settings_{project_id}", type="primary"):
        update_payload = {
            "name": new_name,
            "standard": new_standard,
            "methodology": new_methodology,
            "country": new_country or None,
            "description": new_desc or None,
            "status": new_status,
            "crediting_period_years": cp_years,
            "project_settings": new_settings,
        }
        if cp_start:
            update_payload["crediting_period_start"] = cp_start.isoformat()
        _fetch(f"/projects/{project_id}", method="PATCH", json=update_payload)
        st.success("Project updated.")
        time.sleep(0.5)
        st.rerun()

    st.divider()
    st.subheader("Danger Zone")
    if st.button("Delete Project", key=f"delete_proj_{project_id}", type="secondary"):
        st.session_state[f"confirm_delete_{project_id}"] = True

    if st.session_state.get(f"confirm_delete_{project_id}"):
        st.warning("Are you sure? This will delete the project and all its documents.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete", key=f"confirm_del_yes_{project_id}"):
                _fetch(f"/projects/{project_id}", method="DELETE")
                st.session_state.selected_project_id = None
                st.session_state.pop(f"confirm_delete_{project_id}", None)
                st.rerun()
        with col2:
            if st.button("Cancel", key=f"confirm_del_no_{project_id}"):
                st.session_state.pop(f"confirm_delete_{project_id}", None)
                st.rerun()


if page == "Workspace":
    if "selected_project_id" not in st.session_state:
        st.session_state.selected_project_id = None

    if st.session_state.selected_project_id:
        _render_project_workspace(st.session_state.selected_project_id)
    else:
        _render_home()
elif page == "Admin":
    render_repository()
