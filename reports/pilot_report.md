# Pilot Run Results

**Total runs:** 80
**Architectures:** planning, reactive
**Noise levels:** 0.00, 0.20

## Success metrics

| Architecture | Noise | n | Hard Success | Preference Success | Constraint Satisfaction |
|---|---|---|---|---|---|
| planning | 0.0 | 20 | 25.00% | 5.00% | 51.67% |
| planning | 0.2 | 20 | 0.00% | 0.00% | 0.00% |
| reactive | 0.0 | 20 | 10.00% | 5.00% | 20.00% |
| reactive | 0.2 | 20 | 10.00% | 0.00% | 16.67% |

## Efficiency metrics (means)

| Architecture | Noise | n | Env Steps | LLM Calls | Total Tokens | Wall-Clock (s) |
|---|---|---|---|---|---|---|
| planning | 0.0 | 20 | 9.55 | 2.65 | 6465 | 2.58 |
| planning | 0.2 | 20 | 6.85 | 3.55 | 6344 | 2.68 |
| reactive | 0.0 | 20 | 9.80 | 11.20 | 18393 | 5.54 |
| reactive | 0.2 | 20 | 7.65 | 10.95 | 21856 | 5.60 |

## Failure-mode distribution (per architecture)

### planning (n=40)

- no_purchase:unknown: 13 (32.5%)
- replan_limit_exceeded: 11 (27.5%)
- wrong_product: 9 (22.5%)
- success: 5 (12.5%)
- budget_exhausted: 2 (5.0%)

### reactive (n=40)

- no_purchase:unknown: 18 (45.0%)
- budget_exhausted: 12 (30.0%)
- wrong_product: 6 (15.0%)
- success: 4 (10.0%)


## Per-task Hard Success crosstab (noise=0 only)

| Task | planning | reactive |
|---|---|---|
| T001 | ✓ | ✗ |
| T003 | ✗ | ✗ |
| T005 | ✗ | ✗ |
| T010 | ✗ | ✗ |
| T013 | ✗ | ✗ |
| T016 | ✗ | ✗ |
| T021 | ✗ | ✗ |
| T025 | ✗ | ✗ |
| T026 | ✓ | ✗ |
| T029 | ✗ | ✗ |
| T031 | ✓ | ✓ |
| T032 | ✗ | ✗ |
| T036 | ✓ | ✗ |
| T038 | ✗ | ✗ |
| T040 | ✗ | ✗ |
| T042 | ✗ | ✗ |
| T045 | ✓ | ✓ |
| T046 | ✗ | ✗ |
| T049 | ✗ | ✗ |
| T050 | ✗ | ✗ |