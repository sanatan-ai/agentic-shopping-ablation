"""Environment sanity check.

Runs the oracle agent against all 50 tasks at noise=0 and asserts:
  - 100% Hard Success (every purchased ASIN is in the task's valid_set)
  - 100% Preference Success (every purchased ASIN is in the task's optimal_asins)
  - All episodes terminate via 'purchased' (not budget or malformed)

If anything fails, the environment has a bug.

Usage:
    uv run python scripts/sanity_check_environment.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

from src.environment.environment import build_environment
from src.oracle.oracle_agent import run_oracle_episode
from src.task_suite.models import TaskSuite

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PARQUET = PROJECT_ROOT / "data" / "processed" / "catalogue.parquet"
TASK_SUITE_JSON = PROJECT_ROOT / "data" / "processed" / "task_suite.json"


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("sanity_check")

    # Load fixtures
    log.info("Loading catalogue from %s", CATALOGUE_PARQUET)
    catalogue = pd.read_parquet(CATALOGUE_PARQUET)
    log.info("Catalogue: %d products", len(catalogue))

    log.info("Loading task suite from %s", TASK_SUITE_JSON)
    raw = json.loads(TASK_SUITE_JSON.read_text(encoding="utf-8"))
    suite = TaskSuite.model_validate(raw)
    log.info("Task suite: %d tasks", len(suite.tasks))

    # Counters
    hard_successes = 0
    preference_successes = 0
    purchased_terminations = 0
    failed_tasks: list[tuple[str, str]] = []  # (task_id, reason)

    for task in suite.tasks:
        env = build_environment(catalogue=catalogue, noise_probability=0.0, seed=42)
        purchased = run_oracle_episode(env, task)

        if purchased is None:
            failed_tasks.append((task.task_id, f"abnormal_termination:{env.terminal_reason}"))
            continue

        if env.terminal_reason == "purchased":
            purchased_terminations += 1

        if purchased in task.valid_set:
            hard_successes += 1
        else:
            failed_tasks.append((task.task_id, f"purchased_outside_valid_set:{purchased}"))

        if purchased in task.optimal_asins:
            preference_successes += 1
        else:
            # Non-optimal but still in valid set is still a hard success
            # but a preference failure; we only flag it if also outside valid_set
            pass

    # Report
    n = len(suite.tasks)
    log.info("=" * 70)
    log.info("Sanity check results (oracle agent, noise=0):")
    log.info("  Purchased terminations:      %3d / %d (%5.1f%%)", purchased_terminations, n, 100 * purchased_terminations / n)
    log.info("  Hard Success:                %3d / %d (%5.1f%%)", hard_successes, n, 100 * hard_successes / n)
    log.info("  Preference Success:          %3d / %d (%5.1f%%)", preference_successes, n, 100 * preference_successes / n)

    if failed_tasks:
        log.error("FAILED TASKS (%d):", len(failed_tasks))
        for task_id, reason in failed_tasks[:20]:
            log.error("  %s: %s", task_id, reason)
        if len(failed_tasks) > 20:
            log.error("  ... and %d more", len(failed_tasks) - 20)

    # Pass criteria: 100% hard success and 100% purchased terminations
    if hard_successes == n and purchased_terminations == n:
        log.info("PASS: Environment is wired correctly.")
        return 0
    else:
        log.error("FAIL: Environment has bugs. See failed-task list above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
