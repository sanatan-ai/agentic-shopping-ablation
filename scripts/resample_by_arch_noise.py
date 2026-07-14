"""Resample additional failed traces to reach 3 per (architecture x noise) cell.

Reads existing coding_pass1.csv to see what's already covered. For each
(arch, noise) cell that has fewer than 3 codings, samples from failed runs
NOT already in the coded set. Writes a supplementary sample file the coding
tool can iterate through.

Design:
  - Only samples runs where hard_success = False
  - Only samples runs whose (task_id, architecture, noise, seed) key doesn't
    already appear in coding_pass1.csv
  - Deterministic (seed=42)
  - Output: data/qualitative_coding/sampled_traces_supplementary.json

Usage:
    uv run python scripts/resample_by_arch_noise.py
"""
from __future__ import annotations

import csv
import json
import logging
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_JSON = PROJECT_ROOT / "data" / "results" / "full_experiment_results.json"
PASS1_CSV = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass1.csv"
TRACES_DIR = PROJECT_ROOT / "data" / "traces_full"
SUPP_JSON = PROJECT_ROOT / "data" / "qualitative_coding" / "sampled_traces_supplementary.json"

TARGET_PER_CELL = 3
ARCHITECTURES = ["reactive", "planning"]
NOISE_LEVELS = [0.0, 0.1, 0.2, 0.3]
SAMPLING_SEED = 42


def _trace_filename(run: dict) -> str:
    return (
        f"{run['task_id']}__{run['architecture']}"
        f"__noise{run['noise_level']}__seed{run['seed']}.jsonl"
    )


def _key(run: dict) -> str:
    return f"{run['task_id']}|{run['architecture']}|{run['noise_level']}|{run['seed']}"


def _key_from_row(row: dict) -> str:
    return f"{row['task_id']}|{row['architecture']}|{row['noise_level']}|{row['seed']}"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S")
    log = logging.getLogger("resample_by_arch_noise")

    if SUPP_JSON.exists():
        log.error("Supplementary sample already exists at %s", SUPP_JSON)
        log.error("Delete manually if you want to regenerate.")
        return 1

    if not PASS1_CSV.exists():
        log.error("Existing pass1 CSV not found at %s", PASS1_CSV)
        return 1

    # Load already-coded runs
    already_coded: set[str] = set()
    cell_counts: Counter = Counter()
    with PASS1_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            already_coded.add(_key_from_row(row))
            cell_counts[(row["architecture"], str(float(row["noise_level"])))] += 1

    log.info("Existing pass1 codings: %d", len(already_coded))
    log.info("Current cell coverage (target %d per cell):", TARGET_PER_CELL)
    for arch in ARCHITECTURES:
        for noise in NOISE_LEVELS:
            key = (arch, str(noise))
            n = cell_counts.get(key, 0)
            status = "✓" if n >= TARGET_PER_CELL else f"need {TARGET_PER_CELL - n} more"
            log.info("  %-9s noise=%s: %d %s", arch, noise, n, status)

    # Load full results
    raw = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    log.info("Loaded %d run records total", len(raw))

    # Build pool: failed runs (hard_success=False) not already coded
    by_cell: dict[tuple[str, float], list[dict]] = defaultdict(list)
    for run in raw:
        if run.get("hard_success"):
            continue
        if _key(run) in already_coded:
            continue
        by_cell[(run["architecture"], run["noise_level"])].append(run)

    # Sample the deficit for each cell
    rng = random.Random(SAMPLING_SEED)
    supplementary: list[dict] = []

    for arch in ARCHITECTURES:
        for noise in NOISE_LEVELS:
            already = cell_counts.get((arch, str(noise)), 0)
            deficit = TARGET_PER_CELL - already
            if deficit <= 0:
                continue
            pool = by_cell.get((arch, noise), [])
            if len(pool) < deficit:
                log.warning("Cell (%s, noise=%s) has only %d uncoded failures available (need %d)",
                            arch, noise, len(pool), deficit)
                picked = pool[:]
            else:
                picked = rng.sample(pool, deficit)

            for run in picked:
                trace_file = _trace_filename(run)
                trace_path = TRACES_DIR / trace_file
                supplementary.append({
                    "trace_path": str(trace_path.relative_to(PROJECT_ROOT)),
                    "task_id": run["task_id"],
                    "architecture": run["architecture"],
                    "noise_level": run["noise_level"],
                    "seed": run["seed"],
                    "failure_mode": run.get("failure_mode", "unknown"),
                    "purchased_asin": run.get("purchased_asin"),
                    "hard_success": run["hard_success"],
                    "preference_success": run.get("preference_success", 0.0),
                    "trace_exists": trace_path.exists(),
                })

    log.info("=" * 70)
    log.info("Supplementary sample: %d additional traces", len(supplementary))
    supp_by_cell: Counter = Counter()
    for s in supplementary:
        supp_by_cell[(s["architecture"], s["noise_level"])] += 1
    for arch in ARCHITECTURES:
        for noise in NOISE_LEVELS:
            n = supp_by_cell.get((arch, noise), 0)
            if n > 0:
                log.info("  %-9s noise=%s: +%d", arch, noise, n)
    log.info("=" * 70)

    missing = [s for s in supplementary if not s["trace_exists"]]
    if missing:
        log.warning("%d supplementary traces have missing files", len(missing))

    SUPP_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUPP_JSON.write_text(
        json.dumps({
            "sampling_seed": SAMPLING_SEED,
            "target_per_cell": TARGET_PER_CELL,
            "purpose": "Supplementary sample to reach 3-per-(arch,noise) stratification for Pass 1",
            "sampled": supplementary,
        }, indent=2),
        encoding="utf-8",
    )
    log.info("Wrote supplementary sample to %s", SUPP_JSON)
    log.info("Next: uv run python scripts/code_failed_traces_supp.py --pass 1")
    return 0


if __name__ == "__main__":
    sys.exit(main())