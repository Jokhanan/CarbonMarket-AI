import logging
import os
import json

logger = logging.getLogger(__name__)

MAX_PROJECT_CONTEXT_TOKENS = 3000
MAX_PROJECT_CHUNKS = 10


def index_project_document(project_id, doc_id, parsed_text, parsed_sections=None, file_name=""):
    if not parsed_text or not parsed_text.strip():
        logger.info("No text to index for project doc %s/%s", project_id, doc_id)
        return 0

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No OPENAI_API_KEY, skipping project doc indexing")
        return 0

    from carbongpt.repository.ingestion import chunk_text, create_embeddings

    section_map = _build_section_map(parsed_sections)

    chunks = chunk_text(parsed_text)

    for chunk in chunks:
        chunk["section_title"] = _find_section_for_chunk(chunk, section_map, parsed_text)
        chunk["metadata"] = {
            "file_name": file_name,
            "project_id": project_id,
            "doc_id": doc_id,
        }

    try:
        chunk_texts = [c["content"] for c in chunks]
        embeddings = create_embeddings(chunk_texts, api_key)
        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = "[" + ",".join(str(x) for x in emb) + "]"
    except Exception as e:
        logger.warning("Embedding creation failed for project doc %s: %s", doc_id, e)
        for chunk in chunks:
            chunk["embedding"] = None

    try:
        _save_project_chunks(project_id, doc_id, chunks)
    except Exception as e:
        logger.error("Failed to save project doc chunks for doc %s: %s", doc_id, e)
        return 0

    logger.info("Indexed project doc %s: %d chunks for project %s", doc_id, len(chunks), project_id)
    return len(chunks)


def search_project_chunks(project_id, query_text, limit=None, max_tokens=None):
    if limit is None:
        limit = MAX_PROJECT_CHUNKS
    if max_tokens is None:
        max_tokens = MAX_PROJECT_CONTEXT_TOKENS

    query_embedding = None
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from carbongpt.repository.ingestion import create_embeddings
            query_embedding = create_embeddings([query_text], api_key)[0]
        except Exception as e:
            logger.warning("Failed to create query embedding for project search, using keyword-only: %s", e)

    return _hybrid_search_project(project_id, query_text, query_embedding, limit, max_tokens)


def delete_project_doc_chunks(doc_id):
    from carbongpt.repository.db import get_cursor
    try:
        with get_cursor() as cur:
            cur.execute("DELETE FROM project_doc_chunks WHERE doc_id = %s", (doc_id,))
        logger.info("Deleted chunks for project doc %s", doc_id)
    except Exception as e:
        logger.error("Failed to delete project doc chunks for doc %s: %s", doc_id, e)


def get_project_chunk_count(project_id):
    from carbongpt.repository.db import get_cursor
    try:
        with get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM project_doc_chunks WHERE project_id = %s", (project_id,))
            row = cur.fetchone()
            return row["cnt"] if row else 0
    except Exception:
        return 0


def _build_section_map(parsed_sections):
    if not parsed_sections:
        return []
    sections = parsed_sections if isinstance(parsed_sections, list) else []
    if isinstance(parsed_sections, dict):
        sections = [{"title": k, "content": v} for k, v in parsed_sections.items()]
    result = []
    for s in sections:
        title = s.get("title", "") or s.get("number", "")
        content = s.get("content", "")
        if title:
            result.append({"title": title, "content_preview": content[:200]})
    return result


def _find_section_for_chunk(chunk, section_map, full_text):
    if not section_map:
        return None
    chunk_text = chunk["content"]
    chunk_lower = chunk_text[:100].lower()
    for sec in section_map:
        if sec["title"].lower() in chunk_lower:
            return sec["title"]
        if sec["content_preview"] and sec["content_preview"][:80].lower() in chunk_lower:
            return sec["title"]
    return None


def _save_project_chunks(project_id, doc_id, chunks):
    from carbongpt.repository.db import get_cursor

    with get_cursor() as cur:
        cur.execute("DELETE FROM project_doc_chunks WHERE doc_id = %s", (doc_id,))

        for chunk in chunks:
            embedding_val = chunk.get("embedding")
            section_title = chunk.get("section_title")
            metadata = json.dumps(chunk.get("metadata", {}))
            content = chunk["content"]

            if embedding_val:
                cur.execute(
                    """INSERT INTO project_doc_chunks
                       (project_id, doc_id, chunk_index, content, token_count,
                        embedding, section_title, metadata, search_vector)
                       VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s::jsonb,
                               to_tsvector('english', %s))""",
                    (project_id, doc_id, chunk["chunk_index"], content,
                     chunk.get("token_count", 0), embedding_val, section_title,
                     metadata, content)
                )
            else:
                cur.execute(
                    """INSERT INTO project_doc_chunks
                       (project_id, doc_id, chunk_index, content, token_count,
                        section_title, metadata, search_vector)
                       VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb,
                               to_tsvector('english', %s))""",
                    (project_id, doc_id, chunk["chunk_index"], content,
                     chunk.get("token_count", 0), section_title,
                     metadata, content)
                )


def _hybrid_search_project(project_id, query_text, query_embedding, limit, max_tokens):
    from carbongpt.repository.db import get_cursor

    semantic_results = []
    if query_embedding is not None:
        emb_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        with get_cursor() as cur:
            cur.execute(
                """SELECT id, doc_id, chunk_index, content, token_count,
                          section_title, metadata,
                          embedding <=> %s::vector AS distance
                   FROM project_doc_chunks
                   WHERE project_id = %s AND embedding IS NOT NULL
                   ORDER BY distance ASC
                   LIMIT %s""",
                (emb_str, project_id, limit * 2)
            )
            semantic_results = cur.fetchall()

    with get_cursor() as cur:
        cur.execute(
            """SELECT id, doc_id, chunk_index, content, token_count,
                      section_title, metadata,
                      ts_rank_cd(search_vector, plainto_tsquery('english', %s)) AS rank
               FROM project_doc_chunks
               WHERE project_id = %s
                     AND search_vector @@ plainto_tsquery('english', %s)
               ORDER BY rank DESC
               LIMIT %s""",
            (query_text, project_id, query_text, limit * 2)
        )
        keyword_results = cur.fetchall()

    scored = {}
    if semantic_results:
        semantic_weight = 0.7
        keyword_weight = 0.3
    else:
        semantic_weight = 0.0
        keyword_weight = 1.0

    if semantic_results:
        max_dist = max(r.get("distance", 1.0) for r in semantic_results) or 1.0
        for r in semantic_results:
            dist = r.get("distance", 1.0)
            sem_score = max(0, 1 - dist / max_dist) if max_dist > 0 else 0
            scored[r["id"]] = {**r, "semantic_score": sem_score, "keyword_score": 0}

    if keyword_results:
        max_rank = max(r.get("rank", 0) for r in keyword_results) or 1.0
        for r in keyword_results:
            rank = r.get("rank", 0)
            kw_score = rank / max_rank if max_rank > 0 else 0
            if r["id"] in scored:
                scored[r["id"]]["keyword_score"] = kw_score
            else:
                scored[r["id"]] = {**r, "semantic_score": 0, "keyword_score": kw_score}

    for item in scored.values():
        item["combined_score"] = (
            semantic_weight * item["semantic_score"]
            + keyword_weight * item["keyword_score"]
        )

    ranked = sorted(scored.values(), key=lambda x: x["combined_score"], reverse=True)

    results = []
    total_tokens = 0
    for r in ranked[:limit]:
        token_count = r.get("token_count", 0) or len(r.get("content", "").split())
        if total_tokens + token_count > max_tokens:
            break

        meta = r.get("metadata", {})
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}

        results.append({
            "content": r["content"],
            "source": meta.get("file_name", "Project Document"),
            "section_title": r.get("section_title", ""),
            "relevance": round(min(1.0, r.get("combined_score", 0)), 2),
            "doc_id": r.get("doc_id"),
        })
        total_tokens += token_count

    return results


def format_project_context_for_prompt(chunks):
    if not chunks:
        return ""

    parts = [
        "\n### Relevant Extracts from Project Documents:\n"
        "The following are the most relevant passages from uploaded project documents "
        "for this specific section. Use specific data, numbers, and facts from these extracts.\n"
    ]

    for i, chunk in enumerate(chunks, 1):
        source = chunk["source"]
        section = chunk.get("section_title", "")
        source_label = f"{source} > {section}" if section else source
        relevance = chunk.get("relevance", 0)
        parts.append(
            f"\n**Project Document Extract {i}** (Source: {source_label}, "
            f"Relevance: {relevance:.0%}):\n"
            f"```\n{chunk['content']}\n```\n"
        )

    return "\n".join(parts)


def build_section_search_query(section_title, must_include_items=None, project_info=None):
    parts = [section_title]

    if must_include_items:
        key_items = must_include_items[:5]
        parts.append(" ".join(key_items))

    if project_info:
        methodology = project_info.get("methodology", "")
        if methodology:
            parts.append(methodology)
        country = project_info.get("country", "")
        if country:
            parts.append(country)

    return " ".join(parts)
