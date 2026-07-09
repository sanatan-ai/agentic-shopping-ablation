"""Paired statistical analysis of the full-experiment results.

For each (noise_level, metric) cell, computes:
  - Paired means (reactive, planning) and their difference
  - 95% bootstrap CI for the difference (percentile method, 10,000 resamples)
  - Wilcoxon signed-rank test on paired differences
  - Cliff's delta effect size

Pairing is by (task_id, seed): the same task with the same noise seed run
against both architectures — the natural comparison since both agents faced
identical inputs.

Multiple-comparisons correction: Bonferroni across all tests reported in
this analysis. Conservative and easy to defend.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

# Metrics of interest — the three success measures
SUCCESS_METRICS = [
    ("hard_success", "Hard Success"),
    ("preference_success", "Preference Success"),
    ("constraint_satisfaction", "Constraint Satisfaction"),
]

# Cliff's delta magnitude interpretation (Romano et al. 2006)
_CLIFF_THRESHOLDS = [
    (0.147, "negligible"),
    (0.33, "small"),
    (0.474, "medium"),
    (1.0, "large"),
]

BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 42


@dataclass
class ComparisonResult:
    """One paired comparison (reactive vs planning) for a single (noise, metric)."""

    noise_level: float
    metric: str
    metric_label: str
    n_pairs: int
    reactive_mean: float
    planning_mean: float
    mean_diff: float               # reactive - planning
    ci_lower: float                # 95% bootstrap CI lower
    ci_upper: float                # 95% bootstrap CI upper
    wilcoxon_stat: float
    wilcoxon_p: float
    wilcoxon_p_bonferroni: float   # p * n_tests (capped at 1.0)
    cliffs_delta: float
    cliffs_delta_magnitude: str
    significant_at_005_bonferroni: bool


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """Cliff's delta: P(X > Y) - P(X < Y). Range [-1, +1].

    For binary/ordinal paired data this is a robust effect-size measure
    that doesn't assume any distribution.
    """
    n_x, n_y = len(x), len(y)
    if n_x == 0 or n_y == 0:
        return 0.0
    # Broadcast comparison across all (x_i, y_j) pairs
    x = np.asarray(x).reshape(-1, 1)
    y = np.asarray(y).reshape(1, -1)
    greater = np.sum(x > y)
    less = np.sum(x < y)
    return (greater - less) / (n_x * n_y)


def _cliffs_magnitude(delta: float) -> str:
    """Rough magnitude label per Romano et al. 2006."""
    abs_delta = abs(delta)
    for threshold, label in _CLIFF_THRESHOLDS:
        if abs_delta < threshold:
            return label
    return "large"


def bootstrap_ci_paired(
    diffs: np.ndarray,
    n_iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
    ci_level: float = 0.95,
) -> tuple[float, float]:
    """Percentile bootstrap CI for the mean of paired differences."""
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot_means = np.empty(n_iterations)
    for i in range(n_iterations):
        idx = rng.integers(0, n, size=n)
        boot_means[i] = diffs[idx].mean()
    alpha = 1 - ci_level
    lower = np.percentile(boot_means, 100 * alpha / 2)
    upper = np.percentile(boot_means, 100 * (1 - alpha / 2))
    return float(lower), float(upper)


def pair_by_task_seed(
    df: pd.DataFrame,
    metric: str,
    noise_level: float,
) -> pd.DataFrame:
    """Return a DataFrame with one row per (task_id, seed) and columns for each arch.

    Pairing is exact: both architectures ran on the same 50 tasks × 3 seeds = 150 cells
    at each noise level. If any pair is missing (e.g., a failed run), it is dropped.
    """
    sub = df[df["noise_level"] == noise_level]
    pivot = sub.pivot_table(
        index=["task_id", "seed"],
        columns="architecture",
        values=metric,
        aggfunc="mean",  # tolerates duplicates; in practice there aren't any
    )
    # Drop pairs missing either architecture
    pivot = pivot.dropna(subset=["reactive", "planning"])
    return pivot.reset_index()


def compare_one_cell(
    df: pd.DataFrame,
    noise_level: float,
    metric: str,
    metric_label: str,
) -> ComparisonResult:
    """Compute all statistics for a single (noise_level, metric) cell."""
    paired = pair_by_task_seed(df, metric, noise_level)
    reactive_vals = paired["reactive"].values
    planning_vals = paired["planning"].values
    diffs = reactive_vals - planning_vals
    n = len(diffs)

    # Bootstrap CI on the mean of paired diffs
    ci_lower, ci_upper = bootstrap_ci_paired(diffs)

    # Wilcoxon signed-rank test on paired differences
    # (zero_method="wilcox" drops zero-differences by default, matching classical rank test)
    if np.all(diffs == 0):
        # All identical -> no signed rank possible; return degenerate result
        w_stat, w_p = 0.0, 1.0
    else:
        w_stat, w_p = stats.wilcoxon(reactive_vals, planning_vals, zero_method="wilcox")

    # Cliff's delta on unpaired ordinal comparison
    delta = cliffs_delta(reactive_vals, planning_vals)

    return ComparisonResult(
        noise_level=noise_level,
        metric=metric,
        metric_label=metric_label,
        n_pairs=n,
        reactive_mean=float(reactive_vals.mean()),
        planning_mean=float(planning_vals.mean()),
        mean_diff=float(diffs.mean()),
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        wilcoxon_stat=float(w_stat),
        wilcoxon_p=float(w_p),
        wilcoxon_p_bonferroni=1.0,  # Filled in later based on total tests
        cliffs_delta=float(delta),
        cliffs_delta_magnitude=_cliffs_magnitude(delta),
        significant_at_005_bonferroni=False,
    )


def apply_bonferroni(results: list[ComparisonResult]) -> None:
    """Apply Bonferroni correction: p_corrected = min(1, p * n_tests)."""
    n_tests = len(results)
    for r in results:
        r.wilcoxon_p_bonferroni = min(1.0, r.wilcoxon_p * n_tests)
        r.significant_at_005_bonferroni = r.wilcoxon_p_bonferroni < 0.05


def analyse(
    results_json_path: Path,
    noise_levels: Optional[list[float]] = None,
) -> list[ComparisonResult]:
    """Run the full paired analysis over all (noise, metric) cells.

    Returns a list of ComparisonResult, one per cell.
    """
    raw = json.loads(Path(results_json_path).read_text(encoding="utf-8"))
    df = pd.DataFrame(raw)
    logger.info("Loaded %d run records from %s", len(df), results_json_path)

    if noise_levels is None:
        noise_levels = sorted(df["noise_level"].unique())

    all_results: list[ComparisonResult] = []
    for noise in noise_levels:
        for metric, label in SUCCESS_METRICS:
            result = compare_one_cell(df, noise_level=noise, metric=metric, metric_label=label)
            all_results.append(result)
            logger.info(
                "  noise=%.1f %s: n=%d, reactive=%.3f, planning=%.3f, "
                "diff=%.3f (95%% CI [%.3f, %.3f]), Wilcoxon p=%.4g, Cliff's δ=%.3f (%s)",
                noise, label, result.n_pairs,
                result.reactive_mean, result.planning_mean,
                result.mean_diff, result.ci_lower, result.ci_upper,
                result.wilcoxon_p, result.cliffs_delta, result.cliffs_delta_magnitude,
            )

    apply_bonferroni(all_results)
    return all_results


def write_analysis_report(
    results: list[ComparisonResult],
    out_path: Path,
    title: str = "Statistical Analysis of Full Experiment Results",
) -> None:
    """Render a markdown report with the analysis table + interpretation guide."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# {title}\n")
    lines.append(f"**Total statistical tests reported:** {len(results)}")
    lines.append(f"**Bonferroni correction applied.** α_corrected = 0.05 / {len(results)} = {0.05/len(results):.4g}\n")

    lines.append("## Methodology\n")
    lines.append(
        "Pairing structure: each (task_id, seed) combination provides one paired observation "
        "of (reactive, planning) at a given noise level. For 50 tasks × 3 seeds = 150 pairs per cell.\n"
    )
    lines.append("Three success metrics analysed at four noise levels → 12 tests total.\n")
    lines.append("Test details:")
    lines.append("- **Wilcoxon signed-rank test** on paired differences (non-parametric).")
    lines.append("- **Cliff's δ**: effect size, range [−1, +1]. Positive = reactive > planning.")
    lines.append(f"- **95% CI for mean difference**: percentile bootstrap, {BOOTSTRAP_ITERATIONS:,} resamples, seed={BOOTSTRAP_SEED}.")
    lines.append("- **Bonferroni**: p_corrected = min(1, p × n_tests). Conservative multiple-comparisons correction.\n")

    lines.append("## Cliff's δ magnitude interpretation (Romano et al. 2006)\n")
    lines.append("| \\|δ\\| range | Magnitude |")
    lines.append("|---|---|")
    lines.append("| < 0.147 | negligible |")
    lines.append("| 0.147 – 0.33 | small |")
    lines.append("| 0.33 – 0.474 | medium |")
    lines.append("| ≥ 0.474 | large |\n")

    lines.append("## Results\n")
    lines.append("Δ Mean = reactive_mean − planning_mean. Positive = reactive better on that metric.\n")

    for metric_key, label in SUCCESS_METRICS:
        lines.append(f"### {label}\n")
        lines.append("| Noise | n | Reactive | Planning | Δ Mean | 95% CI | Wilcoxon p | Bonferroni p | Cliff's δ | Effect | Sig. (α=0.05, Bonf.) |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        subset = [r for r in results if r.metric == metric_key]
        for r in subset:
            sig_mark = "✓" if r.significant_at_005_bonferroni else "✗"
            p_bonf_str = f"{r.wilcoxon_p_bonferroni:.4g}" if r.wilcoxon_p_bonferroni < 1.0 else "1.0"
            lines.append(
                f"| {r.noise_level:.1f} | {r.n_pairs} "
                f"| {r.reactive_mean:.3f} | {r.planning_mean:.3f} "
                f"| {r.mean_diff:+.3f} "
                f"| [{r.ci_lower:+.3f}, {r.ci_upper:+.3f}] "
                f"| {r.wilcoxon_p:.4g} | {p_bonf_str} "
                f"| {r.cliffs_delta:+.3f} | {r.cliffs_delta_magnitude} "
                f"| {sig_mark} |"
            )
        lines.append("")

    # Summary observations
    lines.append("## Summary\n")
    n_sig = sum(1 for r in results if r.significant_at_005_bonferroni)
    n_total = len(results)
    lines.append(f"- **{n_sig} of {n_total}** tests reach statistical significance after Bonferroni correction (α=0.05).")

    # Direction of significant effects
    sig_positive = [r for r in results if r.significant_at_005_bonferroni and r.mean_diff > 0]
    sig_negative = [r for r in results if r.significant_at_005_bonferroni and r.mean_diff < 0]
    lines.append(f"- Of the significant tests, {len(sig_positive)} favour reactive, {len(sig_negative)} favour planning.")

    # Large-effect count
    n_large = sum(1 for r in results if r.cliffs_delta_magnitude == "large")
    n_medium = sum(1 for r in results if r.cliffs_delta_magnitude == "medium")
    lines.append(f"- Cliff's δ magnitudes: {n_large} large, {n_medium} medium, remainder small/negligible.")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def results_to_dataframe(results: list[ComparisonResult]) -> pd.DataFrame:
    """Convert results list to a DataFrame for CSV output or further analysis."""
    return pd.DataFrame([r.__dict__ for r in results])