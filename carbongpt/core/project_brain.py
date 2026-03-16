"""
Project Brain — CarbonGPT orchestration layer.

Extends project_state with stale section detection, automation opportunities,
parameter outlier analysis, and proactive workflow suggestions.
"""
from __future__ import annotations
import datetime
from typing import Any

from carbongpt.repository.db import get_cursor
from carbongpt.core.project_state import evaluate_project_state
from carbongpt.core.parameter_engine import PARAMETER_DEFINITIONS, get_project_parameters


# ---------------------------------------------------------------------------
# Methodology benchmark ranges for outlier detection
# Keys are canonical param_key; values are (low_warn, high_warn) inclusive.
# Any value outside this range is flagged as an outlier.
# ---------------------------------------------------------------------------
METHODOLOGY_BENCHMARKS: dict[str, dict[str, tuple[float, float]]] = {
    "VM0050": {
        "fNRB": (0.50, 0.99),
        "NCV_baseline": (14.0, 20.0),
        "EF_CO2_baseline": (90.0, 115.0),
        "baseline_fuel_consumption": (0.2, 5.0),
        "project_fuel_consumption": (0.05, 3.0),
        "usage_rate": (0.5, 1.0),
        "leakage_discount": (0.8, 1.0),
    },
    "TPDDTEC": {
        "fNRB": (0.50, 0.99),
        "SFC_baseline": (0.4, 3.0),
        "SFC_project": (0.1, 1.5),
        "usage_rate": (0.5, 1.0),
        "leakage_discount": (0.8, 1.0),
    },
    "ACM0002": {
        "EF_grid": (0.3, 1.2),
        "EG_PJ_y": (1000.0, 500000.0),
        "lifetime_years": (10.0, 30.0),
    },
    "AMS-I.D.": {
        "EF_grid": (0.3, 1.2),
        "EG_PJ_y": (100.0, 100000.0),
        "lifetime_years": (10.0, 25.0),
    },
    "GS-MECD": {
        "eta_p": (0.5, 0.98),
        "ef_el": (0.2, 1.5),
        "tdl": (0.0, 0.2),
        "n_persons": (100.0, 1000000.0),
    },
}

# Map short methodology codes to benchmark keys
_METHODOLOGY_ALIASES: dict[str, str] = {
    "AMSID": "AMS-I.D.",
    "MECD": "GS-MECD",
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evaluate_project_brain(project_id: int) -> dict[str, Any]:
    """
    Return a rich brain state dict for a project, extending evaluate_project_state
    with orchestration-level intelligence.
    """
    state = evaluate_project_state(project_id)
    if "error" in state:
        return state

    methodology = (
        state.get("standard", "")
        or _get_project_methodology(project_id)
    )
    methodology = _METHODOLOGY_ALIASES.get(methodology, methodology)

    stale = _detect_stale_sections(project_id)
    outliers = _detect_parameter_outliers(project_id, methodology)
    evidence_opps = _detect_evidence_opportunities(project_id)
    automation = _build_automation_opportunities(state, stale, outliers, evidence_opps)
    next_best = _compute_next_best_action(state, automation, stale, outliers, evidence_opps)

    return {
        **state,
        "brain": {
            "stale_sections": stale,
            "parameter_outliers": outliers,
            "evidence_auto_apply_count": evidence_opps["auto_apply_count"],
            "evidence_pending_count": evidence_opps["pending_count"],
            "automation_opportunities": automation,
            "next_best_action": next_best,
        },
    }


# ---------------------------------------------------------------------------
# Stale section detection
# ---------------------------------------------------------------------------

def _detect_stale_sections(project_id: int) -> list[dict[str, Any]]:
    """
    Return a list of written sections where the draft is older than the most
    recent parameter update.  These sections may need re-drafting.
    """
    stale: list[dict[str, Any]] = []
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT section_id, doc_type, status, updated_at
                FROM project_write_sessions
                WHERE project_id = %s
                ORDER BY section_id, updated_at DESC
                """,
                (project_id,),
            )
            sessions = cur.fetchall()

            cur.execute(
                """
                SELECT MAX(updated_at) AS last_param_update
                FROM project_parameters
                WHERE project_id = %s
                """,
                (project_id,),
            )
            row = cur.fetchone()
            last_param_update = row["last_param_update"] if row else None

        if not last_param_update or not sessions:
            return []

        # Deduplicate: keep latest session per section_id
        seen: dict[str, dict] = {}
        for s in sessions:
            sid = s["section_id"]
            if sid not in seen:
                seen[sid] = dict(s)

        for sid, s in seen.items():
            session_updated = s.get("updated_at")
            if session_updated and isinstance(last_param_update, datetime.datetime):
                # Make both timezone-naive for comparison
                if hasattr(session_updated, "tzinfo") and session_updated.tzinfo:
                    session_updated = session_updated.replace(tzinfo=None)
                if hasattr(last_param_update, "tzinfo") and last_param_update.tzinfo:
                    last_param_update = last_param_update.replace(tzinfo=None)
                if session_updated < last_param_update:
                    delta_hours = (last_param_update - session_updated).total_seconds() / 3600
                    stale.append({
                        "section_id": sid,
                        "doc_type": s.get("doc_type", "pdd"),
                        "draft_status": s.get("status", "draft"),
                        "draft_updated_at": str(session_updated),
                        "params_updated_at": str(last_param_update),
                        "staleness_hours": round(delta_hours, 1),
                    })
    except Exception:
        pass
    return stale


# ---------------------------------------------------------------------------
# Parameter outlier detection
# ---------------------------------------------------------------------------

def _detect_parameter_outliers(project_id: int, methodology: str) -> list[dict[str, Any]]:
    """
    Compare each confirmed/measured parameter against methodology benchmarks.
    Returns entries that are outside the expected range.
    """
    outliers: list[dict[str, Any]] = []
    benchmarks = METHODOLOGY_BENCHMARKS.get(methodology, {})
    if not benchmarks:
        return []

    try:
        params = get_project_parameters(project_id)
        for p in params:
            key = p.get("param_key")
            if key not in benchmarks:
                continue
            raw_val = p.get("value")
            if raw_val is None:
                continue
            try:
                val = float(raw_val)
            except (ValueError, TypeError):
                continue

            lo, hi = benchmarks[key]
            if val < lo or val > hi:
                # Look up description from PARAMETER_DEFINITIONS
                defn = PARAMETER_DEFINITIONS.get(key, {})
                param_name = p.get("param_name") or defn.get("param_name", key)
                unit = p.get("unit") or defn.get("unit", "")
                direction = "low" if val < lo else "high"
                outliers.append({
                    "param_key": key,
                    "param_name": param_name,
                    "value": val,
                    "unit": unit,
                    "expected_range": (lo, hi),
                    "direction": direction,
                    "param_status": p.get("param_status", "default"),
                    "source_type": p.get("source_type", "default"),
                    "message": (
                        f"{param_name} = {val:g} {unit} is {direction} relative to "
                        f"the typical range [{lo:g}, {hi:g}] for {methodology}."
                    ),
                })
    except Exception:
        pass
    return outliers


# ---------------------------------------------------------------------------
# Evidence auto-apply opportunities
# ---------------------------------------------------------------------------

def _detect_evidence_opportunities(project_id: int) -> dict[str, Any]:
    """
    Count pending evidence links that could be auto-applied to parameters.
    """
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE evidence_decision = 'pending') AS pending,
                    COUNT(*) FILTER (
                        WHERE evidence_decision = 'pending'
                          AND extracted_value IS NOT NULL
                          AND param_key IS NOT NULL
                    ) AS auto_apply_eligible
                FROM evidence_links
                WHERE project_id = %s AND evidence_type = 'parameter_value'
                """,
                (project_id,),
            )
            row = cur.fetchone()
            return {
                "pending_count": int(row["pending"]) if row else 0,
                "auto_apply_count": int(row["auto_apply_eligible"]) if row else 0,
            }
    except Exception:
        return {"pending_count": 0, "auto_apply_count": 0}


# ---------------------------------------------------------------------------
# Automation opportunities
# ---------------------------------------------------------------------------

def _build_automation_opportunities(
    state: dict,
    stale: list,
    outliers: list,
    evidence_opps: dict,
) -> list[dict[str, Any]]:
    """
    Return a prioritized list of automation opportunities.
    Each entry has: id, label, description, priority (high/medium/low), action_type.
    """
    opps: list[dict[str, Any]] = []

    # Evidence quick-apply
    n_apply = evidence_opps.get("auto_apply_count", 0)
    if n_apply > 0:
        opps.append({
            "id": "evidence_quick_apply",
            "label": f"Apply {n_apply} pending evidence value(s) to parameters",
            "description": (
                f"{n_apply} extracted parameter value(s) from uploaded documents "
                "are ready to apply — confirm them in the Parameters tab."
            ),
            "priority": "high",
            "action_type": "evidence_apply",
            "action_tab": "Parameters",
            "count": n_apply,
        })

    # Stale sections
    n_stale = len(stale)
    if n_stale > 0:
        stale_ids = ", ".join(s["section_id"] for s in stale[:3])
        opps.append({
            "id": "redraft_stale_sections",
            "label": f"Re-draft {n_stale} section(s) stale since last parameter update",
            "description": (
                f"Section(s) {stale_ids}{'...' if n_stale > 3 else ''} "
                "were written before the most recent parameter changes. "
                "Re-drafting will ensure the PDD reflects current values."
            ),
            "priority": "medium",
            "action_type": "redraft",
            "action_tab": "Write",
            "count": n_stale,
        })

    # Parameter outliers
    if outliers:
        n_out = len(outliers)
        opps.append({
            "id": "review_outlier_params",
            "label": f"Review {n_out} parameter(s) outside typical range",
            "description": (
                f"{n_out} parameter(s) have values outside the expected range for this methodology. "
                "Review them in the Parameters tab before running ER simulations."
            ),
            "priority": "medium",
            "action_type": "review_parameters",
            "action_tab": "Parameters",
            "count": n_out,
        })

    # Draft ER section after scenario selection
    scenario = state.get("scenario", {})
    drafts = state.get("drafts", {})
    if scenario.get("has_scenarios") and not drafts.get("has_drafts"):
        opps.append({
            "id": "draft_er_quantification",
            "label": "Draft the ER quantification section of your PDD",
            "description": (
                "You have a saved scenario but no PDD sections drafted yet. "
                "Start drafting in the Write tab."
            ),
            "priority": "medium",
            "action_type": "draft_section",
            "action_tab": "Write",
            "count": 0,
        })

    # Missing parameters
    params_state = state.get("parameters", {})
    missing = params_state.get("missing", 0)
    if missing > 0:
        opps.append({
            "id": "fill_missing_params",
            "label": f"Complete {missing} missing parameter(s)",
            "description": (
                f"{missing} parameter(s) have no value set. "
                "Upload project documents or enter values manually in the Parameters tab."
            ),
            "priority": "high",
            "action_type": "fill_parameters",
            "action_tab": "Parameters",
            "count": missing,
        })

    # Run ER simulation
    if params_state.get("initialized") and not scenario.get("has_scenarios"):
        opps.append({
            "id": "run_er_simulation",
            "label": "Run your first ER simulation",
            "description": (
                "Parameters are initialized. Run an ER simulation to estimate "
                "emission reductions and generate a workbook."
            ),
            "priority": "low",
            "action_type": "run_simulation",
            "action_tab": "ER Simulator",
            "count": 0,
        })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    opps.sort(key=lambda o: priority_order.get(o["priority"], 9))

    return opps


# ---------------------------------------------------------------------------
# Next-best action
# ---------------------------------------------------------------------------

def _compute_next_best_action(
    state: dict,
    automation: list,
    stale: list,
    outliers: list,
    evidence_opps: dict,
) -> dict[str, Any] | None:
    """Return the single highest-priority action for the Copilot panel."""
    if automation:
        top = automation[0]
        return {
            "label": top["label"],
            "description": top["description"],
            "action_type": top["action_type"],
            "action_tab": top.get("action_tab"),
            "priority": top["priority"],
        }
    # Fallback from base state next_actions
    next_actions = state.get("next_actions", [])
    if next_actions:
        a = next_actions[0]
        return {
            "label": a["text"],
            "description": a.get("detail", ""),
            "action_type": "navigate",
            "action_tab": a.get("tab"),
            "priority": a.get("priority", "medium"),
        }
    return None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_project_methodology(project_id: int) -> str:
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT methodology FROM user_projects WHERE id = %s", (project_id,)
            )
            row = cur.fetchone()
            return (row["methodology"] or "") if row else ""
    except Exception:
        return ""
