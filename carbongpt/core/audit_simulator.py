import logging
import json
from carbongpt.repository.db import get_cursor
from carbongpt.core.parameter_engine import get_project_parameters, validate_all_parameters, get_parameter_summary
from carbongpt.core.evidence_engine import get_evidence_completeness
from carbongpt.core.er_simulator import run_scenario

logger = logging.getLogger(__name__)


def run_audit_simulation(project_id):
    findings = []
    parameter_issues = []
    evidence_gaps = []
    consistency_issues = []
    compliance_issues = []
    recommendations = []

    with get_cursor() as cur:
        cur.execute("SELECT * FROM user_projects WHERE id = %s", (project_id,))
        project = cur.fetchone()
        if not project:
            return {"error": "Project not found"}

    _check_project_completeness(project, findings, compliance_issues)
    _check_parameters(project_id, findings, parameter_issues)
    _check_evidence(project_id, findings, evidence_gaps)
    _check_section_consistency(project_id, findings, consistency_issues)
    _check_er_consistency(project_id, project, findings, consistency_issues)
    _generate_recommendations(findings, parameter_issues, evidence_gaps, consistency_issues, recommendations)

    total_issues = len(findings)
    critical = len([f for f in findings if f.get("severity") == "critical"])
    high = len([f for f in findings if f.get("severity") == "high"])
    medium = len([f for f in findings if f.get("severity") == "medium"])
    low = len([f for f in findings if f.get("severity") == "low"])

    if critical > 0:
        risk_level = "CRITICAL"
        score = max(0, 30 - critical * 10)
    elif high > 2:
        risk_level = "HIGH"
        score = max(20, 50 - high * 5)
    elif medium > 5:
        risk_level = "MEDIUM"
        score = max(40, 70 - medium * 3)
    elif total_issues > 0:
        risk_level = "LOW"
        score = max(60, 90 - total_issues * 2)
    else:
        risk_level = "LOW"
        score = 95

    summary = (
        f"Audit simulation identified {total_issues} potential findings: "
        f"{critical} critical, {high} high, {medium} medium, {low} low severity. "
        f"Overall risk: {risk_level}."
    )

    result = {
        "overall_score": score,
        "risk_level": risk_level,
        "findings": findings,
        "summary": summary,
        "parameter_issues": parameter_issues,
        "evidence_gaps": evidence_gaps,
        "consistency_issues": consistency_issues,
        "compliance_issues": compliance_issues,
        "recommendations": recommendations,
        "counts": {"total": total_issues, "critical": critical, "high": high, "medium": medium, "low": low},
    }

    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO audit_simulation_results
            (project_id, simulation_type, overall_score, risk_level,
             findings, summary, parameter_issues, evidence_gaps,
             consistency_issues, compliance_issues, recommendations)
            VALUES (%s, 'full', %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            project_id, score, risk_level,
            json.dumps(findings), summary,
            json.dumps(parameter_issues), json.dumps(evidence_gaps),
            json.dumps(consistency_issues), json.dumps(compliance_issues),
            json.dumps(recommendations),
        ))
        result["simulation_id"] = cur.fetchone()["id"]

    return result


def get_simulation_history(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, simulation_type, overall_score, risk_level, summary, simulated_at
            FROM audit_simulation_results
            WHERE project_id = %s ORDER BY simulated_at DESC
        """, (project_id,))
        return cur.fetchall()


def get_simulation_detail(simulation_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM audit_simulation_results WHERE id = %s", (simulation_id,))
        return cur.fetchone()


def _check_project_completeness(project, findings, compliance_issues):
    if not project.get("methodology"):
        findings.append({
            "type": "CAR", "severity": "critical", "category": "project_setup",
            "title": "Methodology not specified",
            "description": "No methodology has been selected for this project. A methodology is required for PDD development.",
        })

    if not project.get("country"):
        findings.append({
            "type": "CL", "severity": "high", "category": "project_setup",
            "title": "Project country not specified",
            "description": "The project country is required for determining fNRB defaults and other national parameters.",
        })

    if not project.get("crediting_period_start"):
        findings.append({
            "type": "CL", "severity": "medium", "category": "project_setup",
            "title": "Crediting period start date not set",
            "description": "A crediting period start date should be specified.",
        })

    intake = project.get("project_intake") or {}
    if not intake:
        findings.append({
            "type": "CAR", "severity": "high", "category": "project_setup",
            "title": "Project intake not completed",
            "description": "The project intake form has not been filled. Key project parameters and information are missing.",
        })


def _check_parameters(project_id, findings, parameter_issues):
    validation = validate_all_parameters(project_id)
    param_summary = get_parameter_summary(project_id)

    if not param_summary or param_summary["total"] == 0:
        findings.append({
            "type": "CAR", "severity": "critical", "category": "parameters",
            "title": "No parameters initialized",
            "description": "Project parameters have not been initialized. Cannot verify methodology compliance without parameter values.",
        })
        return

    pending_count = param_summary.get("pending", 0)
    invalid_count = param_summary.get("invalid", 0)

    if invalid_count > 0:
        findings.append({
            "type": "CAR", "severity": "high", "category": "parameters",
            "title": f"{invalid_count} parameter(s) have invalid values",
            "description": "Some parameters are outside their allowed range or have incorrect data types.",
        })

    if pending_count > 0:
        findings.append({
            "type": "CL", "severity": "high" if pending_count > 3 else "medium",
            "category": "parameters",
            "title": f"{pending_count} parameter(s) have no value",
            "description": "Some required parameters have not been set. These must be provided before the PDD can be completed.",
        })

    for issue in validation.get("issues", []):
        parameter_issues.append({
            "param_key": issue["param_key"],
            "status": issue["status"],
            "message": issue.get("message", ""),
        })

    defaults_count = param_summary.get("defaults", 0)
    if defaults_count > param_summary["total"] * 0.7:
        findings.append({
            "type": "observation", "severity": "medium", "category": "parameters",
            "title": "Most parameters use default values",
            "description": f"{defaults_count} of {param_summary['total']} parameters use default values. Consider using project-specific measured values where possible for greater accuracy.",
        })


def _check_evidence(project_id, findings, evidence_gaps):
    try:
        completeness = get_evidence_completeness(project_id)
    except Exception:
        return

    param_score = completeness.get("parameters", {}).get("score", 0)
    needs_evidence = completeness.get("parameters", {}).get("needs_evidence", [])

    if param_score < 30:
        findings.append({
            "type": "CAR", "severity": "high", "category": "evidence",
            "title": "Very low evidence coverage",
            "description": f"Only {param_score}% of parameters have supporting evidence. A VVB will require evidence for all key parameters.",
        })
    elif param_score < 60:
        findings.append({
            "type": "CL", "severity": "medium", "category": "evidence",
            "title": "Incomplete evidence coverage",
            "description": f"{param_score}% of parameters have supporting evidence. Additional documentation is recommended.",
        })

    for p in needs_evidence[:5]:
        evidence_gaps.append({
            "param_key": p["param_key"],
            "param_name": p["param_name"],
            "source_type": p["source_type"],
        })


def _check_section_consistency(project_id, findings, consistency_issues):
    with get_cursor() as cur:
        cur.execute("""
            SELECT section_id, section_title, user_text, generated_text
            FROM project_write_sessions
            WHERE project_id = %s AND (user_text IS NOT NULL OR generated_text IS NOT NULL)
            ORDER BY section_id
        """, (project_id,))
        sections = cur.fetchall()

    if not sections:
        findings.append({
            "type": "CL", "severity": "medium", "category": "sections",
            "title": "No document sections drafted",
            "description": "No PDD sections have been drafted yet. Cannot perform consistency analysis.",
        })
        return

    total = len(sections)
    drafted = len([s for s in sections if s.get("user_text") or s.get("generated_text")])

    if drafted < total * 0.5:
        findings.append({
            "type": "observation", "severity": "low", "category": "sections",
            "title": f"Only {drafted} of {total} sections drafted",
            "description": "Many sections are still empty. Complete all sections before submission.",
        })


def _check_er_consistency(project_id, project, findings, consistency_issues):
    try:
        result = run_scenario(project_id)
    except Exception:
        return

    if "error" in result:
        return

    total_er = result["summary"].get("total_er", 0)
    annual_er = result["summary"].get("average_annual_er", 0)

    if total_er <= 0:
        findings.append({
            "type": "CAR", "severity": "critical", "category": "er_calculation",
            "title": "Emission reductions are zero or negative",
            "description": f"Calculated total ER = {total_er} tCO2e. This indicates a configuration issue with parameters.",
        })
    elif annual_er < 100:
        findings.append({
            "type": "observation", "severity": "medium", "category": "er_calculation",
            "title": "Very low emission reductions",
            "description": f"Average annual ER = {annual_er} tCO2e. This may indicate parameter issues or a very small project.",
        })


def _generate_recommendations(findings, parameter_issues, evidence_gaps, consistency_issues, recommendations):
    categories = set(f.get("category") for f in findings)

    if "parameters" in categories:
        recommendations.append("Complete all parameter values, especially those marked as pending or invalid.")

    if "evidence" in categories:
        recommendations.append("Upload supporting documents and link them to parameters as evidence.")

    if "er_calculation" in categories:
        recommendations.append("Review ER calculation parameters. Ensure baseline and project fuel consumption values are correct.")

    if "project_setup" in categories:
        recommendations.append("Complete the project intake form with all required project details.")

    if "sections" in categories:
        recommendations.append("Draft all required PDD sections before running the audit simulation again.")

    if not findings:
        recommendations.append("Project appears ready for internal review. Consider running a full AI review of all sections.")
