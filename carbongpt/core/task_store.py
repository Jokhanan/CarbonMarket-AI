"""
task_store.py — File-backed async task store for long-running operations.

Uses /tmp/carbongpt_tasks/ to persist task state across process restarts.
Writes are atomic (write to temp file, then rename) to prevent partial reads.
"""

import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

TASK_DIR = Path("/tmp/carbongpt_tasks")
TASK_DIR.mkdir(exist_ok=True)


def _task_path(task_id: str) -> Path:
    return TASK_DIR / f"{task_id}.json"


def create_task() -> str:
    task_id = uuid.uuid4().hex[:12]
    _atomic_write(task_id, {"status": "pending", "result": None, "error": None})
    return task_id


def set_status(task_id: str, status: str, result: Any = None, error: str | None = None):
    _atomic_write(task_id, {"status": status, "result": result, "error": error})


def get_task(task_id: str) -> dict[str, Any] | None:
    path = _task_path(task_id)
    if not path.exists():
        return None
    for _ in range(3):
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            import time
            time.sleep(0.05)
    return None


def _atomic_write(task_id: str, data: dict):
    path = _task_path(task_id)
    fd, tmp_path = tempfile.mkstemp(dir=TASK_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
