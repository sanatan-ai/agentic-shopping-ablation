"""Results aggregation: turns a list of RunMetrics into the model-vs-baseline table.

Two outputs:
  1. results_per_run.csv — long-form, one row per run, all metrics
  2. results_summary.md — human-readable table aggregated by (architecture, noise_level)
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from statistics import mean, stdev

import pandas as pd

from src.experiments.scorer import RunMetrics


def runs_to_dataframe(runs: list[RunMetrics]) -> pd.DataFrame:
    """Flatten a list of RunMetrics into a DataFrame."""
    return pd.DataFrame([r.__dict__ for r in runs])


def _safe_mean(xs: list[float]) -> float:
    return mean(xs) if xs else 0.0


def _safe_std(xs: list[float]) -> float:
    return stdev(xs) if len(xs) > 1 else 0.0


def aggregate(runs: list[RunMetrics]) -> pd.DataFrame:
    """Aggregate by (architecture, noise_level). Returns a DataFrame of means."""
    df = runs_to_dataframe(runs)
    grouped = df.groupby(["architecture", "noise_level"]).agg(
        n_runs=("task_id", "count"),
        hard_success_rate=("hard_success", "mean"),
        preference_success_rate=("preference_success", "mean"),
        constraint_satisfaction_mean=("constraint_satisfaction", "mean"),
        env_steps_mean=("env_steps", "mean"),
        llm_calls_mean=("llm_calls", "mean"),
        total_tokens_mean=("total_tokens", "mean"),
        input_tokens_mean=("input_tokens", "mean"),
        output_tokens_mean=("output_tokens", "mean"),
        wall_clock_mean=("wall_clock_seconds", "mean"),
        parse_errors_mean=("parse_errors", "mean"),
    ).reset_index()
    return grouped


def write_summary_report(
    runs: list[RunMetrics],
    out_path: Path,
    title: str = "Pilot Results",
) -> None:
    """Render a markdown summary report with the per-(arch, noise) table + per-arch failure modes."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = runs_to_dataframe(runs)
    agg = aggregate(runs)

    lines: list[str] = []
    lines.append(f"# {title}\n")
    lines.append(f"**Total runs:** {len(runs)}")
    archs = sorted(df["architecture"].unique())
    noises = sorted(df["noise_level"].unique())
    lines.append(f"**Architectures:** {', '.join(archs)}")
    lines.append(f"**Noise levels:** {', '.join(f'{n:.2f}' for n in noises)}\n")

    # ----- Headline table: success metrics ----- #
    lines.append("## Success metrics\n")
    lines.append("| Architecture | Noise | n | Hard Success | Preference Success | Constraint Satisfaction |")
    lines.append("|---|---|---|---|---|---|")
    for _, row in agg.iterrows():
        lines.append(
            f"| {row['architecture']} | {row['noise_level']:.1f} | {int(row['n_runs'])} "
            f"| {row['hard_success_rate']:.2%} "
            f"| {row['preference_success_rate']:.2%} "
            f"| {row['constraint_satisfaction_mean']:.2%} |"
        )

    # ----- Efficiency table ----- #
    lines.append("\n## Efficiency metrics (means)\n")
    lines.append("| Architecture | Noise | n | Env Steps | LLM Calls | Total Tokens | Wall-Clock (s) |")
    lines.append("|---|---|---|---|---|---|---|")
    for _, row in agg.iterrows():
        lines.append(
            f"| {row['architecture']} | {row['noise_level']:.1f} | {int(row['n_runs'])} "
            f"| {row['env_steps_mean']:.2f} "
            f"| {row['llm_calls_mean']:.2f} "
            f"| {row['total_tokens_mean']:.0f} "
            f"| {row['wall_clock_mean']:.2f} |"
        )

    # ----- Failure-mode breakdown ----- #
    lines.append("\n## Failure-mode distribution (per architecture)\n")
    for arch in archs:
        sub = df[df["architecture"] == arch]
        modes = Counter(sub["failure_mode"])
        total = len(sub)
        lines.append(f"### {arch} (n={total})\n")
        for mode, count in sorted(modes.items(), key=lambda kv: -kv[1]):
            pct = 100.0 * count / total
            lines.append(f"- {mode}: {count} ({pct:.1f}%)")
        lines.append("")

    # ----- Per-task crosstab (compact) ----- #
    lines.append("\n## Per-task Hard Success crosstab (noise=0 only)\n")
    sub = df[df["noise_level"] == 0.0]
    if len(sub) > 0:
        pivot = sub.pivot_table(
            index="task_id",
            columns="architecture",
            values="hard_success",
            aggfunc="mean",
        ).fillna(-1.0)
        # Sort task_ids numerically (T001, T002...)
        pivot = pivot.reindex(sorted(pivot.index, key=lambda s: int(s[1:]) if s[1:].isdigit() else 0))
        cols = list(pivot.columns)
        lines.append("| Task | " + " | ".join(cols) + " |")
        lines.append("|---" + "|---" * len(cols) + "|")
        for task_id, row in pivot.iterrows():
            cells = []
            for c in cols:
                v = row[c]
                if v < 0:
                    cells.append("—")
                else:
                    cells.append("✓" if v >= 0.99 else "✗")
            lines.append(f"| {task_id} | " + " | ".join(cells) + " |")

    out_path.write_text("\n".join(lines), encoding="utf-8")
