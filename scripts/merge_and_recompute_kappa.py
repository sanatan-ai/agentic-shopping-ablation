"""Merge Category 6 (replan_treadmill) into Category 3 (failed_narrowing),
then recompute Cohen's kappa on the merged 9-category taxonomy.

Rationale
---------
The two-pass qualitative coding process revealed that Categories 3 and 6
have overlapping signatures on planning traces that fail through bad
filter composition after multiple replans. Post-hoc merging is authorised
by the project supervisor as a principled response to a taxonomy design
issue surfaced by the reliability measurement itself. The methodology
write-up will describe the full process transparently.

What this script does
---------------------
1. Backs up coding_pass1.csv and coding_pass2.csv (once — idempotent)
2. Rewrites every row where category_num == 6 to category_num == 3,
   updating category_name to a merged label
3. Recomputes Cohen's kappa on the merged codings
4. Prints the confusion matrix, agreement rate, and post-merge kappa
5. Writes a new report to reports/kappa_analysis_report_postmerge.md

Merged category
---------------
Old Category 3: failed_narrowing
Old Category 6: replan_treadmill
New Category 3: filter_composition_failure  (subsumes both)

Category 6 becomes a retired category. All references to it should be
removed from any user-facing taxonomy going forward.

Usage:
    uv run python scripts/merge_and_recompute_kappa.py
"""
from __future__ import annotations

import csv
import logging
import shutil
import sys
from collections import Counter, defaultdict
from math import sqrt
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PASS1_CSV = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass1.csv"
PASS2_CSV = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass2.csv"
PASS1_BAK = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass1.csv.pre_merge.bak"
PASS2_BAK = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass2.csv.pre_merge.bak"
REPORT_MD = PROJECT_ROOT / "reports" / "kappa_analysis_report_postmerge.md"

MERGED_CATEGORY_NUM = 3
MERGED_CATEGORY_NAME = "filter_composition_failure"
RETIRED_CATEGORY_NUM = 6


def cohens_kappa(cat1: list[int], cat2: list[int]) -> tuple[float, float]:
    """Return (kappa, agreement_rate) for two paired lists of category ints."""
    assert len(cat1) == len(cat2)
    n = len(cat1)
    if n == 0:
        return 0.0, 0.0

    agree = sum(1 for a, b in zip(cat1, cat2) if a == b)
    p_o = agree / n

    c1 = Counter(cat1)
    c2 = Counter(cat2)
    all_cats = set(c1) | set(c2)
    p_e = sum((c1[c] / n) * (c2[c] / n) for c in all_cats)

    if p_e >= 1.0:
        return 1.0, p_o
    kappa = (p_o - p_e) / (1.0 - p_e)
    return kappa, p_o


def kappa_band(k: float) -> str:
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


def _rewrite_csv(csv_path: Path, backup_path: Path, log: logging.Logger) -> int:
    """Rewrite csv_path applying the 6→3 merge. Backs up first if not already backed up.

    Returns the number of rows changed.
    """
    if not csv_path.exists():
        log.error("CSV missing: %s", csv_path)
        return -1

    # Backup once
    if backup_path.exists():
        log.info("Backup already exists at %s (leaving untouched)", backup_path.name)
    else:
        shutil.copy2(csv_path, backup_path)
        log.info("Backed up %s → %s", csv_path.name, backup_path.name)

    # Load rows
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    changed = 0
    for row in rows:
        try:
            cat_num = int(row["category_num"])
        except (ValueError, KeyError):
            continue
        if cat_num == RETIRED_CATEGORY_NUM:
            row["category_num"] = str(MERGED_CATEGORY_NUM)
            row["category_name"] = MERGED_CATEGORY_NAME
            changed += 1
        elif cat_num == MERGED_CATEGORY_NUM:
            # Rename in place to match new taxonomy label
            row["category_name"] = MERGED_CATEGORY_NAME

    # Write back
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    log.info("Rewrote %s: %d rows changed (%d were originally category 6)",
             csv_path.name, changed, changed)
    return changed


def _load_pairs(csv_path: Path) -> dict[str, int]:
    """Return {trace_path: category_num} from a coding CSV."""
    out: dict[str, int] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out[row["trace_path"]] = int(row["category_num"])
    return out


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("merge_and_recompute")

    # Step 1: pre-merge sanity — read current pass 1 counts of category 6
    log.info("=" * 70)
    log.info("STEP 1 — Pre-merge sanity check")
    log.info("=" * 70)

    if not PASS1_CSV.exists() or not PASS2_CSV.exists():
        log.error("One or both coding CSVs missing.")
        return 1

    pre_p1 = _load_pairs(PASS1_CSV)
    pre_p2 = _load_pairs(PASS2_CSV)
    pre_p1_cat6 = sum(1 for v in pre_p1.values() if v == RETIRED_CATEGORY_NUM)
    pre_p2_cat6 = sum(1 for v in pre_p2.values() if v == RETIRED_CATEGORY_NUM)
    log.info("Pass 1: %d rows category=6 will be merged to category=3", pre_p1_cat6)
    log.info("Pass 2: %d rows category=6 will be merged to category=3", pre_p2_cat6)

    # Step 2: apply the merge
    log.info("")
    log.info("=" * 70)
    log.info("STEP 2 — Apply merge (6 → 3, category_name → %s)", MERGED_CATEGORY_NAME)
    log.info("=" * 70)
    _rewrite_csv(PASS1_CSV, PASS1_BAK, log)
    _rewrite_csv(PASS2_CSV, PASS2_BAK, log)

    # Step 3: recompute kappa on merged data
    log.info("")
    log.info("=" * 70)
    log.info("STEP 3 — Recompute Cohen's kappa on merged data")
    log.info("=" * 70)

    p1 = _load_pairs(PASS1_CSV)
    p2 = _load_pairs(PASS2_CSV)
    common = sorted(set(p1) & set(p2))
    cats1 = [p1[t] for t in common]
    cats2 = [p2[t] for t in common]

    kappa, agree = cohens_kappa(cats1, cats2)

    log.info("Traces in both passes: %d", len(common))
    log.info("Agreement rate: %.1f%% (%d/%d)",
             agree * 100, int(agree * len(common)), len(common))
    log.info("Cohen's kappa:  %.3f  (%s)", kappa, kappa_band(kappa))

    # Confusion matrix
    log.info("")
    log.info("Confusion matrix (row = Pass 1, col = Pass 2):")
    all_cats = sorted(set(cats1) | set(cats2))
    matrix: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for a, b in zip(cats1, cats2):
        matrix[a][b] += 1

    log.info("     P2→ " + "  ".join(f"{c:>3d}" for c in all_cats))
    for a in all_cats:
        row = "  P1 " + f"{a:>3d}:" + "  ".join(f"{matrix[a][b]:>3d}" for b in all_cats)
        log.info(row)

    disagreements = [(t, cats1[i], cats2[i]) for i, t in enumerate(common)
                     if cats1[i] != cats2[i]]
    log.info("")
    log.info("Disagreements (%d):", len(disagreements))
    for t, c1, c2 in disagreements:
        log.info("  %s :  P1=%d ↔ P2=%d", Path(t).name, c1, c2)

    # Distribution of Pass 1 codings across merged taxonomy
    log.info("")
    log.info("Pass 1 distribution across merged taxonomy:")
    p1_dist = Counter(cats1)
    for c in sorted(p1_dist):
        log.info("  Category %d: %d", c, p1_dist[c])

    log.info("")
    log.info("Pass 2 distribution across merged taxonomy:")
    p2_dist = Counter(cats2)
    for c in sorted(p2_dist):
        log.info("  Category %d: %d", c, p2_dist[c])

    # Constraint check
    log.info("")
    log.info("=" * 70)
    if kappa >= 0.60:
        log.info("✓ POST-MERGE κ = %.3f MEETS the 0.60 threshold set by supervisor.", kappa)
        log.info("  Proceed to draft Section 5.6 and taxonomy revision.")
    else:
        log.warning("⚠ POST-MERGE κ = %.3f is BELOW the 0.60 threshold.", kappa)
        log.warning("  Do NOT merge further categories speculatively.")
        log.warning("  Share this confusion matrix with the supervisor before writing.")
    log.info("=" * 70)

    # Write markdown report
    _write_report(REPORT_MD, kappa, agree, len(common), all_cats, matrix,
                  disagreements, p1_dist, p2_dist)
    log.info("Report written to %s", REPORT_MD)

    return 0


def _write_report(path: Path, kappa: float, agree: float, n: int,
                  all_cats: list[int], matrix, disagreements,
                  p1_dist: Counter, p2_dist: Counter) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Post-Merge Intra-Rater Agreement Analysis\n")
    lines.append("**Coder:** Sanatan Shrivastava  ")
    lines.append(f"**Traces coded in both passes:** {n}  ")
    lines.append("**Merge applied:** Category 6 (`replan_treadmill`) merged into Category 3 "
                 "(`failed_narrowing`), renamed `filter_composition_failure`. "
                 "Merge authorised by project supervisor after Pass 1/Pass 2 confusion pattern "
                 "revealed systematic overlap.\n")
    lines.append("## Results (post-merge)\n")
    lines.append(f"- **Agreement rate:** {agree*100:.1f}% ({int(agree*n)}/{n})")
    lines.append(f"- **Cohen's κ:** {kappa:.3f}")
    lines.append(f"- **Interpretation:** {kappa_band(kappa)} agreement (Landis and Koch, 1977)\n")
    if kappa >= 0.60:
        lines.append(f"Post-merge κ = {kappa:.3f} exceeds the 0.60 threshold, indicating "
                     "moderate-or-better intra-rater agreement on the revised taxonomy.\n")
    else:
        lines.append(f"Post-merge κ = {kappa:.3f} remains below the 0.60 threshold. "
                     "The confusion matrix should be examined before any further taxonomy revision.\n")

    lines.append("## Confusion matrix (post-merge)\n")
    lines.append("Rows = Pass 1 category, Columns = Pass 2 category.\n")
    lines.append("| P1 \\ P2 | " + " | ".join(str(c) for c in all_cats) + " |")
    lines.append("|---" * (len(all_cats) + 1) + "|")
    for a in all_cats:
        row = f"| **{a}** | " + " | ".join(str(matrix[a][b]) for b in all_cats) + " |"
        lines.append(row)

    lines.append("\n## Distributions\n")
    lines.append("**Pass 1:** " + ", ".join(f"C{c}: {p1_dist[c]}" for c in sorted(p1_dist)))
    lines.append("")
    lines.append("**Pass 2:** " + ", ".join(f"C{c}: {p2_dist[c]}" for c in sorted(p2_dist)))

    lines.append("\n## Disagreements (post-merge)\n")
    if not disagreements:
        lines.append("None.\n")
    else:
        lines.append("| Trace | Pass 1 | Pass 2 |")
        lines.append("|---|---|---|")
        for t, c1, c2 in disagreements:
            lines.append(f"| `{Path(t).name}` | {c1} | {c2} |")

    lines.append("\n## Process disclosure\n")
    lines.append("The original 10-category taxonomy applied to Pass 1 produced κ = 0.061 "
                 "on the 24 paired codings. The confusion matrix showed a systematic pattern: "
                 "every Pass 1 coding of Category 6 (`replan_treadmill`, n = 5) was reclassified "
                 "as Category 3 (`failed_narrowing`) in Pass 2. Trace inspection confirmed that "
                 "these categories have overlapping signatures on planning traces that fail through "
                 "poor filter composition after multiple replans. Under supervisor authorisation, "
                 "the two categories were merged into a single category "
                 "(`filter_composition_failure`) and κ was recomputed on the resulting "
                 "9-category taxonomy.")

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())