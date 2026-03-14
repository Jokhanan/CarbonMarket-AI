"""
pack_classifier.py — Auto-classification layer for the Methodology Pack Manager.

Scans the existing document repository, detects methodology codes from chunk
text, classifies document types, and auto-links documents to packs.

Entry points
------------
classify_document(doc_id)          → ClassificationResult
scan_repository(target_codes=None) → ScanResult
auto_build_pack(methodology_code, registry=None, dry_run=False) → PackBuildResult
run_repository_audit()             → AuditReport
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Map documents.category → pack document role
CATEGORY_TO_ROLE: dict[str, str] = {
    "example_pdd":    "PDD",
    "example_mr":     "MR",
    "example_fvr":    "VERIFICATION_REPORT",
    "example_valver": "VALIDATION_REPORT",
    "methodology":    "METHODOLOGY_DOC",
    "tool":           "TOOL_DOC",
    "standard_text":  "GUIDANCE_DOC",
    "guidance":       "GUIDANCE_DOC",
    "template":       "TEMPLATE",
    "rule_update":    "GUIDANCE_DOC",
}

# Registry guesses based on methodology code prefixes
def _guess_registry(code: str) -> str:
    c = code.upper()
    if c.startswith("VM") or c.startswith("ACM") or c.startswith("AMS") \
            or c.startswith("AM0") or c.startswith("AR-ACM"):
        return "verra" if c.startswith("VM") else "cdm"
    if c.startswith("TPDDTEC") or c.startswith("GS-"):
        return "goldstandard"
    return "verra"

_REGISTRY_OVERRIDES = {
    "TPDDTEC": "goldstandard",
    "VM0050":  "verra",
    "VM0042":  "verra",
    "VM0007":  "verra",
    "VM0015":  "verra",
    "VM0001":  "verra",
    "VM0006":  "verra",
    "ACM0002": "cdm",
    "ACM0001": "cdm",
    "AMS-I.D": "cdm",
    "AMS-I.E": "cdm",
    "AMS-I.F": "cdm",
    "AMS-III.R": "cdm",
    "AMS-III.C": "cdm",
}

def registry_for(code: str) -> str:
    return _REGISTRY_OVERRIDES.get(code.upper(), _guess_registry(code))


# Regex patterns for methodology code detection (ordered: most specific first)
_METH_PATTERNS: list[str] = [
    r"\b(TPDDTEC)\b",
    r"\b(VM\d{4}[A-Z]?)\b",
    r"\b(ACM\d{4}[A-Z]?)\b",
    r"\b(AMS-[IVX]+\.[A-Z]{1,3}(?:\.\d+)?)\b",
    r"\b(AM\d{4}[A-Z]?)\b",
    r"\b(AR-ACM\d{4}[A-Z]?)\b",
    r"\b(GS-[A-Z]{2,8}(?:\d{4})?)\b",
]

# Tokens that look like methodology codes but are not
_NOISE: frozenset[str] = frozenset({
    "AND", "THE", "FOR", "NOT", "ARE", "CAN", "ISO", "GHG", "VCS", "GS4",
    "FPIC", "TAC", "PDT", "ALL", "NEW", "MRV", "PDD", "CDM", "VMR",
})

# Minimum confidence to auto-link a document
MIN_CONFIDENCE = 0.55

# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class ClassificationResult:
    doc_id: int
    title: str
    category: str
    doc_role: str                      # Mapped from category
    detected_codes: list[str]          # All detected methodology codes
    primary_code: Optional[str]        # Highest-confidence code
    confidence: float                  # 0.0 – 1.0
    signals: list[str]                 # Human-readable explanation


@dataclass
class ScanResult:
    total_docs_scanned: int
    docs_with_chunks:   int
    detected: dict[str, list[ClassificationResult]]   # code → results
    undetected_ids: list[int]
    category_summary: dict[str, int]


@dataclass
class PackBuildResult:
    methodology_code: str
    registry: str
    pack_id: int
    created_new: bool
    docs_linked: int
    docs_already_linked: int
    docs_skipped_low_confidence: int
    readiness: dict
    classified: list[ClassificationResult]


@dataclass
class AuditReport:
    # Repository stats
    total_documents:   int
    completed_ingestion: int
    processing:        int
    failed_ingestion:  int
    total_chunks:      int
    chunks_with_embeddings: int
    category_counts:   dict[str, int]
    # Classification stats
    docs_with_methodology_detected: int
    docs_without_methodology: int
    methodology_summary: dict[str, dict]   # code → {docs, pdd, mr, val, meth}
    # Pack targets
    target_methodologies: dict[str, dict]  # code → report
    # Existing packs
    existing_packs: list[dict]


# ---------------------------------------------------------------------------
# CORE DETECTION
# ---------------------------------------------------------------------------

def detect_methodology_codes(text: str, max_chars: int = 8000) -> dict[str, int]:
    """
    Detect methodology codes in `text` and return {code: hit_count}.
    Only scans the first `max_chars` characters (cover pages, section headings).
    """
    if not text:
        return {}
    sample = text[:max_chars]
    counts: dict[str, int] = {}
    for pat in _METH_PATTERNS:
        for m in re.findall(pat, sample):
            m = m.strip().upper()
            if m and m not in _NOISE and len(m) >= 4:
                counts[m] = counts.get(m, 0) + 1
    return counts


def _fetch_doc_text(doc_id: int, max_chunks: int = 6) -> str:
    """Return concatenated chunk text for the first N chunks of a document."""
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT content FROM document_chunks
            WHERE document_id = %s
            ORDER BY chunk_index
            LIMIT %s
            """,
            (doc_id, max_chunks),
        )
        rows = cur.fetchall()
    return " ".join((r["content"] or "") for r in rows)


def classify_document(doc_id: int) -> Optional[ClassificationResult]:
    """
    Classify a single document: map category → doc_role, detect methodology codes.
    Returns None if the document has no chunks.
    """
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, title, category FROM documents WHERE id = %s",
            (doc_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    row = dict(row)
    doc_role = CATEGORY_TO_ROLE.get(row["category"], "GUIDANCE_DOC")
    text = _fetch_doc_text(doc_id)
    if not text:
        return ClassificationResult(
            doc_id=doc_id, title=row["title"] or "", category=row["category"],
            doc_role=doc_role, detected_codes=[], primary_code=None,
            confidence=0.0, signals=["No chunk text available"],
        )

    counts = detect_methodology_codes(text)
    signals: list[str] = []
    if not counts:
        return ClassificationResult(
            doc_id=doc_id, title=row["title"] or "", category=row["category"],
            doc_role=doc_role, detected_codes=[], primary_code=None,
            confidence=0.0, signals=["No methodology code pattern detected"],
        )

    # Rank codes by hit frequency
    ranked = sorted(counts.items(), key=lambda x: -x[1])
    primary_code, primary_hits = ranked[0]
    total_hits = sum(h for _, h in ranked)

    # Confidence: based on hit count + category match
    raw_conf = min(primary_hits / max(total_hits, 1), 1.0)
    # Boost for project categories (they're clearly project docs)
    if row["category"] in ("example_pdd", "example_mr", "example_fvr", "example_valver"):
        raw_conf = min(raw_conf + 0.3, 1.0)
    # Boost if code appears ≥ 3 times
    if primary_hits >= 3:
        raw_conf = min(raw_conf + 0.2, 1.0)
    confidence = round(raw_conf, 3)

    signals.append(f"Detected {len(counts)} code(s): {list(counts.keys())}")
    signals.append(f"Primary code '{primary_code}' appeared {primary_hits} time(s)")
    signals.append(f"Category '{row['category']}' → role '{doc_role}'")

    return ClassificationResult(
        doc_id=doc_id,
        title=row["title"] or "",
        category=row["category"],
        doc_role=doc_role,
        detected_codes=list(counts.keys()),
        primary_code=primary_code,
        confidence=confidence,
        signals=signals,
    )


# ---------------------------------------------------------------------------
# REPOSITORY SCAN
# ---------------------------------------------------------------------------

def scan_repository(
    target_codes: Optional[list[str]] = None,
    categories: Optional[list[str]] = None,
) -> ScanResult:
    """
    Scan all documents with chunks.  If target_codes is given, only collect
    results for those codes.  Returns a ScanResult.
    """
    from carbongpt.repository.db import get_cursor

    # Pull all doc IDs that have chunks
    where_clauses = ["dc.chunk_index < 6"]
    params: list = []
    if categories:
        placeholders = ",".join(["%s"] * len(categories))
        where_clauses.append(f"d.category IN ({placeholders})")
        params.extend(categories)

    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT DISTINCT d.id, d.category
            FROM documents d
            JOIN document_chunks dc ON dc.document_id = d.id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY d.id
            """,
            params,
        )
        rows = [dict(r) for r in cur.fetchall()]

    total_docs = len(rows)
    cat_summary: dict[str, int] = {}
    for r in rows:
        cat_summary[r["category"]] = cat_summary.get(r["category"], 0) + 1

    detected: dict[str, list[ClassificationResult]] = {}
    undetected: list[int] = []

    for r in rows:
        result = classify_document(r["id"])
        if result is None or result.primary_code is None:
            undetected.append(r["id"])
            continue
        codes_to_record = [result.primary_code]
        if target_codes:
            codes_to_record = [c for c in codes_to_record if c in target_codes]
            if not codes_to_record:
                undetected.append(r["id"])
                continue
        for code in codes_to_record:
            detected.setdefault(code, []).append(result)

    return ScanResult(
        total_docs_scanned=total_docs,
        docs_with_chunks=total_docs,
        detected=detected,
        undetected_ids=undetected,
        category_summary=cat_summary,
    )


# ---------------------------------------------------------------------------
# AUTO PACK BUILDER
# ---------------------------------------------------------------------------

def auto_build_pack(
    methodology_code: str,
    registry: Optional[str] = None,
    dry_run: bool = False,
    min_confidence: float = MIN_CONFIDENCE,
) -> PackBuildResult:
    """
    Scan the repository for documents belonging to `methodology_code`,
    create the pack if it doesn't exist, link qualifying documents,
    compute readiness, and return a PackBuildResult.

    Steps:
      1. Scan repository documents (all categories with chunks)
      2. Detect relevant documents for this methodology
      3. Classify document type from category
      4. Link documents to pack (skip low-confidence)
      5. Compute readiness
      6. Return summary
    """
    from carbongpt.repository.db import get_cursor
    from carbongpt.repository.pack_store import (
        create_pack, add_document_link, evaluate_pack_readiness,
    )

    code_upper = methodology_code.strip().upper()
    reg = registry or registry_for(code_upper)

    # ── Step 1: find or create pack ──────────────────────────────────────────
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM methodology_packs
            WHERE methodology_code = %s AND registry = %s
            AND indexing_status != 'archived'
            LIMIT 1
            """,
            (code_upper, reg),
        )
        row = cur.fetchone()

    pack_created = False
    if row:
        pack = dict(row)
    else:
        if dry_run:
            pack = {"id": -1, "methodology_code": code_upper, "registry": reg}
            pack_created = True
        else:
            pack = create_pack(
                methodology_code=code_upper,
                registry=reg,
                notes=f"Auto-built by repository scan.",
                created_by="auto_classifier",
            )
            pack_created = True
            logger.info("Created pack id=%d for %s (%s)", pack["id"], code_upper, reg)

    pack_id = pack["id"]

    # ── Step 2: scan repository ──────────────────────────────────────────────
    scan = scan_repository(target_codes=[code_upper])
    classified = scan.detected.get(code_upper, [])

    docs_linked = 0
    docs_already = 0
    docs_skipped = 0

    if not dry_run:
        # ── Step 3 & 4: link qualifying documents ────────────────────────────
        for clf in classified:
            if clf.confidence < min_confidence:
                docs_skipped += 1
                continue
            try:
                add_document_link(
                    pack_id=pack_id,
                    document_id=clf.doc_id,
                    document_role=clf.doc_role,
                    added_by="auto_classifier",
                    quality_flags={
                        "auto_classified": True,
                        "confidence": clf.confidence,
                        "signals": clf.signals,
                    },
                )
                docs_linked += 1
            except Exception as exc:
                # Conflict = already linked
                if "duplicate" in str(exc).lower() or "unique" in str(exc).lower() \
                        or "conflict" in str(exc).lower():
                    docs_already += 1
                else:
                    logger.warning("Failed to link doc %d to pack %d: %s", clf.doc_id, pack_id, exc)
                    docs_skipped += 1

        # ── Step 5: compute readiness ─────────────────────────────────────────
        readiness = evaluate_pack_readiness(pack_id)
    else:
        docs_skipped = sum(1 for c in classified if c.confidence < min_confidence)
        docs_linked  = sum(1 for c in classified if c.confidence >= min_confidence)
        readiness = {}

    return PackBuildResult(
        methodology_code=code_upper,
        registry=reg,
        pack_id=pack_id,
        created_new=pack_created,
        docs_linked=docs_linked,
        docs_already_linked=docs_already,
        docs_skipped_low_confidence=docs_skipped,
        readiness=readiness,
        classified=classified,
    )


# ---------------------------------------------------------------------------
# REPOSITORY AUDIT
# ---------------------------------------------------------------------------

def run_repository_audit(
    target_codes: Optional[list[str]] = None,
) -> AuditReport:
    """
    Full repository audit.  Returns an AuditReport with:
      - repository stats
      - per-category document counts
      - detected methodology codes and their doc counts
      - targeted methodology report (TPDDTEC, VM0050, VM0042, ACM0002, AMS-I.D)
      - existing packs
    """
    from carbongpt.repository.db import get_cursor

    _TARGET_CODES = target_codes or [
        "TPDDTEC", "VM0050", "VM0042", "ACM0002", "AMS-I.D", "AMS-I.E",
    ]

    # ── Repository raw stats ─────────────────────────────────────────────────
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM documents")
        total_docs = cur.fetchone()["n"]

        cur.execute(
            "SELECT ingestion_status, COUNT(*) AS n FROM documents GROUP BY ingestion_status"
        )
        status_counts = {r["ingestion_status"]: r["n"] for r in cur.fetchall()}

        cur.execute(
            "SELECT category, COUNT(*) AS n FROM documents GROUP BY category ORDER BY n DESC"
        )
        category_counts = {r["category"]: r["n"] for r in cur.fetchall()}

        cur.execute("SELECT COUNT(*) AS n FROM document_chunks")
        total_chunks = cur.fetchone()["n"]

        cur.execute(
            "SELECT COUNT(*) AS n FROM document_chunks WHERE embedding IS NOT NULL"
        )
        chunks_with_emb = cur.fetchone()["n"]

        cur.execute(
            "SELECT COUNT(DISTINCT document_id) AS n FROM document_chunks"
        )
        docs_with_chunks = cur.fetchone()["n"]

    # ── Full scan ────────────────────────────────────────────────────────────
    logger.info("Running full repository scan for audit...")
    scan = scan_repository()

    # Build methodology summary
    meth_summary: dict[str, dict] = {}
    for code, results in scan.detected.items():
        entry = {"docs": len(results), "pdd": 0, "mr": 0, "val": 0, "meth": 0, "other": 0, "doc_ids": []}
        for r in results:
            entry["doc_ids"].append(r.doc_id)
            role = r.doc_role
            if role == "PDD":               entry["pdd"] += 1
            elif role == "MR":              entry["mr"] += 1
            elif role in ("VALIDATION_REPORT", "VERIFICATION_REPORT"): entry["val"] += 1
            elif role == "METHODOLOGY_DOC": entry["meth"] += 1
            else:                           entry["other"] += 1
        meth_summary[code] = entry

    # ── Targeted methodology report ───────────────────────────────────────────
    target_report: dict[str, dict] = {}
    for code in _TARGET_CODES:
        entry = meth_summary.get(code, {
            "docs": 0, "pdd": 0, "mr": 0, "val": 0, "meth": 0, "other": 0, "doc_ids": [],
        })
        entry["registry"] = registry_for(code)
        entry["pack_viable"] = (
            entry["pdd"] >= 2 or entry["meth"] >= 1 or entry["val"] >= 2
        )
        entry["recommendation"] = (
            "Ready to auto-build" if entry["pack_viable"] else
            "Needs more documents"
        )
        target_report[code] = entry

    # ── Existing packs ────────────────────────────────────────────────────────
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, methodology_code, registry, indexing_status, "
            "       pdd_count, mr_count, validation_count, readiness_score "
            "FROM methodology_packs ORDER BY methodology_code"
        )
        existing_packs = [dict(r) for r in cur.fetchall()]

    return AuditReport(
        total_documents=total_docs,
        completed_ingestion=status_counts.get("completed", 0),
        processing=status_counts.get("processing", 0),
        failed_ingestion=status_counts.get("failed", 0),
        total_chunks=total_chunks,
        chunks_with_embeddings=chunks_with_emb,
        category_counts=category_counts,
        docs_with_methodology_detected=sum(len(v) for v in scan.detected.values()),
        docs_without_methodology=len(scan.undetected_ids),
        methodology_summary=meth_summary,
        target_methodologies=target_report,
        existing_packs=existing_packs,
    )
