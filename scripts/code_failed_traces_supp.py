"""Interactive coding tool — variant that reads from the supplementary sample.

Only iterates the ~7 extra traces sampled to fill undercovered cells.
Appends to the SAME coding_pass1.csv as the original tool. Resumable.

Usage:
    uv run python scripts/code_failed_traces_supp.py --pass 1
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

# Reuse the summary + prompting + append helpers from the main coding tool
sys.path.insert(0, str(Path(__file__).resolve().parent))
from code_failed_traces import (  # type: ignore
    _format_trace_summary,
    _prompt_for_category,
    _load_existing_codings,
    _append_coding,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUPP_JSON = PROJECT_ROOT / "data" / "qualitative_coding" / "sampled_traces_supplementary.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass", dest="pass_num", type=int, required=True, choices=[1, 2])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("code_failed_traces_supp")

    if not SUPP_JSON.exists():
        log.error("Supplementary sample not found at %s", SUPP_JSON)
        log.error("Run 'uv run python scripts/resample_by_arch_noise.py' first.")
        return 1

    sample_data = json.loads(SUPP_JSON.read_text(encoding="utf-8"))
    sample = sample_data["sampled"]

    output_csv = PROJECT_ROOT / "data" / "qualitative_coding" / f"coding_pass{args.pass_num}.csv"
    already_coded = _load_existing_codings(output_csv)

    log.info("Supplementary coding — pass %d", args.pass_num)
    log.info("Supplementary sample size: %d traces", len(sample))
    log.info("Already coded (in pass1.csv): %d", len(already_coded))
    log.info("Remaining supplementary to code: %d",
             sum(1 for r in sample if r["trace_path"] not in already_coded))
    log.info("Output: %s", output_csv)
    log.info("")

    if args.pass_num == 2:
        log.info("⚠ PASS 2 — do NOT look at your pass 1 codings while coding.")
        log.info("")

    input("Press Enter to begin, or Ctrl+C to abort...")

    for i, record in enumerate(sample, start=1):
        trace_path_str = record["trace_path"]
        trace_path = PROJECT_ROOT / trace_path_str

        if trace_path_str in already_coded:
            continue

        print(f"\n[supp {i}/{len(sample)}]")
        print(_format_trace_summary(trace_path, record))

        num, name = _prompt_for_category()

        if num == -1:
            log.info("Quit signal. Re-run to resume.")
            return 0
        if num == -2:
            log.info("Skipped %s", trace_path_str)
            continue

        notes = input("Notes (optional, press Enter to skip): ").strip()

        _append_coding(
            output_csv,
            trace_path=trace_path_str,
            task_id=record["task_id"],
            architecture=record["architecture"],
            noise_level=record["noise_level"],
            seed=record["seed"],
            env_failure_mode=record["failure_mode"],
            category_num=num,
            category_name=name,
            notes=notes,
        )
        log.info("  ✓ Coded as %d: %s", num, name)

    log.info("")
    log.info("=" * 70)
    log.info("Supplementary coding complete.")
    log.info("Next: uv run python scripts/trim_pass1_to_stratification.py")
    log.info("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())