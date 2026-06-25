# Pilot Run Results

**Total runs:** 80
**Architectures:** planning, reactive
**Noise levels:** 0.00, 0.20

## Success metrics

| Architecture | Noise | n | Hard Success | Preference Success | Constraint Satisfaction |
|---|---|---|---|---|---|
| planning | 0.0 | 20 | 35.00% | 0.00% | 50.00% |
| planning | 0.2 | 20 | 25.00% | 0.00% | 38.33% |
| reactive | 0.0 | 20 | 65.00% | 5.00% | 71.67% |
| reactive | 0.2 | 20 | 80.00% | 20.00% | 83.33% |

## Efficiency metrics (means)

| Architecture | Noise | n | Env Steps | LLM Calls | Total Tokens | Wall-Clock (s) | Latency/Call (s) |
|---|---|---|---|---|---|---|---|
| planning | 0.0 | 20 | 6.95 | 2.90 | 5689 | 18.28 | 6.12 |
| planning | 0.2 | 20 | 6.65 | 3.40 | 4756 | 18.59 | 5.38 |
| reactive | 0.0 | 20 | 9.60 | 9.95 | 21931 | 35.13 | 3.44 |
| reactive | 0.2 | 20 | 9.75 | 9.80 | 20303 | 32.82 | 3.29 |

## Failure-mode distribution (per architecture)

### planning (n=40)

- success: 12 (30.0%)
- replan_limit_exceeded: 11 (27.5%)
- wrong_product: 10 (25.0%)
- no_purchase:unknown: 4 (10.0%)
- malformed_limit: 3 (7.5%)

### reactive (n=40)

- success: 29 (72.5%)
- budget_exhausted: 7 (17.5%)
- wrong_product: 3 (7.5%)
- no_purchase:unknown: 1 (2.5%)


## Per-task Hard Success crosstab (noise=0 only)

| Task | planning | reactive |
|---|---|---|
| T001 | ✗ | ✓ |
| T003 | ✗ | ✓ |
| T005 | ✗ | ✓ |
| T010 | ✗ | ✗ |
| T013 | ✗ | ✓ |
| T016 | ✗ | ✗ |
| T021 | ✗ | ✗ |
| T025 | ✗ | ✗ |
| T026 | ✓ | ✓ |
| T029 | ✓ | ✓ |
| T031 | ✓ | ✗ |
| T032 | ✗ | ✓ |
| T036 | ✗ | ✓ |
| T038 | ✓ | ✓ |
| T040 | ✓ | ✓ |
| T042 | ✗ | ✗ |
| T045 | ✓ | ✓ |
| T046 | ✗ | ✓ |
| T049 | ✗ | ✗ |
| T050 | ✓ | ✓ |