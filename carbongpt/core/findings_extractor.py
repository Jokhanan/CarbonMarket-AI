import json
import logging
import os
import re

import pdfplumber

logger = logging.getLogger(__name__)

FINDINGS_EXTRACTION_PROMPT = """You are an expert carbon credit auditor analyzing a validation/verification report or PRR document.

Extract ALL individual findings (CARs, CLs, FARs, observations, PRR comments) from the document text below.

For each finding, provide:
- finding_type: "CAR" | "CL" | "FAR" | "observation" | "prr_comment"
- finding_id: the original ID from the document (e.g., "CAR #1", "CL 05", "Comment 3")
- severity: "critical" (CAR), "high" (CL requiring PDD changes), "medium" (CL clarification only), "low" (FAR/observation)
- pdd_section: which PDD/MR section this relates to (e.g., "1.12", "2.1", "4.3", "Monitoring Plan", "Baseline"). Use the section number if mentioned, otherwise use the topic area.
- topic: short categorization (e.g., "fNRB calculation", "stakeholder engagement", "monitoring parameters", "additionality", "baseline scenario", "double counting", "crediting period", "emission reductions", "sampling methodology", "project boundary", "leakage", "equipment specifications", "data quality")
- description: the VVB's or Verra's question/concern (the actual finding text)
- resolution: how the developer/PP responded and what they changed
- resolution_approach: one of "pdd_update" (PDD was revised), "clarification" (explanation provided, no PDD change), "evidence_provided" (supporting docs submitted), "calculation_corrected" (numbers were fixed), "methodology_reference" (cited methodology clause)
- was_closed: true/false

Return a JSON array of findings objects. If no findings are found, return an empty array [].

Be thorough - extract EVERY finding, even minor clarifications. Include the actual text of the finding and resolution, not just summaries.

Document text:
"""

METHODOLOGY_DETECTION_PROMPT = """Based on this document text from a carbon project validation/verification report, identify:
1. methodology_code: The methodology used (e.g., "VM0050", "ACM0002", "AMS-I.D.", "AMS-II.G")
2. standard: "Verra" or "GoldStandard"  
3. vvb_name: Name of the VVB/auditor organization
4. project_id: The VCS or GS project ID number
5. project_name: The project name
6. doc_type: "validation_report", "verification_report", "joint_valver", or "prr_response"

Return as JSON object. Use null for any field you cannot determine.

Document text (first 3000 chars):
"""


def extract_text_from_pdf(file_path, max_pages=None):
    try:
        pdf = pdfplumber.open(file_path)
        pages = pdf.pages if max_pages is None else pdf.pages[:max_pages]
        text = ""
        for page in pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
        return text
    except Exception as e:
        logger.error("Failed to extract text from %s: %s", file_path, e)
        return ""


def _call_openai_json(system_prompt, user_prompt, max_tokens=4000):
    import openai
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    return json.loads(content)


def detect_document_metadata(text):
    header_text = text[:3000]
    try:
        result = _call_openai_json(
            "You extract metadata from carbon project documents. Return valid JSON.",
            METHODOLOGY_DETECTION_PROMPT + f'"""\n{header_text}\n"""',
            max_tokens=500,
        )
        return result
    except Exception as e:
        logger.error("Metadata detection failed: %s", e)
        return {}


def extract_findings_from_text(text, metadata=None):
    chunks = []
    chunk_size = 15000
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])

    all_findings = []
    for i, chunk in enumerate(chunks):
        context_prefix = ""
        if metadata:
            context_prefix = (
                f"Project: {metadata.get('project_name', 'Unknown')}\n"
                f"Methodology: {metadata.get('methodology_code', 'Unknown')}\n"
                f"Standard: {metadata.get('standard', 'Unknown')}\n\n"
            )

        try:
            result = _call_openai_json(
                "You are an expert carbon credit auditor. Extract findings and return valid JSON with key 'findings' containing an array.",
                FINDINGS_EXTRACTION_PROMPT + f'{context_prefix}"""\n{chunk}\n"""',
                max_tokens=4000,
            )
            findings = result.get("findings", [])
            if isinstance(findings, list):
                all_findings.extend(findings)
                logger.info("Chunk %d/%d: extracted %d findings", i + 1, len(chunks), len(findings))
        except Exception as e:
            logger.error("Findings extraction failed for chunk %d: %s", i + 1, e)

    return all_findings


def process_document_for_findings(document_id, file_path, methodology_code_override=None):
    from carbongpt.repository.store import save_finding, get_findings_by_document

    existing = get_findings_by_document(document_id)
    if existing:
        logger.info("Document %s already has %d findings extracted, skipping", document_id, len(existing))
        return {"document_id": document_id, "status": "already_extracted", "count": len(existing)}

    text = extract_text_from_pdf(file_path)
    if not text or len(text) < 200:
        logger.warning("Document %s has insufficient text (%d chars)", document_id, len(text))
        return {"document_id": document_id, "status": "insufficient_text", "count": 0}

    metadata = detect_document_metadata(text)
    logger.info("Detected metadata for doc %s: %s", document_id, metadata)

    methodology_code = methodology_code_override or metadata.get("methodology_code")
    standard = metadata.get("standard", "Verra")
    vvb_name = metadata.get("vvb_name")
    project_id = metadata.get("project_id")
    project_name = metadata.get("project_name")
    doc_type = metadata.get("doc_type", "verification_report")

    findings = extract_findings_from_text(text, metadata)
    logger.info("Extracted %d findings from document %s", len(findings), document_id)

    saved_count = 0
    for f in findings:
        finding_type = f.get("finding_type", "CL")
        if finding_type not in ("CAR", "CL", "FAR", "observation", "comment", "prr_comment"):
            finding_type = "observation"

        severity = f.get("severity", "medium")
        if severity not in ("critical", "high", "medium", "low", "info"):
            severity = "medium"

        resolution_approach = f.get("resolution_approach")
        if resolution_approach and resolution_approach not in (
            "pdd_update", "clarification", "evidence_provided",
            "calculation_corrected", "methodology_reference"
        ):
            resolution_approach = "clarification"

        try:
            save_finding(
                source_document_id=document_id,
                methodology_code=methodology_code,
                finding_type=finding_type,
                description=f.get("description", ""),
                resolution=f.get("resolution"),
                pdd_section=f.get("pdd_section"),
                topic=f.get("topic"),
                severity=severity,
                resolution_approach=resolution_approach,
                standard=standard,
                doc_type=doc_type,
                vvb_name=vvb_name,
                source_project_id=str(project_id) if project_id else None,
                source_project_name=project_name,
                structured_data={
                    "finding_id": f.get("finding_id"),
                    "was_closed": f.get("was_closed", True),
                },
                extraction_method="ai_assisted",
                confidence=0.8,
            )
            saved_count += 1
        except Exception as e:
            logger.error("Failed to save finding: %s", e)

    return {
        "document_id": document_id,
        "status": "extracted",
        "methodology_code": methodology_code,
        "findings_extracted": len(findings),
        "findings_saved": saved_count,
        "metadata": metadata,
    }


def extract_findings_from_all_fvr_valver(max_documents=50):
    from carbongpt.repository.store import list_documents

    all_docs = list_documents() or []
    target_docs = [
        d for d in all_docs
        if d.get("category") in ("example_fvr", "example_valver")
        and d.get("file_path")
        and d["file_path"].lower().endswith(".pdf")
    ]

    results = {
        "total_documents": len(target_docs),
        "processed": 0,
        "skipped": 0,
        "total_findings": 0,
        "errors": 0,
        "documents": [],
    }

    import time
    for doc in target_docs[:max_documents]:
        doc_id = doc["id"]
        file_path = doc["file_path"]

        if not os.path.exists(file_path):
            results["skipped"] += 1
            continue

        try:
            result = process_document_for_findings(doc_id, file_path)
            results["documents"].append(result)
            if result["status"] == "extracted":
                results["processed"] += 1
                results["total_findings"] += result.get("findings_saved", 0)
            elif result["status"] == "already_extracted":
                results["skipped"] += 1
            else:
                results["skipped"] += 1
        except Exception as e:
            logger.error("Failed to process document %s: %s", doc_id, e)
            results["errors"] += 1

        time.sleep(1)

    return results


def get_findings_context_for_section(methodology_code, section_title):
    from carbongpt.repository.store import get_findings_for_section

    keywords = _derive_section_keywords(section_title)
    if not keywords:
        return ""

    findings = get_findings_for_section(methodology_code, keywords, limit=8)
    if not findings:
        return ""

    lines = []
    lines.append(f"### Common VVB findings for this section (from {len(findings)} past audits):")
    lines.append("The following issues have been raised by VVBs on similar projects. Address these proactively:\n")

    for f in findings:
        ftype = f.get("finding_type", "CL")
        topic = f.get("topic", "")
        desc = f.get("description", "")[:300]
        resolution = f.get("resolution", "")[:200]
        severity = f.get("severity", "medium")

        lines.append(f"- [{ftype}] ({severity}) {topic}: {desc}")
        if resolution:
            lines.append(f"  Resolution: {resolution}")
        lines.append("")

    return "\n".join(lines)


def get_findings_review_context(methodology_code):
    from carbongpt.repository.store import get_findings_by_methodology

    findings = get_findings_by_methodology(methodology_code, limit=30)
    if not findings:
        return ""

    by_topic = {}
    for f in findings:
        topic = f.get("topic", "general")
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(f)

    lines = []
    lines.append("### Known VVB findings patterns for this methodology:")
    lines.append("Based on analysis of past validation/verification reports, VVBs commonly raise these issues:\n")

    for topic, topic_findings in sorted(by_topic.items(), key=lambda x: -len(x[1])):
        car_count = sum(1 for f in topic_findings if f["finding_type"] == "CAR")
        cl_count = sum(1 for f in topic_findings if f["finding_type"] == "CL")
        lines.append(f"**{topic}** ({len(topic_findings)} findings: {car_count} CARs, {cl_count} CLs)")
        for f in topic_findings[:2]:
            desc = f.get("description", "")[:200]
            lines.append(f"  - {f['finding_type']}: {desc}")
        lines.append("")

    return "\n".join(lines)[:4000]


SECTION_TOPIC_MAP = {
    "project_description": ["project description", "project design", "project activity", "technology"],
    "baseline": ["baseline", "baseline scenario", "baseline emissions", "common practice"],
    "additionality": ["additionality", "barrier analysis", "investment analysis", "common practice"],
    "monitoring": ["monitoring", "monitoring plan", "monitoring parameters", "data quality", "QA/QC", "sampling"],
    "emission_reductions": ["emission reductions", "emission calculations", "quantification", "ERs", "calculation"],
    "stakeholder": ["stakeholder", "stakeholder engagement", "consultation", "grievance"],
    "safeguards": ["safeguards", "environmental impact", "social impact", "no net harm", "do no harm"],
    "eligibility": ["eligibility", "applicability", "project boundary", "scope"],
    "crediting_period": ["crediting period", "start date", "project start"],
    "methodology": ["methodology", "methodology deviation", "methodology application"],
    "leakage": ["leakage", "leakage emissions"],
    "sdg": ["sustainable development", "SDG", "co-benefits"],
    "double_counting": ["double counting", "double claim", "other programs", "registry"],
    "ownership": ["ownership", "right of use", "project proponent"],
    "sampling": ["sampling", "sample size", "confidence interval", "statistical"],
    "data_management": ["data management", "data quality", "calibration", "measurement"],
    "fnrb": ["fNRB", "non-renewable biomass", "fraction of non-renewable"],
    "wbt": ["WBT", "water boiling test", "thermal efficiency", "boiling test"],
    "stove_distribution": ["distribution", "stove distribution", "device distribution", "tracking"],
}


def _derive_section_keywords(section_title):
    title_lower = section_title.lower()
    keywords = set()
    for category, terms in SECTION_TOPIC_MAP.items():
        for term in terms:
            if term.lower() in title_lower:
                keywords.update(terms)
                break

    if not keywords:
        words = re.split(r'[\s/,\-]+', title_lower)
        keywords = {w for w in words if len(w) > 3}

    return list(keywords)[:5]
