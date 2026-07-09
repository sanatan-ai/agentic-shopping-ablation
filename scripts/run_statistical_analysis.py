"""Statistical analysis of the full experiment results.

Runs paired Wilcoxon + Cliff's delta + bootstrap CIs across all
(noise_level, success_metric) cells. Applies Bonferroni correction.

Outputs:
  reports/statistical_analysis_report.md    — human-readable report
  data/results/statistical_analysis.csv     — machine-readable per-cell results

Usage:
    uv run python scripts/run_statistical_analysis.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from src.experiments.stats_analysis import (
    analyse,
    results_to_dataframe,
    write_analysis_report,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_JSON = PROJECT_ROOT / "data" / "results" / "full_experiment_results.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "statistical_analysis_report.md"
CSV_PATH = PROJECT_ROOT / "data" / "results" / "statistical_analysis.csv"


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("run_statistical_analysis")

    if not RESULTS_JSON.exists():
        log.error("Results file not found at %s", RESULTS_JSON)
        return 1

    log.info("Loading full-experiment results from %s", RESULTS_JSON)
    results = analyse(RESULTS_JSON)

    log.info("Writing markdown report to %s", REPORT_PATH)
    write_analysis_report(results, REPORT_PATH, title="Statistical Analysis of Full Experiment Results")

    log.info("Writing CSV to %s", CSV_PATH)
    df = results_to_dataframe(results)
    df.to_csv(CSV_PATH, index=False)

    log.info("=" * 70)
    log.info("Analysis complete. %d tests computed, %d significant after Bonferroni.",
             len(results), sum(1 for r in results if r.significant_at_005_bonferroni))
    log.info("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())