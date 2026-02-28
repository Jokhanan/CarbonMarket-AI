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
        results = search_chunks(
            query_embedding,
            limit=MAX_CHUNKS_PER_QUERY,
        )
    except Exception as e:
        logger.warning("Failed to search repository: %s", e)
        return []

    std_label = STANDARD_SLUG_MAP.get(standard, standard)
    context_chunks = []
    total_tokens = 0
    for r in results:
        distance = r.get("distance", 1.0)
        if distance > MAX_DISTANCE:
            continue

        chunk_std = r.get("standard_name", "")
        if chunk_std and chunk_std != std_label:
            continue

        token_count = r.get("token_count", 0) or len(r.get("content", "").split())
        if total_tokens + token_count > MAX_CONTEXT_TOKENS:
            break

        context_chunks.append({
            "content": r["content"],
            "source": r.get("document_title", "Unknown"),
            "category": r.get("document_category", ""),
            "standard": chunk_std,
            "relevance": round(max(0, 1 - distance), 2),
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
