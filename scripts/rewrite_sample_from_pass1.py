"""Rewrite sampled_traces.json to contain only the 24 stratified traces from Pass 1.

The original sampled_traces.json still contains the initial 48-trace sample
(stratified by env failure_mode). After the arch × noise restratification,
coding_pass1.csv is the authoritative list of the 24 traces we're using.
This script rewrites sampled_traces.json to match, so that Pass 2 iterates
the correct 24 traces (showing "N/24" in the tool) rather than the old 48.

Safety:
- Backs up the original sampled_traces.json to sampled_traces.json.pre_restrat.bak
- Only rewrites once; refuses to run again if the backup already exists (idempotent guard)

Usage:
    uv run python scripts/rewrite_sample_from_pass1.py
"""
from __future__ import annotations

import csv
import json
import logging
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_JSON = PROJECT_ROOT / "data" / "qualitative_coding" / "sampled_traces.json"
BACKUP_JSON = PROJECT_ROOT / "data" / "qualitative_coding" / "sampled_traces.json.pre_restrat.bak"
PASS1_CSV = PROJECT_ROOT / "data" / "qualitative_coding" / "coding_pass1.csv"
TRACES_DIR = PROJECT_ROOT / "data" / "traces_full"


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("rewrite_sample")

    if BACKUP_JSON.exists():
        log.error("Backup already exists at %s", BACKUP_JSON)
        log.error("This script has already been run. Refusing to run again to avoid overwriting.")
        return 1

    if not SAMPLE_JSON.exists():
        log.error("Sample JSON missing at %s", SAMPLE_JSON)
        return 1
    if not PASS1_CSV.exists():
        log.error("Pass 1 CSV missing at %s", PASS1_CSV)
        return 1

    # Load Pass 1 CSV — the authoritative 24 traces
    pass1_rows: list[dict] = []
    with PASS1_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pass1_rows.append(row)
    log.info("Loaded %d rows from coding_pass1.csv", len(pass1_rows))

    if len(pass1_rows) != 24:
        log.warning("Expected 24 rows in Pass 1 CSV, got %d — proceeding anyway.", len(pass1_rows))

    # Load original sample JSON to preserve top-level fields (seed, categories, etc.)
    original = json.loads(SAMPLE_JSON.read_text(encoding="utf-8"))

    # Build the new sample entries from Pass 1 rows.
    # Try to look up each trace_path in the original 48-trace list to reuse
    # its metadata (purchased_asin, hard_success, preference_success, trace_exists).
    original_by_path = {s["trace_path"]: s for s in original.get("sampled", [])}
    log.info("Original sample contains %d entries", len(original_by_path))

    new_sampled = []
    for row in pass1_rows:
        trace_path = row["trace_path"]
        noise_level = float(row["noise_level"])
        seed = int(row["seed"])

        if trace_path in original_by_path:
            # Reuse original metadata
            entry = dict(original_by_path[trace_path])
            new_sampled.append(entry)
        else:
            # Fabricate minimal metadata from what we have in the CSV
            trace_file = TRACES_DIR / Path(trace_path).name
            entry = {
                "trace_path": trace_path,
                "task_id": row["task_id"],
                "architecture": row["architecture"],
                "noise_level": noise_level,
                "seed": seed,
                "failure_mode": row["env_failure_mode"],
                "purchased_asin": None,
                "hard_success": False,
                "preference_success": 0.0,
                "trace_exists": trace_file.exists(),
            }
            new_sampled.append(entry)
            log.warning("Trace %s not in original sample; used minimal metadata.", trace_path)

    # Build the new top-level JSON.
    # Preserve original seed/categories fields; update meta to reflect restratification.
    new_json = {
        "sampling_seed": original.get("sampling_seed", 42),
        "per_category_target": 3,  # 3 per arch × noise cell now
        "stratification": "3 per (architecture × noise_level) cell = 2 × 4 × 3 = 24",
        "categories": ["reactive_noise0.0", "reactive_noise0.1", "reactive_noise0.2", "reactive_noise0.3",
                       "planning_noise0.0", "planning_noise0.1", "planning_noise0.2", "planning_noise0.3"],
        "note": "Restratified from initial 48-trace failure_mode sample per supervisor's rule. Original preserved at sampled_traces.json.pre_restrat.bak.",
        "sampled": new_sampled,
    }

    # Backup and write
    shutil.copy2(SAMPLE_JSON, BACKUP_JSON)
    log.info("Backed up original to %s", BACKUP_JSON)

    SAMPLE_JSON.write_text(json.dumps(new_json, indent=2), encoding="utf-8")
    log.info("Wrote %d traces to %s", len(new_sampled), SAMPLE_JSON)

    # Sanity check: cell distribution
    log.info("=" * 70)
    log.info("Final cell distribution:")
    from collections import Counter
    cells: Counter = Counter()
    for s in new_sampled:
        cells[(s["architecture"], s["noise_level"])] += 1
    for arch in ["reactive", "planning"]:
        for noise in [0.0, 0.1, 0.2, 0.3]:
            n = cells.get((arch, noise), 0)
            marker = "✓" if n == 3 else "⚠"
            log.info("  %-9s noise=%.1f: %d %s", arch, noise, n, marker)
    log.info("=" * 70)
    log.info("Pass 2 will now iterate %d traces. Resume with:", len(new_sampled))
    log.info("  uv run python scripts/code_failed_traces.py --pass 2")
    return 0


if __name__ == "__main__":
    sys.exit(main())