# Statistical Analysis of Full Experiment Results

**Total statistical tests reported:** 12
**Bonferroni correction applied.** α_corrected = 0.05 / 12 = 0.004167

## Methodology

Pairing structure: each (task_id, seed) combination provides one paired observation of (reactive, planning) at a given noise level. For 50 tasks × 3 seeds = 150 pairs per cell.

Three success metrics analysed at four noise levels → 12 tests total.

Test details:
- **Wilcoxon signed-rank test** on paired differences (non-parametric).
- **Cliff's δ**: effect size, range [−1, +1]. Positive = reactive > planning.
- **95% CI for mean difference**: percentile bootstrap, 10,000 resamples, seed=42.
- **Bonferroni**: p_corrected = min(1, p × n_tests). Conservative multiple-comparisons correction.

## Cliff's δ magnitude interpretation (Romano et al. 2006)

| \|δ\| range | Magnitude |
|---|---|
| < 0.147 | negligible |
| 0.147 – 0.33 | small |
| 0.33 – 0.474 | medium |
| ≥ 0.474 | large |

## Results

Δ Mean = reactive_mean − planning_mean. Positive = reactive better on that metric.

### Hard Success

| Noise | n | Reactive | Planning | Δ Mean | 95% CI | Wilcoxon p | Bonferroni p | Cliff's δ | Effect | Sig. (α=0.05, Bonf.) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 150 | 0.620 | 0.580 | +0.040 | [-0.033, +0.113] | 0.2733 | 1.0 | +0.040 | negligible | ✗ |
| 0.1 | 150 | 0.607 | 0.407 | +0.200 | [+0.113, +0.287] | 3.179e-05 | 0.0003815 | +0.200 | small | ✓ |
| 0.2 | 150 | 0.640 | 0.353 | +0.287 | [+0.200, +0.373] | 1.23e-08 | 1.476e-07 | +0.287 | small | ✓ |
| 0.3 | 150 | 0.600 | 0.407 | +0.193 | [+0.107, +0.280] | 2.336e-05 | 0.0002803 | +0.193 | small | ✓ |

### Preference Success

| Noise | n | Reactive | Planning | Δ Mean | 95% CI | Wilcoxon p | Bonferroni p | Cliff's δ | Effect | Sig. (α=0.05, Bonf.) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 150 | 0.260 | 0.160 | +0.100 | [+0.047, +0.160] | 0.001063 | 0.01276 | +0.100 | negligible | ✓ |
| 0.1 | 150 | 0.267 | 0.093 | +0.173 | [+0.113, +0.240] | 8.945e-07 | 1.073e-05 | +0.173 | small | ✓ |
| 0.2 | 150 | 0.267 | 0.100 | +0.167 | [+0.107, +0.227] | 1.5e-06 | 1.8e-05 | +0.167 | small | ✓ |
| 0.3 | 150 | 0.240 | 0.127 | +0.113 | [+0.060, +0.173] | 0.0002075 | 0.00249 | +0.113 | negligible | ✓ |

### Constraint Satisfaction

| Noise | n | Reactive | Planning | Δ Mean | 95% CI | Wilcoxon p | Bonferroni p | Cliff's δ | Effect | Sig. (α=0.05, Bonf.) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 150 | 0.747 | 0.713 | +0.033 | [-0.042, +0.107] | 0.2713 | 1.0 | +0.048 | negligible | ✗ |
| 0.1 | 150 | 0.723 | 0.517 | +0.207 | [+0.121, +0.296] | 1.512e-05 | 0.0001815 | +0.247 | small | ✓ |
| 0.2 | 150 | 0.758 | 0.486 | +0.272 | [+0.188, +0.357] | 3.895e-08 | 4.673e-07 | +0.338 | medium | ✓ |
| 0.3 | 150 | 0.727 | 0.539 | +0.187 | [+0.106, +0.268] | 2.995e-05 | 0.0003594 | +0.232 | small | ✓ |

## Summary

- **10 of 12** tests reach statistical significance after Bonferroni correction (α=0.05).
- Of the significant tests, 10 favour reactive, 0 favour planning.
- Cliff's δ magnitudes: 0 large, 1 medium, remainder small/negligible.