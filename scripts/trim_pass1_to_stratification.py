"""Trim overfilled cells in coding_pass1.csv to exactly 3 per (arch, noise) cell.

Applies AFTER supplementary codings have been added to pass1.csv.

Rule: for each (arch, noise) cell, keep the first 3 rows in the order they
appear in the file. Preserves original coding order (early codings are
kept — later duplicates in the same cell are dropped).

Backs up the original CSV to coding_pass1.csv.pre_trim.bak before modifying.

Usage:
    uv run python scripts/trim_pass1_to_stratification.py
"""
from __future__ import annotations

import csv
import logging
import shutil
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PASS1_CSV = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass1.csv"
BACKUP_CSV = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass1.csv.pre_trim.bak"

TARGET_PER_CELL = 3
ARCHITECTURES = ["reactive", "planning"]
NOISE_LEVELS = ["0.0", "0.1", "0.2", "0.3"]


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S")
    log = logging.getLogger("trim_pass1_to_stratification")

    if not PASS1_CSV.exists():
        log.error("Pass 1 CSV not found at %s", PASS1_CSV)
        return 1

    # Read all rows preserving order
    with PASS1_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    log.info("Loaded %d existing codings from %s", len(rows), PASS1_CSV)

    # Sanity-check the cell distribution before trimming
    before: Counter = Counter()
    for r in rows:
        key = (r["architecture"], str(float(r["noise_level"])))
        before[key] += 1
    log.info("Before trim:")
    for arch in ARCHITECTURES:
        for noise in NOISE_LEVELS:
            n = before.get((arch, noise), 0)
            log.info("  %-9s noise=%s: %d", arch, noise, n)

    # Trim: keep first N per cell
    kept: list[dict] = []
    counts: Counter = Counter()
    dropped = 0
    for r in rows:
        key = (r["architecture"], str(float(r["noise_level"])))
        if counts[key] < TARGET_PER_CELL:
            kept.append(r)
            counts[key] += 1
        else:
            dropped += 1

    log.info("Kept %d rows, dropped %d duplicates beyond target", len(kept), dropped)

    # Sanity check: every cell must have exactly TARGET_PER_CELL
    incomplete_cells = []
    for arch in ARCHITECTURES:
        for noise in NOISE_LEVELS:
            n = counts.get((arch, noise), 0)
            if n != TARGET_PER_CELL:
                incomplete_cells.append((arch, noise, n))
    if incomplete_cells:
        log.warning("Some cells are not at target %d:", TARGET_PER_CELL)
        for arch, noise, n in incomplete_cells:
            log.warning("  %-9s noise=%s: %d", arch, noise, n)
        log.warning("Trimming aborted. Run resampler + coding to fill missing cells first.")
        return 1

    # Backup the original
    shutil.copy2(PASS1_CSV, BACKUP_CSV)
    log.info("Backed up original to %s", BACKUP_CSV)

    # Write trimmed
    with PASS1_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)

    log.info("Wrote %d rows to %s", len(kept), PASS1_CSV)
    log.info("=" * 70)
    log.info("Final cell distribution:")
    for arch in ARCHITECTURES:
        for noise in NOISE_LEVELS:
            n = counts.get((arch, noise), 0)
            log.info("  %-9s noise=%s: %d ✓", arch, noise, n)
    log.info("=" * 70)
    log.info("Pass 1 is now stratified 3-per-(arch,noise) — 24 rows total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())