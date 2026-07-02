# Pilot Run Results

**Total runs:** 40
**Architectures:** planning
**Noise levels:** 0.00, 0.20

## Success metrics

| Architecture | Noise | n | Hard Success | Preference Success | Constraint Satisfaction |
|---|---|---|---|---|---|
| planning | 0.0 | 20 | 65.00% | 10.00% | 76.67% |
| planning | 0.2 | 20 | 20.00% | 0.00% | 32.50% |

## Efficiency metrics (means)

| Architecture | Noise | n | Env Steps | LLM Calls | Total Tokens | Wall-Clock (s) | Latency/Call (s) |
|---|---|---|---|---|---|---|---|
| planning | 0.0 | 20 | 9.55 | 2.60 | 7024 | 16.39 | 6.10 |
| planning | 0.2 | 20 | 6.95 | 3.25 | 5418 | 18.07 | 5.51 |

## Failure-mode distribution (per architecture)

### planning (n=40)

- success: 17 (42.5%)
- replan_limit_exceeded: 11 (27.5%)
- wrong_product: 9 (22.5%)
- budget_exhausted: 2 (5.0%)
- no_purchase:unknown: 1 (2.5%)


## Per-task Hard Success crosstab (noise=0 only)

| Task | planning |
|---|---|
| T001 | ✓ |
| T003 | ✗ |
| T005 | ✓ |
| T010 | ✓ |
| T013 | ✓ |
| T016 | ✓ |
| T021 | ✗ |
| T025 | ✓ |
| T026 | ✓ |
| T029 | ✓ |
| T031 | ✗ |
| T032 | ✓ |
| T036 | ✓ |
| T038 | ✓ |
| T040 | ✓ |
| T042 | ✗ |
| T045 | ✗ |
| T046 | ✗ |
| T049 | ✗ |
| T050 | ✓ |