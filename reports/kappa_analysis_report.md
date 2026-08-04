# Intra-Rater Agreement Analysis

**Coder:** Sanatan Shrivastava  
**Pass 1 codings:** 24  
**Pass 2 codings:** 24  
**Traces in both passes:** 24

## Results

- **Agreement rate:** 33.3% (8/24)
- **Cohen's κ:** 0.061
- **Interpretation:** slight agreement (Landis & Koch, 1977)

κ = 0.061 is below the 0.70 threshold typically taken as substantial. Refinement of the operational definitions or re-coding of disagreements is warranted before the categorisations are used in the thesis discussion.

## Confusion matrix

Rows = Pass 1 category, Columns = Pass 2 category.

| P1 \ P2 | 1 | 3 | 4 | 6 | 7 | 9 | 10 |
|---|---|---|---|---|---|---|---|
| **1** | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **3** | 3 | 6 | 0 | 0 | 0 | 2 | 0 |
| **4** | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| **6** | 0 | 5 | 0 | 0 | 0 | 0 | 0 |
| **7** | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| **9** | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **10** | 2 | 1 | 0 | 0 | 0 | 0 | 1 |

## Disagreements

| Trace | Pass 1 | Pass 2 |
|---|---|---|
| `data\traces_full\T003__planning__noise0.3__seed1.jsonl` | 6 | 3 |
| `data\traces_full\T004__planning__noise0.1__seed42.jsonl` | 6 | 3 |
| `data\traces_full\T006__planning__noise0.0__seed42.jsonl` | 9 | 3 |
| `data\traces_full\T006__reactive__noise0.3__seed1.jsonl` | 3 | 9 |
| `data\traces_full\T007__reactive__noise0.0__seed2024.jsonl` | 3 | 1 |
| `data\traces_full\T007__reactive__noise0.0__seed42.jsonl` | 3 | 9 |
| `data\traces_full\T011__planning__noise0.1__seed42.jsonl` | 6 | 3 |
| `data\traces_full\T014__reactive__noise0.3__seed42.jsonl` | 3 | 1 |
| `data\traces_full\T015__planning__noise0.2__seed42.jsonl` | 10 | 1 |
| `data\traces_full\T021__planning__noise0.2__seed1.jsonl` | 10 | 1 |
| `data\traces_full\T022__planning__noise0.1__seed42.jsonl` | 6 | 3 |
| `data\traces_full\T027__planning__noise0.0__seed1.jsonl` | 3 | 1 |
| `data\traces_full\T027__reactive__noise0.2__seed42.jsonl` | 1 | 3 |
| `data\traces_full\T037__planning__noise0.3__seed42.jsonl` | 6 | 3 |
| `data\traces_full\T046__reactive__noise0.1__seed1.jsonl` | 10 | 3 |
| `data\traces_full\T047__reactive__noise0.2__seed1.jsonl` | 4 | 7 |