"""Sanity test the candidate_asins coercion."""
from src.environment.models import FilterArgs

test_cases = [
    ("previous_result placeholder", "previous_result"),
    ("null string", "null"),
    ("stringified list", "['B001', 'B002']"),
    ("proper None", None),
    ("proper list", ["B001", "B002"]),
]

print("Testing candidate_asins coercion:")
print("-" * 70)

for label, input_val in test_cases:
    try:
        args = FilterArgs(
            attribute="price",
            operator="<=",
            value=50,
            candidate_asins=input_val,
        )
        print(f"  {label:35s} input={input_val!r}")
        print(f"  {'':35s} output={args.candidate_asins!r}")
        print(f"  {'':35s} PASS")
    except Exception as e:
        print(f"  {label:35s} input={input_val!r}")
        print(f"  {'':35s} FAIL: {e}")
    print()