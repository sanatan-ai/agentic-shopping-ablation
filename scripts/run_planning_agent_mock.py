"""Mock sanity test for the planning agent.

Two scenarios:
  1. Happy path: initial plan narrows correctly, replan emits a purchase.
  2. Error recovery: first plan hits a noise-injected error, replan recovers.

No AWS spend. Tests planning loop, plan parser, replan trigger, history accumulation.

Usage:
    uv run python scripts/run_planning_agent_mock.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

from src.agents.llm_client import MockClient
from src.agents.planning_agent import PlanningAgent
from src.environment.environment import build_environment
from src.task_suite.models import TaskSuite

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PARQUET = PROJECT_ROOT / "data" / "processed" / "catalogue.parquet"
TASK_SUITE_JSON = PROJECT_ROOT / "data" / "processed" / "task_suite.json"


def _load_fixtures():
    catalogue = pd.read_parquet(CATALOGUE_PARQUET)
    suite = TaskSuite.model_validate(json.loads(TASK_SUITE_JSON.read_text(encoding="utf-8")))
    return catalogue, suite


def scenario_happy_path(catalogue, task) -> bool:
    """Plan 1: narrows by bucket + price. Plan 2 (replan): purchase optimal."""
    log = logging.getLogger("happy_path")
    optimal = task.optimal_asins[0]

    mock_responses = [
        # Initial plan: search + filter
        json.dumps({
            "plan_summary": f"Search and filter for {task.bucket}",
            "plan": [
                {"tool": "search", "args": {"query": task.bucket}},
                {"tool": "filter", "args": {"attribute": "bucket", "operator": "==", "value": task.bucket}},
            ],
        }),
        # Replan: purchase
        json.dumps({
            "plan_summary": "Purchase the optimal product",
            "plan": [
                {"tool": "purchase", "args": {"product_id": optimal}},
            ],
        }),
    ]

    env = build_environment(catalogue=catalogue, noise_probability=0.0, seed=42)
    agent = PlanningAgent(llm=MockClient(responses=mock_responses), env=env)
    result = agent.run_episode(task_id=task.task_id, task_nl=task.natural_language)

    log.info("Result: terminated=%s, reason=%s, purchased=%s, llm_calls=%d, replans=%d",
             result.terminated, result.terminal_reason, result.purchased_asin,
             result.llm_calls, result.replans_used)

    if (result.purchased_asin == optimal
            and result.terminal_reason == "purchased"
            and result.llm_calls == 2  # one plan + one replan
            and result.replans_used == 1):
        log.info("PASS")
        return True
    log.error("FAIL")
    return False


def scenario_error_recovery(catalogue, task) -> bool:
    """First plan has a bad action that hits an env error; replan recovers."""
    log = logging.getLogger("error_recovery")
    optimal = task.optimal_asins[0]

    mock_responses = [
        # First plan: hits an error (unknown ASIN in compare)
        json.dumps({
            "plan_summary": "Compare a known-bad ASIN to trigger an error",
            "plan": [
                {"tool": "search", "args": {"query": task.bucket}},
                {"tool": "compare", "args": {"product_ids": ["B_NONEXISTENT_1", "B_NONEXISTENT_2"]}},
            ],
        }),
        # Replan after error → purchase optimal
        json.dumps({
            "plan_summary": "Recover: purchase the optimal",
            "plan": [
                {"tool": "purchase", "args": {"product_id": optimal}},
            ],
        }),
    ]

    env = build_environment(catalogue=catalogue, noise_probability=0.0, seed=42)
    agent = PlanningAgent(llm=MockClient(responses=mock_responses), env=env)
    result = agent.run_episode(task_id=task.task_id, task_nl=task.natural_language)

    log.info("Result: terminated=%s, reason=%s, purchased=%s, llm_calls=%d, replans=%d",
             result.terminated, result.terminal_reason, result.purchased_asin,
             result.llm_calls, result.replans_used)

    if (result.purchased_asin == optimal
            and result.terminal_reason == "purchased"
            and result.replans_used == 1):
        log.info("PASS")
        return True
    log.error("FAIL")
    return False


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("run_planning_agent_mock")

    catalogue, suite = _load_fixtures()
    log.info("Loaded %d products, %d tasks", len(catalogue), len(suite.tasks))

    task = next((t for t in suite.tasks if t.difficulty == "easy" and len(t.optimal_asins) == 1), None) or suite.tasks[0]
    log.info("Using task %s (%s, %s): %s",
             task.task_id, task.bucket, task.difficulty, task.natural_language)

    results = []
    log.info("=" * 70)
    log.info("Scenario 1: happy path (plan + replan-for-purchase)")
    results.append(scenario_happy_path(catalogue, task))
    log.info("=" * 70)
    log.info("Scenario 2: error recovery")
    results.append(scenario_error_recovery(catalogue, task))
    log.info("=" * 70)
    log.info("Planning agent mock sanity: %d/%d passed", sum(results), len(results))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
