import os
import time
import requests
import streamlit as st

API_BASE = os.getenv("CARBONGPT_API_URL", "http://localhost:3000")

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


def _fetch(endpoint, method="GET", **kwargs):
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=10, **kwargs)
        elif method == "POST":
            resp = requests.post(url, timeout=60, **kwargs)
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


def render_stats():
    stats = _fetch("/admin/stats")
    if not stats:
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Documents", stats.get("total_documents", 0))
    with col2:
        st.metric("Ingested", stats.get("ingested", 0))
    with col3:
        st.metric("Total Words", f"{stats.get('total_words', 0):,}")
    with col4:
        st.metric("Vector Chunks", stats.get("total_chunks", 0))

    pending = stats.get("pending", 0)
    processing = stats.get("processing", 0)
    failed = stats.get("failed", 0)
    if pending > 0 or processing > 0:
        st.info(f"Pending: {pending} | Processing: {processing}")
    if failed > 0:
        st.warning(f"Failed ingestions: {failed}")


def render_upload():
    st.subheader("Upload Documents")
    st.markdown("Drag and drop files below. Supported formats: PDF, DOCX, XLSX, CSV.")

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
            help="Select the type of document you are uploading.",
        )
    with col2:
        version_labels = ["Auto-detect / Not specified"] + list(version_options.keys())
        selected_version = st.selectbox(
            "Standard & Version",
            version_labels,
            key="upload_version",
            help="Select which standard version this document belongs to, or leave as auto-detect.",
        )

    col3, col4 = st.columns(2)
    with col3:
        reference_id = st.text_input(
            "Reference ID (optional)",
            placeholder="e.g., VM0007, AMS-II.G",
            key="upload_ref_id",
        )
    with col4:
        doc_version = st.text_input(
            "Document Version (optional)",
            placeholder="e.g., v6.0, v09",
            key="upload_doc_version",
        )

    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "docx", "xlsx", "csv"],
        accept_multiple_files=True,
        key="upload_files",
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected**")

    upload_btn = st.button(
        "Upload & Ingest",
        type="primary",
        disabled=not uploaded_files,
        key="upload_btn",
    )

    if upload_btn and uploaded_files:
        sv_id = version_options.get(selected_version) if selected_version != "Auto-detect / Not specified" else None
        progress = st.progress(0, text="Uploading...")

        for i, f in enumerate(uploaded_files):
            progress.progress((i + 1) / len(uploaded_files), text=f"Uploading {f.name}...")
            data = {
                "category": (None, category),
                "title": (None, f.name.rsplit(".", 1)[0]),
            }
            if sv_id:
                data["standard_version_id"] = (None, str(sv_id))
            if reference_id:
                data["reference_id"] = (None, reference_id)
            if doc_version:
                data["doc_version"] = (None, doc_version)

            files_data = {"file": (f.name, f.getvalue(), "application/octet-stream")}
            form_data = {}
            for key, val in data.items():
                form_data[key] = val[1]

            result = _fetch(
                "/admin/documents/upload",
                method="POST",
                files=files_data,
                data=form_data,
            )
            if result:
                st.success(f"Uploaded: {f.name} (ID: {result['id']})")
            else:
                st.error(f"Failed to upload: {f.name}")

        progress.empty()
        time.sleep(1)
        st.rerun()


def render_document_library():
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
        filter_version = st.selectbox(
            "Filter by Standard",
            list(version_options.keys()),
            key="filter_version",
        )
    with col3:
        refresh = st.button("Refresh", key="refresh_library")

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

            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if ing_status == "failed" or ing_status == "completed":
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


def render_search():
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


def render_manage_standards():
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


def main():
    st.set_page_config(page_title="CarbonGPT Admin", page_icon="gear", layout="wide")

    st.title("CarbonGPT — Document Repository")
    st.markdown(
        "Manage your carbon standards library. Upload standards, methodologies, guidance documents, "
        "templates, and example project documentation. Documents are automatically parsed, indexed, "
        "and classified by AI."
    )

    render_stats()

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Upload Documents",
        "Document Library",
        "Semantic Search",
        "Manage Standards",
    ])

    with tab1:
        render_upload()

    with tab2:
        render_document_library()

    with tab3:
        render_search()

    with tab4:
        render_manage_standards()


if __name__ == "__main__":
    main()
