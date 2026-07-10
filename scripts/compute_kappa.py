"""Compute Cohen's kappa between two coding passes.

Compares coding_pass1.csv and coding_pass2.csv on the intersection of
trace_paths coded in both. Reports:
  - Agreement rate (raw percentage)
  - Cohen's kappa
  - Kappa interpretation (Landis & Koch 1977)
  - Per-category confusion matrix
  - List of disagreements for qualitative review

Usage:
    uv run python scripts/compute_kappa.py
"""
from __future__ import annotations

import csv
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PASS1_CSV = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass1.csv"
PASS2_CSV = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass2.csv"
REPORT_MD = PROJECT_ROOT / "reports" / "kappa_analysis_report.md"


def _load(csv_path: Path) -> dict[str, dict]:
    """Load a coding CSV into {trace_path: row_dict}."""
    if not csv_path.exists():
        return {}
    out: dict[str, dict] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out[row["trace_path"]] = row
    return out


def cohens_kappa(cat1: list[int], cat2: list[int]) -> tuple[float, float]:
    """Compute Cohen's kappa and observed agreement rate.

    Returns (kappa, agreement_rate).
    """
    assert len(cat1) == len(cat2), "Category lists must be same length"
    n = len(cat1)
    if n == 0:
        return 0.0, 0.0

    # Observed agreement
    agree = sum(1 for a, b in zip(cat1, cat2) if a == b)
    p_o = agree / n

    # Expected agreement by chance
    counts1 = Counter(cat1)
    counts2 = Counter(cat2)
    all_cats = set(counts1) | set(counts2)
    p_e = sum(
        (counts1[c] / n) * (counts2[c] / n) for c in all_cats
    )

    if p_e >= 1.0:
        # All same category → kappa undefined but agreement is 1.0
        return 1.0, p_o

    kappa = (p_o - p_e) / (1.0 - p_e)
    return kappa, p_o


def _kappa_magnitude(k: float) -> str:
    """Landis & Koch 1977 interpretation."""
    if k < 0:
        return "poor (worse than chance)"
    if k < 0.20:
        return "slight"
    if k < 0.40:
        return "fair"
    if k < 0.60:
        return "moderate"
    if k < 0.80:
        return "substantial"
    if k < 1.00:
        return "almost perfect"
    return "perfect"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("compute_kappa")

    if not PASS1_CSV.exists():
        log.error("Pass 1 CSV missing at %s", PASS1_CSV)
        return 1
    if not PASS2_CSV.exists():
        log.error("Pass 2 CSV missing at %s", PASS2_CSV)
        log.error("Run pass 2 first, then re-run this script.")
        return 1

    p1 = _load(PASS1_CSV)
    p2 = _load(PASS2_CSV)

    common = sorted(set(p1) & set(p2))
    only_p1 = set(p1) - set(p2)
    only_p2 = set(p2) - set(p1)

    log.info("Pass 1 codings: %d", len(p1))
    log.info("Pass 2 codings: %d", len(p2))
    log.info("Traces coded in both: %d", len(common))
    if only_p1:
        log.warning("  %d only in pass 1 — excluded from analysis", len(only_p1))
    if only_p2:
        log.warning("  %d only in pass 2 — excluded from analysis", len(only_p2))

    if not common:
        log.error("No overlap between passes. Cannot compute kappa.")
        return 1

    cats1 = [int(p1[t]["category_num"]) for t in common]
    cats2 = [int(p2[t]["category_num"]) for t in common]

    kappa, agree = cohens_kappa(cats1, cats2)

    log.info("=" * 70)
    log.info("Agreement rate: %.1f%% (%d/%d)", agree * 100, int(agree * len(common)), len(common))
    log.info("Cohen's kappa:  %.3f  (%s)", kappa, _kappa_magnitude(kappa))
    log.info("=" * 70)

    # Per-category breakdown
    log.info("Confusion matrix (row = pass 1, col = pass 2):")
    all_cats = sorted(set(cats1) | set(cats2))
    matrix: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for a, b in zip(cats1, cats2):
        matrix[a][b] += 1

    header = "     P2→ " + "  ".join(f"{c:>3d}" for c in all_cats)
    log.info(header)
    for a in all_cats:
        row = "  P1 " + f"{a:>3d}:" + "  ".join(f"{matrix[a][b]:>3d}" for b in all_cats)
        log.info(row)

    # Disagreements
    disagreements = [
        (t, cats1[i], cats2[i]) for i, t in enumerate(common) if cats1[i] != cats2[i]
    ]
    log.info("")
    log.info("Disagreements (%d):", len(disagreements))
    for t, c1, c2 in disagreements[:20]:
        log.info("  %s :  P1=%d ↔ P2=%d", t, c1, c2)
    if len(disagreements) > 20:
        log.info("  ... and %d more", len(disagreements) - 20)

    # Write report
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Intra-Rater Agreement Analysis\n")
    lines.append(f"**Coder:** Sanatan Shrivastava  ")
    lines.append(f"**Pass 1 codings:** {len(p1)}  ")
    lines.append(f"**Pass 2 codings:** {len(p2)}  ")
    lines.append(f"**Traces in both passes:** {len(common)}\n")
    lines.append("## Results\n")
    lines.append(f"- **Agreement rate:** {agree*100:.1f}% ({int(agree*len(common))}/{len(common)})")
    lines.append(f"- **Cohen's κ:** {kappa:.3f}")
    lines.append(f"- **Interpretation:** {_kappa_magnitude(kappa)} agreement (Landis & Koch, 1977)\n")

    if kappa >= 0.7:
        lines.append("κ ≥ 0.70 meets the threshold for substantial intra-rater reliability. "
                     "The failure-mode categorisation is consistent across the temporal gap "
                     "and can be relied upon in the thesis discussion.\n")
    else:
        lines.append(f"κ = {kappa:.3f} is below the 0.70 threshold typically taken as substantial. "
                     "Refinement of the operational definitions or re-coding of disagreements is "
                     "warranted before the categorisations are used in the thesis discussion.\n")

    lines.append("## Confusion matrix\n")
    lines.append("Rows = Pass 1 category, Columns = Pass 2 category.\n")
    lines.append("| P1 \\ P2 | " + " | ".join(str(c) for c in all_cats) + " |")
    lines.append("|---" * (len(all_cats) + 1) + "|")
    for a in all_cats:
        row = f"| **{a}** | " + " | ".join(str(matrix[a][b]) for b in all_cats) + " |"
        lines.append(row)

    lines.append("\n## Disagreements\n")
    if not disagreements:
        lines.append("None. All codings identical across passes.\n")
    else:
        lines.append("| Trace | Pass 1 | Pass 2 |")
        lines.append("|---|---|---|")
        for t, c1, c2 in disagreements:
            trace_short = t.split("/")[-1]
            lines.append(f"| `{trace_short}` | {c1} | {c2} |")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    log.info("")
    log.info("Report written to %s", REPORT_MD)
    return 0


if __name__ == "__main__":
    sys.exit(main())