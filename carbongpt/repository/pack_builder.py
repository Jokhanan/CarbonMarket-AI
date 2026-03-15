"""
pack_builder.py — AI-assisted Methodology Pack Builder.

Orchestrates the full auto-build workflow:
  1. Analyze methodology requirements (static KB + repo content)
  2. Repository-first discovery (reuse existing chunks)
  3. Carbon Intelligence candidate ranking
  4. Remote document discovery (Verra API; GS graceful-fail)
  5. Document classification + auto-linking (high/medium/low)
  6. Findings discovery from val/ver report chunks
  7. Readiness evaluation
  8. Missing-items report generation

Entry point
-----------
build_pack_full(methodology_code, registry, dry_run=False) → AutoBuildReport
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# METHODOLOGY STATIC KNOWLEDGE BASE
# ---------------------------------------------------------------------------

@dataclass
class RequiredDoc:
    doc_type: str           # PDD / MR / METHODOLOGY_DOC / TOOL_DOC / GUIDANCE_DOC / VALIDATION_REPORT
    label: str              # Human-readable label
    confidence: str         # confirmed | probable | unknown
    source_hint: str = ""   # Where to find it
    critical: bool = True   # Is this a hard requirement?


@dataclass
class MethodologyProfile:
    code: str
    registry: str
    full_name: str
    sector: str
    family: str
    required_docs: list[RequiredDoc]
    known_tool_references: list[str]    # Tool codes referenced in methodology text
    target_pdd_count: int
    target_mr_count: int
    target_validation_count: int
    notes: str = ""
    source: str = "static_kb"           # static_kb | repo_analysis | ref_methodologies


# Static knowledge base for the most important methodologies
_STATIC_KB: dict[str, dict] = {
    "TPDDTEC": {
        "full_name": "Technologies and Practices to Displace Decentralized Thermal Energy Consumption",
        "registry": "goldstandard",
        "sector": "Clean Cooking / Energy Efficiency",
        "family": "Clean Cooking",
        "target_pdd_count": 20,
        "target_mr_count": 5,
        "target_validation_count": 5,
        "known_tools": [
            "GS Activity Requirements",
            "Kitchen Performance Test (KPT)",
            "Controlled Cooking Test (CCT)",
            "Total Fuel Consumption (TFC)",
            "Emission Reduction Calculation",
        ],
        "required_docs": [
            RequiredDoc("METHODOLOGY_DOC", "TPDDTEC Methodology Document (full text)", "confirmed",
                        "GS website / sustaincert.com"),
            RequiredDoc("TOOL_DOC", "GS Activity Requirements for ICS", "confirmed",
                        "Gold Standard website"),
            RequiredDoc("TOOL_DOC", "Default values / emission factors tool", "probable",
                        "Gold Standard website"),
            RequiredDoc("PDD", "Registered project PDDs (≥15 recommended)", "confirmed",
                        "Gold Standard SustainCERT platform"),
            RequiredDoc("MR", "Monitoring Reports (≥3 recommended)", "confirmed",
                        "Gold Standard SustainCERT platform"),
            RequiredDoc("VALIDATION_REPORT", "DOE Validation Reports (≥3 recommended)", "probable",
                        "Gold Standard SustainCERT platform"),
            RequiredDoc("VERIFICATION_REPORT", "DOE Verification Reports (≥3 recommended)", "probable",
                        "Gold Standard SustainCERT platform"),
        ],
        "notes": "Primarily used for improved cookstove and thermal energy efficiency projects under Gold Standard.",
    },
    "VM0050": {
        "full_name": "VM0050 Methodology for Energy Efficiency and Fuel Switch Measures in Thermal Applications",
        "registry": "verra",
        "sector": "Energy Efficiency / Fuel Switch",
        "family": "Clean Cooking / Industrial EE",
        "target_pdd_count": 15,
        "target_mr_count": 5,
        "target_validation_count": 5,
        "known_tools": [
            "Verra Tool 33",
            "VM0001 Certification of Cookstoves",
            "IPCC emission factors",
        ],
        "required_docs": [
            RequiredDoc("METHODOLOGY_DOC", "VM0050 Methodology Document v1.0", "confirmed",
                        "verra.org/methodologies/vm0050"),
            RequiredDoc("TOOL_DOC", "Verra Tool 33 (Standardized Baselines)", "probable",
                        "verra.org/tools"),
            RequiredDoc("PDD", "Registered VCS PDDs using VM0050 (≥10 recommended)", "confirmed",
                        "Verra Registry (registry.verra.org)"),
            RequiredDoc("MR", "Monitoring Reports for VM0050 projects (≥3)", "confirmed",
                        "Verra Registry"),
            RequiredDoc("VALIDATION_REPORT", "Third-party VVB validation reports (≥3)", "probable",
                        "Verra Registry"),
        ],
        "notes": "VM0050 covers improved cookstoves and fuel switching for thermal applications.",
    },
    "VM0042": {
        "full_name": "VM0042 Methodology for Improved Agricultural Land Management",
        "registry": "verra",
        "sector": "Agriculture / Land Management",
        "family": "Agriculture Forestry Land Use",
        "target_pdd_count": 20,
        "target_mr_count": 5,
        "target_validation_count": 5,
        "known_tools": [
            "Verra Tool 03 (Additionality)",
            "IPCC Tier 1/2 emission factors",
            "Verra Tool 16 (Uncertainty)",
        ],
        "required_docs": [
            RequiredDoc("METHODOLOGY_DOC", "VM0042 Methodology Document (current version)", "confirmed",
                        "verra.org/methodologies/vm0042"),
            RequiredDoc("TOOL_DOC", "Verra Tool 03 (Additionality of Activity)", "confirmed",
                        "verra.org/tools"),
            RequiredDoc("PDD", "VCS PDDs using VM0042 (≥15 recommended)", "confirmed",
                        "Verra Registry"),
            RequiredDoc("MR", "Monitoring Reports for VM0042 projects (≥5)", "confirmed",
                        "Verra Registry"),
            RequiredDoc("VALIDATION_REPORT", "VVB validation reports (≥5)", "probable",
                        "Verra Registry"),
        ],
        "notes": "VM0042 is a major revision of the AFOLU agriculture methodology with 172 registered projects.",
    },
    "ACM0002": {
        "full_name": "ACM0002 Consolidated Baseline Methodology for Grid-Connected Electricity Generation from Renewable Sources",
        "registry": "cdm",
        "sector": "Energy Industries / Renewable Electricity",
        "family": "Renewable Electricity",
        "target_pdd_count": 30,
        "target_mr_count": 10,
        "target_validation_count": 10,
        "known_tools": [
            "CDM Tool 01 (Methodological tool: Tool to calculate the emission factor for an electricity system)",
            "CDM Tool 05 (Baseline, project and/or leakage emissions from electricity consumption)",
            "CDM Tool 07 (Tool to calculate the emission factor for an electricity system)",
        ],
        "required_docs": [
            RequiredDoc("METHODOLOGY_DOC", "ACM0002 Methodology Document (latest version)", "confirmed",
                        "unfccc.int/methodologies/DB/KHGZ9BDYML"),
            RequiredDoc("TOOL_DOC", "CDM Tool 01 (Electricity emission factor)", "confirmed",
                        "unfccc.int/methodologies/tools"),
            RequiredDoc("TOOL_DOC", "CDM Tool 07 (Emission factor — electricity system)", "confirmed",
                        "unfccc.int/methodologies/tools"),
            RequiredDoc("PDD", "CDM PDDs using ACM0002 (≥20 recommended)", "confirmed",
                        "cdm.unfccc.int"),
            RequiredDoc("MR", "Monitoring Reports for ACM0002 projects (≥8)", "confirmed",
                        "cdm.unfccc.int"),
            RequiredDoc("VALIDATION_REPORT", "DOE validation reports (≥8)", "confirmed",
                        "cdm.unfccc.int"),
        ],
        "notes": "ACM0002 has 25 projects in Carbon Intelligence. Repository already has 111 docs incl. 16 PDDs + 13 MRs.",
    },
    "AMS-I.D": {
        "full_name": "AMS-I.D Small-Scale CDM Methodology for Grid Connected Renewable Electricity Generation",
        "registry": "cdm",
        "sector": "Energy Industries / Renewable Electricity (Small-Scale)",
        "family": "CDM Small-Scale",
        "target_pdd_count": 15,
        "target_mr_count": 5,
        "target_validation_count": 5,
        "known_tools": [
            "CDM Tool 07 (Electricity emission factor)",
            "CDM Standardized Baselines",
        ],
        "required_docs": [
            RequiredDoc("METHODOLOGY_DOC", "AMS-I.D Methodology Document", "confirmed",
                        "unfccc.int/methodologies"),
            RequiredDoc("PDD", "Small-scale CDM PDDs using AMS-I.D (≥10 recommended)", "confirmed",
                        "cdm.unfccc.int"),
            RequiredDoc("MR", "Monitoring Reports for AMS-I.D projects (≥3)", "confirmed",
                        "cdm.unfccc.int"),
            RequiredDoc("VALIDATION_REPORT", "DOE validation reports (≥3)", "probable",
                        "cdm.unfccc.int"),
        ],
        "notes": "AMS-I.D is the small-scale version of ACM0002 for grid-connected renewable electricity.",
    },
    "AMS-I.E": {
        "full_name": "AMS-I.E Switch from Non-Renewable Biomass for Thermal Applications by the User",
        "registry": "cdm",
        "sector": "Energy Efficiency / Biomass Switch",
        "family": "CDM Small-Scale",
        "target_pdd_count": 15,
        "target_mr_count": 5,
        "target_validation_count": 5,
        "known_tools": [
            "CDM Tool 30 (Calculation of the fraction of non-renewable biomass)",
            "CDM fNRB standardized baselines",
        ],
        "required_docs": [
            RequiredDoc("METHODOLOGY_DOC", "AMS-I.E Methodology Document", "confirmed",
                        "unfccc.int/methodologies"),
            RequiredDoc("TOOL_DOC", "CDM Tool 30 (fNRB fraction)", "confirmed",
                        "unfccc.int/methodologies/tools"),
            RequiredDoc("PDD", "Small-scale CDM PDDs using AMS-I.E (≥10 recommended)", "confirmed",
                        "cdm.unfccc.int"),
            RequiredDoc("MR", "Monitoring Reports for AMS-I.E projects (≥3)", "confirmed",
                        "cdm.unfccc.int"),
            RequiredDoc("VALIDATION_REPORT", "DOE validation reports (≥3)", "probable",
                        "cdm.unfccc.int"),
        ],
        "notes": "AMS-I.E focuses on biomass switching for thermal applications, closely related to cookstoves.",
    },
}

_GENERIC_PROFILE = {
    "full_name": "{code} — Methodology",
    "registry": "unknown",
    "sector": "Unknown",
    "family": "Unknown",
    "target_pdd_count": 15,
    "target_mr_count": 5,
    "target_validation_count": 5,
    "known_tools": [],
    "required_docs": [
        RequiredDoc("METHODOLOGY_DOC", "{code} Methodology Document", "unknown", "Registry website"),
        RequiredDoc("PDD", "Project PDDs (≥10 recommended)", "confirmed", "Registry"),
        RequiredDoc("MR", "Monitoring Reports (≥3 recommended)", "confirmed", "Registry"),
        RequiredDoc("VALIDATION_REPORT", "Validation/Verification Reports (≥3)", "probable", "Registry"),
    ],
    "notes": "",
}


# ---------------------------------------------------------------------------
# AUTO-BUILD REPORT STRUCTURE
# ---------------------------------------------------------------------------

@dataclass
class CICandidate:
    project_id: int
    registry_id: str
    name: str
    registry: str
    country: str
    status: str
    estimated_annual_credits: Optional[float]
    registration_date: Optional[str]
    docs_in_repository: int     # How many docs already in repo
    usefulness_score: float     # 0–1 ranking score


@dataclass
class DiscoveryAttempt:
    project_id: int
    registry_id: str
    name: str
    registry: str
    attempted: bool
    success: bool
    doc_id: Optional[int] = None        # Created document ID if success
    doc_url: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ClassifiedDoc:
    doc_id: int
    title: str
    category: str
    doc_role: str
    methodology_code: str
    confidence: float
    tier: str           # high / medium / low
    linked: bool        # Was it auto-linked?
    already_linked: bool


@dataclass
class MissingItem:
    item_type: str              # doc_type code
    label: str                  # Human-readable description
    criticality: str            # critical / recommended / optional
    source_hint: str            # Where to get it
    manual_action: str          # What the admin needs to do


@dataclass
class AutoBuildReport:
    methodology_code: str
    registry: str
    pack_id: int
    created_new_pack: bool
    dry_run: bool

    # Methodology requirements profile
    profile: MethodologyProfile

    # Repository scan results
    docs_high_confidence: list[ClassifiedDoc]       # auto-linked
    docs_medium_confidence: list[ClassifiedDoc]     # suggested for admin review
    docs_low_confidence: list[ClassifiedDoc]        # reported only

    # Carbon Intelligence candidates
    ci_candidates: list[CICandidate]

    # Remote discovery attempts
    remote_discovery: list[DiscoveryAttempt]

    # Findings extracted
    findings_extracted: int

    # Readiness
    readiness: dict

    # Missing items report
    missing_items: list[MissingItem]

    # Summary counters
    total_linked: int
    total_suggested: int
    total_missing: int


# ---------------------------------------------------------------------------
# PART 1 — METHODOLOGY REQUIREMENTS ANALYZER
# ---------------------------------------------------------------------------

def analyze_methodology_requirements(
    methodology_code: str,
    registry: Optional[str] = None,
) -> MethodologyProfile:
    """
    Build a MethodologyProfile for the given methodology.
    Sources (in priority order):
      1. Static knowledge base (confirmed data)
      2. ref_methodologies table (metadata)
      3. Dynamic analysis of methodology doc chunks in repository
    """
    code = methodology_code.strip().upper()
    kb = _STATIC_KB.get(code) or _GENERIC_PROFILE

    full_name = kb["full_name"].replace("{code}", code)
    reg = registry or kb.get("registry", "unknown")

    # Enhance with ref_methodologies if available
    source = "static_kb"
    try:
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute(
                "SELECT methodology_name, methodology_family, sector, technology, status "
                "FROM ref_methodologies WHERE methodology_code = %s LIMIT 1",
                (code,),
            )
            row = cur.fetchone()
        if row:
            if row["methodology_name"]:
                full_name = row["methodology_name"]
            source = "ref_methodologies+static_kb"
    except Exception as exc:
        logger.debug("ref_methodologies lookup failed: %s", exc)

    # Build required docs list — substitute code in generic labels
    req_docs = []
    for rd in kb["required_docs"]:
        req_docs.append(RequiredDoc(
            doc_type=rd.doc_type,
            label=rd.label.replace("{code}", code),
            confidence=rd.confidence,
            source_hint=rd.source_hint,
            critical=rd.critical,
        ))

    # Check if methodology doc is already in repository and annotate
    try:
        from carbongpt.repository.db import get_cursor
        from carbongpt.repository.pack_classifier import detect_methodology_codes
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT d.id, d.title, dc.content
                FROM documents d
                JOIN document_chunks dc ON dc.document_id = d.id
                WHERE d.category = 'methodology' AND dc.chunk_index = 0
                """,
            )
            meth_rows = cur.fetchall()
        found_meth_doc = False
        for mrow in meth_rows:
            codes = detect_methodology_codes(mrow["content"] or "")
            if code in codes:
                found_meth_doc = True
                break
        if found_meth_doc:
            for rd in req_docs:
                if rd.doc_type == "METHODOLOGY_DOC":
                    rd.label += " [FOUND IN REPOSITORY]"
                    source += "+repo_meth_doc"
    except Exception as exc:
        logger.debug("Repository methodology doc check failed: %s", exc)

    return MethodologyProfile(
        code=code,
        registry=reg,
        full_name=full_name,
        sector=kb.get("sector", "Unknown"),
        family=kb.get("family", "Unknown"),
        required_docs=req_docs,
        known_tool_references=kb.get("known_tools", []),
        target_pdd_count=kb.get("target_pdd_count", 15),
        target_mr_count=kb.get("target_mr_count", 5),
        target_validation_count=kb.get("target_validation_count", 5),
        notes=kb.get("notes", ""),
        source=source,
    )


# ---------------------------------------------------------------------------
# PART 3 — CARBON INTELLIGENCE PROJECT DISCOVERY
# ---------------------------------------------------------------------------

def discover_ci_candidates(
    methodology_code: str,
    registry: Optional[str] = None,
    limit: int = 20,
) -> list[CICandidate]:
    """
    Query Carbon Intelligence for projects matching this methodology.
    Ranks by: registration status > docs already in repo > geographic diversity > credits.
    """
    from carbongpt.repository.db import get_cursor

    code = methodology_code.strip().upper()

    with get_cursor() as cur:
        # Projects via project_methodology_codes (canonical normalized codes)
        cur.execute(
            """
            SELECT DISTINCT
                cp.id, cp.registry_id, cp.name, cp.registry, cp.country, cp.status,
                cp.estimated_annual_credits, cp.registration_date
            FROM carbon_projects cp
            JOIN project_methodology_codes pmc ON pmc.project_id = cp.id
            WHERE pmc.methodology_code = %s
            ORDER BY cp.estimated_annual_credits DESC NULLS LAST
            LIMIT %s
            """,
            (code, limit * 2),
        )
        rows_pmc = [dict(r) for r in cur.fetchall()]

        # Also search the freeform methodology field for patterns (TPDDTEC etc.)
        cur.execute(
            """
            SELECT DISTINCT cp.id, cp.registry_id, cp.name, cp.registry, cp.country, cp.status,
                cp.estimated_annual_credits, cp.registration_date
            FROM carbon_projects cp
            WHERE cp.methodology ILIKE %s
            ORDER BY cp.estimated_annual_credits DESC NULLS LAST
            LIMIT %s
            """,
            (f"%%{code}%%", limit),
        )
        rows_field = [dict(r) for r in cur.fetchall()]

    # Merge, dedup by id
    seen: set[int] = set()
    all_rows: list[dict] = []
    for r in rows_pmc + rows_field:
        if r["id"] not in seen:
            seen.add(r["id"])
            all_rows.append(r)

    # Check which projects already have docs in repository (by methodology code in chunks)
    # We approximate by checking if project's registry_id appears in any document title/reference
    with get_cursor() as cur:
        rid_list = [r["registry_id"] for r in all_rows if r["registry_id"]]
        if rid_list:
            placeholders = ",".join(["%s"] * len(rid_list))
            cur.execute(
                f"""
                SELECT reference_id, COUNT(*) AS doc_count
                FROM documents
                WHERE reference_id IN ({placeholders})
                GROUP BY reference_id
                """,
                rid_list,
            )
            docs_map = {r["reference_id"]: r["doc_count"] for r in cur.fetchall()}
        else:
            docs_map = {}

    # Score each candidate
    status_score = {
        "GOLD_STANDARD_CERTIFIED_PROJECT": 1.0,
        "Registered": 1.0,
        "registered": 1.0,
        "Under validation": 0.6,
        "LISTED": 0.4,
        "Listed": 0.4,
    }
    seen_countries: set[str] = set()
    candidates: list[CICandidate] = []

    for r in all_rows:
        reg_filter = registry or ""
        if reg_filter and r["registry"] and r["registry"].lower() != reg_filter.lower():
            continue

        docs_in_repo = docs_map.get(r["registry_id"], 0)
        stat = r["status"] or ""
        s_score = status_score.get(stat, 0.3)
        doc_score = min(docs_in_repo / 3, 0.4)
        geo_score = 0.2 if r["country"] not in seen_countries else 0.0
        seen_countries.add(r["country"] or "")
        cred = r["estimated_annual_credits"] or 0
        cred_score = min(cred / 500000, 0.2)

        score = round(s_score * 0.4 + doc_score + geo_score + cred_score, 3)

        candidates.append(CICandidate(
            project_id=r["id"],
            registry_id=r["registry_id"] or "",
            name=r["name"] or "",
            registry=r["registry"] or "",
            country=r["country"] or "",
            status=stat,
            estimated_annual_credits=r["estimated_annual_credits"],
            registration_date=str(r["registration_date"]) if r["registration_date"] else None,
            docs_in_repository=docs_in_repo,
            usefulness_score=score,
        ))

    # Sort by score
    candidates.sort(key=lambda x: -x.usefulness_score)
    return candidates[:limit]


# ---------------------------------------------------------------------------
# PART 4 — REMOTE DOCUMENT DISCOVERY
# ---------------------------------------------------------------------------

def attempt_remote_discovery(
    candidates: list[CICandidate],
    pack_id: int,
    methodology_code: str,
    max_attempts: int = 8,
    dry_run: bool = False,
) -> list[DiscoveryAttempt]:
    """
    Attempt to discover and download project documents from registries.
    - Verra: uses the registry API to find document URLs
    - Gold Standard: graceful fail (Cloudflare blocked)
    - CDM: graceful fail
    Returns a list of DiscoveryAttempt records.
    """
    results: list[DiscoveryAttempt] = []
    attempted = 0

    for cand in candidates:
        if attempted >= max_attempts:
            break
        if cand.docs_in_repository > 0:
            # Already has docs — skip remote discovery for this project
            continue

        attempt = DiscoveryAttempt(
            project_id=cand.project_id,
            registry_id=cand.registry_id,
            name=cand.name,
            registry=cand.registry,
            attempted=False,
            success=False,
        )

        if cand.registry == "verra":
            attempt.attempted = True
            attempted += 1
            result = _try_verra_document_discovery(cand, pack_id, methodology_code, dry_run)
            attempt.success   = result["success"]
            attempt.doc_id    = result.get("doc_id")
            attempt.doc_url   = result.get("doc_url")
            attempt.error     = result.get("error")

        elif cand.registry == "goldstandard":
            # GS API is Cloudflare-blocked — document download not possible automatically
            attempt.attempted = False
            attempt.success   = False
            attempt.error     = (
                "Gold Standard SustainCERT platform requires authentication. "
                "Please download manually from https://registry.goldstandard.org"
            )

        else:
            attempt.attempted = False
            attempt.success   = False
            attempt.error     = f"Registry '{cand.registry}' not supported for automatic discovery."

        results.append(attempt)

    return results


def _try_verra_document_discovery(
    cand: CICandidate,
    pack_id: int,
    methodology_code: str,
    dry_run: bool = False,
) -> dict:
    """
    Try to find and download a PDD from the Verra registry for a given project.
    Returns {success, doc_id, doc_url, error}.
    """
    import requests

    registry_num = re.sub(r"[^0-9]", "", cand.registry_id)
    if not registry_num:
        return {"success": False, "error": "Could not extract numeric registry ID"}

    try:
        # Step 1: Get project resource summary to find document list
        summary_url = (
            f"https://registry.verra.org/uiapi/resource/resourceSummary/{registry_num}"
        )
        resp = requests.get(summary_url, timeout=10,
                            headers={"Accept": "application/json"})
        if not resp.ok:
            return {"success": False, "error": f"Verra API returned {resp.status_code}"}

        data = resp.json()

        # Step 2: Look for document URLs in the response attributes
        doc_url = _extract_verra_doc_url(data, doc_type="PDD")
        if not doc_url:
            return {
                "success": False,
                "error": "No accessible PDD document link found in Verra project summary",
            }

        if dry_run:
            return {"success": True, "doc_url": doc_url, "doc_id": None}

        # Step 3: Download and ingest
        doc_id = _download_and_ingest_document(
            url=doc_url,
            title=f"{cand.name[:80]} — PDD",
            registry_id=cand.registry_id,
            methodology_code=methodology_code,
            category="example_pdd",
        )
        if doc_id:
            # Link to pack
            from carbongpt.repository.pack_store import add_document_link
            add_document_link(
                pack_id=pack_id,
                document_id=doc_id,
                document_role="PDD",
                project_registry_id=cand.registry_id,
                added_by="auto_builder",
                quality_flags={"auto_discovered": True, "source": "verra_api"},
            )
            return {"success": True, "doc_id": doc_id, "doc_url": doc_url}
        else:
            return {"success": False, "error": "Document download failed — bad response or too large"}

    except Exception as exc:
        logger.warning("Verra discovery failed for %s: %s", cand.registry_id, exc)
        return {"success": False, "error": str(exc)[:200]}


def _extract_verra_doc_url(api_data: dict, doc_type: str = "PDD") -> Optional[str]:
    """
    Parse the Verra resource summary JSON to find a downloadable document URL.
    Returns the URL or None.
    """
    # Verra doesn't directly embed doc URLs in the resourceSummary endpoint.
    # The documents live at a separate endpoint. Build the URL if project has documents.
    resource_id = api_data.get("resourceIdentifier", "")
    if not resource_id:
        return None

    # Known Verra document list endpoint
    # Returns list with issuanceDocument / resourceDocument entries
    try:
        import requests
        doc_list_url = (
            f"https://registry.verra.org/uiapi/resource/resource/{resource_id}"
            f"/documents?documentType=PDD&limit=5"
        )
        resp = requests.get(doc_list_url, timeout=8, headers={"Accept": "application/json"})
        if not resp.ok:
            return None
        docs = resp.json()
        if isinstance(docs, list) and docs:
            first = docs[0]
            # Verra document record has a 'downloadUrl' or 'resourceUrl'
            url = first.get("downloadUrl") or first.get("resourceUrl") or first.get("uri")
            if url and url.startswith("http"):
                return url
    except Exception:
        pass
    return None


def _download_and_ingest_document(
    url: str,
    title: str,
    registry_id: str,
    methodology_code: str,
    category: str,
    max_size_mb: float = 20.0,
) -> Optional[int]:
    """
    Download a PDF from `url` and ingest it using the existing ingestion pipeline.
    Returns the new document ID or None on failure.
    """
    import requests
    from carbongpt.app.config import UPLOAD_DIR
    from carbongpt.repository import store
    from carbongpt.repository.ingestion import ingest_document

    try:
        resp = requests.get(url, timeout=30, stream=True,
                            headers={"User-Agent": "CarbonGPT/1.0"})
        if not resp.ok:
            return None

        content_length = int(resp.headers.get("Content-Length", 0))
        if content_length > max_size_mb * 1024 * 1024:
            logger.warning("Document too large (%d bytes): %s", content_length, url)
            return None

        # Save to upload dir
        safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", registry_id) + "_auto.pdf"
        upload_path = Path(UPLOAD_DIR) / safe_name
        upload_path.parent.mkdir(parents=True, exist_ok=True)

        with open(upload_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)

        file_size = upload_path.stat().st_size
        if file_size < 1000:
            upload_path.unlink(missing_ok=True)
            return None

        # Create document record
        doc_id = store.create_document(
            standard_version_id=None,
            category=category,
            title=title,
            file_path=str(upload_path),
            file_type="pdf",
            reference_id=registry_id,
            file_size_bytes=file_size,
        )

        # Start ingestion asynchronously
        try:
            ingest_document(doc_id)
        except Exception as exc:
            logger.warning("Background ingestion failed for doc %d: %s", doc_id, exc)
            # Document record created; ingestion will be retried

        return doc_id

    except Exception as exc:
        logger.warning("Download failed for %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# PART 6 — FINDINGS DISCOVERY (from val/ver chunk text)
# ---------------------------------------------------------------------------

_FINDING_PATTERNS = [
    # CAR-01, CAR01, CAR 01
    (r"(?:^|\n)\s*(CAR[-\s]?\d+)\s*[:\-]\s*(.{20,500}?)(?=\n\s*(?:CAR|CL|FAR|Response|CR)|\n\n|$)",
     "CAR"),
    (r"(?:^|\n)\s*(CL[-\s]?\d+)\s*[:\-]\s*(.{20,500}?)(?=\n\s*(?:CAR|CL|FAR|Response|CR)|\n\n|$)",
     "CL"),
    (r"(?:^|\n)\s*(FAR[-\s]?\d+)\s*[:\-]\s*(.{20,500}?)(?=\n\s*(?:CAR|CL|FAR|Response|CR)|\n\n|$)",
     "FAR"),
    (r"(?:^|\n)\s*(CR[-\s]?\d+)\s*[:\-]\s*(.{20,500}?)(?=\n\s*(?:CAR|CL|FAR|CR|Response)|\n\n|$)",
     "CR"),
    # Inline table-style: "Corrective Action Request (CAR) No.1"
    (r"Corrective Action Request\s+(?:No\.?\s*)?(\d+)[:\s]+(.{20,500}?)(?=\n\n|$)",
     "CAR"),
    (r"Clarification\s+(?:No\.?\s*)?(\d+)[:\s]+(.{20,500}?)(?=\n\n|$)",
     "CL"),
    (r"Forward Action Request\s+(?:No\.?\s*)?(\d+)[:\s]+(.{20,500}?)(?=\n\n|$)",
     "FAR"),
]


def extract_pack_findings(pack_id: int, max_per_doc: int = 15) -> int:
    """
    Scan validation/verification report chunks already linked to the pack.
    Extract CAR/CL/FAR findings using regex and store them as pack_findings.
    Returns the number of new findings extracted.
    """
    from carbongpt.repository.db import get_cursor
    from carbongpt.repository.pack_store import add_finding

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT mpdl.id AS link_id, mpdl.document_id, mpdl.document_role,
                   mpdl.validation_body
            FROM methodology_pack_document_links mpdl
            WHERE mpdl.pack_id = %s
            AND mpdl.document_role IN ('VALIDATION_REPORT', 'VERIFICATION_REPORT')
            """,
            (pack_id,),
        )
        links = [dict(r) for r in cur.fetchall()]

    if not links:
        return 0

    # Get existing finding references to avoid duplication
    with get_cursor() as cur:
        cur.execute(
            "SELECT finding_reference FROM pack_findings WHERE pack_id = %s",
            (pack_id,),
        )
        existing_refs = {r["finding_reference"] for r in cur.fetchall() if r["finding_reference"]}

    total_new = 0

    for link in links:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT content FROM document_chunks
                WHERE document_id = %s
                ORDER BY chunk_index
                LIMIT 25
                """,
                (link["document_id"],),
            )
            chunks = [r["content"] or "" for r in cur.fetchall()]

        full_text = "\n\n".join(chunks)
        found_in_doc = 0

        for pattern, finding_type in _FINDING_PATTERNS:
            if found_in_doc >= max_per_doc:
                break
            for m in re.finditer(pattern, full_text, re.DOTALL | re.IGNORECASE | re.MULTILINE):
                if found_in_doc >= max_per_doc:
                    break
                ref = f"{finding_type}-{m.group(1).strip()}"
                if ref in existing_refs:
                    continue
                text = m.group(2).strip()
                if len(text) < 20:
                    continue
                try:
                    add_finding(
                        pack_id=pack_id,
                        finding_type=finding_type,
                        finding_text=text[:1000],
                        source_link_id=link["link_id"],
                        finding_reference=ref,
                        validation_body=link["validation_body"],
                        resolution_status="closed",
                        extracted_automatically=True,
                    )
                    existing_refs.add(ref)
                    found_in_doc += 1
                    total_new += 1
                except Exception as exc:
                    logger.debug("Finding insert failed: %s", exc)

    return total_new


# ---------------------------------------------------------------------------
# PART 8 — MISSING ITEMS REPORT GENERATOR
# ---------------------------------------------------------------------------

def generate_missing_report(
    profile: MethodologyProfile,
    readiness: dict,
    docs_high: list[ClassifiedDoc],
    docs_medium: list[ClassifiedDoc],
    ci_candidates: list[CICandidate],
    remote_discovery: list[DiscoveryAttempt],
    pack: dict,
) -> list[MissingItem]:
    """
    Compare the methodology requirements profile against what has been found.
    Return a prioritised list of missing items for the admin.
    """
    missing: list[MissingItem] = []

    # Count what we have
    high_roles = {d.doc_role for d in docs_high}
    all_roles  = {d.doc_role for d in docs_high + docs_medium}
    pdd_count  = sum(1 for d in docs_high + docs_medium if d.doc_role == "PDD")
    mr_count   = sum(1 for d in docs_high + docs_medium if d.doc_role == "MR")
    val_count  = sum(1 for d in docs_high + docs_medium
                     if d.doc_role in ("VALIDATION_REPORT", "VERIFICATION_REPORT"))
    meth_count = sum(1 for d in docs_high + docs_medium if d.doc_role == "METHODOLOGY_DOC")

    gates: dict = readiness.get("gates", {})
    failures: list[str] = readiness.get("gate_failures", [])

    # --- Methodology document ---
    if not gates.get("G1_methodology_doc", False):
        missing.append(MissingItem(
            item_type="METHODOLOGY_DOC",
            label=f"{profile.code} Methodology Document",
            criticality="critical",
            source_hint=next((r.source_hint for r in profile.required_docs
                               if r.doc_type == "METHODOLOGY_DOC"), "Registry website"),
            manual_action=(
                f"Download the {profile.code} methodology PDF from {profile.registry.upper()} "
                f"website and upload via Admin → Upload Documents → category: methodology"
            ),
        ))

    # --- PDD gap ---
    tgt_pdd_floor = max(5, (pack.get("target_pdd_count") or 15) // 2)
    if pdd_count < tgt_pdd_floor:
        need = tgt_pdd_floor - pdd_count
        missing.append(MissingItem(
            item_type="PDD",
            label=f"Additional PDDs (have {pdd_count}, need ≥ {tgt_pdd_floor})",
            criticality="critical",
            source_hint=f"{profile.registry.upper()} Registry",
            manual_action=(
                f"Upload {need} more PDD PDF(s) from {profile.registry.upper()} "
                f"projects using {profile.code}. "
                f"Upload via Admin → Upload Documents → category: example_pdd"
            ),
        ))
    elif pdd_count < (pack.get("target_pdd_count") or 15):
        need = (pack.get("target_pdd_count") or 15) - pdd_count
        missing.append(MissingItem(
            item_type="PDD",
            label=f"More PDDs recommended (have {pdd_count}, target {pack.get('target_pdd_count', 15)})",
            criticality="recommended",
            source_hint=f"{profile.registry.upper()} Registry",
            manual_action=f"Upload {need} more PDDs to reach the pack target.",
        ))

    # --- Monitoring Report gap ---
    tgt_mr_floor = max(1, (pack.get("target_mr_count") or 5) // 2)
    if mr_count < tgt_mr_floor:
        missing.append(MissingItem(
            item_type="MR",
            label=f"Monitoring Reports (have {mr_count}, need ≥ {tgt_mr_floor})",
            criticality="critical" if "G5_monitoring_report" in failures else "recommended",
            source_hint=f"{profile.registry.upper()} Registry",
            manual_action=(
                f"Upload at least {tgt_mr_floor} Monitoring Report PDF(s) for {profile.code} "
                f"projects. Upload via Admin → Upload Documents → category: example_mr"
            ),
        ))

    # --- Tool documents ---
    tool_found = any(d.doc_role == "TOOL_DOC" for d in docs_high + docs_medium)
    for tool_name in profile.known_tool_references[:3]:  # top 3 tools
        missing.append(MissingItem(
            item_type="TOOL_DOC",
            label=tool_name,
            criticality="recommended",
            source_hint=f"{profile.registry.upper()} website",
            manual_action=(
                f"Upload '{tool_name}' PDF. Upload via Admin → Upload Documents → "
                f"category: tool"
            ),
        ))

    # --- Failed remote downloads ---
    failed_downloads = [d for d in remote_discovery if d.attempted and not d.success]
    for dl in failed_downloads:
        missing.append(MissingItem(
            item_type="PDD",
            label=f"PDD for {dl.registry_id} — {dl.name[:50]}",
            criticality="optional",
            source_hint=f"{dl.registry} Registry",
            manual_action=(
                f"Automatic download of PDD for '{dl.registry_id}' failed "
                f"({dl.error}). Please download manually from {dl.registry} registry."
            ),
        ))

    # --- Geographic diversity suggestion ---
    if ci_candidates:
        countries_in_pack = {d.doc_role for d in docs_high + docs_medium}
        unrepresented = [c for c in ci_candidates[:10] if c.docs_in_repository == 0]
        if unrepresented:
            countries = list({c.country for c in unrepresented[:5]})
            missing.append(MissingItem(
                item_type="PDD",
                label=f"Geographic diversity — no docs yet for: {', '.join(countries[:3])}",
                criticality="recommended",
                source_hint=f"{profile.registry.upper()} Registry",
                manual_action=(
                    f"Carbon Intelligence has {len(unrepresented)} {profile.code} projects "
                    f"with no documents in the repository yet. "
                    f"Consider adding a few PDDs from different countries to improve pack quality."
                ),
            ))

    return missing


# ---------------------------------------------------------------------------
# PART 2+5 — CLASSIFIED DOC WITH CONFIDENCE TIER
# ---------------------------------------------------------------------------

def _tier(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.55:
        return "medium"
    return "low"


def _classify_and_link_docs(
    methodology_code: str,
    pack_id: int,
    dry_run: bool = False,
) -> tuple[list[ClassifiedDoc], list[ClassifiedDoc], list[ClassifiedDoc]]:
    """
    Run repository scan for this methodology.
    Return (high_confidence, medium_confidence, low_confidence) lists.
    High confidence docs are auto-linked; medium are flagged as suggestions; low just reported.
    """
    from carbongpt.repository.pack_classifier import scan_repository, CATEGORY_TO_ROLE
    from carbongpt.repository.pack_store import add_document_link

    scan = scan_repository(target_codes=[methodology_code])
    classified_raw = scan.detected.get(methodology_code, [])

    high: list[ClassifiedDoc] = []
    medium: list[ClassifiedDoc] = []
    low: list[ClassifiedDoc] = []

    # Get already-linked doc IDs to avoid duplicate work
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute(
            "SELECT document_id FROM methodology_pack_document_links WHERE pack_id = %s",
            (pack_id,),
        )
        already_linked_ids = {r["document_id"] for r in cur.fetchall()}

    for clf in classified_raw:
        tier = _tier(clf.confidence)
        already = clf.doc_id in already_linked_ids
        linked = already  # already counts as linked

        if tier == "high" and not already and not dry_run:
            try:
                add_document_link(
                    pack_id=pack_id,
                    document_id=clf.doc_id,
                    document_role=clf.doc_role,
                    added_by="auto_builder",
                    quality_flags={
                        "auto_classified": True,
                        "confidence": clf.confidence,
                        "tier": "high",
                    },
                )
                linked = True
            except Exception as exc:
                if "unique" in str(exc).lower() or "conflict" in str(exc).lower():
                    linked = True
                else:
                    logger.warning("Link failed for doc %d: %s", clf.doc_id, exc)

        cdoc = ClassifiedDoc(
            doc_id=clf.doc_id,
            title=clf.title,
            category=clf.category,
            doc_role=clf.doc_role,
            methodology_code=methodology_code,
            confidence=clf.confidence,
            tier=tier,
            linked=(linked or (tier == "high" and not dry_run)),
            already_linked=already,
        )

        if tier == "high":
            high.append(cdoc)
        elif tier == "medium":
            medium.append(cdoc)
        else:
            low.append(cdoc)

    return high, medium, low


# ---------------------------------------------------------------------------
# PART 7 — MAIN AUTO-BUILD WORKFLOW
# ---------------------------------------------------------------------------

def build_pack_full(
    methodology_code: str,
    registry: Optional[str] = None,
    dry_run: bool = False,
    max_remote_attempts: int = 6,
    extract_findings: bool = True,
) -> AutoBuildReport:
    """
    Full AI-assisted pack build workflow.

    Steps:
      1. Create pack if missing
      2. Analyze methodology requirements (static KB + ref_methodologies + repo)
      3. Repository-first discovery — classify & auto-link high-confidence docs
      4. Carbon Intelligence project candidate ranking
      5. Remote document discovery (Verra API; GS graceful-fail)
      6. Findings extraction from val/ver reports in pack
      7. Readiness evaluation
      8. Missing-items report generation
      9. Return AutoBuildReport
    """
    from carbongpt.repository.db import get_cursor
    from carbongpt.repository.pack_store import (
        create_pack, evaluate_pack_readiness, update_pack,
    )
    from carbongpt.repository.pack_classifier import registry_for

    code_upper = methodology_code.strip().upper()
    reg = registry or registry_for(code_upper)

    logger.info("build_pack_full: starting for %s (%s)", code_upper, reg)

    # ── Step 1: Get or create pack ────────────────────────────────────────────
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM methodology_packs
            WHERE methodology_code = %s AND registry = %s
            AND indexing_status != 'archived'
            ORDER BY id LIMIT 1
            """,
            (code_upper, reg),
        )
        row = cur.fetchone()

    created_new = False
    if row:
        pack = dict(row)
    else:
        if dry_run:
            pack = {
                "id": -1, "methodology_code": code_upper, "registry": reg,
                "target_pdd_count": 20, "target_mr_count": 5, "target_validation_count": 5,
            }
            created_new = True
        else:
            kb = _STATIC_KB.get(code_upper, {})
            pack = create_pack(
                methodology_code=code_upper,
                registry=reg,
                target_pdd_count=kb.get("target_pdd_count", 20),
                target_mr_count=kb.get("target_mr_count", 5),
                target_validation_count=kb.get("target_validation_count", 5),
                notes=f"Auto-built by pack_builder.",
                created_by="auto_builder",
            )
            created_new = True
            logger.info("Created pack id=%d for %s", pack["id"], code_upper)

    pack_id = pack["id"]

    # ── Step 2: Analyze methodology requirements ──────────────────────────────
    logger.info("Step 2: analyzing methodology requirements for %s", code_upper)
    profile = analyze_methodology_requirements(code_upper, reg)

    # ── Step 3: Repository-first discovery ────────────────────────────────────
    logger.info("Step 3: repository scan for %s", code_upper)
    docs_high, docs_medium, docs_low = _classify_and_link_docs(code_upper, pack_id, dry_run)
    logger.info("  High: %d, Medium: %d, Low: %d", len(docs_high), len(docs_medium), len(docs_low))

    # ── Step 4: Carbon Intelligence candidate discovery ───────────────────────
    logger.info("Step 4: CI candidate discovery for %s", code_upper)
    ci_candidates = discover_ci_candidates(code_upper, reg, limit=20)
    logger.info("  Found %d CI candidates", len(ci_candidates))

    # ── Step 5: Remote document discovery ────────────────────────────────────
    logger.info("Step 5: remote document discovery")
    remote_discovery: list[DiscoveryAttempt] = []
    if not dry_run and ci_candidates:
        remote_discovery = attempt_remote_discovery(
            ci_candidates,
            pack_id=pack_id,
            methodology_code=code_upper,
            max_attempts=max_remote_attempts,
            dry_run=dry_run,
        )
        success_count = sum(1 for d in remote_discovery if d.success)
        logger.info("  Remote: %d attempted, %d succeeded", len(remote_discovery), success_count)

    # ── Step 6: Findings discovery ────────────────────────────────────────────
    findings_extracted = 0
    if extract_findings and not dry_run and pack_id > 0:
        logger.info("Step 6: extracting findings from val/ver reports")
        findings_extracted = extract_pack_findings(pack_id)
        logger.info("  Extracted %d findings", findings_extracted)

    # ── Step 7: Readiness evaluation ──────────────────────────────────────────
    # Always evaluate readiness for existing packs (read-only, safe in dry_run)
    if pack_id > 0:
        readiness = evaluate_pack_readiness(pack_id)
        if not dry_run:
            if pack.get("indexing_status") == "not_started":
                update_pack(pack_id, indexing_status="collecting_documents")
    else:
        readiness = {}

    # ── Step 8: Missing items report ─────────────────────────────────────────
    logger.info("Step 8: generating missing items report")
    missing = generate_missing_report(
        profile=profile,
        readiness=readiness,
        docs_high=docs_high,
        docs_medium=docs_medium,
        ci_candidates=ci_candidates,
        remote_discovery=remote_discovery,
        pack=pack,
    )

    return AutoBuildReport(
        methodology_code=code_upper,
        registry=reg,
        pack_id=pack_id,
        created_new_pack=created_new,
        dry_run=dry_run,
        profile=profile,
        docs_high_confidence=docs_high,
        docs_medium_confidence=docs_medium,
        docs_low_confidence=docs_low,
        ci_candidates=ci_candidates,
        remote_discovery=remote_discovery,
        findings_extracted=findings_extracted,
        readiness=readiness,
        missing_items=missing,
        total_linked=sum(1 for d in docs_high if d.linked),
        total_suggested=len(docs_medium),
        total_missing=len(missing),
    )
