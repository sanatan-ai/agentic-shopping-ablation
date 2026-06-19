"""Pilot run entry point.

Configuration (locked):
  - 20 stratified tasks across all (bucket, difficulty) cells
  - 2 architectures (reactive, planning)
  - 2 noise levels (0.0 noise-free + 0.2 moderate-noise)
  - 1 seed (42)
  - Total: 80 runs
  - Expected cost: ~$0.24 (well under $100 budget)
  - Expected wall-clock: 15-20 minutes

Usage:
    uv run python scripts/run_pilot.py
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

from src.agents.llm_client import BedrockClient
from src.experiments.results import write_summary_report
from src.experiments.runner import run_pilot, select_stratified_tasks
from src.task_suite.models import TaskSuite

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PARQUET = PROJECT_ROOT / "data" / "processed" / "catalogue.parquet"
TASK_SUITE_JSON = PROJECT_ROOT / "data" / "processed" / "task_suite.json"
TRACES_DIR = PROJECT_ROOT / "data" / "traces"
RESULTS_JSON = PROJECT_ROOT / "data" / "results" / "pilot_results.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "pilot_report.md"

# Model IDs — default 8B; pass --70b on the command line to use 70B instead
DEFAULT_MODEL_ID = "us.meta.llama3-1-8b-instruct-v1:0"
LLAMA_70B_MODEL_ID = "us.meta.llama3-1-70b-instruct-v1:0"

# Pilot configuration
NUM_TASKS = 20
ARCHITECTURES = ["reactive", "planning"]
NOISE_LEVELS = [0.0, 0.2]
SEEDS = [42]


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("run_pilot")

    parser = argparse.ArgumentParser()
    parser.add_argument("--70b", dest="use_70b", action="store_true",
                        help="Use Llama 3.1 70B instead of the default 8B")
    args = parser.parse_args()
    model_id = LLAMA_70B_MODEL_ID if args.use_70b else DEFAULT_MODEL_ID
    log.info("Using model: %s", model_id)

    log.info("Loading catalogue from %s", CATALOGUE_PARQUET)
    catalogue = pd.read_parquet(CATALOGUE_PARQUET)
    log.info("Catalogue: %d products", len(catalogue))

    log.info("Loading task suite from %s", TASK_SUITE_JSON)
    suite = TaskSuite.model_validate(json.loads(TASK_SUITE_JSON.read_text(encoding="utf-8")))
    log.info("Task suite: %d tasks total", len(suite.tasks))

    tasks = select_stratified_tasks(suite, n=NUM_TASKS, seed=42)
    log.info("Selected %d stratified tasks:", len(tasks))
    for t in tasks:
        log.info("  %s (%s, %s)", t.task_id, t.bucket, t.difficulty)

    estimated_runs = len(tasks) * len(ARCHITECTURES) * len(NOISE_LEVELS) * len(SEEDS)
    estimated_cost = estimated_runs * 0.003  # ~$0.003 per run from single-task results
    log.info("=" * 70)
    log.info("Pilot matrix: %d × %d × %d × %d = %d runs",
             len(tasks), len(ARCHITECTURES), len(NOISE_LEVELS), len(SEEDS), estimated_runs)
    log.info("Estimated cost: ~$%.2f (Bedrock)", estimated_cost)
    log.info("=" * 70)

    llm = BedrockClient(model_id=model_id)

    metrics = run_pilot(
        tasks=tasks,
        architectures=ARCHITECTURES,
        noise_levels=NOISE_LEVELS,
        seeds=SEEDS,
        catalogue=catalogue,
        llm=llm,
        traces_dir=TRACES_DIR,
        results_path=RESULTS_JSON,
    )

    write_summary_report(metrics, REPORT_PATH, title="Pilot Run Results")
    log.info("Wrote summary report to %s", REPORT_PATH)
    log.info("Wrote per-run results to %s", RESULTS_JSON)
    log.info("Traces in %s", TRACES_DIR)
    log.info("Total real cost: %s", llm.cost_summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
