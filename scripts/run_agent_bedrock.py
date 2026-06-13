"""Run the reactive agent against ONE task via real Bedrock.

This is the first real LLM-driven agent run. Expected cost: ~$0.01 USD.

Two phases:
  1. Connectivity smoke test (single Bedrock call, ~$0.001)
  2. Full agent episode on one task (~$0.005-$0.01)

Usage:
    uv run python scripts/run_agent_bedrock.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

from src.agents.llm_client import BedrockClient
from src.agents.reactive_agent import ReactiveAgent
from src.environment.environment import build_environment
from src.task_suite.models import TaskSuite

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PARQUET = PROJECT_ROOT / "data" / "processed" / "catalogue.parquet"
TASK_SUITE_JSON = PROJECT_ROOT / "data" / "processed" / "task_suite.json"


def phase_1_connectivity(client: BedrockClient) -> bool:
    """Verify a single Bedrock call works in the agent's context."""
    log = logging.getLogger("phase_1")
    log.info("Sending a single trivial call to verify connectivity...")
    try:
        response = client.complete(
            system="You are a helpful assistant. Reply with one word.",
            messages=[{"role": "user", "content": "Say OK."}],
            max_tokens=10,
            temperature=0.0,
        )
    except Exception:
        log.exception("Connectivity test failed")
        return False
    log.info("Response: %r", response.text)
    log.info("Tokens: in=%d, out=%d (cost ~$%.6f)",
             response.input_tokens, response.output_tokens, response.cost_usd)
    return True


def phase_2_episode(client: BedrockClient, catalogue, suite) -> bool:
    """Run a full agent episode on one task."""
    log = logging.getLogger("phase_2")

    # Pick an Easy task to start — best chance of success on first real run
    task = next((t for t in suite.tasks if t.difficulty == "easy"), suite.tasks[0])
    log.info("Selected task: %s (%s, %s)", task.task_id, task.bucket, task.difficulty)
    log.info("  Prompt: %s", task.natural_language)
    log.info("  Optimal ASINs: %s (valid set size: %d)",
             task.optimal_asins, len(task.valid_set))

    env = build_environment(catalogue=catalogue, noise_probability=0.0, seed=42)
    agent = ReactiveAgent(llm=client, env=env)

    log.info("Starting episode (this will make real Bedrock calls)...")
    result = agent.run_episode(task_id=task.task_id, task_nl=task.natural_language)

    log.info("=" * 70)
    log.info("Episode complete:")
    log.info("  Steps taken:        %d", result.steps_taken)
    log.info("  Terminated:         %s", result.terminated)
    log.info("  Terminal reason:    %s", result.terminal_reason)
    log.info("  Purchased ASIN:     %s", result.purchased_asin)
    log.info("  LLM calls:          %d", result.llm_calls)
    log.info("  Input tokens:       %d", result.total_input_tokens)
    log.info("  Output tokens:      %d", result.total_output_tokens)
    log.info("  Parse errors:       %d", result.parse_errors)
    log.info("  Wall clock:         %.2fs", result.wall_clock_seconds)

    # Outcome interpretation
    if result.purchased_asin is None:
        log.warning("No purchase made. Terminal reason: %s", result.terminal_reason)
        return False  # not strictly a "fail" — agent might rationally give up — but flag it

    in_valid = result.purchased_asin in task.valid_set
    in_optimal = result.purchased_asin in task.optimal_asins
    log.info("  Hard Success:        %s (purchased in valid_set?)", "YES" if in_valid else "NO")
    log.info("  Preference Success:  %s (purchased in optimal_asins?)", "YES" if in_optimal else "NO")

    return True  # phase 2 succeeded if the loop completed cleanly; scoring is observational


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("run_agent_bedrock")

    # Single shared client so cost accounting is end-to-end
    client = BedrockClient()

    log.info("=" * 70)
    log.info("Phase 1: connectivity smoke test")
    log.info("=" * 70)
    if not phase_1_connectivity(client):
        log.error("Phase 1 failed. Aborting.")
        return 1

    log.info("=" * 70)
    log.info("Phase 2: one agent episode on one task")
    log.info("=" * 70)
    catalogue = pd.read_parquet(CATALOGUE_PARQUET)
    suite = TaskSuite.model_validate(json.loads(TASK_SUITE_JSON.read_text(encoding="utf-8")))
    phase_2_episode(client, catalogue, suite)

    log.info("=" * 70)
    log.info(client.cost_summary())
    log.info("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
