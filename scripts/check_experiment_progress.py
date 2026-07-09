"""Check how many runs completed before an interruption."""
import json
from pathlib import Path

results_path = Path("data/results/full_experiment_results.json")

if not results_path.exists():
    print(f"NO RESULTS FILE at {results_path}")
    print("Either the experiment never wrote anything, or the file is elsewhere.")
    exit(1)

data = json.loads(results_path.read_text())
print(f"Completed runs: {len(data)}")
print(f"Total expected:  1200")
print(f"Percent done:    {100 * len(data) / 1200:.1f}%")
print()

if data:
    first = data[0]
    last = data[-1]
    print(f"First run: {first['task_id']}  arch={first['architecture']}  noise={first['noise_level']}  seed={first['seed']}")
    print(f"Last run:  {last['task_id']}  arch={last['architecture']}  noise={last['noise_level']}  seed={last['seed']}")

# Count by seed to see how far through the seed loop we got
from collections import Counter
by_seed = Counter(r["seed"] for r in data)
print(f"\nBy seed: {dict(by_seed)}")
by_arch = Counter(r["architecture"] for r in data)
print(f"By arch: {dict(by_arch)}")