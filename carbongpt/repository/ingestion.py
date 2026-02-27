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

        store.save_sections(doc_id, sections)

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
            except Exception as e:
                logger.warning("Auto-detection failed for doc %s: %s", doc_id, e)

        chunks = chunk_text(full_text)

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

        store.update_document_ingestion(doc_id, "completed",
                                         page_count=page_count, word_count=word_count)
        logger.info("Successfully ingested document %s: %d sections, %d chunks",
                     doc_id, len(sections), len(chunks))

    except Exception as e:
        logger.error("Ingestion failed for document %s: %s", doc_id, e)
        store.update_document_ingestion(doc_id, "failed", error=str(e))
        raise
