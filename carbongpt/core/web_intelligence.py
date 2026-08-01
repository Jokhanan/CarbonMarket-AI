import json
import logging
import os
import re

import requests as http_client

logger = logging.getLogger(__name__)

MODEL = os.getenv("CARBONGPT_AI_MODEL", "claude-sonnet-5")
SERPER_API_URL = "https://google.serper.dev/search"


def _get_serper_key():
    return os.environ.get("SERPER_API_KEY", "")


def web_search(query: str, num_results: int = 5) -> list[dict]:
    serper_key = _get_serper_key()
    if serper_key:
        return _search_serper(query, serper_key, num_results)
    return _search_fallback(query)


def _search_serper(query: str, api_key: str, num_results: int) -> list[dict]:
    try:
        resp = http_client.post(
            SERPER_API_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num_results},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })
        if data.get("answerBox"):
            ab = data["answerBox"]
            results.insert(0, {
                "title": ab.get("title", "Answer"),
                "url": ab.get("link", ""),
                "snippet": ab.get("snippet") or ab.get("answer", ""),
            })
        return results
    except Exception as e:
        logger.warning("Serper search failed: %s", e)
        return []


def _search_fallback(query: str) -> list[dict]:
    logger.info("No SERPER_API_KEY set — web search unavailable, using AI knowledge only")
    return []


def verify_methodology_status(
    methodology: str,
    standard: str = "Verra VCS",
) -> dict | None:
    # Text generation now needs ANTHROPIC_API_KEY, not OPENAI_API_KEY — the
    # check happens inside call_openai() itself (raises, caught below).
    search_query = f"{standard} {methodology} methodology status approved deprecated transition 2024 2025 2026"
    search_results = web_search(search_query)

    context = ""
    if search_results:
        snippets = []
        for r in search_results[:5]:
            snippets.append(f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}")
        context = "\n\n".join(snippets)

    prompt = (
        f"What is the current status of methodology '{methodology}' under {standard}?\n\n"
    )
    if context:
        prompt += f"Web search results:\n{context}\n\n"
    prompt += (
        "Based on your knowledge and any web search results above, answer:\n"
        "1. Is this methodology currently approved/accepted under this standard?\n"
        "2. Has it been deprecated, replaced, or transitioned?\n"
        "3. If replaced, what is the replacement methodology?\n"
        "4. Are there any important deadlines or transition dates?\n"
        "5. What is the source of this information?\n\n"
        "Respond in JSON format with these fields:\n"
        "- status: 'approved' | 'deprecated' | 'transitioning' | 'conditional' | 'unknown'\n"
        "- is_approved: true/false\n"
        "- summary: brief description of current status\n"
        "- replacement: replacement methodology if deprecated (null otherwise)\n"
        "- deadline: transition deadline if applicable (null otherwise)\n"
        "- source_url: most relevant URL from search results (null if none)\n"
        "- source_description: brief source description\n"
        "- confidence: 'high' | 'medium' | 'low'\n"
        "- proposed_rule_title: suggested title for a compliance rule (null if methodology is approved and no issues)\n"
        "- proposed_rule_description: suggested description for a compliance rule (null if no issues)\n"
        "- proposed_severity: 'error' | 'warning' | 'info' (null if no issues)"
    )

    try:
        from carbongpt.core.openai_client import call_openai
        system_prompt = (
            "You are a carbon credit methodology expert. "
            "You provide accurate, factual information about methodology status "
            "under carbon credit standards (Verra VCS, Gold Standard, CDM/UNFCCC). "
            "Only state facts you are confident about. "
            "If unsure, set confidence to 'low' and explain what you don't know. "
            "Respond ONLY with valid JSON."
        )
        content = call_openai(system_prompt, prompt, temperature=0.1, model_override=MODEL)
        return json.loads(content)
    except Exception as e:
        logger.warning("Failed to verify methodology status: %s", e)
        return None


def propose_compliance_rule_from_web(
    methodology: str,
    standard: str = "Verra VCS",
    standard_id: int = None,
) -> dict | None:
    result = verify_methodology_status(methodology, standard)
    if not result:
        return None

    if result.get("confidence") == "low":
        return None

    if not result.get("proposed_rule_title"):
        return None

    from carbongpt.repository.store import check_methodology_rules
    slug_map = {"Verra VCS": "verra", "Gold Standard": "goldstandard", "CDM": "cdm"}
    slug = slug_map.get(standard, standard.lower())
    existing = check_methodology_rules(methodology, slug)
    if existing:
        return None

    conditions = {
        "affected_methodologies": [methodology],
        "keywords": [methodology.lower().replace("-", "").replace(" ", "")],
    }
    if result.get("replacement"):
        conditions["replacement"] = result["replacement"]

    severity = result.get("proposed_severity", "warning")
    if severity not in ("error", "warning", "info"):
        severity = "warning"

    rule_data = {
        "standard_id": standard_id,
        "rule_type": "methodology_status" if result.get("status") == "deprecated" else "methodology_transition",
        "severity": severity,
        "title": result["proposed_rule_title"],
        "description": result["proposed_rule_description"],
        "conditions": conditions,
        "source_url": result.get("source_url"),
        "source_description": result.get("source_description"),
        "status": "proposed",
        "discovered_by": "web_search",
    }

    if result.get("deadline"):
        rule_data["effective_date"] = result["deadline"]

    return rule_data


def research_standard_updates(
    standard: str = "Verra VCS",
    standard_id: int = None,
    topics: list[str] = None,
) -> list[dict]:
    if not topics:
        topics = [
            f"{standard} methodology updates 2025 2026",
            f"{standard} new requirements regulatory changes 2025",
            f"{standard} deprecated methodologies transition deadlines",
            f"{standard} crediting period changes buffer pool updates",
        ]

    # Text generation now needs ANTHROPIC_API_KEY, not OPENAI_API_KEY — the
    # check happens inside call_openai() itself (raises, caught below).
    all_snippets = []
    for topic in topics:
        results = web_search(topic)
        for r in results[:3]:
            all_snippets.append(f"Query: {topic}\nTitle: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}")

    if not all_snippets:
        return []

    context = "\n\n---\n\n".join(all_snippets)

    prompt = (
        f"Based on these web search results about {standard}, identify any regulatory updates, "
        f"methodology changes, new requirements, or compliance-relevant information that carbon project "
        f"developers should be aware of.\n\n"
        f"Search results:\n{context}\n\n"
        f"For each finding, provide a JSON array of objects with:\n"
        f"- rule_type: 'methodology_status' | 'methodology_transition' | 'crediting_period' | "
        f"'eligibility' | 'regulatory' | 'default_value' | 'general'\n"
        f"- severity: 'error' | 'warning' | 'info'\n"
        f"- title: concise title\n"
        f"- description: detailed description of the update/change\n"
        f"- source_url: relevant URL\n"
        f"- source_description: brief source description\n"
        f"- confidence: 'high' | 'medium' | 'low'\n\n"
        f"Only include findings you are confident about. If no relevant updates found, return an empty array.\n"
        f"Respond with valid JSON: {{\"findings\": [...]}}"
    )

    try:
        from carbongpt.core.openai_client import call_openai
        system_prompt = (
            "You are a carbon credit regulatory analyst. Extract factual regulatory "
            "updates from search results. Only include findings with high or medium confidence. "
            "Do not fabricate information. Respond ONLY with valid JSON."
        )
        content = call_openai(system_prompt, prompt, temperature=0.1, model_override=MODEL)
        data = json.loads(content)

        proposed_rules = []
        for finding in data.get("findings", []):
            if finding.get("confidence") == "low":
                continue

            conditions = {}
            if finding.get("affected_methodologies"):
                conditions["affected_methodologies"] = finding["affected_methodologies"]

            proposed_rules.append({
                "standard_id": standard_id,
                "rule_type": finding.get("rule_type", "general"),
                "severity": finding.get("severity", "info"),
                "title": finding["title"],
                "description": finding["description"],
                "conditions": conditions,
                "source_url": finding.get("source_url"),
                "source_description": finding.get("source_description"),
                "status": "proposed",
                "discovered_by": "web_search",
            })

        return proposed_rules
    except Exception as e:
        logger.warning("Failed to research standard updates: %s", e)
        return []
