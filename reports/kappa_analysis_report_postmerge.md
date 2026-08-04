# Post-Merge Intra-Rater Agreement Analysis

**Coder:** Sanatan Shrivastava  
**Traces coded in both passes:** 24  
**Merge applied:** Category 6 (`replan_treadmill`) merged into Category 3 (`failed_narrowing`), renamed `filter_composition_failure`. Merge authorised by project supervisor after Pass 1/Pass 2 confusion pattern revealed systematic overlap.

## Results (post-merge)

- **Agreement rate:** 54.2% (13/24)
- **Cohen's κ:** 0.221
- **Interpretation:** fair agreement (Landis and Koch, 1977)

Post-merge κ = 0.221 remains below the 0.60 threshold. The confusion matrix should be examined before any further taxonomy revision.

## Confusion matrix (post-merge)

Rows = Pass 1 category, Columns = Pass 2 category.

| P1 \ P2 | 1 | 3 | 4 | 7 | 9 | 10 |
|---|---|---|---|---|---|---|
| **1** | 0 | 1 | 0 | 0 | 0 | 0 |
| **3** | 3 | 11 | 0 | 0 | 2 | 0 |
| **4** | 0 | 0 | 0 | 1 | 0 | 0 |
| **7** | 0 | 0 | 0 | 1 | 0 | 0 |
| **9** | 0 | 1 | 0 | 0 | 0 | 0 |
| **10** | 2 | 1 | 0 | 0 | 0 | 1 |

## Distributions

**Pass 1:** C1: 1, C3: 16, C4: 1, C7: 1, C9: 1, C10: 4

**Pass 2:** C1: 5, C3: 14, C7: 2, C9: 2, C10: 1

## Disagreements (post-merge)

| Trace | Pass 1 | Pass 2 |
|---|---|---|
| `T006__planning__noise0.0__seed42.jsonl` | 9 | 3 |
| `T006__reactive__noise0.3__seed1.jsonl` | 3 | 9 |
| `T007__reactive__noise0.0__seed2024.jsonl` | 3 | 1 |
| `T007__reactive__noise0.0__seed42.jsonl` | 3 | 9 |
| `T014__reactive__noise0.3__seed42.jsonl` | 3 | 1 |
| `T015__planning__noise0.2__seed42.jsonl` | 10 | 1 |
| `T021__planning__noise0.2__seed1.jsonl` | 10 | 1 |
| `T027__planning__noise0.0__seed1.jsonl` | 3 | 1 |
| `T027__reactive__noise0.2__seed42.jsonl` | 1 | 3 |
| `T046__reactive__noise0.1__seed1.jsonl` | 10 | 3 |
| `T047__reactive__noise0.2__seed1.jsonl` | 4 | 7 |

## Process disclosure

The original 10-category taxonomy applied to Pass 1 produced κ = 0.061 on the 24 paired codings. The confusion matrix showed a systematic pattern: every Pass 1 coding of Category 6 (`replan_treadmill`, n = 5) was reclassified as Category 3 (`failed_narrowing`) in Pass 2. Trace inspection confirmed that these categories have overlapping signatures on planning traces that fail through poor filter composition after multiple replans. Under supervisor authorisation, the two categories were merged into a single category (`filter_composition_failure`) and κ was recomputed on the resulting 9-category taxonomy.