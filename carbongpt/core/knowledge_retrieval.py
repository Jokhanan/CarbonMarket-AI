import logging
import os

logger = logging.getLogger(__name__)

MAX_CONTEXT_TOKENS = 2000
MAX_CHUNKS_PER_QUERY = 8
MAX_DISTANCE = 0.55

STANDARD_SLUG_MAP = {
    "GoldStandard": "Gold Standard",
    "Verra": "Verra VCS",
}


def _resolve_standard_version_id(standard: str):
    try:
        from carbongpt.repository.store import list_standard_versions
        std_label = STANDARD_SLUG_MAP.get(standard, standard)
        versions = list_standard_versions()
        for v in versions:
            if v.get("standard_name") == std_label:
                return v["id"]
    except Exception:
        pass
    return None


def retrieve_section_context(
    section_title: str,
    section_text: str,
    standard: str = "GoldStandard",
    doc_type: str = "MR",
) -> list[dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []

    try:
        from carbongpt.repository.store import search_chunks, get_chunk_count
        chunk_count = get_chunk_count()
        if chunk_count == 0:
            return []
    except Exception as e:
        logger.debug("Repository not available for context retrieval: %s", e)
        return []

    query = _build_search_query(section_title, section_text, standard, doc_type)

    try:
        from carbongpt.repository.ingestion import create_embeddings
        query_embedding = create_embeddings([query], api_key)[0]
    except Exception as e:
        logger.warning("Failed to create query embedding: %s", e)
        return []

    try:
        from carbongpt.repository.store import hybrid_search
        results = hybrid_search(
            query_text=query,
            query_embedding=query_embedding,
            limit=MAX_CHUNKS_PER_QUERY,
        )
        is_hybrid = True
    except Exception:
        try:
            results = search_chunks(
                query_embedding,
                limit=MAX_CHUNKS_PER_QUERY,
            )
            is_hybrid = False
        except Exception as e:
            logger.warning("Failed to search repository: %s", e)
            return []

    std_label = STANDARD_SLUG_MAP.get(standard, standard)
    context_chunks = []
    total_tokens = 0
    for r in results:
        if is_hybrid:
            score = r.get("combined_score", 0)
            relevance = round(min(1.0, score), 2)
        else:
            distance = r.get("distance", 1.0)
            if distance > MAX_DISTANCE:
                continue
            relevance = round(max(0, 1 - distance), 2)

        chunk_std = r.get("standard_name", "")
        if chunk_std and chunk_std != std_label:
            continue

        token_count = r.get("token_count", 0) or len(r.get("content", "").split())
        if total_tokens + token_count > MAX_CONTEXT_TOKENS:
            break

        meta = r.get("metadata", {})
        if isinstance(meta, str):
            import json
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}

        source = r.get("document_title", "Unknown")
        section_info = meta.get("section_title", "")
        if section_info:
            source = f"{source} > {section_info}"

        context_chunks.append({
            "content": r["content"],
            "source": source,
            "category": r.get("document_category", ""),
            "standard": chunk_std,
            "relevance": relevance,
        })
        total_tokens += token_count

    return context_chunks


def _build_search_query(
    section_title: str,
    section_text: str,
    standard: str,
    doc_type: str,
) -> str:
    standard_label = {
        "GoldStandard": "Gold Standard",
        "Verra": "Verra VCS",
    }.get(standard, standard)

    doc_label = {
        "MR": "Monitoring Report",
        "PDD": "Project Design Document",
        "VCS-PD": "VCS Project Description",
        "VCS-MR": "VCS Monitoring Report",
        "VCS-ValVer": "VCS Validation Verification Report",
    }.get(doc_type, doc_type)

    text_preview = section_text[:300] if section_text else ""

    return (
        f"{standard_label} {doc_label} requirements for section: {section_title}. "
        f"Methodology and standard requirements, eligibility criteria, "
        f"calculation methods, monitoring parameters. "
        f"Context: {text_preview}"
    )


SECTION_DOMAIN_MAP = {
    "B.4": "baseline",
    "B.5": "additionality",
    "B.6": "baseline",
    "D": "monitoring",
    "D.1": "monitoring",
    "D.2": "monitoring",
    "D.3": "monitoring",
    "D.4": "monitoring",
    "D.5": "monitoring",
    "D.6": "monitoring",
    "D.7": "sampling",
    "3": "baseline",
    "3.1": "baseline",
    "3.2": "baseline",
    "3.3": "additionality",
    "3.4": "baseline",
    "3.5": "additionality",
    "3.6": "baseline",
    "4": "baseline",
    "4.1": "baseline",
    "4.2": "baseline",
    "4.3": "baseline",
    "4.4": "baseline",
    "5": "monitoring",
    "5.1": "monitoring",
    "5.2": "monitoring",
    "5.3": "monitoring",
    "7": "monitoring",
    "7.1": "monitoring",
    "7.2": "monitoring",
    "7.3": "monitoring",
    "7.4": "sampling",
}

SECTION_DOMAIN_TITLE_KEYWORDS = {
    "baseline": ["baseline", "base line", "baseline scenario", "business as usual"],
    "additionality": ["additionality", "barrier", "investment analysis", "common practice"],
    "monitoring": ["monitoring", "monitoring plan", "data quality", "qa/qc"],
    "sampling": ["sampling", "sample size", "sample design", "stratification"],
}

MAX_EXEMPLAR_CHARS = 2000


def map_section_to_domain(section_id, section_title=""):
    if section_id in SECTION_DOMAIN_MAP:
        return SECTION_DOMAIN_MAP[section_id]

    base = section_id.split(".")[0] if section_id else ""
    if base in SECTION_DOMAIN_MAP:
        return SECTION_DOMAIN_MAP[base]

    title_lower = (section_title or "").lower()
    for domain, keywords in SECTION_DOMAIN_TITLE_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                return domain

    return None


def retrieve_section_exemplar(section_domain, standard=None, methodology_code=None, project_type=None):
    if not section_domain:
        return ""

    std_label = STANDARD_SLUG_MAP.get(standard, standard) if standard else None

    try:
        from carbongpt.repository.db import get_cursor

        with get_cursor() as cur:
            if methodology_code and std_label:
                cur.execute("""
                    SELECT se.section_title, se.methodology_code, se.project_type,
                           ds.content, d.title as doc_title, ds.section_number
                    FROM section_exemplars se
                    JOIN document_sections ds ON ds.id = se.document_section_id
                    JOIN documents d ON d.id = se.document_id
                    WHERE se.section_domain = %s
                      AND se.is_usable = true
                      AND se.standard = %s
                      AND se.methodology_code = %s
                    ORDER BY se.word_count DESC
                    LIMIT 1
                """, (section_domain, std_label, methodology_code))
                row = cur.fetchone()
                if row:
                    return _format_exemplar(row)

            if project_type and std_label:
                cur.execute("""
                    SELECT se.section_title, se.methodology_code, se.project_type,
                           ds.content, d.title as doc_title, ds.section_number
                    FROM section_exemplars se
                    JOIN document_sections ds ON ds.id = se.document_section_id
                    JOIN documents d ON d.id = se.document_id
                    WHERE se.section_domain = %s
                      AND se.is_usable = true
                      AND se.standard = %s
                      AND se.project_type = %s
                    ORDER BY se.word_count DESC
                    LIMIT 1
                """, (section_domain, std_label, project_type))
                row = cur.fetchone()
                if row:
                    return _format_exemplar(row)

            if std_label:
                cur.execute("""
                    SELECT se.section_title, se.methodology_code, se.project_type,
                           ds.content, d.title as doc_title, ds.section_number
                    FROM section_exemplars se
                    JOIN document_sections ds ON ds.id = se.document_section_id
                    JOIN documents d ON d.id = se.document_id
                    WHERE se.section_domain = %s
                      AND se.is_usable = true
                      AND se.standard = %s
                    ORDER BY se.word_count DESC
                    LIMIT 1
                """, (section_domain, std_label))
                row = cur.fetchone()
                if row:
                    return _format_exemplar(row)

            cur.execute("""
                SELECT se.section_title, se.methodology_code, se.project_type,
                       ds.content, d.title as doc_title, ds.section_number
                FROM section_exemplars se
                JOIN document_sections ds ON ds.id = se.document_section_id
                JOIN documents d ON d.id = se.document_id
                WHERE se.section_domain = %s
                  AND se.is_usable = true
                ORDER BY se.word_count DESC
                LIMIT 1
            """, (section_domain,))
            row = cur.fetchone()
            if row:
                return _format_exemplar(row)

    except Exception as e:
        logger.warning("Section exemplar retrieval failed: %s", e)

    return ""


def _format_exemplar(row):
    content = row["content"] or ""
    if len(content) > MAX_EXEMPLAR_CHARS:
        content = content[:MAX_EXEMPLAR_CHARS] + "\n[... truncated ...]"

    source = row["doc_title"] or "Unknown"
    sec_num = row["section_number"] or ""
    sec_title = row["section_title"] or ""
    ptype = row["project_type"] or ""
    meth = row["methodology_code"] or ""

    source_parts = [source]
    if sec_num:
        source_parts.append(f"Section {sec_num}")
    if sec_title:
        source_parts.append(sec_title)

    meta_parts = []
    if ptype:
        meta_parts.append(f"Project type: {ptype}")
    if meth:
        meta_parts.append(f"Methodology: {meth}")

    header = " > ".join(source_parts)
    if meta_parts:
        header += f" ({', '.join(meta_parts)})"

    return (
        f"### Example from a similar project:\n"
        f"Source: {header}\n"
        f"```\n{content}\n```\n"
    )


def format_context_for_prompt(context_chunks: list[dict]) -> str:
    if not context_chunks:
        return ""

    parts = [
        "\n### Reference Material from Standards & Methodologies:\n"
        "The following extracts are from authoritative standard documents, "
        "methodologies, and guidance materials in the repository. "
        "Use these to verify the document section meets methodology-specific "
        "requirements, calculation rules, and eligibility criteria.\n"
    ]

    for i, chunk in enumerate(context_chunks, 1):
        source = chunk["source"]
        category = chunk["category"]
        relevance = chunk["relevance"]
        parts.append(
            f"\n**Reference {i}** (Source: {source} [{category}], "
            f"Relevance: {relevance:.0%}):\n"
            f"```\n{chunk['content']}\n```\n"
        )

    return "\n".join(parts)
