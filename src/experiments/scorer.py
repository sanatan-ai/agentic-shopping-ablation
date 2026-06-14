"""Scoring: computes per-run metrics from an episode + task ground truth.

Maps to the 9 evaluation metrics locked in the proposal:
  Success: Hard Success, Preference Success, Constraint Satisfaction Rate
  Efficiency: Mean Tool Calls, Mean Tokens, Mean Wall-Clock
  Robustness: Success vs Noise (computed at aggregation), Degradation Slope (later)
  Behavioural: Failure Mode (categorical label per run)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from src.task_suite.models import Task


@dataclass
class RunMetrics:
    """All per-run metrics for a single (task, agent, noise, seed) cell."""

    # Identity
    task_id: str
    architecture: str  # 'reactive' | 'planning'
    noise_level: float
    seed: int

    # Success metrics
    hard_success: bool                # purchased ASIN in valid_set?
    preference_success: float         # 1.0 if optimal, 0.0 otherwise (binary version)
    constraint_satisfaction: float    # fraction of hard constraints satisfied by purchase

    # Efficiency metrics
    env_steps: int
    llm_calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    wall_clock_seconds: float

    # Behavioural / diagnostic
    terminated: bool
    terminal_reason: Optional[str]
    purchased_asin: Optional[str]
    failure_mode: str                  # 'success' | 'no_purchase' | 'wrong_product' | 'budget' | etc.
    parse_errors: int = 0
    replans_used: Optional[int] = None  # planning only


# ---------------------------------------------------------------------- #
# Per-purchase scoring                                                   #
# ---------------------------------------------------------------------- #

def _check_constraints(
    purchased_row: pd.Series, task: Task
) -> tuple[bool, float]:
    """Return (hard_success, constraint_satisfaction_rate) for a purchased product.

    A purchase counts as Hard Success only if EVERY hard constraint is satisfied.
    Constraint Satisfaction is the fraction of constraints satisfied (always between
    1/N and 1.0 — bucket is always satisfied since purchase is from catalogue).
    """
    c = task.constraints
    checks: list[bool] = []

    # Bucket (always present)
    checks.append(str(purchased_row["bucket"]) == c.bucket)

    # Price cap (always present)
    checks.append(float(purchased_row["price"]) <= c.max_price)

    # Optional: stars
    if c.min_stars is not None:
        checks.append(float(purchased_row["stars"]) >= c.min_stars)

    # Optional: brand (case-insensitive)
    if c.brand is not None:
        checks.append(str(purchased_row["brand"]).lower() == c.brand.lower())

    hard = all(checks)
    rate = sum(checks) / len(checks)
    return hard, rate


def _classify_failure(
    hard: bool, terminated: bool, terminal_reason: Optional[str], purchased: Optional[str]
) -> str:
    """Map an episode outcome to a categorical failure-mode label."""
    if hard:
        return "success"
    if purchased is None:
        if terminal_reason == "budget_exhausted":
            return "budget_exhausted"
        if terminal_reason == "malformed_limit":
            return "malformed_limit"
        if terminal_reason == "replan_limit_exceeded":
            return "replan_limit_exceeded"
        return f"no_purchase:{terminal_reason or 'unknown'}"
    # Purchased something but it doesn't satisfy all hard constraints
    return "wrong_product"


def score_run(
    task: Task,
    catalogue: pd.DataFrame,
    architecture: str,
    noise_level: float,
    seed: int,
    # Episode outcome — fields common to both reactive and planning results
    env_steps: int,
    terminated: bool,
    terminal_reason: Optional[str],
    purchased_asin: Optional[str],
    llm_calls: int,
    input_tokens: int,
    output_tokens: int,
    wall_clock_seconds: float,
    parse_errors: int = 0,
    replans_used: Optional[int] = None,
) -> RunMetrics:
    """Score a single completed run, producing all per-run metrics."""
    hard = False
    pref = 0.0
    csr = 0.0

    if purchased_asin is not None:
        sub = catalogue[catalogue["asin"] == purchased_asin]
        if not sub.empty:
            row = sub.iloc[0]
            hard, csr = _check_constraints(row, task)
            pref = 1.0 if purchased_asin in task.optimal_asins else 0.0

    failure = _classify_failure(hard, terminated, terminal_reason, purchased_asin)

    return RunMetrics(
        task_id=task.task_id,
        architecture=architecture,
        noise_level=noise_level,
        seed=seed,
        hard_success=hard,
        preference_success=pref,
        constraint_satisfaction=csr,
        env_steps=env_steps,
        llm_calls=llm_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        wall_clock_seconds=wall_clock_seconds,
        terminated=terminated,
        terminal_reason=terminal_reason,
        purchased_asin=purchased_asin,
        failure_mode=failure,
        parse_errors=parse_errors,
        replans_used=replans_used,
    )
