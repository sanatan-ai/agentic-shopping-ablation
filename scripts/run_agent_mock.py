"""Sanity test the reactive agent loop using MockClient.

Two scenarios:
  1. Happy path: agent receives canned good JSON and completes a purchase.
  2. Recovery: agent receives bad output once, then good output, and recovers.

No AWS spend. Tests the agent loop, JSON parser, message accumulation,
environment interaction, and terminal handling.

Usage:
    uv run python scripts/run_agent_mock.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

from src.agents.llm_client import MockClient
from src.agents.reactive_agent import ReactiveAgent
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
    """Mock LLM returns good JSON that drives a complete episode to purchase."""
    log = logging.getLogger("scenario_happy_path")
    optimal = task.optimal_asins[0]

    # Canned LLM responses: search -> filter -> purchase
    mock_responses = [
        json.dumps({
            "thought": f"Let me search for {task.bucket} products first.",
            "action": {"tool": "search", "args": {"query": task.bucket}}
        }),
        json.dumps({
            "thought": "I'll filter to products matching the bucket.",
            "action": {
                "tool": "filter",
                "args": {"attribute": "bucket", "operator": "==", "value": task.bucket}
            }
        }),
        json.dumps({
            "thought": f"Purchasing the optimal product {optimal}.",
            "action": {"tool": "purchase", "args": {"product_id": optimal}}
        }),
    ]

    env = build_environment(catalogue=catalogue, noise_probability=0.0, seed=42)
    agent = ReactiveAgent(llm=MockClient(responses=mock_responses), env=env)
    result = agent.run_episode(task_id=task.task_id, task_nl=task.natural_language)

    log.info("Result: terminated=%s, reason=%s, purchased=%s, steps=%d",
             result.terminated, result.terminal_reason, result.purchased_asin, result.steps_taken)

    if result.purchased_asin == optimal and result.terminal_reason == "purchased":
        log.info("PASS")
        return True
    else:
        log.error("FAIL: expected purchase of %s, got purchase=%s, reason=%s",
                  optimal, result.purchased_asin, result.terminal_reason)
        return False


def scenario_parse_recovery(catalogue, task) -> bool:
    """Mock LLM emits garbage first, then valid JSON. Agent should recover."""
    log = logging.getLogger("scenario_parse_recovery")
    optimal = task.optimal_asins[0]

    # First response is unparseable; second is valid; third purchases.
    mock_responses = [
        "I'm not going to give you JSON, I'm just going to think out loud.",
        json.dumps({
            "thought": "Let me try get_details on the target product.",
            "action": {"tool": "get_details", "args": {"product_id": optimal}}
        }),
        json.dumps({
            "thought": "Purchasing.",
            "action": {"tool": "purchase", "args": {"product_id": optimal}}
        }),
    ]

    env = build_environment(catalogue=catalogue, noise_probability=0.0, seed=42)
    agent = ReactiveAgent(llm=MockClient(responses=mock_responses), env=env)
    result = agent.run_episode(task_id=task.task_id, task_nl=task.natural_language)

    log.info("Result: terminated=%s, reason=%s, purchased=%s, parse_errors=%d, llm_calls=%d",
             result.terminated, result.terminal_reason, result.purchased_asin,
             result.parse_errors, result.llm_calls)

    if (result.parse_errors == 1
            and result.purchased_asin == optimal
            and result.terminal_reason == "purchased"):
        log.info("PASS")
        return True
    else:
        log.error("FAIL: expected 1 parse error and purchase of %s", optimal)
        return False


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("run_agent_mock")

    catalogue, suite = _load_fixtures()
    log.info("Loaded %d products, %d tasks", len(catalogue), len(suite.tasks))

    # Pick a simple task — Easy with single optimum is easiest to script for
    task = next((t for t in suite.tasks if t.difficulty == "easy" and len(t.optimal_asins) == 1), None)
    if task is None:
        task = suite.tasks[0]
    log.info("Using task %s (%s, %s): %s",
             task.task_id, task.bucket, task.difficulty, task.natural_language)

    results = []
    log.info("=" * 70)
    log.info("Scenario 1: happy path")
    results.append(scenario_happy_path(catalogue, task))
    log.info("=" * 70)
    log.info("Scenario 2: parse-error recovery")
    results.append(scenario_parse_recovery(catalogue, task))
    log.info("=" * 70)
    log.info("Mock sanity tests: %d/%d passed", sum(results), len(results))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
