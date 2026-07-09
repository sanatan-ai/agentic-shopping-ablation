"""Runner extension with checkpoint/resume support for the full experiment.

Extends the pilot's runner.py with:
  - Resume from partial results (skips runs already scored in the results JSON)
  - Progress reporting with ETA
  - Graceful handling of CostThresholdExceeded

Usage: called by scripts/run_full_experiment.py
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import pandas as pd

from src.agents.llm_client import BedrockClient, CostThresholdExceeded
from src.experiments.runner import run_one_episode
from src.experiments.scorer import RunMetrics
from src.task_suite.models import Task

logger = logging.getLogger(__name__)


def _run_key(task_id: str, architecture: str, noise_level: float, seed: int) -> str:
    """Canonical key for identifying a completed run."""
    return f"{task_id}|{architecture}|{noise_level}|{seed}"


def load_completed_runs(results_path: Path) -> tuple[list[RunMetrics], set[str]]:
    """Load the current results file, if any. Returns (metrics, completed_keys)."""
    if not results_path.exists():
        return [], set()

    try:
        raw = json.loads(results_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read existing results at %s (%s). Starting fresh.",
                       results_path, exc)
        return [], set()

    # Reconstruct RunMetrics dataclasses from JSON dicts
    metrics: list[RunMetrics] = []
    completed: set[str] = set()
    for r in raw:
        try:
            m = RunMetrics(**r)
            metrics.append(m)
            completed.add(_run_key(m.task_id, m.architecture, m.noise_level, m.seed))
        except TypeError:
            # Schema mismatch — skip this record but keep going
            logger.warning("Skipping malformed result record: %s", r)
    return metrics, completed


def run_full_experiment(
    tasks: list[Task],
    architectures: list[str],
    noise_levels: list[float],
    seeds: list[int],
    catalogue: pd.DataFrame,
    llm: BedrockClient,
    traces_dir: Path,
    results_path: Path,
) -> list[RunMetrics]:
    """Run the full experiment matrix. Resumes automatically if results file exists."""
    total = len(tasks) * len(architectures) * len(noise_levels) * len(seeds)

    # Load existing progress if any
    all_metrics, completed_keys = load_completed_runs(results_path)
    already_done = len(all_metrics)

    if already_done > 0:
        logger.info("Resuming from checkpoint: %d/%d runs already completed",
                    already_done, total)
    else:
        logger.info("Starting fresh: %d runs to complete", total)

    remaining = total - already_done
    start = time.time()
    since_start_completed = 0

    for task in tasks:
        for arch in architectures:
            for noise in noise_levels:
                for seed in seeds:
                    key = _run_key(task.task_id, arch, noise, seed)
                    if key in completed_keys:
                        continue

                    since_start_completed += 1
                    elapsed = time.time() - start
                    rate = since_start_completed / elapsed if elapsed > 0 else 0
                    eta_seconds = (remaining - since_start_completed) / rate if rate > 0 else 0
                    eta_hours = eta_seconds / 3600.0

                    logger.info(
                        "[%d/%d, ETA %.1fh] task=%s arch=%s noise=%s seed=%d",
                        already_done + since_start_completed, total, eta_hours,
                        task.task_id, arch, noise, seed
                    )

                    try:
                        metrics = run_one_episode(
                            task=task,
                            architecture=arch,
                            noise_level=noise,
                            seed=seed,
                            catalogue=catalogue,
                            llm=llm,
                            traces_dir=traces_dir,
                        )
                        all_metrics.append(metrics)
                        completed_keys.add(key)

                        logger.info(
                            "  → hard=%s pref=%.1f steps=%d llm_calls=%d tokens=%d",
                            metrics.hard_success, metrics.preference_success,
                            metrics.env_steps, metrics.llm_calls, metrics.total_tokens,
                        )

                        # Incremental checkpoint after every run
                        results_path.parent.mkdir(parents=True, exist_ok=True)
                        results_path.write_text(
                            json.dumps([asdict(m) for m in all_metrics], indent=2),
                            encoding="utf-8",
                        )

                    except CostThresholdExceeded as exc:
                        logger.error("=" * 70)
                        logger.error("COST THRESHOLD EXCEEDED — shutting down gracefully")
                        logger.error("Spent: $%.4f (threshold $%.4f) after %d calls",
                                     exc.cost_usd, exc.threshold_usd, exc.calls)
                        logger.error("Completed %d/%d runs before abort", len(all_metrics), total)
                        logger.error("=" * 70)
                        return all_metrics

                    except Exception:
                        logger.exception(
                            "Run failed: %s/%s/noise=%s/seed=%s — continuing to next run",
                            task.task_id, arch, noise, seed,
                        )
                        # Don't add to all_metrics — the run is not counted.
                        # Its key is not added to completed_keys, so a later resume
                        # will retry it.

    logger.info("Experiment complete. %d/%d runs scored.", len(all_metrics), total)
    logger.info(llm.cost_summary())
    return all_metrics
