# Full Experiment Results

**Total runs:** 1200
**Architectures:** planning, reactive
**Noise levels:** 0.00, 0.10, 0.20, 0.30

## Success metrics

| Architecture | Noise | n | Hard Success | Preference Success | Constraint Satisfaction |
|---|---|---|---|---|---|
| planning | 0.0 | 150 | 58.00% | 16.00% | 71.33% |
| planning | 0.1 | 150 | 40.67% | 9.33% | 51.67% |
| planning | 0.2 | 150 | 35.33% | 10.00% | 48.56% |
| planning | 0.3 | 150 | 40.67% | 12.67% | 53.94% |
| reactive | 0.0 | 150 | 62.00% | 26.00% | 74.67% |
| reactive | 0.1 | 150 | 60.67% | 26.67% | 72.33% |
| reactive | 0.2 | 150 | 64.00% | 26.67% | 75.78% |
| reactive | 0.3 | 150 | 60.00% | 24.00% | 72.67% |

## Efficiency metrics (means)

| Architecture | Noise | n | Env Steps | LLM Calls | Total Tokens | Wall-Clock (s) | Latency/Call (s) |
|---|---|---|---|---|---|---|---|
| planning | 0.0 | 150 | 10.03 | 2.67 | 7555 | 17.87 | 6.34 |
| planning | 0.1 | 150 | 9.17 | 2.99 | 7386 | 19.13 | 6.14 |
| planning | 0.2 | 150 | 8.99 | 3.05 | 7415 | 19.59 | 6.22 |
| planning | 0.3 | 150 | 8.63 | 3.21 | 7113 | 19.92 | 6.05 |
| reactive | 0.0 | 150 | 8.05 | 8.51 | 19305 | 30.67 | 3.43 |
| reactive | 0.1 | 150 | 8.23 | 8.68 | 19500 | 31.22 | 3.43 |
| reactive | 0.2 | 150 | 8.28 | 8.65 | 19149 | 30.55 | 3.39 |
| reactive | 0.3 | 150 | 9.09 | 9.43 | 21114 | 33.97 | 3.45 |

## Failure-mode distribution (per architecture)

### planning (n=600)

- success: 262 (43.7%)
- replan_limit_exceeded: 145 (24.2%)
- wrong_product: 130 (21.7%)
- budget_exhausted: 51 (8.5%)
- no_purchase:unknown: 12 (2.0%)

### reactive (n=600)

- success: 370 (61.7%)
- wrong_product: 117 (19.5%)
- budget_exhausted: 71 (11.8%)
- no_purchase:unknown: 42 (7.0%)


## Per-task Hard Success crosstab (noise=0 only)

| Task | planning | reactive |
|---|---|---|
| T001 | ✓ | ✓ |
| T002 | ✗ | ✗ |
| T003 | ✗ | ✓ |
| T004 | ✓ | ✓ |
| T005 | ✓ | ✓ |
| T006 | ✗ | ✗ |
| T007 | ✓ | ✗ |
| T008 | ✗ | ✗ |
| T009 | ✓ | ✗ |
| T010 | ✓ | ✗ |
| T011 | ✓ | ✓ |
| T012 | ✓ | ✓ |
| T013 | ✓ | ✓ |
| T014 | ✗ | ✗ |
| T015 | ✗ | ✗ |
| T016 | ✓ | ✗ |
| T017 | ✗ | ✓ |
| T018 | ✗ | ✗ |
| T019 | ✓ | ✓ |
| T020 | ✓ | ✓ |
| T021 | ✗ | ✗ |
| T022 | ✗ | ✓ |
| T023 | ✓ | ✓ |
| T024 | ✗ | ✗ |
| T025 | ✓ | ✓ |
| T026 | ✓ | ✓ |
| T027 | ✗ | ✗ |
| T028 | ✓ | ✓ |
| T029 | ✓ | ✓ |
| T030 | ✗ | ✗ |
| T031 | ✗ | ✗ |
| T032 | ✓ | ✓ |
| T033 | ✓ | ✓ |
| T034 | ✓ | ✓ |
| T035 | ✓ | ✓ |
| T036 | ✓ | ✓ |
| T037 | ✓ | ✓ |
| T038 | ✓ | ✓ |
| T039 | ✗ | ✓ |
| T040 | ✓ | ✓ |
| T041 | ✓ | ✓ |
| T042 | ✗ | ✗ |
| T043 | ✓ | ✓ |
| T044 | ✓ | ✓ |
| T045 | ✗ | ✓ |
| T046 | ✗ | ✓ |
| T047 | ✗ | ✗ |
| T048 | ✗ | ✗ |
| T049 | ✗ | ✗ |
| T050 | ✓ | ✓ |