"""Pilot run orchestrator.

Drives the experiment matrix:
  for each (task, architecture, noise_level, seed):
    1. Build a fresh environment (seeded noise)
    2. Run the agent
    3. Score the run
    4. Persist trace to JSONL
    5. Append to results
"""
from __future__ import annotations

import json
import logging
import random
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import pandas as pd

from src.agents.llm_client import BedrockClient
from src.agents.planning_agent import PlanningAgent
from src.agents.reactive_agent import ReactiveAgent
from src.environment.environment import build_environment
from src.experiments.scorer import RunMetrics, score_run
from src.experiments.trace_store import write_trace
from src.task_suite.models import Task, TaskSuite

logger = logging.getLogger(__name__)


def select_stratified_tasks(suite: TaskSuite, n: int, seed: int = 42) -> list[Task]:
    """Pick n tasks balanced across (bucket, difficulty) cells.

    Uses round-robin sampling within shuffled-per-cell pools so the selection
    is deterministic but not biased toward task-suite ordering.
    """
    rng = random.Random(seed)
    buckets: dict[tuple[str, str], list[Task]] = defaultdict(list)
    for t in suite.tasks:
        buckets[(t.bucket, t.difficulty)].append(t)

    # Shuffle within each cell for fair sampling
    for cell in buckets:
        rng.shuffle(buckets[cell])

    # Round-robin until we have n tasks
    cell_keys = sorted(buckets.keys())  # deterministic ordering
    selected: list[Task] = []
    cursor = 0
    while len(selected) < n and any(buckets.values()):
        key = cell_keys[cursor % len(cell_keys)]
        if buckets[key]:
            selected.append(buckets[key].pop())
        cursor += 1

    return selected[:n]


def run_one_episode(
    task: Task,
    architecture: str,
    noise_level: float,
    seed: int,
    catalogue: pd.DataFrame,
    llm: BedrockClient,
    traces_dir: Path,
) -> RunMetrics:
    """Run a single episode and return its scored metrics."""
    env = build_environment(catalogue=catalogue, noise_probability=noise_level, seed=seed)

    if architecture == "reactive":
        agent = ReactiveAgent(llm=llm, env=env)
        result = agent.run_episode(task_id=task.task_id, task_nl=task.natural_language)
        replans = None
    elif architecture == "planning":
        agent = PlanningAgent(llm=llm, env=env)
        result = agent.run_episode(task_id=task.task_id, task_nl=task.natural_language)
        replans = result.replans_used
    else:
        raise ValueError(f"Unknown architecture: {architecture}")

    # Score the outcome
    metrics = score_run(
        task=task,
        catalogue=catalogue,
        architecture=architecture,
        noise_level=noise_level,
        seed=seed,
        env_steps=result.steps_taken,
        terminated=result.terminated,
        terminal_reason=result.terminal_reason,
        purchased_asin=result.purchased_asin,
        llm_calls=result.llm_calls,
        input_tokens=result.total_input_tokens,
        output_tokens=result.total_output_tokens,
        wall_clock_seconds=result.wall_clock_seconds,
        parse_errors=result.parse_errors,
        replans_used=replans,
    )

    # Persist trace
    write_trace(
        out_dir=traces_dir,
        task_id=task.task_id,
        architecture=architecture,
        noise_level=noise_level,
        seed=seed,
        trace_steps=env.trace,
        metadata={
            "task_id": task.task_id,
            "architecture": architecture,
            "noise_level": noise_level,
            "seed": seed,
            "task_nl": task.natural_language,
            "constraints": task.constraints.model_dump(),
            "preference": task.preference,
            "optimal_asins": task.optimal_asins,
            "valid_set_size": len(task.valid_set),
            "purchased_asin": result.purchased_asin,
            "hard_success": metrics.hard_success,
            "preference_success": metrics.preference_success,
            "input_tokens": result.total_input_tokens,
            "output_tokens": result.total_output_tokens,
            "llm_calls": result.llm_calls,
        },
    )

    return metrics


def run_pilot(
    tasks: list[Task],
    architectures: list[str],
    noise_levels: list[float],
    seeds: list[int],
    catalogue: pd.DataFrame,
    llm: BedrockClient,
    traces_dir: Path,
    results_path: Path,
) -> list[RunMetrics]:
    """Run the full pilot matrix. Returns all run metrics."""
    total = len(tasks) * len(architectures) * len(noise_levels) * len(seeds)
    logger.info("Pilot matrix: %d tasks × %d archs × %d noise × %d seeds = %d runs",
                len(tasks), len(architectures), len(noise_levels), len(seeds), total)

    all_metrics: list[RunMetrics] = []
    completed = 0

    for task in tasks:
        for arch in architectures:
            for noise in noise_levels:
                for seed in seeds:
                    completed += 1
                    logger.info("[%d/%d] task=%s arch=%s noise=%s seed=%d",
                                completed, total, task.task_id, arch, noise, seed)
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
                        logger.info("  → hard=%s pref=%.1f steps=%d llm_calls=%d tokens=%d",
                                    metrics.hard_success, metrics.preference_success,
                                    metrics.env_steps, metrics.llm_calls, metrics.total_tokens)

                        # Write results incrementally to survive crashes
                        results_path.parent.mkdir(parents=True, exist_ok=True)
                        results_path.write_text(
                            json.dumps([asdict(m) for m in all_metrics], indent=2),
                            encoding="utf-8",
                        )
                    except Exception:
                        logger.exception("Run failed: %s/%s/noise=%s/seed=%s — continuing",
                                         task.task_id, arch, noise, seed)

    logger.info("Pilot complete. %d runs scored.", len(all_metrics))
    logger.info(llm.cost_summary())
    return all_metrics
