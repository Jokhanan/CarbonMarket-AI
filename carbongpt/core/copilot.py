import os
import json
import logging

logger = logging.getLogger(__name__)

COPILOT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "Create a new carbon project. Use when the user wants to start a new project, develop a project, or register a new project activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name"},
                    "standard": {"type": "string", "enum": ["GoldStandard", "Verra"], "description": "Carbon standard"},
                    "methodology": {"type": "string", "description": "Methodology code (e.g. GS-TPDDTEC, VM0050, ACM0002)"},
                    "country": {"type": "string", "description": "Host country name"},
                    "description": {"type": "string", "description": "Brief project description"},
                    "project_type": {"type": "string", "enum": ["standalone_pdd", "poa_dd", "vpa_dd"], "description": "Project type. Default standalone_pdd"},
                },
                "required": ["name", "standard"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "initialize_parameters",
            "description": "Initialize methodology parameters for the current project. Use when the user wants to set up parameters, load default values, or prepare for ER calculations.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_er_simulation",
            "description": "Run emission reduction (ER) simulation/calculation for the current project. Use when the user wants to estimate, calculate, or simulate emission reductions, carbon credits, or tCO2e.",
            "parameters": {
                "type": "object",
                "properties": {
                    "parameter_overrides": {
                        "type": "object",
                        "description": "Optional parameter overrides as key-value pairs (e.g. {\"households\": 100000})",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_section",
            "description": "Draft/write a document section using AI. Use when the user wants to generate, write, or draft a PDD section, MR section, concept note, or any document section.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_id": {"type": "string", "description": "Section ID to draft (e.g. 'A1', 'B1', 'concept_note')"},
                    "doc_type": {"type": "string", "description": "Document type: pdd, mr, poa_dd, vpa_dd, valver. Default: pdd"},
                    "user_instructions": {"type": "string", "description": "Special instructions for the AI writer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_audit",
            "description": "Run audit simulation to check project readiness for VVB validation. Use when the user wants to audit, check compliance, assess readiness, or simulate validation.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_review",
            "description": "Run AI compliance review on the project's drafted sections. Use when the user wants to review their draft, check for gaps, or validate their document against standards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_type": {"type": "string", "description": "Document type to review: pdd, mr, poa_dd, vpa_dd. Default: pdd"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_methodology",
            "description": "Recommend applicable carbon credit methodologies based on project description, technology, or sector. Use when the user asks which methodology to use, or describes a project idea without specifying a methodology.",
            "parameters": {
                "type": "object",
                "properties": {
                    "technology": {"type": "string", "description": "Technology type (e.g. cookstoves, solar, wind, biogas, water purification)"},
                    "sector": {"type": "string", "description": "Sector (e.g. energy, waste, agriculture, forestry, transport)"},
                    "description": {"type": "string", "description": "Project description or idea"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_status",
            "description": "Get a comprehensive summary of the current project's status, progress, and recommended next steps. Use when the user asks about project status, what to do next, or wants a progress overview.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "navigate_to_tab",
            "description": "Direct the user to a specific workspace tab. Use when the user wants to go to a specific section like parameters, documents, simulator, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tab_name": {
                        "type": "string",
                        "enum": ["Setup", "Documents", "Parameters", "ER Simulator", "Write / Draft", "Review", "Audit", "Findings", "Lifecycle", "Monitoring", "Export"],
                        "description": "Tab to navigate to",
                    },
                },
                "required": ["tab_name"],
            },
        },
    },
]

TAB_NAME_TO_INDEX = {
    "Setup": 0, "Documents": 1, "Parameters": 2, "ER Simulator": 3,
    "Write / Draft": 4, "Review": 5, "Audit": 6, "Findings": 7,
    "Lifecycle": 8, "Monitoring": 9, "Export": 10,
}

METHODOLOGY_RECOMMENDATIONS = {
    "cookstove": [
        {"code": "GS-TPDDTEC", "standard": "GoldStandard", "name": "Technologies and Practices to Displace Decentralized Thermal Energy Consumption", "reason": "The primary Gold Standard methodology for improved cookstove projects. Covers fuel savings from efficient stoves replacing traditional biomass cooking."},
        {"code": "VM0050", "standard": "Verra", "name": "Energy Efficiency and Fuel-Switch Measures in Cookstoves", "reason": "Verra's dedicated cookstove methodology. Supports both efficiency improvements and fuel switching."},
        {"code": "GS-SIMPLIFIED-COOKSTOVE", "standard": "GoldStandard", "name": "Simplified Methodology for Clean and Efficient Cookstoves", "reason": "Simplified Gold Standard approach for smaller cookstove projects with streamlined monitoring."},
        {"code": "AMS-II.G.", "standard": "CDM", "name": "Energy efficiency measures in thermal applications of non-renewable biomass", "reason": "CDM small-scale methodology applicable to cookstove efficiency improvements."},
    ],
    "water": [
        {"code": "GS-SAFE-WATER", "standard": "GoldStandard", "name": "Emission Reductions from Safe Drinking Water Supply", "reason": "Gold Standard methodology for water purification projects that displace fuel used for boiling water."},
        {"code": "GS-WASH", "standard": "GoldStandard", "name": "Water Access and WASH Methodology", "reason": "Covers water, sanitation, and hygiene projects that reduce fuel for water treatment."},
        {"code": "AMS-III.AV.", "standard": "CDM", "name": "Low greenhouse gas emitting water purification systems", "reason": "CDM methodology for point-of-use water purification displacing boiling."},
    ],
    "solar": [
        {"code": "AMS-I.D.", "standard": "CDM", "name": "Grid-connected renewable electricity generation", "reason": "The most widely used methodology for grid-connected solar PV projects."},
        {"code": "ACM0002", "standard": "CDM", "name": "Grid-connected electricity generation from renewable sources", "reason": "Large-scale consolidated methodology for utility-scale solar and wind."},
        {"code": "AMS-I.F.", "standard": "CDM", "name": "Renewable electricity generation for captive use and mini-grid", "reason": "For off-grid and mini-grid solar installations."},
    ],
    "wind": [
        {"code": "ACM0002", "standard": "CDM", "name": "Grid-connected electricity generation from renewable sources", "reason": "The standard large-scale methodology for wind power projects."},
        {"code": "AMS-I.D.", "standard": "CDM", "name": "Grid-connected renewable electricity generation", "reason": "Small-scale version for wind projects under 15 MW."},
    ],
    "biogas": [
        {"code": "GS-BIODIGESTER", "standard": "GoldStandard", "name": "Baseline and Monitoring Methodology for Biodigester", "reason": "Gold Standard methodology specifically for household and small-farm biodigesters."},
        {"code": "AMS-I.I.", "standard": "CDM", "name": "Biogas/biomass thermal applications for households/small users", "reason": "CDM methodology for small-scale biogas thermal applications."},
        {"code": "AMS-III.D.", "standard": "CDM", "name": "Methane recovery in animal manure management systems", "reason": "For biogas from animal manure with methane recovery."},
    ],
    "waste": [
        {"code": "ACM0001", "standard": "CDM", "name": "Flaring or use of landfill gas", "reason": "Primary methodology for landfill gas capture and flaring/utilization."},
        {"code": "AMS-III.G.", "standard": "CDM", "name": "Landfill methane recovery", "reason": "Small-scale methodology for landfill methane recovery."},
        {"code": "ACM0022", "standard": "CDM", "name": "Alternative waste treatment processes", "reason": "For composting, anaerobic digestion, or other waste treatment alternatives."},
    ],
    "forestry": [
        {"code": "VM0007", "standard": "Verra", "name": "REDD+ Methodology Framework", "reason": "The primary Verra methodology for avoided deforestation and forest degradation projects."},
        {"code": "VM0047", "standard": "Verra", "name": "Afforestation, Reforestation and Revegetation", "reason": "Verra's methodology for tree planting and revegetation projects."},
        {"code": "AR-ACM0003", "standard": "CDM", "name": "Afforestation and reforestation of lands except wetlands", "reason": "CDM large-scale methodology for A/R projects."},
        {"code": "GS-AR", "standard": "GoldStandard", "name": "Afforestation/Reforestation GHG Emissions Reduction and Sequestration", "reason": "Gold Standard A/R methodology."},
    ],
    "transport": [
        {"code": "ACM0016", "standard": "CDM", "name": "Mass Rapid Transit Projects", "reason": "For bus rapid transit and mass transit projects."},
        {"code": "AMS-III.C.", "standard": "CDM", "name": "Emission reductions by electric and hybrid vehicles", "reason": "For electric vehicle fleet projects."},
    ],
    "agriculture": [
        {"code": "VM0042", "standard": "Verra", "name": "Improved Agricultural Land Management", "reason": "Verra methodology for sustainable agriculture and soil carbon projects."},
        {"code": "VM0017", "standard": "Verra", "name": "Adoption of Sustainable Agricultural Land Management", "reason": "For adopting sustainable land management practices."},
        {"code": "VM0022", "standard": "Verra", "name": "Quantifying N2O Emissions Reductions in Agricultural Crops", "reason": "For nitrogen management in crops."},
    ],
    "charcoal": [
        {"code": "AMS-III.BG.", "standard": "CDM", "name": "Emission reduction through sustainable charcoal production and consumption", "reason": "CDM methodology for improved charcoal production and efficient charcoal stoves."},
        {"code": "ACM0021", "standard": "CDM", "name": "Reduction of emissions from charcoal production by improved kiln design", "reason": "For improved kilns and charcoal production."},
        {"code": "GS-TPDDTEC", "standard": "GoldStandard", "name": "TPDDTEC", "reason": "Also applicable for charcoal-based cooking projects under Gold Standard."},
    ],
    "rice": [
        {"code": "VM0051", "standard": "Verra", "name": "Improved Management in Rice Production Systems", "reason": "Verra's dedicated methodology for rice paddy methane reduction."},
        {"code": "AMS-III.AU.", "standard": "CDM", "name": "Methane emission reduction by adjusted water management in rice cultivation", "reason": "CDM small-scale methodology for rice water management."},
    ],
}

TECHNOLOGY_KEYWORDS = {
    "cookstove": ["cookstove", "stove", "cooking", "kitchen", "biomass cooking", "clean cooking", "improved cooking", "fuel-efficient"],
    "water": ["water", "purification", "drinking water", "boiling", "wash", "sanitation", "water filter", "water treatment"],
    "solar": ["solar", "photovoltaic", "pv", "solar panel", "solar farm", "solar power"],
    "wind": ["wind", "wind farm", "wind turbine", "wind power"],
    "biogas": ["biogas", "biodigester", "anaerobic digestion", "methane capture", "bio-gas"],
    "waste": ["waste", "landfill", "solid waste", "composting", "waste treatment", "municipal waste"],
    "forestry": ["forest", "redd", "afforestation", "reforestation", "tree planting", "deforestation", "degradation", "revegetation"],
    "transport": ["transport", "bus", "transit", "vehicle", "electric vehicle", "ev", "brt"],
    "agriculture": ["agriculture", "farming", "soil carbon", "crop", "nitrogen", "sustainable agriculture"],
    "charcoal": ["charcoal", "kiln", "charcoal production"],
    "rice": ["rice", "paddy", "rice cultivation"],
}


def _detect_technology(text: str) -> list[str]:
    text_lower = text.lower()
    matches = []
    for tech, keywords in TECHNOLOGY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                matches.append(tech)
                break
    return matches


def recommend_methodologies(technology: str = "", sector: str = "", description: str = "") -> list[dict]:
    combined = f"{technology} {sector} {description}".strip()
    if not combined:
        return []

    detected = _detect_technology(combined)
    if not detected:
        detected = _detect_technology(sector) if sector else []

    results = []
    seen = set()
    for tech in detected:
        for m in METHODOLOGY_RECOMMENDATIONS.get(tech, []):
            if m["code"] not in seen:
                seen.add(m["code"])
                results.append(m)

    return results[:5]


def _ensure_message(result: dict) -> dict:
    if not result.get("message") and result.get("error"):
        result["message"] = result["error"]
    return result


def _execute_action(action_name: str, args: dict, project_id: int | None) -> dict:
    if action_name == "create_project":
        return _ensure_message(_action_create_project(args))
    elif action_name == "initialize_parameters":
        return _ensure_message(_action_initialize_parameters(project_id))
    elif action_name == "run_er_simulation":
        return _ensure_message(_action_run_er_simulation(project_id, args.get("parameter_overrides", {})))
    elif action_name == "draft_section":
        return _ensure_message(_action_draft_section(project_id, args))
    elif action_name == "run_audit":
        return _ensure_message(_action_run_audit(project_id))
    elif action_name == "run_review":
        return _ensure_message(_action_run_review(project_id, args.get("doc_type", "pdd")))
    elif action_name == "suggest_methodology":
        return _ensure_message(_action_suggest_methodology(args))
    elif action_name == "get_project_status":
        return _ensure_message(_action_get_project_status(project_id))
    elif action_name == "navigate_to_tab":
        tab = args.get("tab_name", "Setup")
        return {"success": True, "action": "navigate", "tab": tab, "tab_index": TAB_NAME_TO_INDEX.get(tab, 0), "message": f"Navigating to {tab} tab."}
    else:
        return {"success": False, "error": f"Unknown action: {action_name}", "message": f"Unknown action: {action_name}"}


def _action_create_project(args: dict) -> dict:
    from carbongpt.repository.store import create_user_project
    try:
        project_name = args.get("name", "New Project")
        project_id = create_user_project(
            name=project_name,
            standard=args.get("standard", "GoldStandard"),
            doc_type=args.get("doc_type", "pdd"),
            methodology=args.get("methodology", ""),
            country=args.get("country", ""),
            description=args.get("description", ""),
            project_type=args.get("project_type", "standalone_pdd"),
        )
        return {
            "success": True,
            "action": "create_project",
            "project_id": project_id,
            "project_name": project_name,
            "message": f"Project '{project_name}' created successfully (ID: {project_id}).",
            "navigation_hint": "Setup",
            "navigation_index": 0,
        }
    except Exception as e:
        logger.error("Copilot create_project error: %s", e)
        return {"success": False, "error": str(e), "message": f"Failed to create project: {e}"}


def _action_initialize_parameters(project_id: int | None) -> dict:
    if not project_id:
        return {"success": False, "error": "No project selected. Please select or create a project first."}
    from carbongpt.core.parameter_engine import initialize_project_parameters
    try:
        result = initialize_project_parameters(project_id)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        return {
            "success": True,
            "action": "initialize_parameters",
            "message": f"Initialized {result['inserted']} parameters for methodology {result['methodology']}.",
            "count": result["inserted"],
            "methodology": result["methodology"],
            "navigation_hint": "Parameters",
            "navigation_index": 2,
        }
    except Exception as e:
        logger.error("Copilot init_params error: %s", e)
        return {"success": False, "error": str(e)}


def _action_run_er_simulation(project_id: int | None, overrides: dict) -> dict:
    if not project_id:
        return {"success": False, "error": "No project selected. Please select or create a project first."}
    from carbongpt.core.er_simulator import run_scenario
    try:
        result = run_scenario(project_id, parameter_overrides=overrides)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        summary = result.get("summary", {})
        return {
            "success": True,
            "action": "run_er_simulation",
            "message": f"ER simulation complete. Total: {summary.get('total_er', 0):,.0f} tCO2e over {summary.get('crediting_years', 0)} years (average {summary.get('average_annual_er', 0):,.0f} tCO2e/yr).",
            "total_er": summary.get("total_er", 0),
            "average_annual_er": summary.get("average_annual_er", 0),
            "crediting_years": summary.get("crediting_years", 0),
            "result_data": result,
            "navigation_hint": "ER Simulator",
            "navigation_index": 3,
        }
    except Exception as e:
        logger.error("Copilot run_er_sim error: %s", e)
        return {"success": False, "error": str(e)}


def _action_draft_section(project_id: int | None, args: dict) -> dict:
    if not project_id:
        return {"success": False, "error": "No project selected. Please select or create a project first."}

    section_id = args.get("section_id")
    doc_type = args.get("doc_type", "pdd")
    user_instructions = args.get("user_instructions", "")

    if not section_id:
        return {
            "success": True,
            "action": "navigate",
            "tab": "Write / Draft",
            "tab_index": 4,
            "message": "Opening the Write / Draft tab. Select a section to begin drafting.",
            "navigation_hint": "Write / Draft",
            "navigation_index": 4,
        }

    from carbongpt.core.ai_writer import write_section
    try:
        result = write_section(project_id, section_id, doc_type=doc_type, user_instructions=user_instructions)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        preview = (result.get("text", "") or "")[:300]
        return {
            "success": True,
            "action": "draft_section",
            "message": f"Section '{section_id}' ({doc_type.upper()}) drafted successfully.",
            "section_id": section_id,
            "preview": preview,
            "navigation_hint": "Write / Draft",
            "navigation_index": 4,
        }
    except Exception as e:
        logger.error("Copilot draft_section error: %s", e)
        return {"success": False, "error": str(e)}


def _action_run_audit(project_id: int | None) -> dict:
    if not project_id:
        return {"success": False, "error": "No project selected. Please select or create a project first."}
    from carbongpt.core.audit_simulator import run_audit_simulation
    try:
        result = run_audit_simulation(project_id)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        score = result.get("overall_score", 0)
        risk = result.get("risk_level", "UNKNOWN")
        counts = result.get("counts", {})
        return {
            "success": True,
            "action": "run_audit",
            "message": f"Audit simulation complete. Score: {score}%, Risk Level: {risk}. Findings: {counts.get('critical', 0)} critical, {counts.get('major', 0)} major, {counts.get('minor', 0)} minor.",
            "overall_score": score,
            "risk_level": risk,
            "counts": counts,
            "result_data": result,
            "navigation_hint": "Audit",
            "navigation_index": 6,
        }
    except Exception as e:
        logger.error("Copilot run_audit error: %s", e)
        return {"success": False, "error": str(e)}


def _action_run_review(project_id: int | None, doc_type: str) -> dict:
    if not project_id:
        return {"success": False, "error": "No project selected. Please select or create a project first."}
    try:
        from carbongpt.repository.store import get_write_sessions
        sessions = get_write_sessions(project_id, doc_type=doc_type)
        drafted = [s for s in (sessions or []) if s.get("generated_text") or s.get("user_text")]
        if not drafted:
            return {"success": False, "error": f"No drafted sections found for {doc_type.upper()}. Write some sections first."}
        return {
            "success": True,
            "action": "navigate",
            "tab": "Review",
            "tab_index": 5,
            "message": f"Found {len(drafted)} drafted section(s) for {doc_type.upper()} review. Opening the Review tab.",
            "navigation_hint": "Review",
            "navigation_index": 5,
        }
    except Exception as e:
        logger.error("Copilot run_review error: %s", e)
        return {"success": False, "error": str(e)}


def _action_suggest_methodology(args: dict) -> dict:
    recs = recommend_methodologies(
        technology=args.get("technology", ""),
        sector=args.get("sector", ""),
        description=args.get("description", ""),
    )
    if not recs:
        return {
            "success": True,
            "action": "suggest_methodology",
            "message": "I couldn't find specific methodology recommendations for that description. Could you provide more details about the technology or sector?",
            "recommendations": [],
        }
    rec_text = "\n".join([f"- **{r['code']}** ({r['standard']}): {r['name']} — {r['reason']}" for r in recs])
    return {
        "success": True,
        "action": "suggest_methodology",
        "message": f"Based on your project description, here are recommended methodologies:\n\n{rec_text}",
        "recommendations": recs,
    }


def _action_get_project_status(project_id: int | None) -> dict:
    if not project_id:
        return {"success": False, "error": "No project selected. Please select or create a project first."}
    from carbongpt.repository.store import get_user_project, get_write_sessions
    from carbongpt.core.parameter_engine import get_project_parameters, get_parameter_summary

    project = get_user_project(project_id)
    if not project:
        return {"success": False, "error": "Project not found."}

    summary_parts = [f"**{project['name']}**"]
    summary_parts.append(f"Standard: {project.get('standard', 'Not set')}")
    summary_parts.append(f"Methodology: {project.get('methodology') or 'Not selected'}")
    summary_parts.append(f"Country: {project.get('country') or 'Not set'}")
    summary_parts.append(f"Status: {project.get('status', 'draft')}")
    summary_parts.append(f"Documents: {len(project.get('documents', []))}")

    param_summary = get_parameter_summary(project_id)
    if param_summary and param_summary.get("total", 0) > 0:
        summary_parts.append(f"Parameters: {param_summary['configured']}/{param_summary['total']} configured ({param_summary.get('pending', 0)} pending)")
    else:
        summary_parts.append("Parameters: Not initialized")

    sessions = get_write_sessions(project_id)
    drafted = [s for s in (sessions or []) if s.get("generated_text") or s.get("user_text")]
    summary_parts.append(f"Drafted sections: {len(drafted)}")

    next_steps = []
    if not project.get("methodology"):
        next_steps.append("Select a methodology in the Setup tab")
    if not project.get("country"):
        next_steps.append("Set the project country")
    if not param_summary or param_summary.get("total", 0) == 0:
        next_steps.append("Initialize parameters from methodology")
    elif param_summary.get("pending", 0) > 0:
        next_steps.append(f"Configure {param_summary['pending']} missing parameters")
    if len(project.get("documents", [])) == 0:
        next_steps.append("Upload supporting documents")
    if not drafted:
        next_steps.append("Draft your first document section")

    if next_steps:
        summary_parts.append("\n**Recommended next steps:**")
        for i, step in enumerate(next_steps[:3], 1):
            summary_parts.append(f"{i}. {step}")

    return {
        "success": True,
        "action": "get_project_status",
        "message": "\n".join(summary_parts),
    }


def process_copilot_message(message: str, project_id: int | None, history: list[dict], project_context: str = "") -> dict:
    system_prompt = (
        "You are CarbonGPT Copilot, an intelligent AI assistant that helps users develop carbon credit projects.\n\n"
        "You can perform actions directly:\n"
        "- Create new projects\n"
        "- Initialize methodology parameters\n"
        "- Run emission reduction (ER) simulations\n"
        "- Draft PDD/MR document sections\n"
        "- Run audit simulations\n"
        "- Review drafted documents\n"
        "- Recommend methodologies\n"
        "- Check project status\n"
        "- Navigate to specific workspace tabs\n\n"
        "When the user asks you to do something actionable, use the appropriate tool.\n"
        "When the user asks a general question, answer conversationally.\n"
        "Be concise, practical, and use specific numbers and references.\n\n"
        "Your expertise covers:\n"
        "- Carbon credit standards: Gold Standard (GS4GG), Verra VCS, CDM\n"
        "- Project Design Documents (PDDs), Monitoring Reports (MRs)\n"
        "- Methodologies for emission reduction calculations\n"
        "- Baseline assessments, additionality, monitoring\n"
        "- Technical parameters: emission factors, fNRB, NCV\n"
    )

    if project_context:
        system_prompt += f"\n\nCURRENT PROJECT CONTEXT:\n{project_context}"

    messages = []
    for msg in (history or [])[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    try:
        from carbongpt.core.openai_client import call_with_tools
        model = os.getenv("CARBONGPT_AI_MODEL")  # None is fine — call_with_tools falls back to its own default
        choice = call_with_tools(
            system_prompt, messages, COPILOT_TOOLS,
            max_tokens=2000, temperature=0.3, model_override=model,
        )
        finish_reason = choice["finish_reason"]
        assistant_msg = choice["message"]

        if finish_reason == "tool_calls" and assistant_msg.get("tool_calls"):
            tool_call = assistant_msg["tool_calls"][0]
            func_name = tool_call["function"]["name"]
            try:
                func_args = json.loads(tool_call["function"].get("arguments", "{}"))
            except (json.JSONDecodeError, TypeError):
                func_args = {}

            logger.info("Copilot action: %s(%s)", func_name, func_args)
            action_result = _execute_action(func_name, func_args, project_id)

            tool_result_msg = json.dumps(action_result)
            followup_messages = messages + [
                assistant_msg,
                {"role": "tool", "tool_call_id": tool_call["id"], "content": tool_result_msg},
            ]
            followup_choice = call_with_tools(
                system_prompt, followup_messages, [],
                max_tokens=1500, temperature=0.3, model_override=model,
            )
            reply = followup_choice["message"]["content"]

            nav_hint = action_result.get("navigation_hint")
            nav_index = action_result.get("navigation_index")

            return {
                "reply": reply,
                "action_taken": action_result,
                "navigation_hint": nav_hint,
                "navigation_index": nav_index,
            }
        else:
            reply = assistant_msg.get("content") or "I'm sorry, I couldn't process that request."
            return {"reply": reply, "action_taken": None, "navigation_hint": None}

    except Exception as e:
        logger.error("Copilot error: %s", e)
        err_str = str(e)
        if "429" in err_str or "rate" in err_str.lower():
            return {"reply": "Rate limit reached. Please wait a moment and try again.", "action_taken": None, "navigation_hint": None}
        return {"reply": f"I encountered an error processing your request. Please try again.", "action_taken": None, "navigation_hint": None}
