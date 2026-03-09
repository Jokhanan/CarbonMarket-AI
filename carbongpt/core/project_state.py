import logging
from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

SEVERITY_BLOCKER = "blocker"
SEVERITY_WARNING = "warning"
SEVERITY_SUGGESTION = "suggestion"
SEVERITY_INSIGHT = "insight"


def evaluate_project_state(project_id):
    project = _load_project(project_id)
    if not project:
        return {"error": "Project not found"}

    state = {
        "project_id": project_id,
        "project_name": project.get("name", ""),
        "project_type": project.get("project_type", "standalone_pdd"),
        "standard": project.get("standard", ""),
        "status": project.get("status", "draft"),
        "stage": _evaluate_stage(project_id, project),
        "parameters": _evaluate_parameters(project_id),
        "scenario": _evaluate_scenario(project_id, project),
        "documents": _evaluate_documents(project_id, project),
        "drafts": _evaluate_drafts(project_id, project),
        "evidence": _evaluate_evidence(project_id),
        "audit": _evaluate_audit(project_id),
        "items": [],
        "readiness_score": 0,
    }

    state["items"] = _classify_items(state)
    state["readiness_score"] = _compute_readiness_score(state)
    state["next_actions"] = _build_next_actions(state)

    return state


def _load_project(project_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM user_projects WHERE id = %s", (project_id,))
        proj = cur.fetchone()
        if not proj:
            return None
        cur.execute(
            "SELECT * FROM project_documents WHERE project_id = %s ORDER BY created_at DESC",
            (project_id,),
        )
        docs = cur.fetchall()
        result = dict(proj)
        result["documents"] = [dict(d) for d in docs]
        return result


def _evaluate_stage(project_id, project):
    with get_cursor() as cur:
        cur.execute("""
            SELECT stage, status, started_at FROM project_lifecycle
            WHERE project_id = %s ORDER BY started_at DESC LIMIT 1
        """, (project_id,))
        row = cur.fetchone()

    if not row:
        return {
            "current": "not_initialized",
            "display": "Not Initialized",
            "initialized": False,
        }

    stage_display = {
        "feasibility": "Feasibility",
        "pdd_design": "PDD Design",
        "internal_review": "Internal Review",
        "validation": "Validation",
        "registration": "Registration",
        "monitoring": "Monitoring",
        "verification": "Verification",
        "issuance": "Issuance",
    }

    return {
        "current": row["stage"],
        "display": stage_display.get(row["stage"], row["stage"]),
        "status": row["status"],
        "initialized": True,
        "started_at": str(row.get("started_at", "")),
    }


def _evaluate_parameters(project_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM project_parameters WHERE project_id = %s", (project_id,))
        params = cur.fetchall()

    if not params:
        return {
            "initialized": False,
            "total": 0,
            "configured": 0,
            "missing": 0,
            "confirmed": 0,
            "default": 0,
            "estimated": 0,
            "pct_complete": 0,
            "by_status": {},
        }

    total = len(params)
    configured = sum(1 for p in params if p.get("value") is not None)
    missing = total - configured

    by_status = {}
    for p in params:
        ps = p.get("param_status") or ("configured" if p.get("value") is not None else "missing")
        by_status[ps] = by_status.get(ps, 0) + 1

    return {
        "initialized": True,
        "total": total,
        "configured": configured,
        "missing": missing,
        "confirmed": by_status.get("confirmed", 0),
        "default": by_status.get("default", 0),
        "estimated": by_status.get("estimated", 0),
        "pct_complete": round(configured / total * 100) if total > 0 else 0,
        "by_status": by_status,
    }


def _evaluate_scenario(project_id, project):
    selected_id = project.get("selected_scenario_id")

    with get_cursor() as cur:
        cur.execute("SELECT count(*) as cnt FROM er_scenarios WHERE project_id = %s", (project_id,))
        total = cur.fetchone()["cnt"]

        cur.execute("""
            SELECT count(*) as cnt FROM er_scenarios
            WHERE project_id = %s AND scenario_purpose = 'shortlisted'
        """, (project_id,))
        shortlisted = cur.fetchone()["cnt"]

    result = {
        "total_saved": total,
        "shortlisted": shortlisted,
        "has_selected": False,
        "selected_id": selected_id,
        "selected_name": None,
        "selected_total_er": None,
        "selected_annual_er": None,
        "selected_stale": False,
    }

    if selected_id:
        with get_cursor() as cur:
            cur.execute(
                "SELECT name, results_summary FROM er_scenarios WHERE id = %s AND project_id = %s",
                (selected_id, project_id),
            )
            row = cur.fetchone()
            if row:
                result["has_selected"] = True
                result["selected_name"] = row["name"]
                summary = row.get("results_summary") or {}
                if isinstance(summary, str):
                    import json
                    try:
                        summary = json.loads(summary)
                    except Exception:
                        summary = {}
                result["selected_total_er"] = summary.get("total_er")
                result["selected_annual_er"] = summary.get("average_annual_er")
            else:
                result["selected_stale"] = True
                result["selected_id"] = None

    return result


def _evaluate_documents(project_id, project):
    docs = project.get("documents", [])
    return {
        "count": len(docs),
        "has_documents": len(docs) > 0,
    }


PROJECT_TYPE_DOC_DEFAULTS = {
    "standalone_pdd": "pdd",
    "poa_programme": "poa_dd",
    "vpa_component": "vpa_dd",
    "monitoring_report": "mr",
    "valver_report": "valver",
}


def _evaluate_drafts(project_id, project):
    project_type = project.get("project_type", "standalone_pdd")
    default_dt = PROJECT_TYPE_DOC_DEFAULTS.get(project_type, "pdd")

    with get_cursor() as cur:
        cur.execute("""
            SELECT section_id, status FROM project_write_sessions
            WHERE project_id = %s AND doc_type = %s
            ORDER BY updated_at DESC
        """, (project_id, default_dt))
        sessions = cur.fetchall()

    if not sessions:
        return {
            "has_drafts": False,
            "total_sections": 0,
            "drafted": 0,
            "approved": 0,
            "doc_type": default_dt,
        }

    seen = {}
    for s in sessions:
        sid = s["section_id"]
        if sid not in seen:
            seen[sid] = s["status"]

    drafted = sum(1 for st in seen.values() if st == "draft")
    approved = sum(1 for st in seen.values() if st == "approved")

    return {
        "has_drafts": True,
        "total_sections": len(seen),
        "drafted": drafted,
        "approved": approved,
        "doc_type": default_dt,
    }


def _evaluate_evidence(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT count(*) as cnt FROM evidence_links WHERE project_id = %s
        """, (project_id,))
        total = cur.fetchone()["cnt"]

        cur.execute("""
            SELECT count(*) as cnt FROM evidence_links
            WHERE project_id = %s AND verified = true
        """, (project_id,))
        verified = cur.fetchone()["cnt"]

        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE evidence_decision = 'pending') as pending,
                COUNT(*) FILTER (WHERE evidence_decision = 'accepted') as accepted,
                COUNT(*) FILTER (WHERE evidence_decision = 'accepted_as_reference') as reference,
                COUNT(DISTINCT param_key) FILTER (WHERE evidence_decision = 'accepted') as accepted_params
            FROM evidence_links
            WHERE project_id = %s AND evidence_type = 'parameter_value'
        """, (project_id,))
        decision_row = cur.fetchone()

    return {
        "total_links": total,
        "verified": verified,
        "has_evidence": total > 0,
        "pending": decision_row["pending"] if decision_row else 0,
        "accepted": decision_row["accepted"] if decision_row else 0,
        "reference": decision_row["reference"] if decision_row else 0,
        "accepted_params": decision_row["accepted_params"] if decision_row else 0,
    }


def _evaluate_audit(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT overall_score, risk_level, findings, created_at
            FROM audit_simulation_results
            WHERE project_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (project_id,))
        row = cur.fetchone()

    if not row:
        return {
            "has_audit": False,
            "score": None,
            "risk_level": None,
            "findings_count": 0,
        }

    findings = row.get("findings") or {}
    if isinstance(findings, str):
        import json
        try:
            findings = json.loads(findings)
        except Exception:
            findings = {}

    if isinstance(findings, list):
        car_count = sum(1 for f in findings if f.get("type", "").upper() in ("CAR",))
        cl_count = sum(1 for f in findings if f.get("type", "").upper() in ("CL",))
        fwd_count = sum(1 for f in findings if f.get("type", "").upper() in ("FWD",))
    elif isinstance(findings, dict):
        car_count = len(findings.get("CARs", findings.get("cars", [])))
        cl_count = len(findings.get("CLs", findings.get("cls", [])))
        fwd_count = len(findings.get("FWDs", findings.get("fwds", [])))
    else:
        car_count = cl_count = fwd_count = 0

    return {
        "has_audit": True,
        "score": row.get("overall_score"),
        "risk_level": row.get("risk_level"),
        "findings_count": car_count + cl_count + fwd_count,
        "cars": car_count,
        "cls": cl_count,
        "fwds": fwd_count,
        "last_run": str(row.get("created_at", "")),
    }


def _classify_items(state):
    items = []
    params = state["parameters"]
    scenario = state["scenario"]
    docs = state["documents"]
    drafts = state["drafts"]
    audit = state["audit"]
    evidence = state["evidence"]
    stage = state["stage"]
    project = state

    has_methodology = bool(state.get("standard"))

    if not has_methodology:
        items.append({
            "severity": SEVERITY_BLOCKER,
            "category": "setup",
            "message": "No standard or methodology selected",
            "detail": "Select a carbon standard and methodology before configuring parameters or running simulations.",
            "action_tab": "Setup",
        })

    if not params["initialized"]:
        items.append({
            "severity": SEVERITY_BLOCKER,
            "category": "parameters",
            "message": "Parameters not initialized",
            "detail": "Initialize methodology parameters to begin project configuration.",
            "action_tab": "Parameters",
        })
    elif params["missing"] > 0:
        sev = SEVERITY_BLOCKER if params["pct_complete"] < 50 else SEVERITY_WARNING
        items.append({
            "severity": sev,
            "category": "parameters",
            "message": f"{params['missing']} parameter{'s' if params['missing'] != 1 else ''} missing values",
            "detail": f"{params['configured']}/{params['total']} configured ({params['pct_complete']}% complete). Set measured or estimated values for accurate ER calculations.",
            "action_tab": "Parameters",
        })

    if params["default"] > 0 and params["initialized"]:
        items.append({
            "severity": SEVERITY_SUGGESTION,
            "category": "parameters",
            "message": f"{params['default']} parameter{'s' if params['default'] != 1 else ''} still using default values",
            "detail": "Consider confirming these with measured or site-specific data for more accurate projections.",
            "action_tab": "Parameters",
        })

    if params["estimated"] > 0 and params["initialized"]:
        items.append({
            "severity": SEVERITY_WARNING,
            "category": "parameters",
            "message": f"{params['estimated']} parameter{'s' if params['estimated'] != 1 else ''} based on estimates",
            "detail": "Estimated parameters may need supporting evidence for VVB validation.",
            "action_tab": "Parameters",
        })

    if scenario["total_saved"] == 0 and params["pct_complete"] >= 50:
        items.append({
            "severity": SEVERITY_WARNING,
            "category": "scenario",
            "message": "No ER scenarios saved",
            "detail": "Run and save at least one emission reduction scenario to quantify project impact.",
            "action_tab": "ER Simulator",
        })
    elif not scenario["has_selected"] and scenario["total_saved"] > 0:
        msg = "No scenario selected for PDD drafting"
        detail = f"{scenario['total_saved']} scenario{'s' if scenario['total_saved'] != 1 else ''} saved but none selected. The AI writer needs a selected scenario to include ER projections."
        if scenario.get("selected_stale"):
            msg = "Selected scenario reference is stale"
            detail = "The previously selected scenario no longer exists. Please select a new scenario for PDD drafting."
        items.append({
            "severity": SEVERITY_WARNING,
            "category": "scenario",
            "message": msg,
            "detail": detail,
            "action_tab": "ER Simulator",
        })
    elif scenario["has_selected"]:
        er_text = ""
        if scenario["selected_annual_er"]:
            er_text = f" ({scenario['selected_annual_er']:,.0f} tCO2e/yr)"
        items.append({
            "severity": SEVERITY_INSIGHT,
            "category": "scenario",
            "message": f"Selected scenario: {scenario['selected_name']}{er_text}",
            "detail": "This scenario's ER projections will be used in AI-drafted document sections.",
        })

    if scenario["shortlisted"] >= 2:
        items.append({
            "severity": SEVERITY_INSIGHT,
            "category": "scenario",
            "message": f"{scenario['shortlisted']} shortlisted scenarios available for comparison",
            "detail": "Use the Compare tab in the ER Simulator to evaluate alternatives.",
        })

    if not docs["has_documents"]:
        items.append({
            "severity": SEVERITY_SUGGESTION,
            "category": "documents",
            "message": "No supporting documents uploaded",
            "detail": "Upload KPT reports, feasibility studies, or reference documents to give the AI writer better context.",
            "action_tab": "Documents",
        })

    if not drafts["has_drafts"] and params["pct_complete"] >= 75:
        items.append({
            "severity": SEVERITY_SUGGESTION,
            "category": "drafts",
            "message": "Ready to start drafting",
            "detail": "Parameters are substantially configured. Begin drafting your document sections.",
            "action_tab": "Write / Draft",
        })
    elif drafts["has_drafts"]:
        if drafts["approved"] > 0:
            items.append({
                "severity": SEVERITY_INSIGHT,
                "category": "drafts",
                "message": f"{drafts['approved']} section{'s' if drafts['approved'] != 1 else ''} approved, {drafts['drafted']} in draft",
                "detail": f"{drafts['total_sections']} total sections drafted for {drafts['doc_type'].upper()}.",
            })
        else:
            items.append({
                "severity": SEVERITY_INSIGHT,
                "category": "drafts",
                "message": f"{drafts['total_sections']} section{'s' if drafts['total_sections'] != 1 else ''} drafted (none approved yet)",
                "detail": "Review and approve sections when ready.",
                "action_tab": "Write / Draft",
            })

    if evidence.get("pending", 0) > 0:
        pending_count = evidence["pending"]
        items.append({
            "severity": SEVERITY_WARNING,
            "category": "evidence",
            "message": f"{pending_count} evidence item{'s' if pending_count != 1 else ''} pending review",
            "detail": "Review extracted parameter evidence in the Documents tab.",
            "action_tab": "Documents",
        })

    if evidence.get("accepted_params", 0) > 0:
        items.append({
            "severity": SEVERITY_INSIGHT,
            "category": "evidence",
            "message": f"{evidence['accepted_params']} parameter{'s' if evidence['accepted_params'] != 1 else ''} backed by document evidence",
            "detail": f"{evidence.get('accepted', 0)} accepted, {evidence.get('reference', 0)} as reference.",
        })
    elif not evidence["has_evidence"] and drafts["has_drafts"]:
        items.append({
            "severity": SEVERITY_WARNING,
            "category": "evidence",
            "message": "No evidence links established",
            "detail": "Link parameters and claims to supporting documents before audit submission.",
            "action_tab": "Documents",
        })
    elif evidence["has_evidence"] and evidence["verified"] < evidence["total_links"]:
        unverified = evidence["total_links"] - evidence["verified"]
        items.append({
            "severity": SEVERITY_SUGGESTION,
            "category": "evidence",
            "message": f"{unverified} evidence link{'s' if unverified != 1 else ''} not yet verified",
            "detail": f"{evidence['verified']}/{evidence['total_links']} evidence links verified.",
        })

    if not audit["has_audit"] and drafts["has_drafts"]:
        items.append({
            "severity": SEVERITY_SUGGESTION,
            "category": "audit",
            "message": "No audit simulation run yet",
            "detail": "Run an AI audit simulation to identify compliance gaps before VVB submission.",
            "action_tab": "Audit",
        })
    elif audit["has_audit"]:
        score = audit.get("score", 0)
        risk = audit.get("risk_level", "UNKNOWN")
        if score < 60:
            items.append({
                "severity": SEVERITY_WARNING,
                "category": "audit",
                "message": f"Audit score {score}% ({risk} risk) -- {audit['cars']} CARs, {audit['cls']} CLs",
                "detail": "Address corrective action requests before submitting to VVB.",
                "action_tab": "Findings",
            })
        elif score < 80:
            items.append({
                "severity": SEVERITY_SUGGESTION,
                "category": "audit",
                "message": f"Audit score {score}% ({risk} risk) -- review {audit['findings_count']} finding{'s' if audit['findings_count'] != 1 else ''}",
                "detail": "Good progress. Address remaining findings to improve audit readiness.",
                "action_tab": "Findings",
            })
        else:
            items.append({
                "severity": SEVERITY_INSIGHT,
                "category": "audit",
                "message": f"Audit score {score}% ({risk} risk) -- {audit['findings_count']} finding{'s' if audit['findings_count'] != 1 else ''}",
                "detail": "Strong audit readiness. Review findings in detail before final submission.",
            })

    return items


def _compute_readiness_score(state):
    weights = {
        "methodology": 15,
        "parameters": 25,
        "scenario": 15,
        "documents": 10,
        "drafts": 20,
        "evidence": 5,
        "audit": 10,
    }

    score = 0

    if state.get("standard"):
        score += weights["methodology"]

    params = state["parameters"]
    if params["initialized"]:
        score += weights["parameters"] * (params["pct_complete"] / 100)

    scenario = state["scenario"]
    if scenario["has_selected"]:
        score += weights["scenario"]
    elif scenario["total_saved"] > 0:
        score += weights["scenario"] * 0.4

    if state["documents"]["has_documents"]:
        score += weights["documents"]

    drafts = state["drafts"]
    if drafts["has_drafts"]:
        total = drafts["total_sections"]
        approved = drafts["approved"]
        if total > 0:
            score += weights["drafts"] * (0.5 + 0.5 * (approved / total))

    evidence = state["evidence"]
    if evidence["has_evidence"]:
        if evidence["total_links"] > 0:
            score += weights["evidence"] * (evidence["verified"] / evidence["total_links"])

    audit = state["audit"]
    if audit["has_audit"] and audit["score"] is not None:
        score += weights["audit"] * min(audit["score"] / 100, 1.0)

    return round(score)


def _build_next_actions(state):
    actions = []

    blockers = [i for i in state["items"] if i["severity"] == SEVERITY_BLOCKER]
    warnings = [i for i in state["items"] if i["severity"] == SEVERITY_WARNING]
    suggestions = [i for i in state["items"] if i["severity"] == SEVERITY_SUGGESTION]

    for item in blockers:
        actions.append({
            "priority": "high",
            "text": item["message"],
            "detail": item["detail"],
            "tab": item.get("action_tab"),
        })

    for item in warnings:
        if len(actions) < 5:
            actions.append({
                "priority": "medium",
                "text": item["message"],
                "detail": item["detail"],
                "tab": item.get("action_tab"),
            })

    for item in suggestions:
        if len(actions) < 5:
            actions.append({
                "priority": "low",
                "text": item["message"],
                "detail": item["detail"],
                "tab": item.get("action_tab"),
            })

    return actions[:5]
