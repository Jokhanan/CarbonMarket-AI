import json
import logging
import os
import re

logger = logging.getLogger(__name__)

STANDARD_SLUG_MAP = {
    "GoldStandard": "goldstandard",
    "Verra": "verra",
}


def extract_methodology_references(text: str) -> list[str]:
    patterns = [
        (r'\bAMS[-\s]*(?:I{1,3}|IV)[-.\s]*[A-Z](?:\.\d+)?', None),
        (r'\bAM\d{4}', None),
        (r'\bACM\d{4}', None),
        (r'\bVM\d{4}', None),
        (r'\bVMR\d{4}', None),
        (r'\bM\d{4}', None),
        (r'\bAR[-\s]*(?:AM|AMS)\d+', None),
        (r'\bTPDDTEC\b', None),
    ]
    refs = set()
    for pat, _ in patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            raw = match.group().strip()
            cleaned = re.sub(r'[-\s]+', '-', raw).upper()
            cleaned = cleaned.rstrip("-.")
            refs.add(cleaned)
    return sorted(refs)


def check_document_compliance(document_text: str, standard: str = "GoldStandard") -> list[dict]:
    slug = STANDARD_SLUG_MAP.get(standard, standard.lower())
    findings = []

    methodology_refs = extract_methodology_references(document_text)
    if methodology_refs:
        try:
            from carbongpt.repository.store import check_methodology_rules
            for ref in methodology_refs:
                matching_rules = check_methodology_rules(ref, slug)
                for rule in matching_rules:
                    findings.append({
                        "type": "compliance_rule",
                        "rule_id": rule["id"],
                        "rule_type": rule["rule_type"],
                        "severity": rule["severity"],
                        "title": rule["title"],
                        "description": rule["description"],
                        "methodology": ref,
                        "source_url": rule.get("source_url"),
                        "source_description": rule.get("source_description"),
                    })
        except Exception as e:
            logger.debug("Could not check methodology rules: %s", e)

    try:
        from carbongpt.repository.store import get_active_rules_for_standard
        active_rules = get_active_rules_for_standard(slug)
        text_lower = document_text.lower()
        for rule in active_rules:
            if rule["id"] in [f.get("rule_id") for f in findings]:
                continue
            cond = rule["conditions"] if isinstance(rule["conditions"], dict) else json.loads(rule["conditions"])
            check_keywords = cond.get("check_in_document", [])
            if check_keywords and any(kw.lower() in text_lower for kw in check_keywords):
                findings.append({
                    "type": "compliance_rule",
                    "rule_id": rule["id"],
                    "rule_type": rule["rule_type"],
                    "severity": rule["severity"],
                    "title": rule["title"],
                    "description": rule["description"],
                    "methodology": None,
                    "source_url": rule.get("source_url"),
                    "source_description": rule.get("source_description"),
                })
    except Exception as e:
        logger.debug("Could not check general rules: %s", e)

    return findings


def format_compliance_findings_for_prompt(findings: list[dict]) -> str:
    if not findings:
        return ""

    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    infos = [f for f in findings if f["severity"] == "info"]

    parts = [
        "\n### COMPLIANCE ALERTS (from verified rules database):\n"
        "The following compliance issues were detected by matching document content "
        "against the compliance rules database. These are verified regulatory facts, "
        "not AI opinions. Incorporate these into your review.\n"
    ]

    if errors:
        parts.append("\n**CRITICAL ISSUES:**")
        for f in errors:
            meth = f" (methodology: {f['methodology']})" if f.get("methodology") else ""
            parts.append(f"- **{f['title']}**{meth}: {f['description']}")
            if f.get("source_url"):
                parts.append(f"  Source: {f['source_url']}")

    if warnings:
        parts.append("\n**WARNINGS:**")
        for f in warnings:
            meth = f" (methodology: {f['methodology']})" if f.get("methodology") else ""
            parts.append(f"- **{f['title']}**{meth}: {f['description']}")

    if infos:
        parts.append("\n**NOTICES:**")
        for f in infos:
            meth = f" (methodology: {f['methodology']})" if f.get("methodology") else ""
            parts.append(f"- {f['title']}{meth}: {f['description']}")

    return "\n".join(parts)
