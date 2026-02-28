import logging
import os
import re
from pathlib import Path

import tiktoken

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

try:
    _enc = tiktoken.encoding_for_model("text-embedding-3-small")
except Exception:
    _enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def extract_text_from_docx(file_path: str) -> dict:
    from docx import Document
    doc = Document(file_path)
    sections = []
    full_text_parts = []
    current_section = {"number": None, "title": "Preamble", "content": ""}
    section_pattern = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)")

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        full_text_parts.append(text)

        is_heading = para.style and para.style.name and "Heading" in para.style.name
        match = section_pattern.match(text)

        if is_heading or (match and len(text) < 200):
            if current_section["content"].strip():
                sections.append(current_section)
            if match:
                current_section = {
                    "number": match.group(1),
                    "title": match.group(2).strip(),
                    "content": "",
                }
            else:
                current_section = {
                    "number": None,
                    "title": text,
                    "content": "",
                }
        else:
            current_section["content"] += text + "\n"

    if current_section["content"].strip():
        sections.append(current_section)

    full_text = "\n".join(full_text_parts)
    return {
        "sections": sections,
        "full_text": full_text,
        "page_count": len(doc.sections),
        "word_count": len(full_text.split()),
    }


def extract_text_from_pdf(file_path: str) -> dict:
    import pdfplumber
    sections = []
    full_text_parts = []
    current_section = {"number": None, "title": "Document", "content": ""}
    section_pattern = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)")
    page_count = 0

    with pdfplumber.open(file_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                full_text_parts.append(line)
                match = section_pattern.match(line)
                if match and len(line) < 200:
                    if current_section["content"].strip():
                        sections.append(current_section)
                    current_section = {
                        "number": match.group(1),
                        "title": match.group(2).strip(),
                        "content": "",
                    }
                else:
                    current_section["content"] += line + "\n"

    if current_section["content"].strip():
        sections.append(current_section)

    full_text = "\n".join(full_text_parts)
    return {
        "sections": sections,
        "full_text": full_text,
        "page_count": page_count,
        "word_count": len(full_text.split()),
    }


def extract_text(file_path: str) -> dict:
    ext = Path(file_path).suffix.lower()
    if ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".pdf":
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    tokens = _enc.encode(text)
    chunks = []
    start = 0
    idx = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _enc.decode(chunk_tokens)
        chunks.append({
            "chunk_index": idx,
            "content": chunk_text,
            "token_count": len(chunk_tokens),
        })
        idx += 1
        start += chunk_size - overlap
    return chunks


def create_embeddings(texts: list[str], api_key: str) -> list[list[float]]:
    import requests
    batch_size = 100
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "text-embedding-3-small",
                "input": batch,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        batch_embeddings = [item["embedding"] for item in data["data"]]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def detect_document_metadata(text_preview: str, api_key: str) -> dict:
    import requests
    import json

    prompt = (
        "Analyze the following document text and detect:\n"
        "1. Which carbon credit standard it belongs to (e.g., 'Gold Standard', 'Verra VCS', 'CDM', 'Plan Vivo', etc.)\n"
        "2. The version of the standard or document (e.g., 'v4.4', 'v1.2')\n"
        "3. The document category: one of 'standard_text', 'methodology', 'guidance', 'tool', "
        "'template', 'example_pdd', 'example_mr', 'example_fvr', 'example_valver', 'example_other', 'rule_update', 'other'\n"
        "4. Applicability conditions (what project types, sectors, or methodologies this applies to)\n\n"
        "Return JSON with keys: standard, version, category, applicability\n"
        "If you cannot determine a field, use null.\n\n"
        f"Document text (first ~2000 words):\n{text_preview[:8000]}"
    )

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a carbon credit standards expert. Analyze documents and classify them accurately. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        },
        timeout=30,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def _assign_chunks_to_sections(chunks, sections, section_ids, full_text=""):
    if not sections or not section_ids:
        return chunks

    section_boundaries = []
    full_tokens = _enc.encode(full_text) if full_text else []
    full_text_lower = full_text.lower() if full_text else ""

    search_start = 0
    for i, sec in enumerate(sections):
        sec_content = sec.get("content", "")
        sec_title = sec.get("title", "")
        marker = sec_content[:80].strip() if sec_content else sec_title
        marker_lower = marker.lower()

        char_pos = full_text_lower.find(marker_lower, search_start)
        if char_pos < 0:
            char_pos = search_start

        prefix = full_text[:char_pos]
        prefix_tokens = len(_enc.encode(prefix))

        heading_text = sec_title + "\n" if sec_title else ""
        sec_combined = heading_text + sec_content
        sec_tokens = count_tokens(sec_combined)

        section_boundaries.append({
            "section_id": section_ids[i],
            "section_number": sec.get("number"),
            "section_title": sec_title,
            "start_token": prefix_tokens,
            "end_token": prefix_tokens + sec_tokens,
        })
        search_start = char_pos + len(marker)

    for chunk in chunks:
        chunk_start = chunk["chunk_index"] * (CHUNK_SIZE - CHUNK_OVERLAP)
        chunk_end = chunk_start + chunk.get("token_count", CHUNK_SIZE)
        best_section = None
        best_overlap = 0
        for sb in section_boundaries:
            overlap_start = max(chunk_start, sb["start_token"])
            overlap_end = min(chunk_end, sb["end_token"])
            overlap = max(0, overlap_end - overlap_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_section = sb
        if best_section:
            chunk["section_id"] = best_section["section_id"]
            chunk["metadata"] = {
                **(chunk.get("metadata") or {}),
                "section_number": best_section["section_number"],
                "section_title": best_section["section_title"],
            }
    return chunks


def _build_chunk_metadata(chunk, doc_info):
    meta = chunk.get("metadata") or {}
    if doc_info:
        meta["document_title"] = doc_info.get("title", "")
        meta["document_category"] = doc_info.get("category", "")
        meta["standard_name"] = doc_info.get("standard_name") or doc_info.get("auto_detected_standard", "")
        meta["reference_id"] = doc_info.get("reference_id", "")
    chunk["metadata"] = meta
    return chunk


def generate_document_summary(text_preview: str, api_key: str) -> str:
    import requests
    import json

    prompt = (
        "Write a concise 2-3 sentence summary of this carbon credit document. "
        "Include: what type of document it is, which standard/methodology it relates to, "
        "the project type or sector, and key topics covered.\n\n"
        f"Document text (first ~3000 words):\n{text_preview[:12000]}"
    )

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a carbon credit standards expert. Summarize documents concisely."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": 200,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def ingest_document(doc_id: int, file_path: str, api_key: str = None):
    from carbongpt.repository import store

    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    store.update_document_ingestion(doc_id, "processing")

    try:
        extracted = extract_text(file_path)
        sections = extracted["sections"]
        full_text = extracted["full_text"]
        page_count = extracted["page_count"]
        word_count = extracted["word_count"]

        section_ids = store.save_sections(doc_id, sections)

        if api_key:
            try:
                detection = detect_document_metadata(full_text[:8000], api_key)
                store.update_document_detection(
                    doc_id,
                    auto_standard=detection.get("standard"),
                    auto_version=detection.get("version"),
                    auto_category=detection.get("category"),
                    auto_applicability=detection.get("applicability"),
                )
                _auto_apply_detection(doc_id, detection)
            except Exception as e:
                logger.warning("Auto-detection failed for doc %s: %s", doc_id, e)

            try:
                summary = generate_document_summary(full_text[:12000], api_key)
                store.update_document_summary(doc_id, summary)
            except Exception as e:
                logger.warning("Summary generation failed for doc %s: %s", doc_id, e)

        chunks = chunk_text(full_text)

        chunks = _assign_chunks_to_sections(chunks, sections, section_ids, full_text)

        doc_info = store.get_document(doc_id)
        for chunk in chunks:
            _build_chunk_metadata(chunk, doc_info)

        if api_key:
            try:
                chunk_texts = [c["content"] for c in chunks]
                embeddings = create_embeddings(chunk_texts, api_key)
                for chunk, emb in zip(chunks, embeddings):
                    emb_str = "[" + ",".join(str(x) for x in emb) + "]"
                    chunk["embedding"] = emb_str
            except Exception as e:
                logger.warning("Embedding creation failed for doc %s: %s", doc_id, e)

        store.save_chunks(doc_id, chunks)

        store.update_search_vector(doc_id)

        store.update_document_ingestion(doc_id, "completed",
                                         page_count=page_count, word_count=word_count)
        logger.info("Successfully ingested document %s: %d sections, %d chunks",
                     doc_id, len(sections), len(chunks))

    except Exception as e:
        logger.error("Ingestion failed for document %s: %s", doc_id, e)
        store.update_document_ingestion(doc_id, "failed", error=str(e))
        raise


VALID_CATEGORIES = {
    "standard_text", "methodology", "guidance", "tool", "template",
    "example_pdd", "example_mr", "example_fvr", "example_valver",
    "example_other", "rule_update", "other",
}


def _auto_apply_detection(doc_id: int, detection: dict):
    from carbongpt.repository import store

    doc = store.get_document(doc_id)
    if not doc:
        return

    updates = {}

    detected_cat = detection.get("category")
    if detected_cat and detected_cat in VALID_CATEGORIES:
        user_cat = doc.get("category")
        if user_cat in ("other", None) or user_cat == "standard_text":
            updates["category"] = detected_cat
            logger.info("Auto-applied category '%s' for doc %s", detected_cat, doc_id)

    if not doc.get("standard_version_id"):
        detected_std = detection.get("standard")
        detected_ver = detection.get("version")
        if not detected_ver:
            filename = doc.get("file_path", "")
            ver_match = re.search(r'v(\d+\.\d+)', filename, re.IGNORECASE)
            if ver_match:
                detected_ver = ver_match.group(1)
                logger.info("Extracted version '%s' from filename for doc %s", detected_ver, doc_id)
        if detected_std:
            matched_sv_id = store.match_standard_version(detected_std, detected_ver)
            if matched_sv_id:
                updates["standard_version_id"] = matched_sv_id
                logger.info("Auto-linked doc %s to standard_version %s", doc_id, matched_sv_id)

    if updates:
        store.update_document_metadata(doc_id, **updates)
