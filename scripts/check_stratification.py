"""Check whether existing pass1 codings satisfy the (arch x noise) stratification."""
import csv
from collections import Counter
from pathlib import Path

pass1_csv = Path("data/qualitative_coding/coding_pass1.csv")

if not pass1_csv.exists():
    print("No pass1.csv yet")
    exit()

cells = Counter()
with pass1_csv.open("r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        key = (row["architecture"], row["noise_level"])
        cells[key] += 1

print(f"Total coded so far: {sum(cells.values())}")
print()
print("Distribution across (architecture × noise) cells:")
print(f"{'arch':<10} {'noise':<8} {'n':>4}")
for arch in ["reactive", "planning"]:
    for noise in ["0.0", "0.1", "0.2", "0.3"]:
        n = cells.get((arch, noise), 0)
        marker = " ← target=3" if n == 3 else (" ← short" if n < 3 else " ← over")
        print(f"{arch:<10} {noise:<8} {n:>4}{marker}")