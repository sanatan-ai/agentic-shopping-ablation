# Failure-Mode Taxonomy v1 (for qualitative coding of full-experiment failed traces)

**Purpose:** Provide a reasoning-level taxonomy of *why* an agent's episode failed, going beyond the environment-side `failure_mode` label (which captures only the terminal state).

**Use both in Pass 1 (now) and Pass 2 (in ~10 days).** Do not modify between passes — modifications after Pass 1 would compromise the intra-rater agreement measurement.

**Coder:** Sanatan Shrivastava (single coder; Cohen's kappa computed as intra-rater self-agreement across the temporal gap).

---

## Categories

### 1. Wrong-product-satisfying
The agent successfully purchased a product from the catalogue but the purchased product does not satisfy all hard constraints (bucket, max_price, min_stars, brand). It is *in* the catalogue but *not* in `valid_set`.

**Signature:** `purchased_asin is not None`, but at least one hard constraint is violated.

### 2. Search-blindness
The agent's search returned mostly cross-bucket results (e.g. `search("camera")` returns phone accessories with "camera" in the title). The agent proceeded to filter/purchase from these irrelevant results without recognising the mismatch.

**Signature:** search returns products from ≥2 buckets; agent doesn't refine bucket before proceeding.

### 3. Failed-narrowing
The agent tried to progressively filter but the filters didn't compose — either the agent called `filter` without `candidate_asins`, or the candidate_asins arg was coerced to None (whole-catalogue fallback). Result: subsequent filters "reset" to the whole catalogue.

**Signature:** ≥2 filter calls where the second was intended to narrow the first but returned products outside the first's scope.

### 4. Non-commitment
The agent thought and acted repeatedly (search, filter, get_details, compare) but never invoked `purchase()`. Ended with `budget_exhausted` or by hitting parse-error limits without a purchase.

**Signature:** `purchased_asin is None`, terminal_reason is `budget_exhausted` or timeout, and no purchase attempted in any step.

### 5. Plan-execution-mismatch (planning only)
The planning agent's plan references ASINs it hadn't yet retrieved. The execution of the plan therefore reaches a step that can't be resolved.

**Signature:** planning agent, plan includes `purchase(product_id=X)` where X wasn't returned by any prior step in that plan.

### 6. Replan-treadmill (planning only)
The planning agent hit consecutive replans, each replan failing to converge on a purchasing plan. Terminated via `replan_limit_exceeded`.

**Signature:** planning agent, `terminal_reason == "replan_limit_exceeded"`, ≥3 replans logged.

### 7. Budget-exhaustion-mid-narrowing (reactive typically)
The agent used all 15 step budget still exploring/comparing without deciding. Different from Non-commitment in that the agent *was* making progress toward a decision but ran out of steps.

**Signature:** `terminal_reason == "budget_exhausted"`, at least one `compare` or `get_details` call in the last 3 steps.

### 8. Malformed-action-recovery-failure
The agent's actions were rejected by the environment schema on 3 consecutive attempts, triggering `malformed_limit`. (Rare after the coercion fix; should be near-zero in the full experiment.)

**Signature:** `terminal_reason == "malformed_limit"`.

### 9. Constraint-misinterpretation
The agent purchased a product that matches part of the task NL but violates a specific constraint (e.g. task says "under $16" and agent buys at $16.50; or task says "4.7+ stars" and agent buys 4.5-star).

**Signature:** `purchased_asin is not None`, valid bucket, but numeric constraint fails by a small margin. Distinguishable from category 1 (which is more scattershot).

### 10. Other / uncoded
Genuine ambiguity, or a new pattern not covered by categories 1-9. Add free-text notes to justify.

---

## Coding rules

1. **Assign exactly one primary category.** If multiple apply, choose the one most causally proximate to the failure.
2. **When a run is technically a Hard Success but Preference failure**, code it if it's in the sample. Use category 1 or a note.
3. **When in doubt between 3 and 5**, remember: 3 is a filter-composition problem (either agent); 5 is planning-specific structural mismatch.
4. **Free-text notes** (optional but encouraged) capture nuance the category doesn't.
5. **Do not modify this taxonomy** between passes.

---

## Sample provenance

- 48 failed traces sampled from the full experiment
- Stratified: 12 per environment-side `failure_mode` category (wrong_product, replan_limit_exceeded, budget_exhausted, no_purchase:unknown)
- Sampling seed: 42 (fixed for reproducibility)
- Sample paths locked at `data/qualitative_coding/sampled_traces.json`
- Same sample used for both passes