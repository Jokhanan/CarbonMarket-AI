#!/usr/bin/env python3
"""
ai_review_worker.py — Subprocess worker for AI review.

Runs independently of the FastAPI process so the workflow manager
doesn't kill it. Reads task_id and doc_path from command line args,
runs the AI review, and writes results to the file-backed task store.
"""

import sys
import os

sys.path.insert(0, os.environ.get("PYTHONPATH", "/home/runner/workspace"))

import logging
from carbongpt.core.task_store import set_status
from carbongpt.core.ai_review import run_ai_review

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <task_id> <doc_path>", file=sys.stderr)
        sys.exit(1)

    task_id = sys.argv[1]
    doc_path = sys.argv[2]

    set_status(task_id, "running")
    logger.info("AI review worker started: task=%s doc=%s", task_id, doc_path)

    try:
        result = run_ai_review(doc_path=doc_path)
        set_status(task_id, "complete", result=result)
        logger.info("AI review worker completed: task=%s", task_id)
    except Exception as exc:
        logger.error("AI review worker failed: task=%s error=%s", task_id, exc)
        set_status(task_id, "failed", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
