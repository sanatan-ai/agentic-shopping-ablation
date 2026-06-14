"""Trace store: persists per-run interaction traces to JSONL files.

Each run produces one JSONL file at:
  data/traces/<task_id>__<architecture>__noise<p>__seed<n>.jsonl

Each line is a step record. Used downstream for failure-mode coding and
reproducibility / debugging.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.environment.models import TraceStep


def trace_filename(task_id: str, architecture: str, noise_level: float, seed: int) -> str:
    """Canonical filename for a run's trace."""
    return f"{task_id}__{architecture}__noise{noise_level}__seed{seed}.jsonl"


def write_trace(
    out_dir: Path,
    task_id: str,
    architecture: str,
    noise_level: float,
    seed: int,
    trace_steps: list[TraceStep],
    metadata: dict[str, Any],
) -> Path:
    """Persist a trace to JSONL. First line is metadata; subsequent lines are steps."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / trace_filename(task_id, architecture, noise_level, seed)

    with path.open("w", encoding="utf-8") as f:
        # Header line: metadata for the run
        f.write(json.dumps({"record_type": "metadata", **metadata}) + "\n")
        # One line per step
        for step in trace_steps:
            f.write(
                json.dumps(
                    {
                        "record_type": "step",
                        "step_index": step.step_index,
                        "thought": step.thought,
                        "action": step.action.model_dump() if step.action is not None else None,
                        "observation": step.observation.model_dump(),
                    }
                )
                + "\n"
            )

    return path
