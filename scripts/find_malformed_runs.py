"""Find pilot runs that failed with malformed_limit."""
import json
from pathlib import Path

results_path = Path("data/results/pilot_results.json")
data = json.loads(results_path.read_text())

failures = [r for r in data if r["failure_mode"] == "malformed_limit"]

print(f"Found {len(failures)} runs with malformed_limit failure:\n")
for f in failures:
    print(f"  {f['task_id']}  arch={f['architecture']}  noise={f['noise_level']}  seed={f['seed']}")
    print(f"    parse_errors={f['parse_errors']}, llm_calls={f['llm_calls']}, env_steps={f['env_steps']}")
    print(f"    purchased={f['purchased_asin']}")
    print()