"""Interactive qualitative coding tool for sampled failed traces.

Iterates through the locked sample of 48 traces. For each trace, prints
a compact summary of the task, the reasoning steps, and outcome. Prompts
the user to assign one of the 10 taxonomy categories + optional free-text
notes. Saves each coding to a CSV as you go — so you can quit and resume.

Usage:
    # Pass 1 (now)
    uv run python scripts/code_failed_traces.py --pass 1

    # Pass 2 (in ~10 days)
    uv run python scripts/code_failed_traces.py --pass 2

You can resume mid-session — already-coded traces are skipped.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_JSON = PROJECT_ROOT / "data" / "qualitative_coding" / "sampled_traces.json"

TAXONOMY_CATEGORIES = [
    (1, "wrong_product_satisfying", "Purchased but violates hard constraint(s)"),
    (2, "search_blindness", "Search returned cross-bucket noise; agent proceeded"),
    (3, "failed_narrowing", "Filters didn't compose; each ran on whole catalogue"),
    (4, "non_commitment", "Explored but never called purchase()"),
    (5, "plan_execution_mismatch", "Plan referenced unknown ASINs (planning only)"),
    (6, "replan_treadmill", "Kept replanning without converging (planning only)"),
    (7, "budget_exhaustion_mid_narrowing", "Made progress but ran out of steps"),
    (8, "malformed_action_recovery_failure", "3+ consecutive schema rejections"),
    (9, "constraint_misinterpretation", "Bought near-miss (e.g. $16.50 vs $16 cap)"),
    (10, "other_uncoded", "Other / genuine ambiguity"),
]


def _format_trace_summary(trace_path: Path, sample_record: dict) -> str:
    """Render a compact summary of a trace for coding review."""
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append(f"Trace: {trace_path.name}")
    lines.append(f"  task={sample_record['task_id']}  "
                 f"arch={sample_record['architecture']}  "
                 f"noise={sample_record['noise_level']}  "
                 f"seed={sample_record['seed']}")
    lines.append(f"  env failure_mode={sample_record['failure_mode']}  "
                 f"purchased={sample_record.get('purchased_asin')}")
    lines.append("-" * 72)

    if not trace_path.exists():
        lines.append(f"  ⚠ TRACE FILE NOT FOUND at {trace_path}")
        return "\n".join(lines)

    # Read the JSONL
    with trace_path.open("r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    meta = next((r for r in records if r.get("record_type") == "metadata"), None)
    steps = [r for r in records if r.get("record_type") == "step"]

    if meta:
        lines.append(f"  TASK: {meta.get('task_nl', '(unknown)')}")
        lines.append(f"  CONSTRAINTS: {meta.get('constraints', {})}")
        lines.append(f"  PREFERENCE: {meta.get('preference')}")
        lines.append(f"  OPTIMAL: {meta.get('optimal_asins')}  "
                     f"(valid_set_size: {meta.get('valid_set_size')})")

    lines.append("-" * 72)
    lines.append(f"  STEPS: {len(steps)}")
    for step in steps:
        si = step.get("step_index", "?")
        thought = step.get("thought") or "(no thought)"
        action = step.get("action")
        obs = step.get("observation", {})
        status = obs.get("status", "?")

        # Truncate thought for readability
        if len(thought) > 90:
            thought = thought[:87] + "..."

        if action is not None:
            tool = action.get("tool", "?")
            args = action.get("args", {})
            args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
            if len(args_str) > 90:
                args_str = args_str[:87] + "..."
            lines.append(f"    [{si}] {tool}({args_str})")
        else:
            lines.append(f"    [{si}] (terminal, no action)")

        lines.append(f"       thought: {thought}")

        if status == "ok":
            n = len(obs.get("products", []))
            total = obs.get("total_matches")
            truncated = obs.get("truncated")
            if total is not None:
                lines.append(f"       → OK: {n} shown, {total} total"
                             + (" (truncated)" if truncated else ""))
            else:
                lines.append(f"       → OK: {n} products")
        elif status == "error":
            lines.append(f"       → ERROR: {obs.get('error_code')} — {obs.get('error_message')}")
        elif status == "terminal":
            lines.append(f"       → TERMINAL: {obs.get('terminal_reason')}")
        else:
            lines.append(f"       → status={status}")

    return "\n".join(lines)


def _prompt_for_category() -> tuple[int, str]:
    """Prompt user for a category (1-10). Returns (int, canonical_name)."""
    print()
    print("Categories:")
    for num, key, desc in TAXONOMY_CATEGORIES:
        print(f"  {num:>2}. {key:<40s} — {desc}")
    print()

    while True:
        raw = input("Category (1-10, or 'q' to quit, 's' to skip): ").strip().lower()
        if raw in ("q", "quit"):
            return -1, "quit"
        if raw in ("s", "skip"):
            return -2, "skip"
        try:
            num = int(raw)
            if 1 <= num <= 10:
                return num, TAXONOMY_CATEGORIES[num - 1][1]
        except ValueError:
            pass
        print("Please enter a number 1-10, or 'q' or 's'.")


def _load_existing_codings(csv_path: Path) -> set[str]:
    """Return the set of trace paths already coded in the CSV."""
    if not csv_path.exists():
        return set()
    coded = set()
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            coded.add(row["trace_path"])
    return coded


def _append_coding(
    csv_path: Path,
    trace_path: str,
    task_id: str,
    architecture: str,
    noise_level: float,
    seed: int,
    env_failure_mode: str,
    category_num: int,
    category_name: str,
    notes: str,
) -> None:
    """Append one coding row to the CSV. Creates the file with header if new."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not csv_path.exists()
    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow([
                "trace_path", "task_id", "architecture", "noise_level", "seed",
                "env_failure_mode", "category_num", "category_name", "notes",
            ])
        writer.writerow([
            trace_path, task_id, architecture, noise_level, seed,
            env_failure_mode, category_num, category_name, notes,
        ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass", dest="pass_num", type=int, required=True, choices=[1, 2],
                        help="Which coding pass (1 = first, 2 = second)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger("code_failed_traces")

    if not SAMPLE_JSON.exists():
        log.error("Sample file not found at %s", SAMPLE_JSON)
        log.error("Run 'uv run python scripts/sample_failed_traces.py' first.")
        return 1

    sample_data = json.loads(SAMPLE_JSON.read_text(encoding="utf-8"))
    sample = sample_data["sampled"]

    output_csv = PROJECT_ROOT / "data" / "qualitative_coding" / f"coding_pass{args.pass_num}.csv"
    already_coded = _load_existing_codings(output_csv)

    log.info("Qualitative coding — pass %d", args.pass_num)
    log.info("Sample size: %d traces", len(sample))
    log.info("Already coded (resuming): %d", len(already_coded))
    log.info("Remaining: %d", len(sample) - len(already_coded))
    log.info("Output: %s", output_csv)
    log.info("")

    if args.pass_num == 2:
        log.info("⚠ PASS 2 — do NOT look at your pass 1 codings while coding.")
        log.info("  If you need a break, quit ('q') and resume later.")
        log.info("")

    input("Press Enter to begin coding, or Ctrl+C to abort...")

    for i, record in enumerate(sample, start=1):
        trace_path_str = record["trace_path"]
        trace_path = PROJECT_ROOT / trace_path_str

        if trace_path_str in already_coded:
            continue

        # Show summary
        print()
        print(f"\n[{i}/{len(sample)}]")
        print(_format_trace_summary(trace_path, record))

        # Prompt for category
        num, name = _prompt_for_category()

        if num == -1:
            log.info("Quit signal received. %d of %d traces coded in this session.",
                     i - 1 - len(already_coded) + (1 if trace_path_str not in already_coded else 0),
                     len(sample) - len(already_coded))
            log.info("Resume by re-running: uv run python scripts/code_failed_traces.py --pass %d",
                     args.pass_num)
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
    log.info("Pass %d complete. All %d traces coded.", args.pass_num, len(sample))
    log.info("=" * 70)
    if args.pass_num == 1:
        log.info("Next: wait ~10 days, then run 'uv run python scripts/code_failed_traces.py --pass 2'.")
    else:
        log.info("Next: compute Cohen's kappa with 'uv run python scripts/compute_kappa.py'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())