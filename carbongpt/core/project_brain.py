"""
Project Brain — CarbonGPT orchestration layer.

Provides a deep project intelligence model including:
- True 7-stage project model derived from actual data state
- Methodology-aware required parameters and blocker detection
- Cross-module state synthesis (scenario drift, evidence coverage, audit linkage)
- Proactive AI workflow signals
- Priority-ranked automation opportunities
- Stage-gated next-best-action
"""
from __future__ import annotations
import datetime
import json
from typing import Any

from carbongpt.repository.db import get_cursor
from carbongpt.core.project_state import evaluate_project_state
from carbongpt.core.parameter_engine import PARAMETER_DEFINITIONS, get_project_parameters


# ── Stage constants ────────────────────────────────────────────────────────
STAGE_SETUP = "setup"                      # No methodology/country set
STAGE_PARAMETERIZATION = "parameterization"  # Methodology set, params < 75 % complete
STAGE_SIMULATION = "simulation"            # Params ≥ 75 %, no approved scenario
STAGE_DRAFTING = "drafting"               # Has scenarios, drafting in progress
STAGE_REVIEW = "review"                   # Drafts exist, no audit run yet
STAGE_AUDIT_PREP = "audit_prep"           # Audit run but score < 80 or CARs open
STAGE_SUBMISSION_READY = "submission_ready"  # Audit ≥ 80, no open CARs

STAGE_LABELS = {
    STAGE_SETUP: "Setup",
    STAGE_PARAMETERIZATION: "Parameterization",
    STAGE_SIMULATION: "Simulation",
    STAGE_DRAFTING: "Drafting",
    STAGE_REVIEW: "Review",
    STAGE_AUDIT_PREP: "Audit Prep",
    STAGE_SUBMISSION_READY: "Submission Ready",
}

# Five-phase pipeline (what shows in the progress strip)
PIPELINE_PHASES = [
    ("Define",    [STAGE_SETUP]),
    ("Quantify",  [STAGE_PARAMETERIZATION, STAGE_SIMULATION]),
    ("Draft",     [STAGE_DRAFTING, STAGE_REVIEW]),
    ("Validate",  [STAGE_AUDIT_PREP]),
    ("Submit",    [STAGE_SUBMISSION_READY]),
]

# ── Methodology-aware required parameter sets ─────────────────────────────
# param_key → human label.  Checked for missing/default status.
METHODOLOGY_REQUIRED_PARAMS: dict[str, dict[str, str]] = {
    "VM0050": {
        "fNRB": "Fraction non-renewable biomass (fNRB)",
        "NCV_baseline": "Baseline fuel net calorific value",
        "EF_CO2_baseline": "Baseline CO2 emission factor",
        "baseline_fuel_consumption": "Baseline fuel consumption",
        "project_fuel_consumption": "Project fuel consumption",
        "num_devices": "Number of devices deployed",
        "usage_rate": "Device usage rate",
        "leakage_discount": "Leakage discount factor",
    },
    "TPDDTEC": {
        "fNRB": "Fraction non-renewable biomass (fNRB)",
        "SFC_baseline": "Specific fuel consumption (baseline)",
        "SFC_project": "Specific fuel consumption (project)",
        "NCV_baseline": "Baseline fuel net calorific value",
        "EF_CO2_baseline": "Baseline CO2 emission factor",
        "num_devices": "Number of devices deployed",
        "usage_rate": "Device usage rate",
        "leakage_discount": "Leakage discount factor",
    },
    "ACM0002": {
        "EF_grid": "Grid emission factor",
        "EG_PJ_y": "Annual electricity generation (project)",
        "lifetime_years": "Plant lifetime",
    },
    "AMS-I.D.": {
        "EF_grid": "Grid emission factor",
        "EG_PJ_y": "Annual electricity generation (project)",
        "lifetime_years": "Plant lifetime",
    },
    "GS-MECD": {
        "n_persons": "Number of persons served",
        "eg_p_mwh_annual": "Annual project electricity (MWh/yr)",
        "ef_el": "Grid emission factor (tCO2e/MWh)",
        "eta_p": "Project device efficiency",
        "tdl": "Transmission and distribution losses",
    },
}

# Alias resolution
_METH_ALIASES: dict[str, str] = {
    "AMSID": "AMS-I.D.",
    "MECD": "GS-MECD",
    "TPDDTEC/VM0050": "TPDDTEC",
}

# Benchmark ranges per methodology — (low_warn, high_warn)
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
        "n_persons": (100.0, 1_000_000.0),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# Public entry point
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_project_brain(project_id: int) -> dict[str, Any]:
    """Return a comprehensive brain-state dict for a project."""
    state = evaluate_project_state(project_id)
    if "error" in state:
        return state

    methodology = _resolve_methodology(state, project_id)
    country     = state.get("country", "") or _get_project_field(project_id, "country")

    # ── Core sub-evaluations ───────────────────────────────────────────────
    derived_stage  = _derive_project_stage(state)
    meth_blockers  = _methodology_blockers(project_id, methodology, state)
    cross          = _cross_module_synthesis(project_id, state)
    stale          = _detect_stale_sections(project_id)
    outliers       = _detect_parameter_outliers(project_id, methodology)
    evidence_opps  = _detect_evidence_opportunities(project_id)

    # ── V2: deeper knowledge-source diagnostics ────────────────────────────
    pack_context        = _fetch_pack_context(methodology)
    comparable          = _benchmark_comparable_projects(methodology, country)
    param_confidence    = _parameter_source_confidence(project_id)
    pack_warnings       = _pack_benchmark_warnings(project_id, methodology, pack_context)
    meth_version        = _methodology_version_check(methodology, pack_context)
    audit_risks         = _audit_risk_signals(state, meth_blockers, cross, pack_warnings, evidence_opps)
    missing_evidence    = _build_missing_evidence_list(project_id, cross)

    tab_badges = _compute_tab_badges(
        state, meth_blockers, stale, outliers, cross, audit_risks, pack_warnings
    )
    automation = _build_automation_opportunities(
        state, derived_stage, stale, outliers, evidence_opps,
        meth_blockers, cross, pack_warnings, audit_risks, meth_version, param_confidence
    )
    next_best    = _compute_next_best_action(state, derived_stage, automation)
    pipeline_pos = _compute_pipeline_position(derived_stage)

    return {
        **state,
        "brain": {
            # Stage model
            "derived_stage": derived_stage,
            "derived_stage_label": STAGE_LABELS.get(derived_stage, derived_stage),
            "pipeline_phase_index": pipeline_pos,
            # Methodology
            "methodology": methodology,
            "methodology_blockers": meth_blockers,
            "methodology_version": meth_version,
            # Cross-module
            "cross": cross,
            # Per-detector outputs
            "stale_sections": stale,
            "parameter_outliers": outliers,
            "evidence_auto_apply_count": evidence_opps["auto_apply_count"],
            "evidence_pending_count": evidence_opps["pending_count"],
            "evidence_coverage_rate": cross.get("evidence_coverage_rate", 0),
            "missing_evidence": missing_evidence,
            # V2 knowledge diagnostics
            "pack_context": pack_context,
            "comparable_projects": comparable,
            "parameter_confidence": param_confidence,
            "pack_benchmark_warnings": pack_warnings,
            "audit_risk_signals": audit_risks,
            # Orchestration
            "automation_opportunities": automation,
            "next_best_action": next_best,
            "tab_badges": tab_badges,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# Stage model
# ══════════════════════════════════════════════════════════════════════════════

def _derive_project_stage(state: dict) -> str:
    """Derive the true project stage from actual data, independent of lifecycle table."""
    methodology = state.get("standard", "")
    params       = state.get("parameters", {})
    scenario     = state.get("scenario", {})
    drafts       = state.get("drafts", {})
    audit        = state.get("audit", {})

    if not methodology:
        return STAGE_SETUP

    if not params.get("initialized") or params.get("pct_complete", 0) < 75:
        return STAGE_PARAMETERIZATION

    if scenario.get("total_saved", 0) == 0 or not scenario.get("has_selected"):
        return STAGE_SIMULATION

    if not drafts.get("has_drafts"):
        return STAGE_DRAFTING

    if not audit.get("has_audit"):
        return STAGE_REVIEW

    score = audit.get("score") or 0
    cars  = audit.get("cars", 0)
    if score >= 80 and cars == 0:
        return STAGE_SUBMISSION_READY

    return STAGE_AUDIT_PREP


def _compute_pipeline_position(stage: str) -> int:
    """Return 0-based phase index in PIPELINE_PHASES."""
    for idx, (_, stages) in enumerate(PIPELINE_PHASES):
        if stage in stages:
            return idx
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# Methodology-aware blockers
# ══════════════════════════════════════════════════════════════════════════════

def _methodology_blockers(
    project_id: int, methodology: str, state: dict
) -> list[dict[str, Any]]:
    """
    Return blockers that are specific to the active methodology.
    Each entry: {param_key, param_name, issue, severity}
    """
    blockers: list[dict[str, Any]] = []
    required = METHODOLOGY_REQUIRED_PARAMS.get(methodology, {})
    if not required:
        return []

    try:
        params = get_project_parameters(project_id)
        param_map = {p["param_key"]: p for p in params}
    except Exception:
        return []

    for key, label in required.items():
        p = param_map.get(key)
        if p is None:
            blockers.append({
                "param_key": key,
                "param_name": label,
                "issue": "not_initialized",
                "severity": "blocker",
                "message": f"{label} ({key}) is required for {methodology} but not yet initialized.",
            })
            continue

        val  = p.get("value")
        stat = p.get("param_status", "missing")

        if val is None:
            blockers.append({
                "param_key": key,
                "param_name": label,
                "issue": "missing_value",
                "severity": "blocker",
                "message": f"{label} ({key}) has no value. {methodology} cannot run an ER calculation without it.",
            })
        elif stat == "default":
            blockers.append({
                "param_key": key,
                "param_name": label,
                "issue": "using_default",
                "severity": "warning",
                "message": f"{label} ({key}) is still at its default value. Measure or source a site-specific value for accurate results.",
            })
        elif stat == "estimated":
            blockers.append({
                "param_key": key,
                "param_name": label,
                "issue": "estimated",
                "severity": "caution",
                "message": f"{label} ({key}) is estimated. Link supporting evidence to satisfy VVB review.",
            })

    return blockers


# ══════════════════════════════════════════════════════════════════════════════
# Cross-module synthesis
# ══════════════════════════════════════════════════════════════════════════════

def _cross_module_synthesis(project_id: int, state: dict) -> dict[str, Any]:
    """
    Detect conditions that span multiple modules.
    Returns a dict of synthesis signals.
    """
    result: dict[str, Any] = {}

    # 1. Scenario param drift: selected scenario created before last param change
    result.update(_check_scenario_param_drift(project_id, state))

    # 2. Audit re-run need: params changed after last audit run
    result.update(_check_audit_rerun_needed(project_id, state))

    # 3. Evidence coverage rate: % of numeric params with at least one accepted evidence
    result.update(_check_evidence_coverage(project_id, state))

    # 4. Draft coverage rate: % of required sections drafted
    result.update(_check_draft_coverage(project_id, state))

    # 5. Audit unresolved CARs referencing specific parameters
    result.update(_check_audit_car_params(project_id, state))

    return result


def _check_scenario_param_drift(project_id: int, state: dict) -> dict[str, Any]:
    """Detect if the selected scenario is older than the most recent param update."""
    scenario = state.get("scenario", {})
    if not scenario.get("has_selected"):
        return {"scenario_param_drift": False}

    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT created_at FROM er_scenarios WHERE id = %s",
                (scenario["selected_id"],),
            )
            row = cur.fetchone()
            scenario_ts = row["created_at"] if row else None

            cur.execute(
                "SELECT MAX(updated_at) AS last_update FROM project_parameters WHERE project_id = %s",
                (project_id,),
            )
            row2 = cur.fetchone()
            param_ts = row2["last_update"] if row2 else None

        if scenario_ts and param_ts:
            s = _strip_tz(scenario_ts)
            p = _strip_tz(param_ts)
            if p > s:
                delta_h = (p - s).total_seconds() / 3600
                return {
                    "scenario_param_drift": True,
                    "scenario_param_drift_hours": round(delta_h, 1),
                }
    except Exception:
        pass
    return {"scenario_param_drift": False}


def _check_audit_rerun_needed(project_id: int, state: dict) -> dict[str, Any]:
    """Detect if params changed after the last audit run."""
    audit = state.get("audit", {})
    if not audit.get("has_audit") or not audit.get("last_run"):
        return {"audit_rerun_needed": False}

    try:
        audit_ts = _parse_ts(audit["last_run"])
        with get_cursor() as cur:
            cur.execute(
                "SELECT MAX(updated_at) AS last_update FROM project_parameters WHERE project_id = %s",
                (project_id,),
            )
            row = cur.fetchone()
            param_ts = row["last_update"] if row else None

        if param_ts:
            p = _strip_tz(param_ts)
            a = _strip_tz(audit_ts)
            if p > a:
                delta_h = (p - a).total_seconds() / 3600
                return {
                    "audit_rerun_needed": True,
                    "audit_rerun_hours_since": round(delta_h, 1),
                }
    except Exception:
        pass
    return {"audit_rerun_needed": False}


def _check_evidence_coverage(project_id: int, state: dict) -> dict[str, Any]:
    """
    Compute evidence coverage: % of numeric required params backed by accepted evidence.
    """
    try:
        with get_cursor() as cur:
            # Count numeric confirmed/measured params
            cur.execute(
                """
                SELECT param_key
                FROM project_parameters
                WHERE project_id = %s AND data_type = 'number' AND value IS NOT NULL
                """,
                (project_id,),
            )
            numeric_params = {r["param_key"] for r in cur.fetchall()}

            if not numeric_params:
                return {"evidence_coverage_rate": 0, "evidence_uncovered_params": []}

            # Count how many of these have accepted evidence
            cur.execute(
                """
                SELECT DISTINCT param_key
                FROM evidence_links
                WHERE project_id = %s
                  AND evidence_decision IN ('accepted', 'accepted_as_reference')
                  AND param_key IS NOT NULL
                """,
                (project_id,),
            )
            covered = {r["param_key"] for r in cur.fetchall()}

        uncovered = sorted(numeric_params - covered)
        rate = round(len(covered) / len(numeric_params) * 100) if numeric_params else 0
        return {
            "evidence_coverage_rate": rate,
            "evidence_uncovered_params": uncovered[:10],  # top 10
            "evidence_covered_count": len(covered),
            "evidence_total_numeric": len(numeric_params),
        }
    except Exception:
        return {"evidence_coverage_rate": 0, "evidence_uncovered_params": []}


def _check_draft_coverage(project_id: int, state: dict) -> dict[str, Any]:
    """
    Compute section draft coverage rate.
    """
    try:
        with get_cursor() as cur:
            # Expected sections for this project type
            cur.execute(
                "SELECT project_type FROM user_projects WHERE id = %s",
                (project_id,),
            )
            row = cur.fetchone()
            project_type = row["project_type"] if row else "standalone_pdd"

            # Sections drafted
            cur.execute(
                """
                SELECT COUNT(DISTINCT section_id) AS cnt
                FROM project_write_sessions
                WHERE project_id = %s
                """,
                (project_id,),
            )
            drafted_count = cur.fetchone()["cnt"]

        # Rough expected section counts by doc type
        expected_by_type = {
            "standalone_pdd": 12,
            "poa_programme": 10,
            "vpa_component": 8,
            "monitoring_report": 6,
            "validation_report": 10,
        }
        expected = expected_by_type.get(project_type, 12)
        rate = round(min(drafted_count / expected, 1.0) * 100)
        return {
            "draft_coverage_rate": rate,
            "draft_sections_done": drafted_count,
            "draft_sections_expected": expected,
        }
    except Exception:
        return {"draft_coverage_rate": 0, "draft_sections_done": 0, "draft_sections_expected": 12}


def _check_audit_car_params(project_id: int, state: dict) -> dict[str, Any]:
    """
    Extract which parameter keys are referenced in open audit CARs.
    """
    audit = state.get("audit", {})
    if not audit.get("has_audit") or audit.get("cars", 0) == 0:
        return {"audit_car_params": []}

    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT findings FROM audit_simulation_results WHERE project_id = %s ORDER BY created_at DESC LIMIT 1",
                (project_id,),
            )
            row = cur.fetchone()
        if not row:
            return {"audit_car_params": []}

        findings_raw = row.get("findings") or {}
        if isinstance(findings_raw, str):
            try:
                findings_raw = json.loads(findings_raw)
            except Exception:
                findings_raw = {}

        car_list = []
        if isinstance(findings_raw, dict):
            car_list = findings_raw.get("CARs", findings_raw.get("cars", []))
        elif isinstance(findings_raw, list):
            car_list = [f for f in findings_raw if f.get("type", "").upper() == "CAR"]

        # Scan CAR descriptions for parameter key mentions
        known_keys = {p["param_key"] for p in get_project_parameters(project_id)}
        mentioned: list[str] = []
        for car in car_list:
            desc = str(car.get("description", "")) + " " + str(car.get("detail", ""))
            for key in known_keys:
                if key in desc and key not in mentioned:
                    mentioned.append(key)

        return {"audit_car_params": mentioned}
    except Exception:
        return {"audit_car_params": []}


# ══════════════════════════════════════════════════════════════════════════════
# Stale section detection
# ══════════════════════════════════════════════════════════════════════════════

def _detect_stale_sections(project_id: int) -> list[dict[str, Any]]:
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
                "SELECT MAX(updated_at) AS last_update FROM project_parameters WHERE project_id = %s",
                (project_id,),
            )
            row = cur.fetchone()
            last_param_update = row["last_update"] if row else None

        if not last_param_update or not sessions:
            return []

        seen: dict[str, dict] = {}
        for s in sessions:
            sid = s["section_id"]
            if sid not in seen:
                seen[sid] = dict(s)

        lp = _strip_tz(last_param_update)
        for sid, s in seen.items():
            su = _strip_tz(s.get("updated_at"))
            if su and lp and su < lp:
                delta_h = (lp - su).total_seconds() / 3600
                stale.append({
                    "section_id": sid,
                    "doc_type": s.get("doc_type", "pdd"),
                    "draft_status": s.get("status", "draft"),
                    "staleness_hours": round(delta_h, 1),
                })
    except Exception:
        pass
    return stale


# ══════════════════════════════════════════════════════════════════════════════
# Parameter outlier detection
# ══════════════════════════════════════════════════════════════════════════════

def _detect_parameter_outliers(project_id: int, methodology: str) -> list[dict[str, Any]]:
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
                        f"the typical range [{lo:g}–{hi:g}] for {methodology}."
                    ),
                })
    except Exception:
        pass
    return outliers


# ══════════════════════════════════════════════════════════════════════════════
# Evidence opportunities
# ══════════════════════════════════════════════════════════════════════════════

def _detect_evidence_opportunities(project_id: int) -> dict[str, Any]:
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
                    ) AS auto_apply_eligible,
                    COUNT(*) FILTER (
                        WHERE evidence_decision = 'pending'
                          AND confidence >= 0.80
                          AND extracted_value IS NOT NULL
                    ) AS high_conf
                FROM evidence_links
                WHERE project_id = %s AND evidence_type = 'parameter_value'
                """,
                (project_id,),
            )
            row = cur.fetchone()
            return {
                "pending_count": int(row["pending"]) if row else 0,
                "auto_apply_count": int(row["auto_apply_eligible"]) if row else 0,
                "high_confidence_count": int(row["high_conf"]) if row else 0,
            }
    except Exception:
        return {"pending_count": 0, "auto_apply_count": 0, "high_confidence_count": 0}


# ══════════════════════════════════════════════════════════════════════════════
# V2: Knowledge-source diagnostics
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_pack_context(methodology: str) -> dict[str, Any]:
    """
    Fetch methodology pack status and quality metrics.
    Returns metadata about the Pack Manager's knowledge base for this methodology.
    """
    if not methodology:
        return {"has_pack": False}
    try:
        with get_cursor() as cur:
            # Find the best (most recent indexed) pack for this methodology
            cur.execute(
                """
                SELECT id, methodology_code, methodology_version, indexing_status,
                       pdd_count, mr_count, validation_count, tool_doc_count,
                       target_pdd_count, readiness_score, readiness_gates_passed,
                       last_updated
                FROM methodology_packs
                WHERE UPPER(methodology_code) = UPPER(%s)
                ORDER BY
                    CASE indexing_status WHEN 'indexed' THEN 0 WHEN 'ready_for_indexing' THEN 1 ELSE 2 END,
                    last_updated DESC
                LIMIT 1
                """,
                (methodology.strip(),),
            )
            pack = cur.fetchone()
            if not pack:
                return {"has_pack": False, "methodology": methodology}

            pack_id = pack["id"]

            # Count pack findings
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE finding_type = 'CAR') AS car_count,
                    COUNT(*) FILTER (WHERE finding_type = 'CL')  AS cl_count,
                    COUNT(*) FILTER (WHERE finding_type = 'FAR') AS far_count
                FROM pack_findings WHERE pack_id = %s
                """,
                (pack_id,),
            )
            findings = cur.fetchone()

            return {
                "has_pack": True,
                "pack_id": pack_id,
                "methodology": pack["methodology_code"],
                "version": pack["methodology_version"],
                "status": pack["indexing_status"],
                "pdd_count": pack["pdd_count"] or 0,
                "mr_count": pack["mr_count"] or 0,
                "validation_count": pack["validation_count"] or 0,
                "target_pdd_count": pack["target_pdd_count"] or 30,
                "readiness_score": pack["readiness_score"] or 0,
                "car_count": int(findings["car_count"]) if findings else 0,
                "cl_count": int(findings["cl_count"]) if findings else 0,
                "far_count": int(findings["far_count"]) if findings else 0,
                "last_updated": str(pack["last_updated"] or ""),
            }
    except Exception:
        return {"has_pack": False}


def _benchmark_comparable_projects(methodology: str, country: str) -> dict[str, Any]:
    """
    Count comparable registered projects (Carbon Intelligence) for peer context.
    """
    if not methodology:
        return {"comparable_count": 0, "same_country_count": 0}
    try:
        with get_cursor() as cur:
            # Projects with this methodology code
            cur.execute(
                """
                SELECT COUNT(DISTINCT cp.id) AS total,
                       COUNT(DISTINCT cp.id) FILTER (
                           WHERE LOWER(cp.country) = LOWER(%s)
                       ) AS same_country
                FROM carbon_projects cp
                JOIN project_methodology_codes pmc ON pmc.project_id = cp.id
                WHERE UPPER(pmc.methodology_code) = UPPER(%s)
                  AND cp.status IN ('registered', 'under_validation', 'active')
                """,
                (country or "", methodology),
            )
            row = cur.fetchone()
            total   = int(row["total"])   if row else 0
            country_n = int(row["same_country"]) if row else 0

            # Also check freeform methodology field (handles TPDDTEC which uses it)
            if total == 0:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total,
                           COUNT(*) FILTER (WHERE LOWER(country) = LOWER(%s)) AS same_country
                    FROM carbon_projects
                    WHERE UPPER(methodology) LIKE UPPER(%s)
                      AND status IN ('registered', 'under_validation', 'active')
                    """,
                    (country or "", f"%{methodology}%"),
                )
                row2 = cur.fetchone()
                if row2:
                    total     = max(total,     int(row2["total"]))
                    country_n = max(country_n, int(row2["same_country"]))

        return {
            "comparable_count": total,
            "same_country_count": country_n,
            "has_peers": total > 0,
        }
    except Exception:
        return {"comparable_count": 0, "same_country_count": 0, "has_peers": False}


def _parameter_source_confidence(project_id: int) -> dict[str, Any]:
    """
    Analyse the quality distribution of parameter sources.
    Returns a breakdown of how many parameters use each source type,
    and highlights the lowest-confidence numeric parameters.
    """
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    source_type,
                    COUNT(*) AS cnt,
                    AVG(CASE
                        WHEN source_type = 'measured'            THEN 1.0
                        WHEN source_type = 'document_extracted'  THEN 0.9
                        WHEN source_type = 'calculated'          THEN 0.8
                        WHEN source_type = 'national_inventory'  THEN 0.75
                        WHEN source_type = 'ipcc'                THEN 0.7
                        WHEN source_type = 'methodology'         THEN 0.65
                        WHEN source_type = 'user_override'       THEN 0.6
                        ELSE 0.4
                    END) AS avg_conf
                FROM project_parameters
                WHERE project_id = %s AND value IS NOT NULL
                GROUP BY source_type
                """,
                (project_id,),
            )
            rows = cur.fetchall()

            source_dist: dict[str, int] = {}
            weighted_sum = 0.0
            total = 0
            for r in rows:
                source_dist[r["source_type"]] = int(r["cnt"])
                weighted_sum += float(r["avg_conf"] or 0) * int(r["cnt"])
                total += int(r["cnt"])

            avg_confidence = round(weighted_sum / total, 3) if total else 0.0

            # Find low-confidence parameters (default or estimated with no evidence)
            cur.execute(
                """
                SELECT pp.param_key, pp.param_name, pp.source_type
                FROM project_parameters pp
                LEFT JOIN evidence_links el
                    ON el.project_id = pp.project_id
                   AND el.param_key   = pp.param_key
                   AND el.evidence_decision IN ('accepted', 'accepted_as_reference')
                WHERE pp.project_id = %s
                  AND pp.source_type IN ('default', 'user_override')
                  AND pp.data_type = 'number'
                  AND pp.value IS NOT NULL
                  AND el.id IS NULL
                ORDER BY pp.param_key
                LIMIT 10
                """,
                (project_id,),
            )
            low_conf_rows = cur.fetchall()
            low_confidence_params = [
                {"param_key": r["param_key"], "param_name": r["param_name"], "source_type": r["source_type"]}
                for r in low_conf_rows
            ]

        measured = source_dist.get("measured", 0) + source_dist.get("document_extracted", 0)
        default_n = source_dist.get("default", 0)

        return {
            "total_with_value": total,
            "source_distribution": source_dist,
            "avg_confidence": avg_confidence,
            "measured_count": measured,
            "measured_pct": round(measured / total * 100) if total else 0,
            "default_count": default_n,
            "default_pct": round(default_n / total * 100) if total else 0,
            "low_confidence_params": low_confidence_params,
        }
    except Exception:
        return {
            "total_with_value": 0, "source_distribution": {},
            "avg_confidence": 0.0, "measured_count": 0, "measured_pct": 0,
            "default_count": 0, "default_pct": 0, "low_confidence_params": [],
        }


def _pack_benchmark_warnings(
    project_id: int, methodology: str, pack_context: dict
) -> list[dict[str, Any]]:
    """
    Cross-reference project parameter keys against recurring CAR/CL patterns
    from the methodology pack's findings database.
    Returns a list of params that match known high-frequency finding patterns.
    """
    warnings: list[dict[str, Any]] = []
    if not pack_context.get("has_pack") or pack_context.get("car_count", 0) == 0:
        return warnings

    pack_id = pack_context["pack_id"]
    try:
        # Get the top recurring finding patterns
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT finding_text, finding_type, section_reference, finding_reference
                FROM pack_findings
                WHERE pack_id = %s AND finding_type IN ('CAR', 'CL')
                ORDER BY id DESC
                LIMIT 50
                """,
                (pack_id,),
            )
            findings = [dict(r) for r in cur.fetchall()]

            # Get current project params (keys + names)
            cur.execute(
                "SELECT param_key, param_name, value, source_type, param_status FROM project_parameters WHERE project_id = %s",
                (project_id,),
            )
            params = {r["param_key"]: dict(r) for r in cur.fetchall()}

        if not params or not findings:
            return warnings

        # Match: for each finding, check if any param_key appears in the finding text
        for finding in findings:
            text = (finding.get("finding_text") or "").lower()
            for key, param in params.items():
                if key.lower() in text or (param["param_name"] or "").lower()[:20] in text:
                    # Only warn if the param has a suspicious status
                    if param.get("param_status") in ("default", "estimated", "missing") or param.get("value") is None:
                        # Avoid duplicate param_key warnings
                        if not any(w["param_key"] == key for w in warnings):
                            warnings.append({
                                "param_key": key,
                                "param_name": param.get("param_name", key),
                                "finding_type": finding["finding_type"],
                                "finding_text": (finding["finding_text"] or "")[:200],
                                "section_reference": finding.get("section_reference", ""),
                                "severity": "blocker" if finding["finding_type"] == "CAR" else "warning",
                                "message": (
                                    f"{param.get('param_name', key)} has been flagged in a {finding['finding_type']} "
                                    f"pattern from comparable {methodology} audits. "
                                    f"Current status: {param.get('param_status', 'unknown')}."
                                ),
                            })
                        if len(warnings) >= 8:
                            break
            if len(warnings) >= 8:
                break
    except Exception:
        pass
    return warnings


def _methodology_version_check(methodology: str, pack_context: dict) -> dict[str, Any]:
    """
    Check if the methodology version in use is current.
    Uses version_history table and pack context.
    """
    result: dict[str, Any] = {
        "version_current": True,
        "latest_version": None,
        "current_version": pack_context.get("version"),
        "update_available": False,
    }
    if not methodology:
        return result
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT version, supersedes_version, valid_from, valid_to
                FROM methodology_version_history
                WHERE UPPER(methodology_code) = UPPER(%s)
                ORDER BY valid_from DESC NULLS LAST
                LIMIT 3
                """,
                (methodology,),
            )
            versions = cur.fetchall()

        if not versions:
            return result

        latest = versions[0]
        result["latest_version"] = latest["version"]
        current = pack_context.get("version") or ""

        if current and latest["version"] and current.strip() != latest["version"].strip():
            result["version_current"] = False
            result["update_available"] = True
            result["update_message"] = (
                f"Methodology {methodology} has a newer version ({latest['version']}) available. "
                f"Currently using: {current}. Review if your project is affected."
            )
    except Exception:
        pass
    return result


def _audit_risk_signals(
    state: dict,
    meth_blockers: list,
    cross: dict,
    pack_warnings: list,
    evidence_opps: dict,
) -> list[dict[str, Any]]:
    """
    Generate pre-emptive VVB audit risk signals based on:
    - Hard methodology blockers
    - Parameters with zero evidence in audit-sensitive categories
    - Pack CAR patterns matching current params
    - Evidence coverage gaps
    - Open audit CARs from previous simulation
    """
    risks: list[dict[str, Any]] = []

    # 1. Hard methodology blockers = certain audit failure
    hard_blks = [b for b in meth_blockers if b["severity"] == "blocker"]
    if hard_blks:
        risks.append({
            "risk_type": "methodology_blocker",
            "severity": "critical",
            "title": f"{len(hard_blks)} required parameter(s) missing",
            "message": (
                f"{len(hard_blks)} parameter(s) required by your methodology have no value. "
                "A VVB would issue CARs for each missing required parameter."
            ),
            "param_keys": [b["param_key"] for b in hard_blks],
            "action_tab": "Parameters",
        })

    # 2. Pack CAR patterns
    high_risk_pack = [w for w in pack_warnings if w["severity"] == "blocker"]
    if high_risk_pack:
        risks.append({
            "risk_type": "pack_car_pattern",
            "severity": "high",
            "title": f"{len(high_risk_pack)} parameter(s) match known CAR patterns",
            "message": (
                f"{len(high_risk_pack)} of your parameters match recurring CARs from comparable "
                f"projects in the methodology pack. Address these before VVB review."
            ),
            "param_keys": [w["param_key"] for w in high_risk_pack],
            "action_tab": "Parameters",
        })

    # 3. Evidence coverage below VVB threshold
    ev_rate = cross.get("evidence_coverage_rate", 100)
    if ev_rate < 60:
        risks.append({
            "risk_type": "evidence_gap",
            "severity": "high",
            "title": f"Evidence coverage at {ev_rate}% — likely VVB CL",
            "message": (
                f"Only {ev_rate}% of numeric parameters are backed by document evidence. "
                "VVBs typically issue CLs for parameters without traceable source documents."
            ),
            "param_keys": cross.get("evidence_uncovered_params", [])[:5],
            "action_tab": "Documents",
        })

    # 4. Unresolved audit CARs
    audit = state.get("audit", {})
    open_cars = audit.get("cars", 0)
    if open_cars > 0:
        risks.append({
            "risk_type": "open_audit_cars",
            "severity": "critical",
            "title": f"{open_cars} open CAR(s) from previous audit simulation",
            "message": (
                f"{open_cars} corrective action request(s) from the audit simulation are unresolved. "
                "These must be addressed before VVB submission."
            ),
            "param_keys": cross.get("audit_car_params", []),
            "action_tab": "Findings",
        })

    # 5. High-confidence evidence pending (missed opportunity)
    high_conf = evidence_opps.get("high_confidence_count", 0)
    if high_conf >= 3:
        risks.append({
            "risk_type": "pending_evidence_risk",
            "severity": "medium",
            "title": f"{high_conf} high-confidence extractions pending review",
            "message": (
                f"{high_conf} parameter values were extracted from your documents with high confidence "
                "but have not yet been accepted. Unreviewed evidence weakens the audit trail."
            ),
            "param_keys": [],
            "action_tab": "Documents",
        })

    # Sort: critical first, then high, then medium
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    risks.sort(key=lambda r: sev_order.get(r.get("severity", "low"), 9))
    return risks


def _build_missing_evidence_list(project_id: int, cross: dict) -> list[dict[str, Any]]:
    """
    Build a richer list of uncovered parameters including extraction hints.
    """
    uncovered_keys = cross.get("evidence_uncovered_params", [])
    if not uncovered_keys:
        return []
    try:
        result = []
        for key in uncovered_keys[:8]:
            defn = PARAMETER_DEFINITIONS.get(key, {})
            result.append({
                "param_key": key,
                "param_name": defn.get("param_name", key),
                "unit": defn.get("unit", ""),
                "extraction_hint": defn.get("extraction_hint", ""),
                "category": defn.get("category", "other"),
            })
        return result
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# Tab badge computation
# ══════════════════════════════════════════════════════════════════════════════

def _compute_tab_badges(
    state: dict,
    meth_blockers: list,
    stale: list,
    outliers: list,
    cross: dict,
    audit_risks: list | None = None,
    pack_warnings: list | None = None,
) -> dict[str, Any]:
    """
    Return a dict mapping tab index → badge dict {count, severity}.
    Tab indices correspond to BASE_TAB_LABELS order.
    """
    badges: dict[int, dict] = {}
    audit_risks   = audit_risks   or []
    pack_warnings = pack_warnings or []

    def _add(tab_idx: int, count: int, sev: str):
        existing = badges.get(tab_idx)
        if existing is None:
            badges[tab_idx] = {"count": count, "severity": sev}
        else:
            sev_order = {"blocker": 0, "warning": 1, "caution": 2, "info": 3}
            new_sev = sev if sev_order.get(sev, 9) < sev_order.get(existing["severity"], 9) else existing["severity"]
            badges[tab_idx] = {"count": existing["count"] + count, "severity": new_sev}

    params   = state.get("parameters", {})
    evidence = state.get("evidence", {})
    audit    = state.get("audit", {})

    # Tab 2: Parameters
    missing = params.get("missing", 0)
    if missing > 0:
        _add(2, missing, "blocker")
    blocker_count = sum(1 for b in meth_blockers if b["severity"] == "blocker")
    warning_count = sum(1 for b in meth_blockers if b["severity"] == "warning")
    if blocker_count:
        _add(2, blocker_count, "blocker")
    elif warning_count:
        _add(2, warning_count, "warning")
    if outliers:
        _add(2, len(outliers), "caution")
    # Pack benchmark warnings on Parameters tab
    pack_blocker_params = {w["param_key"] for w in pack_warnings if w.get("severity") == "blocker"}
    if pack_blocker_params:
        _add(2, len(pack_blocker_params), "warning")

    # Tab 1: Documents (pending evidence)
    pending_ev = evidence.get("pending", 0)
    if pending_ev > 0:
        _add(1, pending_ev, "warning")

    # Tab 4: Write/Draft (stale sections)
    if stale:
        _add(4, len(stale), "warning")

    # Tab 6: Audit (needs re-run, open CARs, or audit risk signals)
    if cross.get("audit_rerun_needed"):
        _add(6, 1, "warning")
    if audit.get("cars", 0) > 0:
        _add(6, audit["cars"], "blocker")
    critical_risks = [r for r in audit_risks if r.get("severity") == "critical"]
    if critical_risks:
        _add(6, len(critical_risks), "blocker")

    # Tab 7: Findings (open CARs)
    cars = audit.get("cars", 0)
    if cars > 0:
        _add(7, cars, "blocker")

    return badges


# ══════════════════════════════════════════════════════════════════════════════
# Automation opportunities
# ══════════════════════════════════════════════════════════════════════════════

def _build_automation_opportunities(
    state: dict,
    derived_stage: str,
    stale: list,
    outliers: list,
    evidence_opps: dict,
    meth_blockers: list,
    cross: dict,
    pack_warnings: list | None = None,
    audit_risks: list | None = None,
    meth_version: dict | None = None,
    param_confidence: dict | None = None,
) -> list[dict[str, Any]]:
    opps: list[dict[str, Any]] = []
    pack_warnings    = pack_warnings    or []
    audit_risks      = audit_risks      or []
    meth_version     = meth_version     or {}
    param_confidence = param_confidence or {}

    params_state = state.get("parameters", {})
    scenario      = state.get("scenario", {})
    drafts        = state.get("drafts", {})
    audit         = state.get("audit", {})
    evidence      = state.get("evidence", {})

    # ── Blockers (highest priority) ────────────────────────────────────────
    missing = params_state.get("missing", 0)
    if missing > 0:
        opps.append({
            "id": "fill_missing_params",
            "label": f"Set values for {missing} missing parameter(s)",
            "description": f"{missing} required parameter(s) have no value. ER simulation cannot run until these are set.",
            "priority": "high",
            "action_type": "fill_parameters",
            "action_tab": "Parameters",
            "count": missing,
        })

    # ── Methodology blockers ────────────────────────────────────────────────
    meth_hard_blockers = [b for b in meth_blockers if b["severity"] == "blocker"]
    if meth_hard_blockers:
        param_names = ", ".join(b["param_key"] for b in meth_hard_blockers[:3])
        opps.append({
            "id": "resolve_methodology_blockers",
            "label": f"Resolve {len(meth_hard_blockers)} methodology-required parameter(s)",
            "description": f"The following parameters are required by your methodology and are missing or unset: {param_names}.",
            "priority": "high",
            "action_type": "fill_parameters",
            "action_tab": "Parameters",
            "count": len(meth_hard_blockers),
        })

    # ── Evidence quick-apply ────────────────────────────────────────────────
    n_apply = evidence_opps.get("auto_apply_count", 0)
    n_high  = evidence_opps.get("high_confidence_count", 0)
    if n_apply > 0:
        opps.append({
            "id": "evidence_quick_apply",
            "label": f"Review and apply {n_apply} extracted parameter value(s)",
            "description": (
                f"{n_apply} parameter value(s) were extracted from your documents"
                + (f" ({n_high} with high confidence)" if n_high > 0 else "")
                + ". Confirm them in the Documents tab."
            ),
            "priority": "high",
            "action_type": "evidence_apply",
            "action_tab": "Documents",
            "count": n_apply,
        })

    # ── Scenario param drift ────────────────────────────────────────────────
    if cross.get("scenario_param_drift"):
        hours = cross.get("scenario_param_drift_hours", 0)
        opps.append({
            "id": "resimulate_after_param_change",
            "label": "Re-run ER simulation — parameters changed since last scenario",
            "description": (
                f"Your selected scenario was created {hours:.0f}h before the most recent parameter update. "
                "Re-run the simulation to keep ER projections in sync with current parameters."
            ),
            "priority": "high",
            "action_type": "run_simulation",
            "action_tab": "ER Simulator",
            "count": 0,
        })

    # ── Audit re-run ────────────────────────────────────────────────────────
    if cross.get("audit_rerun_needed"):
        hours = cross.get("audit_rerun_hours_since", 0)
        opps.append({
            "id": "rerun_audit",
            "label": "Re-run audit — parameters updated since last audit",
            "description": (
                f"Parameters were updated {hours:.0f}h after the last audit run. "
                "Re-run the audit simulation to ensure findings reflect current values."
            ),
            "priority": "medium",
            "action_type": "run_audit",
            "action_tab": "Audit",
            "count": 0,
        })

    # ── Open CARs ──────────────────────────────────────────────────────────
    open_cars = audit.get("cars", 0)
    if open_cars > 0:
        car_params = cross.get("audit_car_params", [])
        detail = ""
        if car_params:
            detail = f" Key parameters referenced: {', '.join(car_params[:3])}."
        opps.append({
            "id": "resolve_audit_cars",
            "label": f"Resolve {open_cars} open Corrective Action Request(s)",
            "description": (
                f"{open_cars} CAR(s) from the audit simulation need to be addressed before submission.{detail}"
            ),
            "priority": "high",
            "action_type": "navigate",
            "action_tab": "Findings",
            "count": open_cars,
        })

    # ── Stale sections ─────────────────────────────────────────────────────
    n_stale = len(stale)
    if n_stale > 0:
        stale_ids = ", ".join(s["section_id"] for s in stale[:3])
        opps.append({
            "id": "redraft_stale_sections",
            "label": f"Re-draft {n_stale} section(s) outdated by parameter changes",
            "description": (
                f"Section(s) [{stale_ids}{'…' if n_stale > 3 else ''}] were drafted before "
                "the most recent parameter update. Re-drafting will incorporate current values."
            ),
            "priority": "medium",
            "action_type": "redraft",
            "action_tab": "Write / Draft",
            "count": n_stale,
        })

    # ── Parameter outliers ─────────────────────────────────────────────────
    if outliers:
        n_out = len(outliers)
        opps.append({
            "id": "review_outlier_params",
            "label": f"Review {n_out} parameter(s) outside the expected range",
            "description": (
                f"{n_out} parameter value(s) fall outside typical ranges for this methodology. "
                "Verify them or add supporting evidence before simulation."
            ),
            "priority": "medium",
            "action_type": "review_parameters",
            "action_tab": "Parameters",
            "count": n_out,
        })

    # ── Evidence coverage gap ──────────────────────────────────────────────
    cov_rate = cross.get("evidence_coverage_rate", 100)
    uncovered = cross.get("evidence_uncovered_params", [])
    if drafts.get("has_drafts") and cov_rate < 50 and uncovered:
        opps.append({
            "id": "improve_evidence_coverage",
            "label": f"Link supporting evidence to {len(uncovered)} parameter(s)",
            "description": (
                f"Only {cov_rate}% of your numeric parameters are backed by document evidence. "
                "VVB auditors will expect evidence for all key parameters."
            ),
            "priority": "medium",
            "action_type": "navigate",
            "action_tab": "Documents",
            "count": len(uncovered),
        })

    # ── Default parameters in default status (confirm top ones) ───────────
    default_count = params_state.get("default", 0)
    if default_count > 0 and derived_stage in (STAGE_SIMULATION, STAGE_DRAFTING, STAGE_REVIEW):
        opps.append({
            "id": "confirm_default_params",
            "label": f"Confirm or update {default_count} parameter(s) still using default values",
            "description": (
                f"{default_count} parameter(s) are still at methodology defaults. "
                "For a credible ER calculation, use measured or site-specific values."
            ),
            "priority": "medium",
            "action_type": "fill_parameters",
            "action_tab": "Parameters",
            "count": default_count,
        })

    # ── V2: Pack CAR pattern warnings ────────────────────────────────────────
    car_pattern_hits = [w for w in pack_warnings if w.get("finding_type") == "CAR"]
    if car_pattern_hits:
        sample = ", ".join(w["param_key"] for w in car_pattern_hits[:3])
        opps.append({
            "id": "pack_car_pattern_warning",
            "label": f"Resolve {len(car_pattern_hits)} parameter(s) matching known CAR patterns",
            "description": (
                f"Parameters ({sample}{'...' if len(car_pattern_hits) > 3 else ''}) match "
                "recurring corrective action patterns from comparable projects in the methodology pack. "
                "Review and update these before VVB audit."
            ),
            "priority": "high",
            "action_type": "review_parameters",
            "action_tab": "Parameters",
            "count": len(car_pattern_hits),
        })

    # ── V2: Audit pre-emptive risk signals ───────────────────────────────────
    critical_risks = [r for r in audit_risks if r.get("severity") == "critical"]
    high_risks     = [r for r in audit_risks if r.get("severity") == "high"]
    if critical_risks:
        risk = critical_risks[0]
        opps.append({
            "id": "audit_critical_risk",
            "label": f"Critical audit risk: {risk['title']}",
            "description": risk["message"],
            "priority": "high",
            "action_type": "navigate",
            "action_tab": risk.get("action_tab", "Audit"),
            "count": len(critical_risks),
        })
    elif high_risks:
        opps.append({
            "id": "audit_high_risk",
            "label": f"{len(high_risks)} pre-emptive audit risk(s) detected",
            "description": high_risks[0]["message"],
            "priority": "medium",
            "action_type": "navigate",
            "action_tab": high_risks[0].get("action_tab", "Audit"),
            "count": len(high_risks),
        })

    # ── V2: Methodology version update ───────────────────────────────────────
    if meth_version.get("update_available"):
        opps.append({
            "id": "methodology_version_update",
            "label": "New methodology version available",
            "description": meth_version.get("update_message", "A newer version of your methodology has been released. Check if your project is affected."),
            "priority": "medium",
            "action_type": "navigate",
            "action_tab": "Setup",
            "count": 0,
        })

    # ── V2: High-confidence evidence quick-apply (specific signal) ───────────
    n_high_conf = evidence_opps.get("high_confidence_count", 0)
    n_apply = evidence_opps.get("auto_apply_count", 0)
    if n_high_conf > 0 and n_apply == 0:
        opps.append({
            "id": "evidence_high_confidence_pending",
            "label": f"{n_high_conf} high-confidence parameter extraction(s) pending review",
            "description": (
                f"{n_high_conf} parameter value(s) were extracted with ≥80% confidence from your documents. "
                "Review and accept them to strengthen your evidence trail."
            ),
            "priority": "medium",
            "action_type": "evidence_apply",
            "action_tab": "Documents",
            "count": n_high_conf,
        })

    # ── V2: Low source confidence — suggest improvements ─────────────────────
    low_conf_params = param_confidence.get("low_confidence_params", [])
    measured_pct    = param_confidence.get("measured_pct", 100)
    if low_conf_params and measured_pct < 40 and derived_stage in (STAGE_REVIEW, STAGE_AUDIT_PREP):
        sample_names = ", ".join(p["param_key"] for p in low_conf_params[:3])
        opps.append({
            "id": "improve_source_confidence",
            "label": f"Improve evidence quality for {len(low_conf_params)} default/override parameter(s)",
            "description": (
                f"Only {measured_pct}% of your parameters use measured or document-extracted values. "
                f"Consider adding source references for: {sample_names}."
            ),
            "priority": "medium",
            "action_type": "fill_parameters",
            "action_tab": "Parameters",
            "count": len(low_conf_params),
        })

    # ── Stage-based forward suggestions ───────────────────────────────────
    if derived_stage == STAGE_SIMULATION:
        opps.append({
            "id": "run_er_simulation",
            "label": "Run your first ER simulation",
            "description": (
                "Parameters are sufficiently configured. Run an ER simulation to "
                "quantify emission reductions and save a scenario for PDD drafting."
            ),
            "priority": "low",
            "action_type": "run_simulation",
            "action_tab": "ER Simulator",
            "count": 0,
        })

    if derived_stage == STAGE_DRAFTING:
        opps.append({
            "id": "start_drafting",
            "label": "Start drafting your PDD sections",
            "description": (
                "You have a confirmed ER scenario. The AI writer can now draft your "
                "PDD sections using your project parameters and scenario results."
            ),
            "priority": "low",
            "action_type": "draft_section",
            "action_tab": "Write / Draft",
            "count": 0,
        })

    if derived_stage == STAGE_REVIEW and not audit.get("has_audit"):
        opps.append({
            "id": "run_first_audit",
            "label": "Run an AI audit simulation",
            "description": (
                "You have PDD drafts. Run the audit simulation to identify compliance "
                "gaps before submitting to the VVB."
            ),
            "priority": "low",
            "action_type": "run_audit",
            "action_tab": "Audit",
            "count": 0,
        })

    # Sort: high → medium → low, then by count descending
    priority_order = {"high": 0, "medium": 1, "low": 2}
    opps.sort(key=lambda o: (priority_order.get(o["priority"], 9), -o.get("count", 0)))
    return opps


# ══════════════════════════════════════════════════════════════════════════════
# Next-best action (stage-gated)
# ══════════════════════════════════════════════════════════════════════════════

# Stage-to-primary-action mapping (fallback when automation list is empty)
_STAGE_DEFAULT_ACTIONS: dict[str, dict] = {
    STAGE_SETUP: {
        "label": "Complete project setup",
        "description": "Set your carbon standard, methodology, country, and project start date.",
        "action_tab": "Setup",
        "priority": "high",
    },
    STAGE_PARAMETERIZATION: {
        "label": "Configure your methodology parameters",
        "description": "Enter or confirm parameter values required for ER calculation.",
        "action_tab": "Parameters",
        "priority": "high",
    },
    STAGE_SIMULATION: {
        "label": "Run an ER simulation to estimate emission reductions",
        "description": "Parameters are ready. Run a scenario and save it for PDD drafting.",
        "action_tab": "ER Simulator",
        "priority": "medium",
    },
    STAGE_DRAFTING: {
        "label": "Draft your PDD sections with the AI writer",
        "description": "Your scenario is ready. Start drafting project description sections.",
        "action_tab": "Write / Draft",
        "priority": "medium",
    },
    STAGE_REVIEW: {
        "label": "Run an AI audit simulation to check compliance",
        "description": "Sections are drafted. Audit the project before VVB submission.",
        "action_tab": "Audit",
        "priority": "medium",
    },
    STAGE_AUDIT_PREP: {
        "label": "Address open CARs and CLs from audit simulation",
        "description": "Review and respond to audit findings to reach submission readiness.",
        "action_tab": "Findings",
        "priority": "high",
    },
    STAGE_SUBMISSION_READY: {
        "label": "Export your final PDD document",
        "description": "Audit is passed. Export the completed PDD for VVB submission.",
        "action_tab": "Export",
        "priority": "low",
    },
}


def _compute_next_best_action(
    state: dict,
    derived_stage: str,
    automation: list,
) -> dict[str, Any] | None:
    # High-priority automation items take precedence
    high_opps = [o for o in automation if o.get("priority") == "high"]
    if high_opps:
        top = high_opps[0]
        return {
            "label": top["label"],
            "description": top["description"],
            "action_type": top["action_type"],
            "action_tab": top.get("action_tab"),
            "priority": "high",
        }

    # Fall back to stage-default action
    default = _STAGE_DEFAULT_ACTIONS.get(derived_stage)
    if default:
        return {
            "action_type": "navigate",
            **default,
        }

    # Fall back to first automation item
    if automation:
        top = automation[0]
        return {
            "label": top["label"],
            "description": top["description"],
            "action_type": top["action_type"],
            "action_tab": top.get("action_tab"),
            "priority": top.get("priority", "medium"),
        }

    return None


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_methodology(state: dict, project_id: int) -> str:
    raw = state.get("standard", "") or _get_project_field(project_id, "methodology") or ""
    return _METH_ALIASES.get(raw, raw)


def _get_project_field(project_id: int, field: str) -> str:
    try:
        with get_cursor() as cur:
            cur.execute(f"SELECT {field} FROM user_projects WHERE id = %s", (project_id,))
            row = cur.fetchone()
            return (row[field] or "") if row else ""
    except Exception:
        return ""


def _strip_tz(dt: Any) -> datetime.datetime | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = _parse_ts(dt)
    if isinstance(dt, datetime.datetime) and dt.tzinfo:
        return dt.replace(tzinfo=None)
    return dt


def _parse_ts(ts_str: str) -> datetime.datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00").split("+")[0])
    except Exception:
        return None
