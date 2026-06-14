# Pilot Run Results

**Total runs:** 80
**Architectures:** planning, reactive
**Noise levels:** 0.00, 0.20

## Success metrics

| Architecture | Noise | n | Hard Success | Preference Success | Constraint Satisfaction |
|---|---|---|---|---|---|
| planning | 0.0 | 20 | 15.00% | 0.00% | 26.67% |
| planning | 0.2 | 20 | 0.00% | 0.00% | 0.00% |
| reactive | 0.0 | 20 | 15.00% | 5.00% | 17.50% |
| reactive | 0.2 | 20 | 25.00% | 10.00% | 30.00% |

## Efficiency metrics (means)

| Architecture | Noise | n | Env Steps | LLM Calls | Total Tokens | Wall-Clock (s) |
|---|---|---|---|---|---|---|
| planning | 0.0 | 20 | 10.40 | 3.20 | 8967 | 2.53 |
| planning | 0.2 | 20 | 6.90 | 3.55 | 6490 | 2.52 |
| reactive | 0.0 | 20 | 11.00 | 12.55 | 21305 | 6.39 |
| reactive | 0.2 | 20 | 6.75 | 10.35 | 24070 | 5.54 |

## Failure-mode distribution (per architecture)

### planning (n=40)

- replan_limit_exceeded: 19 (47.5%)
- no_purchase:unknown: 10 (25.0%)
- budget_exhausted: 4 (10.0%)
- wrong_product: 4 (10.0%)
- success: 3 (7.5%)

### reactive (n=40)

- no_purchase:unknown: 19 (47.5%)
- budget_exhausted: 10 (25.0%)
- success: 8 (20.0%)
- wrong_product: 3 (7.5%)


## Per-task Hard Success crosstab (noise=0 only)

| Task | planning | reactive |
|---|---|---|
| T001 | ✓ | ✗ |
| T003 | ✗ | ✗ |
| T005 | ✗ | ✓ |
| T010 | ✗ | ✗ |
| T013 | ✗ | ✗ |
| T016 | ✗ | ✗ |
| T021 | ✗ | ✗ |
| T025 | ✗ | ✗ |
| T026 | ✗ | ✗ |
| T029 | ✓ | ✗ |
| T031 | ✗ | ✓ |
| T032 | ✗ | ✗ |
| T036 | ✓ | ✗ |
| T038 | ✗ | ✗ |
| T040 | ✗ | ✗ |
| T042 | ✗ | ✗ |
| T045 | ✗ | ✓ |
| T046 | ✗ | ✗ |
| T049 | ✗ | ✗ |
| T050 | ✗ | ✗ |