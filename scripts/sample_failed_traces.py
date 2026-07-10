"""Sample 48 failed traces from the full experiment, stratified by failure_mode.

Sampling design (locked):
  - Only failed runs (hard_success = False)
  - 4 failure_mode categories: wrong_product, replan_limit_exceeded,
    budget_exhausted, no_purchase:unknown
  - 12 traces per category = 48 total
  - Within each category, split roughly equally between architectures
    where both are present (replan_limit_exceeded is planning-only)
  - Seed: 42

The output is a locked JSON file used for BOTH coding passes.
Do NOT re-run after Pass 1 has begun — that would change the sample.

Usage:
    uv run python scripts/sample_failed_traces.py
"""
from __future__ import annotations

import json
import logging
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_JSON = PROJECT_ROOT / "data" / "results" / "full_experiment_results.json"
TRACES_DIR = PROJECT_ROOT / "data" / "traces_full"
OUTPUT_JSON = PROJECT_ROOT / "data" / "qualitative_coding" / "sampled_traces.json"

# Sampling config (locked)
CATEGORIES = [
    "wrong_product",
    "replan_limit_exceeded",
    "budget_exhausted",
    "no_purchase:unknown",
]
PER_CATEGORY = 12
SAMPLING_SEED = 42


def _trace_filename(run: dict) -> str:
    """Canonical trace filename for a run record."""
    return (
        f"{run['task_id']}__{run['architecture']}"
        f"__noise{run['noise_level']}__seed{run['seed']}.jsonl"
    )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("sample_failed_traces")

    if OUTPUT_JSON.exists():
        log.error("Sample file already exists at %s", OUTPUT_JSON)
        log.error("Re-running would produce a different sample and invalidate Pass 1 codings.")
        log.error("Delete manually only if you're sure Pass 1 has NOT started yet.")
        return 1

    if not RESULTS_JSON.exists():
        log.error("Full-experiment results not found at %s", RESULTS_JSON)
        return 1

    raw = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    log.info("Loaded %d run records", len(raw))

    # Group failed runs by failure_mode
    by_category: dict[str, list[dict]] = defaultdict(list)
    for run in raw:
        if run.get("hard_success"):
            continue  # Skip successes
        mode = run.get("failure_mode", "unknown")
        if mode in CATEGORIES:
            by_category[mode].append(run)

    log.info("Failure runs available per category:")
    for cat in CATEGORIES:
        log.info("  %s: %d runs", cat, len(by_category[cat]))

    # Sample deterministically
    rng = random.Random(SAMPLING_SEED)
    sampled: list[dict[str, Any]] = []

    for cat in CATEGORIES:
        pool = by_category[cat]
        if len(pool) < PER_CATEGORY:
            log.warning(
                "Category '%s' has only %d runs; taking all of them (wanted %d)",
                cat, len(pool), PER_CATEGORY,
            )
            picked = pool[:]
        else:
            # Try to balance architectures within the category
            by_arch: dict[str, list[dict]] = defaultdict(list)
            for run in pool:
                by_arch[run["architecture"]].append(run)

            picked = []
            archs = sorted(by_arch.keys())
            n_archs = len(archs)
            per_arch = PER_CATEGORY // n_archs if n_archs > 0 else PER_CATEGORY

            for arch in archs:
                arch_pool = by_arch[arch]
                if len(arch_pool) >= per_arch:
                    picked.extend(rng.sample(arch_pool, per_arch))
                else:
                    picked.extend(arch_pool)

            # If we underfilled due to arch imbalance, top up randomly
            deficit = PER_CATEGORY - len(picked)
            if deficit > 0:
                remaining = [r for r in pool if r not in picked]
                picked.extend(rng.sample(remaining, min(deficit, len(remaining))))

        # Build sample records
        for run in picked:
            trace_file = _trace_filename(run)
            trace_path = TRACES_DIR / trace_file
            sampled.append({
                "trace_path": str(trace_path.relative_to(PROJECT_ROOT)),
                "task_id": run["task_id"],
                "architecture": run["architecture"],
                "noise_level": run["noise_level"],
                "seed": run["seed"],
                "failure_mode": cat,
                "purchased_asin": run.get("purchased_asin"),
                "hard_success": run["hard_success"],
                "preference_success": run.get("preference_success", 0.0),
                "trace_exists": trace_path.exists(),
            })

    log.info("=" * 70)
    log.info("Sample composition:")
    for cat in CATEGORIES:
        n = sum(1 for s in sampled if s["failure_mode"] == cat)
        log.info("  %s: %d traces", cat, n)
    log.info("  Total: %d traces", len(sampled))
    log.info("=" * 70)

    # Check trace files all exist
    missing = [s for s in sampled if not s["trace_exists"]]
    if missing:
        log.warning("%d sampled traces have missing files!", len(missing))
        for s in missing[:5]:
            log.warning("  Missing: %s", s["trace_path"])

    # Write the sample
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps({
            "sampling_seed": SAMPLING_SEED,
            "per_category_target": PER_CATEGORY,
            "categories": CATEGORIES,
            "sampled": sampled,
        }, indent=2),
        encoding="utf-8",
    )
    log.info("Wrote %d sampled traces to %s", len(sampled), OUTPUT_JSON)
    log.info("This sample is LOCKED. Do not re-run this script for the same experiment.")
    return 0


if __name__ == "__main__":
    sys.exit(main())