import logging
from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

LIFECYCLE_STAGES = [
    {"key": "feasibility", "name": "Feasibility", "order": 1},
    {"key": "pdd_design", "name": "PDD Design", "order": 2},
    {"key": "internal_review", "name": "Internal Review", "order": 3},
    {"key": "validation", "name": "Validation", "order": 4},
    {"key": "registration", "name": "Registration", "order": 5},
    {"key": "monitoring", "name": "Monitoring", "order": 6},
    {"key": "verification", "name": "Verification", "order": 7},
    {"key": "issuance", "name": "Issuance", "order": 8},
]

STAGE_KEYS = [s["key"] for s in LIFECYCLE_STAGES]

DEFAULT_TASKS_BY_STAGE = {
    "feasibility": [
        {"title": "Identify project type and technology", "task_type": "general"},
        {"title": "Select applicable methodology", "task_type": "general"},
        {"title": "Preliminary ER estimation", "task_type": "general"},
        {"title": "Stakeholder identification", "task_type": "stakeholder"},
        {"title": "Financial feasibility assessment", "task_type": "financial"},
    ],
    "pdd_design": [
        {"title": "Complete project intake form", "task_type": "document"},
        {"title": "Upload baseline survey data", "task_type": "data_collection"},
        {"title": "Set all methodology parameters", "task_type": "general"},
        {"title": "Draft PDD sections", "task_type": "document"},
        {"title": "Run ER scenario simulation", "task_type": "general"},
        {"title": "Prepare monitoring plan", "task_type": "document"},
        {"title": "Complete additionality assessment", "task_type": "document"},
        {"title": "Compile evidence register", "task_type": "document"},
    ],
    "internal_review": [
        {"title": "Run audit simulation", "task_type": "review"},
        {"title": "Review parameter completeness", "task_type": "review"},
        {"title": "Cross-section consistency check", "task_type": "review"},
        {"title": "Evidence completeness check", "task_type": "review"},
        {"title": "Address internal review findings", "task_type": "review"},
    ],
    "validation": [
        {"title": "Submit PDD to VVB", "task_type": "submission"},
        {"title": "Respond to VVB findings (CARs/CLs)", "task_type": "review"},
        {"title": "Revise PDD based on VVB comments", "task_type": "document"},
        {"title": "Submit revised PDD", "task_type": "submission"},
        {"title": "Obtain validation report", "task_type": "document"},
    ],
    "registration": [
        {"title": "Submit to registry for registration", "task_type": "submission"},
        {"title": "Pay registration fees", "task_type": "financial"},
        {"title": "Address registry comments (if any)", "task_type": "review"},
        {"title": "Confirm registration", "task_type": "general"},
    ],
    "monitoring": [
        {"title": "Conduct baseline/project monitoring surveys", "task_type": "monitoring"},
        {"title": "Collect usage rate data", "task_type": "monitoring"},
        {"title": "Compile monitoring data", "task_type": "data_collection"},
        {"title": "Draft monitoring report", "task_type": "document"},
    ],
    "verification": [
        {"title": "Submit MR to VVB for verification", "task_type": "submission"},
        {"title": "Respond to verification findings", "task_type": "review"},
        {"title": "Obtain verification report", "task_type": "document"},
    ],
    "issuance": [
        {"title": "Submit issuance request to registry", "task_type": "submission"},
        {"title": "Confirm credit issuance", "task_type": "general"},
        {"title": "Record issuance details", "task_type": "financial"},
    ],
}


def initialize_lifecycle(project_id):
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM project_lifecycle WHERE project_id = %s", (project_id,))
        if cur.fetchone()["cnt"] > 0:
            return get_lifecycle(project_id)

        cur.execute("""
            INSERT INTO project_lifecycle (project_id, stage, status)
            VALUES (%s, 'feasibility', 'active')
        """, (project_id,))

        for stage_key, tasks in DEFAULT_TASKS_BY_STAGE.items():
            for i, task in enumerate(tasks):
                cur.execute("""
                    INSERT INTO project_tasks
                    (project_id, lifecycle_stage, title, task_type, priority, status, sort_order)
                    VALUES (%s, %s, %s, %s, 'medium', 'pending', %s)
                """, (project_id, stage_key, task["title"], task["task_type"], i))

        return get_lifecycle(project_id)


def get_lifecycle(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM project_lifecycle
            WHERE project_id = %s ORDER BY started_at
        """, (project_id,))
        stages = cur.fetchall()

        current_stage = None
        completed_stages = []
        for s in stages:
            if s["status"] == "active":
                current_stage = s["stage"]
            elif s["status"] == "completed":
                completed_stages.append(s["stage"])

        if not current_stage and not completed_stages:
            current_stage = "feasibility"

        cur.execute("""
            SELECT * FROM project_tasks
            WHERE project_id = %s ORDER BY lifecycle_stage, sort_order
        """, (project_id,))
        tasks = cur.fetchall()

        stage_info = []
        for stage_def in LIFECYCLE_STAGES:
            key = stage_def["key"]
            stage_tasks = [t for t in tasks if t["lifecycle_stage"] == key]
            total = len(stage_tasks)
            completed = len([t for t in stage_tasks if t["status"] == "completed"])

            status = "upcoming"
            if key in completed_stages:
                status = "completed"
            elif key == current_stage:
                status = "active"

            stage_info.append({
                "key": key,
                "name": stage_def["name"],
                "order": stage_def["order"],
                "status": status,
                "tasks_total": total,
                "tasks_completed": completed,
                "tasks": stage_tasks,
            })

        return {
            "current_stage": current_stage,
            "completed_stages": completed_stages,
            "stages": stage_info,
        }


def advance_stage(project_id, to_stage=None):
    with get_cursor() as cur:
        lifecycle = get_lifecycle(project_id)
        current = lifecycle["current_stage"]

        if to_stage:
            if to_stage not in STAGE_KEYS:
                return {"error": f"Invalid stage: {to_stage}"}
            next_stage = to_stage
        else:
            idx = STAGE_KEYS.index(current) if current in STAGE_KEYS else -1
            if idx >= len(STAGE_KEYS) - 1:
                return {"error": "Already at the final stage"}
            next_stage = STAGE_KEYS[idx + 1]

        cur.execute("""
            UPDATE project_lifecycle SET status = 'completed', completed_at = NOW()
            WHERE project_id = %s AND stage = %s AND status = 'active'
        """, (project_id, current))

        cur.execute("""
            INSERT INTO project_lifecycle (project_id, stage, status)
            VALUES (%s, %s, 'active')
        """, (project_id, next_stage))

        return get_lifecycle(project_id)


def get_tasks(project_id, stage=None, status=None):
    with get_cursor() as cur:
        query = "SELECT * FROM project_tasks WHERE project_id = %s"
        params = [project_id]
        if stage:
            query += " AND lifecycle_stage = %s"
            params.append(stage)
        if status:
            query += " AND status = %s"
            params.append(status)
        query += " ORDER BY lifecycle_stage, sort_order"
        cur.execute(query, params)
        return cur.fetchall()


def update_task(task_id, status=None, title=None, due_date=None, priority=None):
    with get_cursor() as cur:
        updates = ["updated_at = NOW()"]
        params = []
        if status:
            updates.append("status = %s")
            params.append(status)
            if status == "completed":
                updates.append("completed_at = NOW()")
        if title:
            updates.append("title = %s")
            params.append(title)
        if due_date:
            updates.append("due_date = %s")
            params.append(due_date)
        if priority:
            updates.append("priority = %s")
            params.append(priority)

        params.append(task_id)
        cur.execute(f"UPDATE project_tasks SET {', '.join(updates)} WHERE id = %s RETURNING *", params)
        return cur.fetchone()


def add_task(project_id, title, stage=None, task_type="general", priority="medium", due_date=None, description=None):
    with get_cursor() as cur:
        if not stage:
            lifecycle = get_lifecycle(project_id)
            stage = lifecycle["current_stage"]

        cur.execute("""
            INSERT INTO project_tasks
            (project_id, lifecycle_stage, title, description, task_type, priority, due_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (project_id, stage, title, description, task_type, priority, due_date))
        return cur.fetchone()


def delete_task(task_id):
    with get_cursor() as cur:
        cur.execute("DELETE FROM project_tasks WHERE id = %s RETURNING id", (task_id,))
        return cur.fetchone()


def get_issuances(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM issuance_records
            WHERE project_id = %s ORDER BY vintage_year
        """, (project_id,))
        return cur.fetchall()


def add_issuance(project_id, vintage_year, credits_requested=None, credits_issued=None,
                 monitoring_period_start=None, monitoring_period_end=None,
                 verification_date=None, issuance_date=None,
                 buffer_contribution=None, vvb_name=None, registry_status="planned", notes=None):
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO issuance_records
            (project_id, vintage_year, credits_requested, credits_issued,
             monitoring_period_start, monitoring_period_end,
             verification_date, issuance_date,
             buffer_contribution, vvb_name, registry_status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (project_id, vintage_year, credits_requested, credits_issued,
              monitoring_period_start, monitoring_period_end,
              verification_date, issuance_date,
              buffer_contribution, vvb_name, registry_status, notes))
        return cur.fetchone()


def update_issuance(issuance_id, **kwargs):
    with get_cursor() as cur:
        allowed = ["vintage_year", "credits_requested", "credits_issued",
                    "monitoring_period_start", "monitoring_period_end",
                    "verification_date", "issuance_date",
                    "buffer_contribution", "vvb_name", "registry_status", "notes"]
        updates = ["updated_at = NOW()"]
        params = []
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                updates.append(f"{k} = %s")
                params.append(v)
        params.append(issuance_id)
        cur.execute(f"UPDATE issuance_records SET {', '.join(updates)} WHERE id = %s RETURNING *", params)
        return cur.fetchone()


def get_monitoring_tasks(project_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM monitoring_tasks
            WHERE project_id = %s ORDER BY status, next_due_date
        """, (project_id,))
        return cur.fetchall()


def initialize_monitoring_tasks(project_id, methodology=None):
    if not methodology:
        with get_cursor() as cur:
            cur.execute("SELECT methodology FROM user_projects WHERE id = %s", (project_id,))
            row = cur.fetchone()
            methodology = (row["methodology"] or "").upper().replace("GS-", "") if row else ""

    monitoring_defs = {
        "VM0050": [
            {"param_key": "usage_rate", "task_name": "Usage survey (device adoption rate)", "frequency": "annual", "method": "Household survey with 90/30 confidence/precision"},
            {"param_key": "SFC_project", "task_name": "Kitchen Performance Test (KPT)", "frequency": "annual", "method": "Field testing per methodology requirements"},
            {"param_key": "fNRB", "task_name": "fNRB verification", "frequency": "per_crediting_period", "method": "TOOL33 default or TOOL30 calculation"},
            {"param_key": "num_households", "task_name": "Device distribution tracking", "frequency": "continuous", "method": "Distribution records and serial number tracking"},
        ],
        "TPDDTEC": [
            {"param_key": "usage_rate", "task_name": "Usage survey (device adoption rate)", "frequency": "annual", "method": "Household survey with 90/30 confidence/precision"},
            {"param_key": "SFC_baseline", "task_name": "Baseline fuel consumption survey", "frequency": "once", "method": "KPT or WBT field testing"},
            {"param_key": "SFC_project", "task_name": "Project fuel consumption monitoring", "frequency": "annual", "method": "KPT or WBT field testing"},
            {"param_key": "num_households", "task_name": "Device distribution tracking", "frequency": "continuous", "method": "Distribution records"},
        ],
        "ACM0002": [
            {"param_key": "EG_PJ_y", "task_name": "Electricity generation metering", "frequency": "continuous", "method": "Calibrated electricity meters"},
            {"param_key": "EF_grid", "task_name": "Grid emission factor update", "frequency": "annual", "method": "TOOL07 or national grid data"},
        ],
        "AMS-I.D.": [
            {"param_key": "EG_PJ_y", "task_name": "Electricity generation metering", "frequency": "continuous", "method": "Calibrated electricity meters"},
            {"param_key": "EF_grid", "task_name": "Grid emission factor update", "frequency": "annual", "method": "TOOL07 or national grid data"},
        ],
    }

    defs = monitoring_defs.get(methodology, [])
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM monitoring_tasks WHERE project_id = %s", (project_id,))
        if cur.fetchone()["cnt"] > 0:
            return get_monitoring_tasks(project_id)

        for d in defs:
            cur.execute("""
                INSERT INTO monitoring_tasks
                (project_id, param_key, task_name, frequency, method, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """, (project_id, d["param_key"], d["task_name"], d["frequency"], d["method"]))

    return get_monitoring_tasks(project_id)


def get_portfolio_summary():
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) as total_projects,
                COUNT(DISTINCT country) as countries,
                COUNT(DISTINCT methodology) as methodologies,
                array_agg(DISTINCT status) as statuses
            FROM user_projects
        """)
        summary = cur.fetchone()

        cur.execute("""
            SELECT country, COUNT(*) as count
            FROM user_projects
            WHERE country IS NOT NULL AND country != ''
            GROUP BY country ORDER BY count DESC
        """)
        by_country = cur.fetchall()

        cur.execute("""
            SELECT methodology, COUNT(*) as count
            FROM user_projects
            WHERE methodology IS NOT NULL AND methodology != ''
            GROUP BY methodology ORDER BY count DESC
        """)
        by_methodology = cur.fetchall()

        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM user_projects
            GROUP BY status ORDER BY count DESC
        """)
        by_status = cur.fetchall()

        cur.execute("""
            SELECT p.id, p.name, p.standard, p.methodology, p.country, p.status,
                   COALESCE(s.total_er, 0) as projected_er
            FROM user_projects p
            LEFT JOIN LATERAL (
                SELECT (results_summary->>'total_er')::float as total_er
                FROM er_scenarios
                WHERE project_id = p.id AND is_baseline = true
                ORDER BY calculated_at DESC LIMIT 1
            ) s ON true
            ORDER BY p.updated_at DESC
        """)
        projects = cur.fetchall()

        total_projected_er = sum(p.get("projected_er", 0) or 0 for p in projects)

        return {
            "total_projects": summary["total_projects"],
            "countries": summary["countries"],
            "methodologies": summary["methodologies"],
            "total_projected_er": round(total_projected_er, 2),
            "by_country": by_country,
            "by_methodology": by_methodology,
            "by_status": by_status,
            "projects": projects,
        }
