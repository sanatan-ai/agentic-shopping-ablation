# Research Journal

**Project:** Controlled Architectural Ablation of Reactive and Planning-Based LLM Agents on Constrained Multi-Step Web Shopping Tasks
**Student:** Sanatan Shrivastava (25103130) — MSCAI1

Working notebook for the practicum. Used for tracking what's done, what's open, what surprised me, and what I'd want to remember later when writing the thesis discussion.

---

## Session 1

Got the initial CA1 proposal back with my own reading of it. Topic: comparing reactive (ReAct-style) and planning-based LLM agents on multi-step web shopping tasks. The framing feels right — the literature has lots of new architectures but very few controlled comparisons holding everything else constant.

Tried to step back and identify weak points:
- ReWOO is being cited as if it's "the planning paradigm" but it's actually one specific flavour. Need to be more careful — ReWOO is a planner/worker/solver decomposition, not just "planning vs reactive."
- "Robustness" appears in the proposal but isn't operationalised anywhere. What does robustness even mean here? Noisy tools? Failed observations? Need a concrete definition before Phase 2.
- Bibliography has AgentBench's first author wrong (used Zhenyu Liu — it's actually Xiao Liu). Easy fix but caught only by checking.
- The planning agent's replanning behaviour isn't specified. No-replan planner is a strawman, full-replan blurs the architectural distinction. Need to pick a middle ground.
- Hadn't committed to whether to fork WebShop or build a custom environment.

So Phase 2 (the detailed proposal) is going to need to nail these down rather than leaving them for the Capstone semester.

---

## Session 2

Phase 2 detailed proposal scoping. Worked through each of the weak points from Session 1.

Planning agent design — went with **plan-then-execute + replan-on-failure, max 3 replans**. This is the middle ground: not so rigid that the planner is dumb (no-replan), not so flexible that it's basically reactive (full-replan). The replan trigger is "tool error or plan-contradicting observation" — same semantics as a real production agent.

Environment — decided to **build a custom one from scratch** rather than fork WebShop. Reason: WebShop's tool interface was designed for a particular task distribution that pre-dates the planning literature. Hard to claim "controlled ablation" if the environment is doing some of the work. A small custom environment with five tools (search, filter, compare, get_details, purchase) means we're truly controlling everything.

Noise model — settled on stochastic tool failures plus observation corruption (price ±10%, rating ±0.3), each applied with probability p/2 within a total failure probability p. Four noise levels: p ∈ {0, 0.1, 0.2, 0.3}. p=0 is the ceiling, the rest probe degradation.

Sized the experiment matrix:
```
50 tasks × 2 architectures × 4 noise levels × 3 seeds = 1,200 runs
```
This balances statistical power against compute. Not huge, but enough to do paired tests with confidence intervals.

Defined three-tier success: **Hard Success** (binary — all hard constraints met), **Preference Success** (continuous — how close to the optimal under preference function), **Constraint Satisfaction Rate** (continuous — fraction of hard constraints met). Headline metric is Hard Success; the others are diagnostic.

Defined nine evaluation metrics in a table — 3 success + 3 efficiency + 2 robustness + 1 behavioural. Statistical protocol: paired Wilcoxon signed-rank across seeds, Cliff's delta for effect size, 95% CIs. Non-parametric because sample is small and partly ordinal.

**Compute decision was the interesting one.** Initially talked through local Llama 3.1 8B via Ollama as the LLM — open-weight, mid-capacity, reproducible. Then mid-discussion the NCI AWS Educate survey came up. $100 credit available. Switched the plan entirely:

- **Primary:** AWS Bedrock + Llama 3.1 8B Instruct (`meta.llama3-1-8b-instruct-v1:0`). Temperature 0.0 throughout (the seed varies task ordering and noise, not model sampling). Estimated cost ~$15–20 for the full experiment.
- **Fallback 1:** Llama 3.1 70B if 8B saturates and architectural differences become invisible.
- **Fallback 2:** Local Ollama if Bedrock latency or quota becomes a bottleneck.

Bedrock gives us cloud-managed inference (no infrastructure overhead) while keeping the model open-weight (reproducibility argument still holds). Should have led with this option, but didn't think of it until the AWS thing came up.

Still open: synthetic catalogue vs real dataset. Defaulted to "synthetic" in the proposal text but it doesn't feel right — ecological validity argument is going to be a target.

---

## Session 3

Writing the Phase 2 proposal in earnest. Following NCI's CA2 marking grid: Title, ≤150-word Abstract, 1-2-page Introduction, ≤3-page LR with ≤10 refs, ≤4-page Research Method, Bibliography. The weight is 40% LR + 40% Method + 20% structure/refs.

Got supervisor feedback partway through:
1. Expand the research question — make it clearer.
2. Mention types of models being used / how this contributes to agentic AI.
3. Define "success" and "ground truth" precisely.
4. Make the goals measurable.

Worked these in. The RQ got a substantial expansion — instead of "how do reactive and planning agents compare" it became a full paragraph naming the architectures, the controlled variables (model, tools, task suite), and the three measurement dimensions. Better. Also added three sub-questions (proto-RQs) breaking the headline question into success / efficiency / robustness.

Got a second round of feedback:
1. Final goal needs to be stated as something measurable.
2. "Multi-step shopping tasks" is unclear — define it.
3. Make clear this isn't automating end-user web shopping.
4. Highlight contribution to agentic AI; maybe put "agentic AI" in the RQ itself.

All four were fair. The "not end-user automation" framing was a big one — there's a genuine misread risk where someone thinks we're trying to build a deployable shopping bot. We're not. The simulated environment is a methodological instrument. Wrote that explicitly into §1.2.

Defined "multi-step shopping task" formally: a task that can't be solved in one tool call, requires ≥4 calls, combines hard constraints with a preference function, requires search → filter → compare → purchase. Example: *"Find a laptop under €900 with at least 4-star rating and 1,000+ reviews — pick the cheapest."*

For the literature review locked a **3+3+2+2 thematic split**: 3 reactive (ReAct, Reflexion, Toolformer), 3 planning (ReWOO, Plan-and-Solve, LLMCompiler), 2 benchmarks (WebShop, WebArena), 2 evaluation (AgentBench, τ-Bench). Initially had 11 entries because Mind2Web slipped in. Dropped Mind2Web — it wasn't pulling weight in the prose anyway.

Every LR paragraph has to critically contrast at least two works. That actually wrote naturally — ReAct vs Reflexion (within-episode vs cross-episode), ReAct family vs Toolformer (in-context vs parametric), ReWOO vs Plan-and-Solve (architectural vs prompting separation), Plan-and-Solve vs LLMCompiler (sequential vs DAG), WebShop vs WebArena (control vs realism), AgentBench vs τ-Bench (model-varied vs reliability-focused). Each pair has a natural axis of contrast.

LaTeX conversion was its own thing. The CA2 template uses `article` class with `natbib` + `agsm` (Harvard) style. Wrote `main.tex` matching the template. Tried to compile locally — failed because `\euro` requires `eurosym` which I hadn't included. Added the package. Then `agsm.bst` was missing in the local TeX install, but it's standard on Overleaf so didn't matter for the final submission.

The whole thing came in at ~5,300 words across all sections. About right for the page budget.

Still open: dataset question. Going to revisit.

---

## Session 4

Asked about which dataset to use. The proposal as-written specified a synthetic catalogue, but I'd already downloaded the **Asaniczka Amazon Products Dataset 2023** (1.4M products, Kaggle, ODC-By v1.0). Two CSVs: `amazon_products.csv` (~360 MB) and `amazon_categories.csv` (4 KB lookup table). Schema: `asin, title, imgUrl, productURL, stars, reviews, price, listPrice, category_id, isBestSeller, boughtInLastMonth`.

Decided to use the real dataset. Ecological validity is stronger, and the synthetic-catalogue critique just goes away. Switched the proposal text to reference Asaniczka rather than "synthetic catalogue."

Important catch: the dataset has no `shipping_time` field. Real Amazon scrapes rarely capture it because it's user-/location-dependent. So the example task — *"laptop under €900, 4+ stars, shipping within 3 days, 1000+ reviews"* — won't work as written. Dropped the shipping clause.

Supervisor then asked for **EDA + pre-processing code alongside the proposal**. Pushed back on the implicit "and the task suite too" because tasks depend on the curated catalogue. Right order is: EDA → cleaning decisions → curated catalogue → tasks. Building tasks against an unvalidated catalogue would mean redoing them. Got agreement to do EDA + pipeline now, defer task suite to a follow-up.

Set up the project on Windows + VS Code. Stack: Python 3.11, `uv` for package management (modern, fast — much better than pip+venv), virtual env at `.venv/`, dependencies in `pyproject.toml`. Created the standard project layout:

```
agentic-shopping-ablation/
├── data/
│   ├── raw/         (gitignored — too big)
│   └── processed/   (curated catalogue lives here)
├── notebooks/
├── reports/
├── scripts/
├── src/
│   └── preprocessing/
├── tests/
├── .gitignore
├── pyproject.toml
└── uv.lock
```

Wrote the EDA notebook (`notebooks/01_eda.ipynb`, 9 sections, 35 cells). Worked through it cell-by-cell, eyeballing the output of each section before moving to the next. This is where the most consequential design changes happened.

**Section 1 (load + inspect)** — 1,426,337 rows, 11 columns. No NaN missingness *anywhere* — but `.describe()` showed something off. The 25%, 50%, *and* 75% percentiles of the `reviews` column are all zero. Meaning ≥75% of the entire dataset has `reviews = 0`. Suspicious — that's not "no reviews", that's missing data encoded as zeros.

**Section 2 (category filtering)** — searched the 248 categories for our five target buckets (laptops, headphones, smartphones, watches, cameras). Surfaced multiple problems:
- **No actual laptops.** Only "Laptop Accessories" (id 65) and "Laptop Bags" (id 109). Not a clean match for "laptops under €900."
- **Cell Phones & Accessories** (id 75) — single ID, 3,444 products.
- **Watches split into 4 IDs:** Men's (113), Women's (121), Boys' (89), Girls' (96). Kids' watches are a different product class — drop them; merge Men's + Women's.
- **Camera & Photo** (id 79) was fine but there's also a Security Cameras category (id 190) we should exclude.

Locked the five buckets as: **Headphones (71), Cameras (79), Watches (113+121), LaptopAccessories (65), Phones (75)**. Substituting laptops with laptop accessories is the honest call. Updated the example task accordingly: "laptop sleeve under €40" instead of "laptop under €900."

Filtering brought 1.4M down to ~45k products. About 3.15% of the dataset.

**Section 3 (missing values)** — this is where the reviews finding got worse. Within target categories:
- price = 0: 2.41% of rows
- stars = 0: 7.32% of rows
- **reviews = 0: 70.02% of rows**

Per-bucket breakdown was even more revealing. Cameras, LaptopAccessories, and Phones had 100% of products with `reviews = 0`. Headphones 15.5%, Watches 70.7%.

If we dropped on `reviews = 0`, we'd lose three entire buckets. That kills the study.

But: many of these zero-review products have non-zero stars. Mathematically impossible for a real rated product to have literally zero reviews. So `reviews = 0` is *scrape-side missingness* — the scraper just didn't capture the field for those products, didn't mean the product has no reviews.

Decision: **drop the reviews constraint entirely**. Keep `reviews` in the catalogue as an informational field but don't use it as a task constraint. New constraint set is category + price + stars + optional brand. Updated the example task to drop the "1000+ reviews" clause too. Now: *"Find a laptop sleeve under €40 with at least 4 stars — pick the cheapest."*

Missing-value rule simplifies to: drop where `title` is null/empty, `price ≤ 0`, or `stars ≤ 0`.

**Section 4 (duplicates)** — 0 duplicate ASINs (good — ASIN is supposed to be unique). 1,285 duplicate titles. Sampled them: e.g. "Women's Bracelet Watch" appears 41 times with *different* ASINs, prices, ratings, review counts. These are genuinely different products with generic titles, not duplicates. Decision: dedupe on ASIN only.

**Section 5 (price distribution)** — per-bucket medians:
- Phones: **$14** (this is suspicious)
- Headphones: $26
- LaptopAccessories: $25
- Cameras: $40
- Watches: $55

Phones median of $14 is wrong. Real smartphones are $100-$1000+. Category 75 must be dominated by accessories.

**Section 6 (ratings)** — "4+ stars" filters 81-94% of products in 4 of 5 buckets, only 67% in Headphones. Way too loose. Locked three tiers: 4.3 (loose), 4.5 (standard), 4.7 (tight) — calibrated against the median ≈4.4.

Stars-vs-reviews scatter plot was the smoking gun for the reviews finding. Only Headphones and Watches had any non-zero review data visible in the scatter. Three other buckets were completely blank. Confirmed the scrape-side-missingness theory.

**Section 7 (phones deep dive)** — sampled 15 random titles from the Phones bucket. **Zero of them were phones.** All accessories: screen protectors, watch bands (yes, in the phones category), USB-C adapters, charging cable winders, etc. Applied a keyword filter for obvious accessory terms — even the "likely-phones" survivors had median price $22, max $650. Smartphones don't cost $22. There are no actual phones in this dataset.

Decision: rename the bucket to **PhoneAccessories**. Keep all products, no filtering. Bucket is now honest about its contents. The research question doesn't care if the products are phones or phone cases — what matters is varied constrained-shopping tasks over a real catalogue.

**Section 8 (brand extraction)** — looked at the top-20 most-frequent first-words per bucket. Mixed results:
- Cameras: clean. Canon, Nikon, Sony, Fujifilm, GoPro, DJI all in the top 20. ~70% usable.
- Headphones: Sony, JBL, Sennheiser — but also "Wireless" at #1 with 482 occurrences. Generic feature words sneaking in.
- LaptopAccessories: "Laptop" #1 with 315, "65W" at 241, only a few real brands. ~20% usable.
- PhoneAccessories: Spigen, JETech, PopSockets all there. ~50% usable.
- Watches: **completely broken**. Top tokens are "Men's" (3,650), "Women's" (1,898), "Mens" (826), "Ladies" (317). Brands appear deep in the title.

First-word extraction won't work. Switched to **curated per-bucket allowlist** approach: ~35-40 known brands per bucket in a YAML file, whole-word case-insensitive matching anywhere in the title. Unknown → "Unknown" label.

Built the pre-processing pipeline as 5 Python modules:
- `config.py` — all locked decisions as a single config object
- `clean.py` — filter categories, drop missing, dedupe, extract brand, select final columns
- `sample.py` — stratified sampling
- `pipeline.py` — orchestrator
- `brands.yaml` — the brand allowlist

Plus `scripts/build_catalogue.py` as a one-command entry point.

Stratified sample at 100 products per bucket × 5 buckets = 500 total. Seed = 42 (standard convention). Output: `data/processed/catalogue.parquet`.

**Ran the pipeline.** First time, no errors. Final stats:

| Bucket | n | Price median | Stars median | Brand known |
|---|---|---|---|---|
| Cameras | 100 | $39.99 | 4.50 | 56% |
| Headphones | 100 | $21.49 | 4.20 | 27% |
| LaptopAccessories | 100 | $27.99 | 4.45 | 53% |
| PhoneAccessories | 100 | $13.97 | 4.50 | 52% |
| Watches | 100 | $42.99 | 4.40 | **8%** |

Watches brand coverage at 8% is the genuine long-tail distribution — watches in this dataset come from hundreds of small sellers. No allowlist would meaningfully improve that without false positives. Accepted. Brand-constrained tasks will mostly come from the four buckets at 50%+ coverage; Watches tasks will use price + stars + category only.

Verified the Parquet file: shape (500, 10), all buckets exactly 100, brands populating correctly, mix of branded and Unknown as expected.

Spot-checked one row: a Samsung Galaxy S21 screen protector was tagged brand="Samsung". The extractor matched the *device brand* in the title rather than the *seller brand* (NEW'C is the seller, Samsung is the phone brand). For our task purposes this is actually the more useful interpretation — "find a Samsung phone case" matches these. Accepted.

Wrote the EDA + pre-processing report (≤2 pages per the page budget). Eight EDA findings each with evidence and a locked decision. Per-bucket summary table. "Why only 500 products" justification got added later when supervisor asked for it — covered tractability, controlled difficulty, agent budget, sufficiency.

Initial Git commit: hash **37e630c**. EDA notebook + pipeline + catalogue Parquet + report all committed together. Reproducibility statement: anyone with the two raw CSVs in `data/raw/` can run `uv run python scripts/build_catalogue.py` and get a byte-identical catalogue.

Long day. Lots of design changes from EDA — but every one of them was *evidenced* by the data, which is a stronger story than the original assumptions would have been.

---

## Lessons accumulating so far

- Don't trust `.isna().sum()`. Check distributions and look for impossible patterns. Zeros where there shouldn't be any are missingness markers in disguise.
- Renaming buckets to match what's actually in the data is stronger than fighting the data to match what you wanted.
- EDA before commitments. Generating tasks against an unvalidated catalogue would have wasted a week and produced unreproducible artefacts.

---

## Session 5

Architecture + metrics study + draw.io diagram. Less data-archaeology, more documentation-heavy.

**Technical architecture.** Wrote a five-layer description: Data, Environment, Agent, Inference, Evaluation, with the orchestrator on top and a trace store on the side. Key invariant: **only the Agent layer differs between conditions**; everything else is shared and identical. That's what makes "controlled ablation" a defensible claim.

First draft ran 4+ pages with full pydantic schema definitions, retry/backoff logic, all the swappable interfaces spelled out. Too long. Cut it down to ≤2 pages — kept the layer diagram and the per-layer summary, dropped the implementation details (those go in the code).

**Draw.io diagram.** Generated a `.drawio` XML file: 6 colour-coded layers, solid arrows for synchronous control flow, dashed for async logging. Validated as well-formed XML. Can be opened in app.diagrams.net or via the VS Code Draw.io Integration extension (which is the cleanest because it keeps the diagram in the repo alongside everything else).

**Metric study report.** Supervisor wanted the 9 metrics justified against the literature review. Mapped each metric to at least one paper:
- Hard Success → WebShop, AgentBench
- Preference Success → WebShop's graded task score
- Constraint Satisfaction Rate → τ-Bench's policy-adherence framing
- Mean Tool Calls → ReAct, ReWOO
- Mean Tokens → ReWOO (this is *the* defining planning-paradigm efficiency metric)
- Mean Wall-Clock Time → LLMCompiler (latency as a first-class metric)
- Success vs Noise (curve) → τ-Bench pass@k (reliability framing)
- **Degradation Slope** → no direct precedent. Flagged honestly as synthesised. Justified pragmatically — needed a single number per architecture to support paired statistical testing.
- Failure Mode Distribution → Reflexion, AgentBench (both do qualitative trace coding)

Statistical protocol note: Wilcoxon + Cliff's delta is standard practice in NLP/ML eval but no specific paper in our LR prescribes it. Mentioned briefly.

Eight of nine metrics have published precedent. One synthesised. Acknowledging this honestly is better than pretending Degradation Slope has prior art it doesn't.

---

## Session 6

Two new supervisor asks:
1. 10 papers (5 seminal + 5 recent, last 2 years) with a gap analysis table. Report on similar papers + how mine differs.
2. Frame 2-3 RQs in the form *"To what extent does [method] outperform [baseline] on [metric] under [conditions]?"*

**Gap analysis.**

Hardest part was the "seminal" interpretation. Strict reading = foundational works pre-dating the LLM-agent wave. Lenient reading = highly-cited recent foundations like ReAct itself. Went with strict — better academic credibility, even though it meant reaching back further than I'd planned.

Final 10 papers:

*Seminal (5):*
1. Russell & Norvig — *AI: A Modern Approach* (multiple editions; 4th = 2020)
2. Fikes & Nilsson — STRIPS (1971) — ancestor of all modern planning
3. Brown et al. — GPT-3 (NeurIPS 2020) — established in-context learning
4. Wei et al. — Chain-of-Thought (NeurIPS 2022) — direct precursor to ReAct
5. Sutton & Barto — *Reinforcement Learning: An Introduction* (2nd ed, 2018)

*Recent (5, all 2023-2024):*
6. Yao et al. — ReAct (ICLR 2023)
7. Xu et al. — ReWOO (arXiv 2023)
8. Zhou et al. — WebArena (ICLR 2024)
9. Liu et al. — AgentBench (ICLR 2024)
10. Yao et al. — τ-Bench (NeurIPS 2024)

This drops Reflexion, Toolformer, Plan-and-Solve, and LLMCompiler vs the original Phase 2 LR composition. Trade-off: less coverage of planning variants in the recent set, but a genuine historical lineage from STRIPS to ReWOO that the previous composition lacked.

The gap analysis table has 8 columns: Domain, Architecture studied, Controlled ablation?, Model held constant?, Tools held constant?, Robustness tested?, Multi-step constraint reasoning?, Open-weight evaluated? Reading down each column makes the gap visible — almost every "No" in the table is filled by my work in the final row.

Niche statement: this is the only work in the comparison set simultaneously doing (i) architecture as sole IV, (ii) fixed model + tools + task suite, (iii) systematic noise variation, and (iv) open-weight mid-capacity model. Intersection of all four is empty in prior literature.

Also collected download links for all 10 papers — arXiv for 7, IJCAI archive for STRIPS, Stanford mirror for Sutton & Barto, Berkeley official for AIMA. Wrote a PowerShell one-shot to download the 9 free ones at once.

**Research questions.**

Template: *"To what extent does [method] outperform [baseline] on [metric] under [conditions]?"*

Three RQs, one per dimension:

**RQ1 (Success):** plan-then-execute > reactive on Hard Success, noise-free. Directional prediction grounded in ReWOO + Plan-and-Solve both reporting planning's edge on multi-step tasks.

**RQ2 (Efficiency / Tokens):** reactive > planning on mean tokens, noise-free. This is the contestable one. ReWOO's central claim is that planning *reduces* tokens. But ReWOO tested on GPT-3.5; we're on Llama 3.1 8B. Planning's upfront prompt + replanning cost may dominate per-step savings at smaller scale. The hypothesis is reactive wins. A refutation would itself be a finding — it would extend ReWOO's claim to small-model settings.

**RQ3 (Robustness):** planning > reactive on Degradation Slope (smaller slope = more robust), noise levels p ∈ {0, 0.1, 0.2, 0.3}. Planning has explicit replan-on-failure; reactive has no equivalent recovery mechanism. Lined up with τ-Bench's pass@k framing.

The three predictions go: planning, reactive, planning. Differing winners. More interesting than a uniform-winner story would have been.

---

## Open at this point

- Task suite generation. Hasn't been done. Depends on the catalogue (done) and the locked constraint types (done — category + price + stars + optional brand). Probably 50 tasks, calibrated per-bucket thresholds. TODO: do this in the next session.
- Whether the 8% Watches brand coverage will actually limit downstream Watches brand-constrained tasks. Won't know until task generation runs.
- Llama 3.1 8B saturation risk — unmeasurable until pilot run. Decision gate is Capstone Week 7 (P4 pilot phase).
- Need to chase up whether AWS Bedrock has Llama 3.1 8B in eu-west-1 or whether I'll need us-east-1 (which is fine for research but adds latency).

---

## Session 7

Started keeping this journal more formally. Realised mid-project that I should have been doing this since day one — having a running record of decisions and surprises would have saved time recalling rationale when supervisor asks "why did you decide X". Decided to backfill the existing sessions from memory + the chat history with my AI collaborator.

Also adding a quick index because the journal has gotten long enough to need one — was getting hard to find specific decisions otherwise.

---

## Index

| Subject | Find in |
|---|---|
| Final research question | Session 3 |
| Three operationalised RQs (RQ1, RQ2, RQ3) | Session 6 |
| Reactive agent design | Session 2 |
| Planning agent design (plan-then-execute + replan) | Session 2 |
| Why custom environment, not WebShop | Session 2 |
| LLM choice (Llama 3.1 8B on Bedrock) | Session 2 |
| Why AWS Bedrock specifically | Session 2 |
| Dataset choice (Asaniczka Amazon 2023) | Session 4 |
| Five buckets + bucket renaming | Session 4 |
| Missing-value policy (drop on stars=0; reviews kept but unused) | Session 4 |
| Why reviews aren't a task constraint | Session 4 |
| Star-rating tiers (4.3 / 4.5 / 4.7) | Session 4 |
| Brand extraction (curated allowlist) | Session 4 |
| 500 products / 100 per bucket / seed=42 | Session 4 |
| Catalogue Parquet artefact + Git commit hash 37e630c | Session 4 |
| Noise model (failures + observation corruption) | Session 2 |
| Experiment matrix size (1,200 runs) | Session 2 |
| Nine evaluation metrics + 3-tier success | Session 2, Session 5 |
| Statistical protocol (Wilcoxon + Cliff's delta) | Session 2 |
| Literature review composition (5+5 seminal+recent) | Session 6 |
| Gap analysis (8-column table) | Session 6 |
| Niche statement | Session 6 |

---

## Decisions worth pinning

This is a running list — added after I noticed the journal entries were where the actual decisions lived, and supervisor would probably want a quick-reference. Tagged against the session they were locked in.

| # | Decision | Locked in |
|---|---|---|
| 1 | Research question = controlled architectural ablation | S1 |
| 2 | Reactive agent = pure single-episode ReAct (no cross-episode memory) | S2 |
| 3 | Planning agent = plan-then-execute + replan-on-failure (max 3 replans) | S2 |
| 4 | Custom simulated environment, not WebShop fork | S2 |
| 5 | Noise model: tool failure or observation corruption, each at p/2 | S2 |
| 6 | 1,200 runs (50×2×4×3) | S2 |
| 7 | 3-tier success: Hard / Preference / Constraint Satisfaction | S2 |
| 8 | 9 evaluation metrics across 4 dimensions | S2 |
| 9 | LLM = Llama 3.1 8B on AWS Bedrock; fallbacks 70B + Ollama local | S2 |
| 10 | Dataset = Asaniczka Amazon Products 2023, ODC-By v1.0 | S4 |
| 11 | Drop reviews as constraint (kept as info field only) | S4 |
| 12 | Rename "Laptops" → LaptopAccessories | S4 |
| 13 | Rename "Phones" → PhoneAccessories | S4 |
| 14 | Merge Men's + Women's watches into single "Watches" bucket | S4 |
| 15 | Star tiers 4.3 / 4.5 / 4.7 | S4 |
| 16 | Curated brand allowlist (~35-40 per bucket); unmatched → "Unknown" | S4 |
| 17 | 500 products, 100 per bucket, seed = 42 | S4 |
| 18 | LR composition: 5 seminal + 5 recent (supersedes original 3-3-2-2 thematic split from S3) | S6 |
| 19 | RQ2 direction = reactive > planning on tokens (contestable; flips ReWOO's claim for small-model context) | S6 |
| 20 | Task suite: 50 tasks, 15 easy / 20 medium / 15 hard, 10 per bucket. Brand-gated Hard tasks (Cameras / LaptopAccessories / PhoneAccessories only) | S8 |
| 21 | Task constraint thresholds calibrated per-bucket (price quantiles 50th/30th/15th; stars 4.3/4.5/4.7); valid-set bounded to [2, 30] | S8 |
| 22 | Action format = structured JSON (Pydantic-validated); search = pure text matching; result cap = 10 with overflow flag | S9 |
| 23 | Noise injector seeded independently per (task, noise_level, seed) → identical perturbations across architectures (fairness invariant) | S9 |

---

## Lessons (added over time, ordered by when I noticed them)

- **(after S4)** Missing data is rarely null. This dataset encodes it as zeros — would have wasted days assuming `.isna().sum()` was the whole story. Always check distributions for impossible patterns.
- **(after S4)** Don't fight the data. The "Phones" bucket has no phones. Renaming was the right call, not trying to filter accessories more aggressively.
- **(after S4)** EDA before commitments. Pushing back on "do tasks now" saved a complete redo.
- **(after S5)** Be honest about novelty. Flagging Degradation Slope as a synthesised metric (no precedent) is stronger than pretending it has one.
- **(after S6)** Directional hypotheses make experiments tell stories. RQ2 framed as "reactive wins on tokens for small models" is more interesting than "planning wins" — opens both outcomes to being publishable findings.
- **(after S7)** Reproducibility is a contribution, not infrastructure. The fixed seed + deterministic pipeline + committed Parquet artefact is worth pointing to in the thesis, not burying in a methods footnote.
- **(after S8)** Resampling-with-validity is more robust than upfront constraint design. Letting the generator try up to 200 constraint combinations per task slot and discarding ones outside the [2, 30] valid-set band means I don't need a perfectly-tuned constraint distribution — the validity check enforces difficulty for me.
- **(after S9)** Pure text search is a deliberate research choice, not a limitation. A semantic search would do the agent's work for it and contaminate the architectural comparison. Document this explicitly in the thesis.
- **(after S9)** Oracle-agent sanity checks are cheap and catch real bugs. Writing 50 lines of cheating code that exercises every tool against every task gave 100% confidence the environment is wired correctly *before* any LLM was involved. Lesson: separate environment correctness from agent correctness, test them independently, in that order.

---

## Session 8

Task suite generation. Catalogue's been fixed for a while; time to build the benchmark of 50 constrained shopping tasks against it.

Locked the structure upfront: each task carries a natural-language prompt, a structured constraint spec, a preference function, the full valid set, and the optimal product(s) under the preference. The structured spec and the ground truth never go to the agent — they're for scoring only.

Difficulty mix was 15 easy / 20 medium / 15 hard. Two design moves to keep this honest:

- **Brand gating.** Hard tasks require a brand constraint, which means brands need to be identifiable from the catalogue. Cameras (56%), LaptopAccessories (53%), PhoneAccessories (52%) make the cut. Headphones (27%) and Watches (8%) don't — so Hard tasks only generate from the eligible buckets, and Headphones/Watches absorb their Hard slots as additional Medium tasks. Allocation works out exactly: 3 brand-eligible × 5 Hard = 15, 2 ineligible × 7 Medium + 3 brand-eligible × 2 Medium = 20, 3 Easy × 5 = 15. Total 50 ✓
- **Per-bucket threshold calibration.** Price caps drawn at the 50th / 30th / 15th percentile of each bucket's price distribution, not from absolute ranges. Star tiers fixed at 4.3 / 4.5 / 4.7. Constraint thresholds get rounded to natural numbers ($25 not $24.83) before getting rendered into prose, so the prompts read like a person wrote them.

Natural-language rendering: 3 surface variants per (preference × stars × brand) combination. "Find a... and choose the cheapest." vs "I need a... Pick the cheapest one." vs "Looking for the cheapest...". Same constraint spec, different wording. Helps test that the agent's NL interpretation is robust to surface variation, without confounding architecture.

Validity check: any sampled task whose valid set falls outside [2, 30] gets discarded and resampled. Lower bound is so the task has alternatives (not just "find the one product that exists"); upper bound is so the constraint is non-trivial (filters out a meaningful fraction). Up to 200 resampling attempts per task slot. Final run: no failures.

Wrote it as 3 modules (`config.py`, `models.py`, `generator.py`) plus `scripts/build_task_suite.py`. Pydantic schemas for the data types — same discipline as the catalogue pipeline.

Smoke-tested locally before running on the real catalogue. Then ran the script on the committed catalogue, no errors. Allocation came out exactly as designed (15 easy / 20 medium / 15 hard, 10 per bucket). Valid-set sizes ranged 2-29 with median ~13. Three sample tasks looked clean:
- Easy (T005, PhoneAccessories): *"I need a phone accessory priced below $8.00..."* — valid set 21.
- Medium (T002, Headphones): *"Looking for the best-rated pair of headphones under $17.00 with 4.5+ stars."* — valid set 9, with 5 tied optima at 5.0 stars (good — tests that the scorer handles ties).
- Hard (T001, PhoneAccessories): *"I need a phone accessory by Samsung, priced below $10.00, rated at least 4.5 stars..."* — valid set 5.

Committed: `c94dce4`. Also caught a Git oddity where 6 of the preprocessing files showed as "modified" — turned out to be a mix of intentional manual cleanups (real) and CRLF/LF normalisation on copy-pastes (cosmetic). Committed as-is; flagged the line-ending issue for future cleanup with `.gitattributes`.

---

## Session 9

Environment + sanity check. This is the simulated world the agents will act on. Five tools, action validation, observation contract, noise injector middleware, episode controller. Zero LLM involvement at this stage.

Big design decisions to settle before code:

- **Action format.** Structured JSON, not function-call strings. Agent emits `{"tool": "filter", "args": {...}}`. Pydantic-validated. Fail-fast on malformed.
- **`search` semantics.** Pure text matching — return products whose title contains all query words. No semantic understanding, no bucket inference. This is deliberate: it forces the agent to use `search` + `filter` together for multi-step solutions, which is exactly the architectural behaviour under study. A semantic search would conflate retrieval quality with reasoning quality.
- **Result cap.** 10 products per observation, with an overflow flag. Mirrors real e-commerce pagination and bounds the context size for the agent.

Implementation split across 4 modules under `src/environment/`:
- `models.py` — Pydantic schemas for Action, Observation, Product, TraceStep.
- `tools.py` — Pure functions for the 5 tools. Each takes the catalogue + typed args, returns an Observation.
- `noise.py` — `NoiseInjector` middleware. With probability *p*, either inject a structured `transient_failure` error or return a perturbed observation (price ±10%, stars ±0.3, reviews ±5%). Two modes, equal probability *p*/2 each. Terminal observations never perturbed.
- `environment.py` — Top-level `Environment` class composing the above plus episode state (step budget=15, malformed-action limit=3 consecutive).

Critical property of the noise injector: it carries its own seeded `random.Random`. Same (task, noise_level, seed) → identical noise pattern regardless of architecture. Without this, robustness comparison wouldn't be fair.

**Sanity test via oracle agent.** Wrote a deliberately cheating "agent" in `src/oracle/oracle_agent.py` that knows the ground truth and executes a deterministic 4-step sequence: search → compare → get_details → purchase optimal. If the oracle doesn't score 100% Hard Success at noise=0, the environment has a bug. Not the agent — the environment.

Ran the sanity check script:
Purchased terminations:    50 / 50  (100.0%)
Hard Success:              50 / 50  (100.0%)
Preference Success:        50 / 50  (100.0%)
PASS: Environment is wired correctly.

Also smoke-tested the noise injector at p ∈ {0, 0.1, 0.2, 0.3}. Error rates came out as 0%, 5%, 9%, 13% — close to the expected p/2 (theoretical: 0%, 5%, 10%, 15%). Sample size is only 100 trials so small noise around the expected rate is fine.

The environment is now a fixed, tested substrate. Agents will compose against it without modifying it. The `Action`/`Observation` contract is the interface they have to honour — that's what comes next.

Committed: `1075590`.

---

*Next: reactive agent + Bedrock integration.*
