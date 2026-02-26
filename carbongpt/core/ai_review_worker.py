#!/usr/bin/env python3
"""
ai_review_worker.py — Background worker daemon for AI review.

Runs as a standalone process alongside FastAPI/Streamlit. Watches
/tmp/carbongpt_tasks/ for pending tasks and processes them.
"""

import sys
import os
import time
import json
import logging
from pathlib import Path

sys.path.insert(0, os.environ.get("PYTHONPATH", "/home/runner/workspace"))

from carbongpt.core.task_store import TASK_DIR, get_task, set_status
from carbongpt.core.ai_review import run_ai_review

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POLL_INTERVAL = 2


def find_actionable_tasks():
    tasks = []
    for f in TASK_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if data.get("status") in ("pending", "running"):
                task_id = f.stem
                doc_path = data.get("doc_path", "")
                standard = data.get("standard", "GoldStandard")
                doc_type = data.get("doc_type", "MR")
                if doc_path:
                    tasks.append((task_id, doc_path, standard, doc_type))
        except (json.JSONDecodeError, OSError):
            continue
    return tasks


def process_task(task_id: str, doc_path: str, standard: str, doc_type: str):
    set_status(task_id, "running")
    logger.info("Processing task %s for %s (standard=%s, doc_type=%s)", task_id, doc_path, standard, doc_type)

    try:
        result = run_ai_review(doc_path=doc_path, standard=standard, doc_type=doc_type)
        set_status(task_id, "complete", result=result)
        logger.info("Task %s completed", task_id)
    except Exception as exc:
        logger.error("Task %s failed: %s", task_id, exc)
        set_status(task_id, "failed", error=str(exc))


def main():
    logger.info("AI review worker started, watching %s", TASK_DIR)
    TASK_DIR.mkdir(exist_ok=True)

    while True:
        try:
            tasks = find_actionable_tasks()
            for task_id, doc_path, standard, doc_type in tasks:
                process_task(task_id, doc_path, standard, doc_type)
        except Exception as exc:
            logger.error("Worker loop error: %s", exc)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
