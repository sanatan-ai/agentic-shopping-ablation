"""Build the task suite from the curated catalogue.

Usage:
    uv run python scripts/build_task_suite.py
"""
from __future__ import annotations

import logging
import sys

from src.task_suite.config import TaskSuiteConfig
from src.task_suite.generator import generate_tasks, write_task_suite


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    cfg = TaskSuiteConfig()
    try:
        suite = generate_tasks(cfg)
        write_task_suite(suite, cfg)
    except Exception:
        logging.exception("Task suite generation failed")
        return 1

    # Final summary to stdout
    logging.info("=" * 60)
    logging.info("Task suite generated: %d tasks", len(suite.tasks))
    for (bucket, difficulty), count in sorted(suite.summary().items()):
        logging.info("  %-20s %-8s %d", bucket, difficulty, count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
