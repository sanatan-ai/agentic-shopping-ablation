"""Full experiment entry point.

Configuration (locked in the proposal + supervisor's approval):
  - 50 tasks (whole suite)
  - 2 architectures (reactive, planning)
  - 4 noise levels: 0.0, 0.1, 0.2, 0.3
  - 3 seeds: 42, 1, 2024
  - Total: 1,200 runs
  - Model: Llama 3.1 70B via Bedrock
  - Cost projection: ~$30-45 USD
  - Wall-clock projection: ~10-12 hours

Safety mechanisms:
  - Incremental checkpointing after every run (resume automatically on restart)
  - Retry-with-backoff on Bedrock throttling
  - Cost-abort threshold at $50 USD (well above projected $30-45)

Usage:
    uv run python scripts/run_full_experiment.py

Resume behaviour:
    If data/results/full_experiment_results.json exists, already-completed runs
    are skipped and the experiment resumes from where it left off.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

from src.agents.llm_client import BedrockClient
from src.experiments.full_runner import run_full_experiment
from src.experiments.results import write_summary_report
from src.task_suite.models import TaskSuite

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PARQUET = PROJECT_ROOT / "data" / "processed" / "catalogue.parquet"
TASK_SUITE_JSON = PROJECT_ROOT / "data" / "processed" / "task_suite.json"
TRACES_DIR = PROJECT_ROOT / "data" / "traces_full"
RESULTS_JSON = PROJECT_ROOT / "data" / "results" / "full_experiment_results.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "full_experiment_report.md"

# Full-experiment configuration (locked)
ARCHITECTURES = ["reactive", "planning"]
NOISE_LEVELS = [0.0, 0.1, 0.2, 0.3]
SEEDS = [42, 1, 2024]

MODEL_ID = "us.meta.llama3-1-70b-instruct-v1:0"
COST_THRESHOLD_USD = 50.0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("run_full_experiment")

    parser = argparse.ArgumentParser()
    parser.add_argument("--cost-threshold", type=float, default=COST_THRESHOLD_USD,
                        help=f"Abort if cumulative Bedrock spend exceeds this USD (default: {COST_THRESHOLD_USD})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the matrix and exit without running")
    args = parser.parse_args()

    # Load fixtures
    log.info("Loading catalogue from %s", CATALOGUE_PARQUET)
    catalogue = pd.read_parquet(CATALOGUE_PARQUET)
    log.info("Catalogue: %d products", len(catalogue))

    log.info("Loading task suite from %s", TASK_SUITE_JSON)
    suite = TaskSuite.model_validate(json.loads(TASK_SUITE_JSON.read_text(encoding="utf-8")))
    log.info("Task suite: %d tasks", len(suite.tasks))

    tasks = suite.tasks  # ALL 50 tasks
    total_runs = len(tasks) * len(ARCHITECTURES) * len(NOISE_LEVELS) * len(SEEDS)

    log.info("=" * 70)
    log.info("Full experiment matrix:")
    log.info("  Tasks:         %d (whole suite)", len(tasks))
    log.info("  Architectures: %s", ARCHITECTURES)
    log.info("  Noise levels:  %s", NOISE_LEVELS)
    log.info("  Seeds:         %s", SEEDS)
    log.info("  Total runs:    %d", total_runs)
    log.info("  Model:         %s", MODEL_ID)
    log.info("  Cost threshold: $%.2f USD", args.cost_threshold)
    log.info("  Results file:  %s", RESULTS_JSON)
    log.info("  Traces dir:    %s", TRACES_DIR)
    log.info("=" * 70)

    if args.dry_run:
        log.info("--dry-run set; exiting without running")
        return 0

    # Instantiate Bedrock client with retry + cost threshold
    llm = BedrockClient(
        model_id=MODEL_ID,
        cost_threshold_usd=args.cost_threshold,
    )

    metrics = run_full_experiment(
        tasks=tasks,
        architectures=ARCHITECTURES,
        noise_levels=NOISE_LEVELS,
        seeds=SEEDS,
        catalogue=catalogue,
        llm=llm,
        traces_dir=TRACES_DIR,
        results_path=RESULTS_JSON,
    )

    write_summary_report(metrics, REPORT_PATH, title="Full Experiment Results")
    log.info("Wrote summary report to %s", REPORT_PATH)
    log.info("Wrote per-run results to %s", RESULTS_JSON)
    log.info("Traces in %s", TRACES_DIR)
    log.info("Total real cost: %s", llm.cost_summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())