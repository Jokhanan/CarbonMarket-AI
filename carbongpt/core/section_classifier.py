import json
import logging
import os
import re

from carbongpt.repository.db import get_cursor
from carbongpt.core.knowledge_retrieval import map_section_to_purpose

logger = logging.getLogger(__name__)

MODEL = os.getenv("CARBONGPT_AI_MODEL", "claude-sonnet-5")

DOMAIN_KEYWORDS = {
    "baseline": [
        "baseline", "base line", "baseline scenario", "baseline emission",
        "business as usual", "project scenario", "baseline identification",
    ],
    "additionality": [
        "additionality", "barrier", "investment analysis", "first of its kind",
        "common practice", "regulatory surplus",
    ],
    "monitoring": [
        "monitoring", "monitoring plan", "monitoring approach", "data quality",
        "qa/qc", "quality assurance", "quality control", "data management",
        "monitoring parameter", "monitoring methodology",
    ],
    "sampling": [
        "sampling", "sample size", "sample design", "confidence", "precision",
        "statistical", "sample frame", "stratification",
    ],
}

PROJECT_TYPES = ["cookstove", "solar", "wind", "hydro", "landfill_biogas_waste", "other"]

PILOT_DOC_IDS = [
    258, 259, 270, 231, 224, 225,
    123,
    468, 319, 330, 328, 382,
    565, 569, 414,
    505, 579, 487, 484, 472,
    311, 313, 314, 342, 233, 216,
    380, 266, 368, 320,
]


def _call_llm(system_prompt, user_prompt, temperature=0):
    from carbongpt.core.openai_client import call_openai
    try:
        return call_openai(system_prompt, user_prompt, temperature=temperature, model_override=MODEL)
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return None


def _parse_json_response(raw):
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            if "sections" in parsed:
                return parsed["sections"]
            return [parsed]
    except (json.JSONDecodeError, ValueError):
        return []
    return []


def _match_domain(title):
    title_lower = (title or "").lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                return domain
    return None


def _get_candidate_sections(doc_ids):
    with get_cursor() as cur:
        placeholders = ",".join(["%s"] * len(doc_ids))
        cur.execute(f"""
            SELECT ds.id as section_id, ds.document_id, ds.section_number, ds.title,
                   ds.word_count, LEFT(ds.content, 800) as content_preview,
                   d.category as doc_type, d.auto_detected_standard as standard,
                   d.title as doc_title
            FROM document_sections ds
            JOIN documents d ON d.id = ds.document_id
            WHERE ds.document_id IN ({placeholders})
              AND ds.word_count > 100
              AND d.category = 'example_pdd'
            ORDER BY ds.document_id, ds.section_number
        """, doc_ids)
        return cur.fetchall()


def _build_classification_prompt(sections_batch):
    system_prompt = (
        "You are a carbon market document analyst. You classify sections from "
        "Project Design Documents (PDDs) for a carbon credit registry.\n\n"
        "For each section provided, determine:\n"
        "1. section_domain: Which domain does this section belong to? "
        "Must be one of: baseline, additionality, monitoring, sampling. "
        "Only assign a domain if the section genuinely covers that topic.\n"
        "2. project_type: What type of carbon project is this? "
        "Must be one of: cookstove, solar, wind, hydro, landfill_biogas_waste, other\n"
        "3. methodology_code: If a specific methodology is referenced (e.g., VM0050, ACM0002, "
        "AMS-I.D., AM0031), extract the code. Otherwise null.\n"
        "4. is_usable: Is this section a substantive, well-written exemplar that could "
        "serve as a model for drafting similar sections? Mark false if the section is:\n"
        "   - Mostly boilerplate or template placeholder text\n"
        "   - Primarily references, bibliography, or cross-references\n"
        "   - An appendix/annex with raw data tables rather than narrative\n"
        "   - A stub or placeholder with no substantive argument\n"
        "   - Mostly duplicated standard text without project-specific content\n\n"
        "Return a JSON array. Each element must have:\n"
        '{"section_id": <int>, "section_domain": "<string>", '
        '"project_type": "<string>", "methodology_code": "<string or null>", '
        '"is_usable": <boolean>}\n\n'
        "Return ONLY the JSON array, no other text."
    )

    section_texts = []
    for s in sections_batch:
        section_texts.append(
            f"[Section ID: {s['section_id']}] "
            f"Title: {s['title'] or 'Untitled'} | "
            f"Section Number: {s['section_number'] or 'N/A'} | "
            f"Word Count: {s['word_count']} | "
            f"Doc: {s['doc_title'][:80]}\n"
            f"Content Preview: {s['content_preview'][:500]}\n"
        )

    user_prompt = (
        f"Classify the following {len(sections_batch)} PDD sections.\n\n"
        + "\n---\n".join(section_texts)
    )

    return system_prompt, user_prompt


def classify_pilot_sections(doc_ids=None):
    if doc_ids is None:
        doc_ids = PILOT_DOC_IDS

    all_sections = _get_candidate_sections(doc_ids)
    logger.info("Found %d candidate sections across %d docs", len(all_sections), len(doc_ids))

    target_sections = []
    for s in all_sections:
        domain = _match_domain(s["title"])
        if domain:
            s["pre_domain"] = domain
            target_sections.append(s)

    logger.info("Filtered to %d target-domain sections", len(target_sections))

    with get_cursor() as cur:
        cur.execute("DELETE FROM section_exemplars WHERE document_id = ANY(%s)", (doc_ids,))
        deleted = cur.rowcount
        if deleted:
            logger.info("Cleared %d existing exemplars for pilot docs", deleted)

    batch_size = 15
    classified_count = 0
    failed_count = 0

    for i in range(0, len(target_sections), batch_size):
        batch = target_sections[i : i + batch_size]
        system_prompt, user_prompt = _build_classification_prompt(batch)

        raw = _call_llm(system_prompt, user_prompt)
        results = _parse_json_response(raw)

        if not results:
            logger.warning("Empty LLM response for batch %d-%d", i, i + len(batch))
            failed_count += len(batch)
            continue

        result_map = {r["section_id"]: r for r in results if "section_id" in r}

        rows_to_insert = []
        for s in batch:
            sid = s["section_id"]
            r = result_map.get(sid)
            if not r:
                failed_count += 1
                continue

            domain = r.get("section_domain", s["pre_domain"])
            if domain not in ("baseline", "additionality", "monitoring", "sampling"):
                domain = s["pre_domain"]

            ptype = r.get("project_type", "other")
            if ptype not in PROJECT_TYPES:
                ptype = "other"

            meth = r.get("methodology_code")
            if meth and len(meth) > 30:
                meth = meth[:30]

            is_usable = r.get("is_usable", True)
            if not isinstance(is_usable, bool):
                is_usable = bool(is_usable)

            purpose = map_section_to_purpose(
                s.get("section_number", ""), s["title"]
            )

            rows_to_insert.append((
                s["section_id"],
                s["document_id"],
                s["doc_type"],
                s["standard"],
                meth,
                ptype,
                domain,
                s["title"],
                purpose,
                is_usable,
                s["word_count"],
            ))

        if rows_to_insert:
            with get_cursor() as cur:
                for row in rows_to_insert:
                    cur.execute("""
                        INSERT INTO section_exemplars
                            (document_section_id, document_id, doc_type, standard,
                             methodology_code, project_type, section_domain,
                             section_title, section_purpose, is_usable, word_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, row)
            classified_count += len(rows_to_insert)

        logger.info(
            "Batch %d-%d: %d classified, %d failed",
            i, i + len(batch), len(rows_to_insert), len(batch) - len(rows_to_insert),
        )

    logger.info(
        "Classification complete: %d classified, %d failed out of %d target sections",
        classified_count, failed_count, len(target_sections),
    )

    _print_summary()
    return classified_count


def _print_summary():
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM section_exemplars")
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT section_domain, COUNT(*) as cnt,
                   SUM(CASE WHEN is_usable THEN 1 ELSE 0 END) as usable
            FROM section_exemplars
            GROUP BY section_domain ORDER BY cnt DESC
        """)
        domains = cur.fetchall()

        cur.execute("""
            SELECT project_type, COUNT(*) as cnt
            FROM section_exemplars WHERE is_usable = true
            GROUP BY project_type ORDER BY cnt DESC
        """)
        ptypes = cur.fetchall()

        cur.execute("""
            SELECT standard, COUNT(*) as cnt
            FROM section_exemplars WHERE is_usable = true
            GROUP BY standard ORDER BY cnt DESC
        """)
        standards = cur.fetchall()

    print(f"\n=== Section Exemplar Summary ===")
    print(f"Total classified: {total}")
    print(f"\nBy domain:")
    for d in domains:
        print(f"  {d['section_domain']:15s}: {d['cnt']:3d} total, {d['usable']:3d} usable")
    print(f"\nUsable by project_type:")
    for p in ptypes:
        print(f"  {p['project_type']:25s}: {p['cnt']:3d}")
    print(f"\nUsable by standard:")
    for s in standards:
        print(f"  {s['standard'] or 'Unknown':25s}: {s['cnt']:3d}")
