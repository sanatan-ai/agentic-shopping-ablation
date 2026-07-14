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
| 24 | Project location moved out of OneDrive to `C:\Users\sanat\Projects\` — venv operations were locking on sync conflicts | S10 |
| 25 | LLM client architecture: Protocol with `BedrockClient` (real) + `MockClient` (canned). Cost tracking baked in. Lazy boto3 import. | S10 |
| 26 | Bedrock model ID requires `us.` inference-profile prefix: `us.meta.llama3-1-8b-instruct-v1:0` (AWS migrated Llama 3.1 8B off direct on-demand invocation) | S10 |
| 27 | Planning agent's plan/purchase resolution = option (b): plan up to narrowing, replan for the final purchase. Trigger on either error OR plan-finished-without-purchase. | S11 |
| 28 | Pilot configuration locked: 20 stratified tasks × 2 architectures × 2 noise levels × 1 seed = 80 runs at ~$0.24 cost | S12 |
| 29 | Prompt addendum teaching `candidate_asins` chaining locked into both agents identically. Wording: same paragraph in same position. The post-fix prompts are the "fair comparison" condition. | S13 |
| 30 | Stop pilot iteration here. n=20 per cell is too small to discriminate prompt-effect noise from signal. Capstone full experiment is the right place to retest. Both pilots cited as a documented chaining-instruction ablation in the thesis. | S13 |`
| 31 | Region locked at us-east-1 (supervisor confirmed). eu-west-1 was a latency-convenience suggestion, not correctness. Document the deviation as a methodology note. | S14 |
| 32 | Full Capstone experiment runs on Llama 3.1 70B (`us.meta.llama3-1-70b-instruct-v1:0`). Floor-effect criterion met after post-fix pilot showed 8B below 30% Hard Success. Supervisor authorised. | S14 |
| 33 | CloudWatch latency = primary source for full experiment. Python local timing = sanity cross-check. Methodology footnote will note the difference between pilot (Python) and main experiment (CloudWatch). | S14 |
| 34 | Permissive coercion in FilterArgs.candidate_asins: string "null"/"previous_result" → None; stringified lists → parsed. Tool semantics unchanged; parser tolerance only. | S17 |
| 35 | Full experiment safety mechanisms locked: checkpoint/resume, retry-with-backoff (5 attempts, exp base=1s), cost-abort threshold $50 USD. | S18 |
| 36 | Full experiment seeds locked: {42, 1, 2024}. Varied, memorable, three genuinely different values. | S18 |
| 37 | Cliff's δ methodology footnote: on binary paired outcomes, δ reduces to paired proportion difference; magnitude labels understate practical importance. | S20 |
| 38 | Thesis Discussion chapter to be structured around RQ3 (noise-conditional divergence) as the headline. RQ1 and RQ2 presented in service of that story. | S20 |


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
- **(after S10)** OneDrive is incompatible with Python virtual environments. The sync engine holds file handles open intermittently, which makes any operation that touches the venv (uv add, pip install, even `git status` occasionally) susceptible to "Access denied" errors. Should have moved the project out at first sign of trouble, not waited until step C. Move was 30 seconds, problem disappeared.
- **(after S10)** Bedrock's model invocation requirements change over time. AWS migrated Llama 3.1 8B Instruct from on-demand to inference-profile-only invocation. The fix was a 3-character prefix (`us.`), but the error message was clear about the cause. Worth keeping the `BedrockClient.model_id` constant explicit and the error-handling resilient — these invocation conventions are not stable AWS contracts.
- **(after S11)** Edit Python carefully, especially around `@dataclass` classes. A small indentation slip turned a class method into a module-level orphan and produced an AttributeError that took 5 minutes to track down. After any manual edit, run a quick import check on the affected module before moving on.
- **(after S12)** Always inspect at least one trace file before declaring a pilot's findings final. The aggregated numbers told a story about architectural performance, but the trace revealed *why* — the agents weren't using `candidate_asins`, so progressive narrowing wasn't actually happening. This is the kind of observation that turns a numerical result into a methodologically defensible thesis chapter, and it's only visible from individual traces, never from aggregates.
- **(after S13)** Identical prompt interventions don't have identical effects across architectures on small open-weight models. The chaining instruction helped planning by +10pp Hard Success and hurt reactive by −5pp. Likely mediated by per-call system-prompt overhead: reactive consults the system prompt every step (~11 times per episode), planning only 3-4 times. Architectures that "pay" for the prompt more often suffer more when the prompt gets longer. This asymmetry is real and worth foregrounding in the thesis — it cautions against assuming a prompt-engineering improvement is architecture-agnostic.
- **(after S13)** Know when to stop iterating. The temptation to keep tweaking prompts until both architectures improve was strong. Resisting it is the right call. Pilot iteration with n=20 chases noise; the full experiment is where statistical claims get made. Document the interim findings honestly and move on.
- **(after S14)** Always check for pre-existing supervisor instructions before scoping infrastructure work. The AWS checklist had been sent before Session 10 and I missed it because I was focused on the plan I was building with the AI collaborator. Four items needed retrofitting. Cost a day. Lesson: at every new phase of work, ask "did the supervisor send any instructions about this?" before designing from scratch.
- **(after S14)** When you've missed something, the only winning move is to be transparent fast. Acknowledged the gaps, took ownership, asked his guidance on the open question (region), started the cheap items in parallel. Result: he made clean calls, accepted the receipts, authorised the 70B escalation. Trying to hide the gaps or rationalise them would have damaged trust. Direct ownership repaired it.
- **(after S14)** Trust your pre-experimental decisions even when results invert your hypotheses. All three RQ directional predictions appear to be falsified in the pilot. The first instinct is to question the methodology — "did we make a mistake somewhere?" Often the discipline of the locked decisions (action format, prompts, seeds, valid-set bounds) is exactly what gives the result credibility. RQ inversions are the most scientifically interesting outcome possible. Don't second-guess them; report them honestly.
- **(after S16)** Small-model prompt engineering interventions can create novel failure modes at higher model scales. The chaining instruction added in Session 13 to help both agents was quietly ignored by 8B and actively tried by 70B, exposing a new schema-validation gap that only manifested at the higher capability level. This is worth flagging in the thesis discussion: interventions calibrated for one model scale don't transfer for free to another.
- **(after S17)** When a fix does more than it was designed to do, that's worth understanding, not just celebrating. The coercion fix targeted 3 malformed_limit failures but also unblocked ~10 previously stuck runs. Understanding *why* (coercion falls back to whole-catalogue, letting planning at least *complete* plans) revealed a deeper architectural constraint that supervisor flagged for the discussion.
- **(after S18)** Build safety mechanisms before you need them. Checkpoint/resume, retry-with-backoff, and cost-abort each felt like paranoia when I built them. All three got exercised. The accidental laptop shutdown in Session 19 would have wiped 917 runs without the checkpoint; the throttling retries silently saved individual runs during the full experiment; the cost cap didn't trigger but was the right thing to have.
- **(after S19)** End-to-end verification of a safety mechanism sometimes writes itself. The accidental shutdown at 917/1200 runs was an unplanned test of the checkpoint/resume system. It worked exactly as designed and became a concrete methodology-chapter data point.
- **(after S20)** Recognise the boundary between AI-assisted tooling and AI-performed analysis. Building code with an AI collaborator, drafting text for review, exploring design choices — all appropriate. Asking the collaborator to perform the qualitative coding I promised the supervisor I would do — not appropriate. The collaborator refused correctly. The temptation to offload came from real fatigue, but the check needed to be my judgement, not its. Recording this because the pattern will recur across the thesis-writing phase and the answer needs to be the same each time.

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

## Session 10

Reactive agent + first real LLM in the loop. The week's been about getting Bedrock fully wired up and Llama 3.1 8B actually answering a query, then plugging it into a real ReAct loop.

AWS setup was the day-one drag. Started with the AWS Academy Lab from NCI but quickly switched to a personal account with $100 free credit — Academy Lab has time-limited sessions and restricted services, which would be a pain to manage across the whole project. Personal account = full Bedrock access, no time pressure.

Setup steps that ate the time:
- Billing alert (zero-spend budget at $10 threshold) → 2 min.
- Region switch to us-east-1 → 1 min. Llama 3.1 8B isn't in eu-west-1, has to be us-east-1.
- Model access — turned out to be the easiest step. AWS retired the manual "Model access" page; serverless foundation models are now auto-enabled on first invocation. Was bracing for a "wait 24 hours for approval" thing, didn't need to. Saved a day.
- IAM user with `AmazonBedrockFullAccess` policy → 5 min.
- Generated access keys, saved them somewhere safe.
- `winget install Amazon.AWSCLI` then `aws configure` then `aws sts get-caller-identity` to verify. Worked first try.

Then the smoke test. First attempt:

```python
MODEL_ID = "meta.llama3-1-8b-instruct-v1:0"
```

→ `ValidationException: Invocation of model ID ... with on-demand throughput isn't supported. Retry your request with the ID or ARN of an inference profile that contains this model.`

Turns out AWS recently moved Llama 3.1 8B to inference-profile-only invocation. The fix is a prefix:

```python
MODEL_ID = "us.meta.llama3-1-8b-instruct-v1:0"   # the us.* prefix
```

Re-ran, got back `'\n\nOK.'` with 28 tokens used. Working.

Cost = $0.000007. Microscopic. Even if every call were that small, we'd spend pennies on a thousand runs.

**OneDrive bit me again.** When trying to `uv add boto3`, got an Access Denied error on `.venv\Lib\site-packages\agentic_shopping_ablation-0.1.0.dist-info`. OneDrive was holding the dist-info files open. The Move-Item command to relocate the project also failed once ("item is in use") — had to `cd C:\Users\sanat` to release the directory, then close VS Code, then the move worked. Project now lives at `C:\Users\sanat\Projects\agentic-shopping-ablation`. Should have done this in Session 4. The .venv is fully out of OneDrive now and the pain has stopped.

Built the reactive agent itself across 4 modules in `src/agents/`:
- `llm_client.py` — `LLMClient` Protocol + `BedrockClient` + `MockClient`. Cost tracking baked into BedrockClient (every call accumulates `total_input_tokens`, `total_output_tokens`).
- `prompts.py` — system message with the 5-tool spec + initial user message template + per-step observation message template.
- `parser.py` — JSON output parsing with markdown-fence stripping and balanced-brace extraction. Falls back gracefully if Llama wraps the JSON in ```json ... ``` (it sometimes does).
- `reactive_agent.py` — the actual loop. Thought → Action → Observation. Max 5 consecutive parse errors before giving up. Conversation history accumulates verbatim (no summarisation — would muddle the architectural comparison).

Three things I built into the design that I want to remember for the thesis methodology:
1. The Protocol abstraction means the agent never imports boto3. Sanity tests run against MockClient with zero AWS spend. Same agent code.
2. BedrockClient's cost-tracking gives every run a token + dollar receipt. Useful for the thesis methodology section ("each run logged its cost").
3. Lazy boto3 client creation. MockClient users don't even need boto3 installed.

Mock sanity tests, 2 scenarios, both pass:
- Happy path: 3 canned responses → agent executes search/filter/purchase → buys optimal product.
- Parse recovery: first response is unparseable garbage, agent gets an error observation and self-corrects → buys optimal on the 2nd valid response.

Then the first real Bedrock run, single task T005 ("phone accessory under $8, highest-rated"):

```
Steps taken:        8
Terminated:         True
Terminal reason:    purchased
Purchased ASIN:     B07Q3G17GD
LLM calls:          8
Input tokens:       13,068
Output tokens:      460
Parse errors:       0  ← every JSON valid first try
Wall clock:         4.69s
Hard Success:       YES (purchased in valid_set)
Preference Success: NO (not the optimal)
Cost:               $0.002983
```

Worked first try. 0 parse errors. Hard Success = YES. Llama 3.1 8B emitting clean JSON without prompt-tuning was a pleasant surprise. The Preference Success = NO is interesting — the task said "highest-rated" and the agent picked a valid-but-not-optimal product. That's nuanced behaviour exactly aligned with what RQ1 is trying to measure. Cost projection for 1,200 runs: ~$3.60. Way under budget.

Also: every Bedrock call now logs `BedrockClient initialised: model=us.meta.llama3-1-8b-instruct-v1:0, region=us-east-1` on session start. Methodologically defensible — every experimental run has a provable model ID in its trace. Supervisor or thesis reviewer can audit.

Committed: `062a5f6` for the agent code + `3397985` for the bedrock_smoke_test script (committed earlier).

---

## Session 11

Planning agent (plan-then-execute + replan-on-failure). Same infrastructure as the reactive agent — same `LLMClient`, same `Environment`, same parsing utilities — but a different prompt and a fundamentally different control loop.

The interesting design question was how to handle ASIN-based actions in the initial plan. The agent can't know which ASIN to `purchase()` upfront because it hasn't done any search yet. Two options:

(a) Symbolic placeholders. Agent emits `"product_id": "<TO_BE_DETERMINED>"` and we resolve it during execution by looking at prior observations.
(b) Plan only up to narrowing; once execution finishes (because the plan ended without a purchase), trigger a replan that has the narrowed candidates in context, and now the agent emits the final purchase.

Went with (b). Cleaner. Closer to how ReWOO's evidence-collection-then-solver works. And our replan-on-failure mechanism already covers the trigger — "plan finished without purchasing" is just another replan trigger alongside "tool error".

Built across 3 new modules in `src/agents/`:
- `planning_prompts.py` — separate system message explaining the two-phase model. Initial plan prompt + replan prompt (with execution-history-so-far passed in).
- `planning_parser.py` — parses `{"plan_summary": "...", "plan": [<action>, <action>, ...]}` into a list of validated Action objects. Reuses the markdown-stripping and JSON-extraction helpers from the reactive parser.
- `planning_agent.py` — the loop. Plan → execute action-by-action → if error or plan-finished-without-purchase, replan (up to 3 times). Critical: NO LLM call between actions during execution. That's the efficiency claim ReWOO makes.

Hit a real bug after wiring it all up. The Bedrock test failed with:
```
AttributeError: 'BedrockClient' object has no attribute 'complete'
```
Confusing because we'd literally been using `BedrockClient.complete()` an hour earlier for the reactive agent. Traced it to the runtime log line I added earlier for model-ID provenance. The edit had screwed up indentation:

```python
class BedrockClient:
    model_id: str = BEDROCK_MODEL_ID
    ...
def _ensure_client(self):   # ← NOT indented as a method — class ends here
    ...
    def complete(           # ← orphan, not a class member anymore
```

So `BedrockClient` had no `complete()` because Python saw the class as ending after the fields. Re-indented properly, ran again, worked.

**Lesson:** when manually editing Python files, especially around `@dataclass` classes, indentation is everything. I should have run the file's `python -c "from src.agents.llm_client import BedrockClient; print(BedrockClient.complete)"` *immediately* after the edit, not waited until I was running the planning agent and got a cryptic AttributeError.

Mock tests passed (2/2). Real Bedrock test on T005 (same task as the reactive run for direct comparison) gave:

| | Reactive (S10) | Planning (S11) |
|---|---|---|
| Steps | 8 | 14 |
| LLM calls | 8 | **4** |
| Input tokens | 13,068 | **11,975** |
| Output tokens | 460 | 489 |
| Wall clock | 4.69s | **3.43s** |
| Hard Success | YES | YES |
| Preference Success | NO | NO |
| Replans used | — | **3/3** |

Planning halved the LLM calls (4 vs 8) — that's the central efficiency claim manifesting. Token reduction was smaller (~8%) because each plan after the first includes execution history. Wall-clock 2.5× faster. Both got Hard=YES / Pref=NO — same as reactive.

Important caveat: **planning burned all 3 replans on this single task.** Replan budget hit max. The plan-then-execute architecture had to keep trying because each plan terminated without a purchase. That's brittle in a way I didn't fully appreciate at design time — the architecture *forces* a replan whenever a plan ends without `purchase()` in it, even when the plan was perfectly reasonable.

Committed: `7569fe6`.

---

## Session 12

The pilot. The actual model-vs-baseline experimental run that the supervisor's points 3 + 4 wanted. 80 runs (20 stratified tasks × 2 architectures × 2 noise levels × 1 seed). Took 18 minutes wall-clock, cost $0.24. All runs completed without unrecoverable errors.

Built the experimental machinery first in `src/experiments/`:
- `scorer.py` — produces `RunMetrics` from an episode + task ground truth. Computes Hard Success, Preference Success, Constraint Satisfaction Rate, the 4 efficiency metrics, and a categorical `failure_mode` label.
- `trace_store.py` — writes a JSONL per run at `data/traces/<task>__<arch>__noise<p>__seed<n>.jsonl`. Header line = metadata; subsequent lines = step records.
- `results.py` — aggregates runs, renders the markdown summary report with success table + efficiency table + failure-mode breakdown + per-task crosstab.
- `runner.py` — orchestrator. Stratified task selection (round-robin per (bucket, difficulty)). Iterates the matrix. Writes results incrementally so a crash mid-run doesn't lose progress.

Smoke-tested the orchestrator with MockClient first (zero AWS spend) — 4 mock runs end-to-end. Verified: stratified selection picks balanced tasks, both agents run, scoring produces the right metrics, traces get written with canonical names, summary report renders without errors. Cleared the path for the real run.

Real pilot run. The headline results:

**Success metrics (means):**

| | Noise | Hard Success | Pref Success | Constraint Sat |
|---|---|---|---|---|
| Reactive | 0.0 | 15% | 5% | 17.5% |
| Reactive | 0.2 | **25%** | **10%** | **30%** |
| Planning | 0.0 | 15% | 0% | 26.7% |
| Planning | 0.2 | **0%** | 0% | 0% |

**Efficiency metrics (means):**

| | Noise | Env Steps | LLM Calls | Total Tokens | Wall-Clock |
|---|---|---|---|---|---|
| Reactive | 0.0 | 11.0 | 12.55 | 21,305 | 6.39s |
| Reactive | 0.2 | 6.75 | 10.35 | 24,070 | 5.54s |
| Planning | 0.0 | 10.4 | **3.20** | **8,967** | **2.53s** |
| Planning | 0.2 | 6.9 | 3.55 | 6,490 | 2.52s |

Three findings stand out, and **two of our three directional hypotheses appear to be pointing the wrong way**:

**1. Planning wins on efficiency by a wide margin.** 3.5–4× fewer LLM calls. 50–73% fewer tokens. 2.5× faster wall-clock. This contradicts RQ2's prediction that reactive would win on tokens for small open-weight models. The pilot suggests ReWOO's efficiency claim extends to Llama 3.1 8B. If this holds in the full experiment, that's a publishable finding.

**2. Reactive's robustness is unexpected.** Hard Success went 15% → 25% under noise. Performance *improved* with perturbation. Could be small-sample noise (n=20 per cell), or genuine — noise as regulariser. Need more seeds to know.

**3. Planning collapses under noise.** 15% → 0% Hard Success. The replan mechanism, designed to provide structured recovery, instead consumes its 3-replan budget on transient failures without converging. **This contradicts RQ3's prediction** that planning would be more robust. The failure-mode distribution confirms it: 47.5% of planning runs hit `replan_limit_exceeded`.

Failure modes are *qualitatively different* between architectures. Reactive's dominant failure mode is `no_purchase:unknown` (47.5%) — thinks and acts but never commits to a `purchase()`. Planning's dominant failure is `replan_limit_exceeded` (47.5%) — burns its 3 replans. Both fail at similar rates but in completely different ways. This is the kind of mechanism-level finding that needs to be foregrounded in the thesis discussion.

Then I opened one trace file — `T010__planning__noise0.2__seed42.jsonl` — to understand why so many runs were failing. Found something important:

The agent did `filter(price ≤ 16)` and then `filter(stars ≥ 4.7)`. Both calls *succeeded*. But each was applied to the **whole catalogue** rather than to the previous result set. The `filter` tool accepts a `candidate_asins` argument for progressive narrowing, but the agent didn't pass it. Each filter call was effectively a fresh global query. Looking at the observations:

- After `filter(price ≤ 16)`: 143 matches returned — products from EVERY bucket, not just cameras.
- After `filter(stars ≥ 4.7)`: 92 matches — again all buckets. The cameras matching the original task aren't surfaced because the filter is global.

This is a real methodological observation. The agent assumes filters chain. They don't, unless `candidate_asins` is explicitly passed. **This affects both architectures equally** — so the relative comparison (reactive vs planning) is still valid — but the absolute Hard Success numbers are depressed across the board.

The fix is simple: add explicit instruction in the system prompt about `candidate_asins` chaining. That's a single prompt change, applied identically to both agents.

Decided to write up the pilot report *first*, then make the prompt fix, then re-run the pilot, so we have a clean before/after comparison. The current results stand on their own as an honest snapshot of small-model performance without explicit chaining instruction. Re-running will let us measure how much of the absolute-success gap was the chaining limitation vs. genuine model capacity.

Committed pilot run: TBD next commit. Pilot report written at `reports/pilot_report.md`.

TODO before re-run:
- Add explicit `candidate_asins` instruction to both `prompts.py` (reactive) and `planning_prompts.py` (planning).
- Quick mock test to verify the prompt change doesn't break anything.
- Re-run pilot. Same seed, same matrix.
- Compare side-by-side. Expected: Hard Success rises meaningfully for both agents.

---

## Session 13

Chaining-fix iteration. The pilot inspection in Session 12 surfaced that both agents were calling `filter` without `candidate_asins`, so each filter was a global query rather than progressive narrowing. Today's session: write a prompt addendum teaching both agents to chain, re-run the same pilot matrix, compare before/after.

Made the intervention identical for both architectures — exactly the same paragraph inserted into both system prompts at the same position (after the tool spec, before the response/plan format section). Same wording, same examples. The point of identical phrasing is so any architectural performance difference can't be attributed to differential prompt quality.

The instruction was:

```
IMPORTANT — Chaining filters:
The filter tool, when called without candidate_asins, searches the ENTIRE catalogue.
To progressively narrow a result set, you MUST pass the ASINs from your previous
result as candidate_asins. For example:
  1. filter(attribute="bucket", operator="==", value="Cameras") → returns a list of cameras
  2. filter(attribute="price", operator="<=", value=50, candidate_asins=[<asins from step 1>])
     → narrows the cameras to under $50
Without candidate_asins, step 2 would search the whole catalogue (not just cameras),
which would dilute your result.
```

Hit some Git friction before the rerun. I had to:
- stash the prompt edits (`git stash push`)
- rename baseline artefacts (`reports/pilot_report.md` → `pilot_report_baseline.md`, results JSON likewise, `data/traces/` → `data/traces_baseline/`)
- commit the renames (Git correctly detected them as renames, not deletes+adds — 80+ files, all clean)
- pop the stash — which hit a `.gitignore` conflict because both the stash and working tree had `.gitignore` edits
- resolve by `git checkout -- .gitignore` (the stashed version was a superset, added both `data/traces/` and `data/results/`)
- pop succeeded cleanly the second time

Added `data/traces/` and `data/results/` to gitignore going forward. The baseline traces are committed (they're historical record of the pre-fix behaviour); future runs' traces stay local only. Cleaner repo.

Mock sanity tests on both agents still passed 2/2 each. Then re-ran the pilot: same matrix (20 tasks × 2 archs × 2 noise × 1 seed = 80 runs), same seed=42, ~$0.24 again, ~18 min.

### Results comparison

The before/after on the noise=0 cell:

| | Baseline | Post-fix | Δ |
|---|---|---|---|
| Planning Hard Success | 15% | **25%** | +10pp ✓ |
| Planning Constraint Sat | 26.7% | **51.7%** | +25pp ✓ |
| Planning total tokens | 8,967 | 6,465 | −28% |
| Reactive Hard Success | 15% | **10%** | **−5pp** ✗ |
| Reactive Constraint Sat | 17.5% | 20.0% | +2.5pp |
| Reactive total tokens | 21,305 | 18,393 | −14% |

And the noise=0.2 cell:

| | Baseline | Post-fix | Δ |
|---|---|---|---|
| Planning Hard Success | 0% | 0% | 0 (still collapsed) |
| Reactive Hard Success | **25%** | **10%** | **−15pp** ✗ |

**The fix helped planning meaningfully and hurt reactive.** Same instruction. Different effects. This was not what I predicted.

### Why I think this happened

The chaining instruction adds ~120 tokens to the system prompt. Reactive uses the system prompt **once per step** — with 11+ calls per episode at noise=0, that's 1,320+ tokens of system prompt repetition. Planning uses the system prompt **3-4 times per episode** (one per plan + replans).

For a small model (Llama 3.1 8B), longer system prompts hurt the per-step decision quality. The model has a fixed "attention budget" — more prompt to parse means less left for the actual task. Reactive consults the system prompt more often per episode, so it pays this cost more often.

This is a *small-model phenomenon*. GPT-4-class models wouldn't show this asymmetry because they have more attention headroom. But this study is *specifically* about small open-weight models, so the asymmetry isn't a confounder — it's a real architectural finding: **on small models, prompt engineering interventions don't generalize across architectures uniformly. The same instruction can help one and hurt another, mediated by how often each architecture consults the system prompt.**

This is publishable in its own right. I should be honest about it in the thesis.

### Why I'm stopping iteration here

The intuitive next move is to try different chaining-instruction wordings until both architectures improve. I am explicitly NOT doing that, because:

1. Further prompt tweaking risks p-hacking — optimising prompts until results match my hypotheses is bad science.
2. The pilot's purpose was to verify the pipeline works and surface unexpected behaviour. **It did both.** Two complete data points (baseline + post-fix) at the same seed are enough to demonstrate methodology.
3. n=20 per cell is too small to firmly conclude the differential prompt effect is real vs sample noise. The Capstone semester full experiment (50 tasks × 3 seeds = 150 per cell) will give the statistical power to discriminate. Iterating on the pilot risks chasing noise.
4. The data we have *is* a story: a chaining-instruction ablation showing asymmetric architectural sensitivity. Honest framing.

### What goes into the full experiment

Both architectures will use the **post-fix prompts** for the full Capstone experiment. The chaining instruction is now methodologically locked. Both pilot runs (baseline and post-fix) will be cited in the thesis as a pre-experiment ablation, with the post-fix prompts justified as the "fair" comparison condition where both agents have been told how `candidate_asins` works.

Committed: `be181c3` (post-fix results) + `03ee532` (the prompt change itself) + `6e68816` (the rename). Three commits for the iteration.

### What's still surprising / needs the full experiment to resolve

- Planning's collapse at noise=0.2 is now consistent across both pilots. Either genuine architectural fragility or interaction with another bug we haven't found. Want more seeds + more tasks before concluding.
- Reactive's robustness pattern (improved under noise in baseline, didn't improve post-fix) is unstable across pilots. Statistical noise more likely than real signal at this sample size.
- Both architectures' absolute Hard Success is still low (≤25%). Llama 3.1 8B's capacity on these tasks is the dominant constraint, not the prompt. Worth examining whether 70B-class would clear this ceiling — that's a planned fallback (D-9).

### Where the project sits

Methodology demonstrated end-to-end. Both pilots in Git. Reports written. Journal current. **The Capstone semester opens with a working pipeline, two pilots-worth of preliminary signal, three sharpened research questions, and a known set of interesting tensions to investigate.** That's a good place to start a 1,200-run experiment.

---

## Session 14

Three things happened back-to-back: a supervisor checklist I'd missed surfaced, the infrastructure gaps got closed, and the 70B escalation pilot ran. Big session. Worth capturing all of it.

### The checklist gap

Supervisor pinged about pilot findings and tacked on requests for the determinism test and CloudWatch latency, framed as "part of last week's checklist." I went back through old messages and found he had sent a 7-item AWS setup checklist before Session 10. I'd ignored it at the time because I was confident in the plan I was working through with the AI collaborator and wanted to keep momentum.

What I'd actually done vs what he'd asked for:

| Supervisor asked for | Status |
|---|---|
| Bedrock in eu-west-1 | ❌ Used us-east-1 |
| 8B + 70B access | ⚠️ Got 8B (auto-enabled), no 70B |
| S3 bucket for artefacts | ❌ Local disk only |
| Five-line boto3 smoke test | ✅ Done |
| Determinism test at temp=0 | ❌ Not done |
| CloudWatch latency capture | ❌ Used Python local timing |
| 10-task mini pilot | ✅ Done (20-task, bigger than required) |

So 4 of 7 items unmet. The reactive instinct was to scramble. The right move was to be honest about it — write the supervisor, take ownership of the gaps, ask his guidance on the region question rather than just unilaterally switching.

Sent a short acknowledgement message taking responsibility for the gaps, flagging us-east-1 as a deliberate-but-unauthorised choice, and asking him to call between (a) switch to eu-west-1 and rerun, or (b) stay and document. Started the cheap items in parallel without waiting for his reply.

### Closing the gaps

**Determinism test.** Wrote `scripts/bedrock_determinism_test.py`. Two consecutive Bedrock Converse calls at temperature=0.0 with the prompt "List the first 5 prime numbers as a comma-separated list. Reply with the list and nothing else." Both returned byte-identical: `'\n\n2, 3, 5, 7, 11'`. Identical token counts (in=36, out=15).

Important methodological caveat noted in the journal: AWS doesn't formally guarantee determinism at temp=0. Two calls is empirical evidence, not proof. The pilot's reproducibility argument rests on this empirical observation. Mentioning it explicitly in the thesis methodology.

**CloudWatch latency.** Wrote `scripts/bedrock_cloudwatch_latency.py`. Queries the `AWS/Bedrock` `InvocationLatency` metric — AWS auto-captures it on every Bedrock call. First attempt failed with AccessDenied because `bedrock-research-user` only had `AmazonBedrockFullAccess`. Added `CloudWatchReadOnlyAccess` policy. Re-ran. Got mean 287.5ms for the two determinism-test calls. Server-side latency working.

Decision (post-supervisor-call): keep pilot reports as Python local timing, switch to CloudWatch as primary source for the full Capstone experiment, with Python as sanity cross-check. Will note this explicitly as a methodology footnote — defensible design choice, not a flaw.

**S3 bucket.** Created `bedrock-research-sanatan-25103130` (used student ID for global uniqueness) in us-east-1. Added `AmazonS3FullAccess` to the IAM user. Verified with `aws s3 ls`.

**70B access.** Tested directly with a small Converse call using `us.meta.llama3-1-70b-instruct-v1:0`. Returned `'\n\nOK.'` first try. AWS auto-enables 70B same as 8B; no manual request needed.

Sent the full receipts package to the supervisor with all five items confirmed plus a flag on the floor-effect criterion (post-fix pilot shows both architectures below 30% Hard Success at noise=0 → escalate to 70B per his criterion).

### Supervisor's response and final decisions

Supervisor accepted the receipts. Made three calls:

- **Region:** stay us-east-1. The eu-west-1 suggestion was about latency convenience, not correctness.
- **CloudWatch:** Option 2 — keep pilot as Python timing, switch to CloudWatch for the full experiment, document the methodology shift.
- **70B:** authorised escalation. Run same 80-run pilot matrix on 70B for a clean before/after.

Also asked two important sanity-check questions about the post-fix pilot results: was the rerun on the same 20-task stratified sample (yes, deterministic from seed=42), and at n=20 isn't the 5pp reactive drop within sample noise (yes, exactly — one task flipping = 5pp). That's the right read. The 10pp planning improvement is more suggestive but still marginal. Need to be careful in the writeup not to over-interpret either.

Also asked to track per-call latency separately from total wall-clock and to project the timeline impact of 70B escalation on the full 1,200-run experiment.

### 70B pilot

Code changes were minimal because the LLM client architecture was already set up to swap model IDs via the `model_id` parameter. Added a `--70b` CLI flag to `scripts/run_pilot.py` that switches to `us.meta.llama3-1-70b-instruct-v1:0`. Also added a `latency_per_call_mean` column to the results aggregator (= wall-clock / llm_calls per run).

Renamed the 8B post-fix artefacts to `*_8b_postfix` so the 70B run wouldn't overwrite them. Now have three preserved pilot runs in the repo: baseline (8B pre-fix), 8B post-fix, and 70B post-fix.

Ran the 70B pilot: 80 runs, ~30 minutes wall-clock, cost ~$2.50 (vs $0.24 for 8B — ~10x per-token cost).

### Results — three-way comparison

**Hard Success at noise=0:**

| | 8B baseline | 8B post-fix | 70B post-fix |
|---|---|---|---|
| Reactive | 15% | 10% | **65%** |
| Planning | 15% | 25% | **35%** |

**Hard Success at noise=0.2:**

| | 8B baseline | 8B post-fix | 70B post-fix |
|---|---|---|---|
| Reactive | 25% | 10% | **80%** |
| Planning | 0% | 0% | **25%** |

The floor effect lifted exactly as the criterion predicted. Both architectures cleared 25%+ at noise=0; reactive jumped to 65-80%. Capacity was the binding constraint at 8B, not implementation.

**Efficiency at noise=0:** Planning still uses 74% fewer tokens (5,689 vs 21,931) and is 1.9× faster total wall-clock (18.3s vs 35.1s) than reactive. But latency-per-call shows planning is *slower per call* (6.12s vs 3.44s) because plans are longer outputs — planning wins on total only because it makes ~3× fewer calls.

### The three directional hypotheses

Looking at the 70B pilot vs the original predictions:

| RQ | Prediction | 70B pilot |
|---|---|---|
| RQ1 (Hard Success) | Planning > Reactive | **Reactive >> Planning** (30-55pp gap) |
| RQ2 (Tokens) | Reactive > Planning | **Planning >> Reactive** (74% fewer tokens) |
| RQ3 (Robustness) | Planning > Reactive | **Reactive > Planning** (consistent at both scales) |

All three predictions appear to be inverted. The effect sizes at 70B are well above n=20 sample noise (15pp would be ~3 task flips; 55pp would be ~11 task flips). The full experiment with 50 tasks × 3 seeds = 150 runs per cell will give the statistical power to confirm.

This is the most scientifically interesting outcome possible — three falsified directional hypotheses, with effect sizes that look real. The thesis story now becomes: ReAct's "think before each action" beats plan-then-execute's "think once, execute many" on this kind of constrained shopping task, *and* reactive is more noise-robust because each step's reasoning includes the latest observation. Plan-then-execute's efficiency advantage is real but in this domain the success cost is steep.

### Timeline projection for the full experiment

Sent these to supervisor as part of the 70B receipts:
- 1,200 runs at ~26s/run = ~8.7 hr sequential, realistically 10-12 hr with throttling/CloudWatch propagation.
- Cost: ~$30-45 on 70B (vs ~$3-4 on 8B).
- Both well within budget; 70B doubles wall-clock but is the right call given the floor effect.

### Things to investigate before the full experiment

- **`malformed_limit` (7.5% of planning runs)** is a new failure mode that didn't appear at 8B. 70B emitting persistent malformed JSON for some plan attempts. Need to look at one of those traces and tighten the planning prompt if there's a fixable pattern.
- **Per-call latency for planning (6.12s) vs reactive (3.44s)** at 70B. Planning's longer outputs incur more per-call time. Worth noting in the methodology but doesn't change anything mechanically.
- **The full experiment should run on 70B with post-fix prompts**, same architecture configs as the pilots. No more pilot tweaking.

Committed: `679649e` (70B pilot results) + `73baf77` (renames + flag + per-call latency) + `a34d27a` (infrastructure scripts).

---

## Session 15

Supervisor exchange revealed I'd missed his original AWS setup checklist. Long session — closed the gaps, ran a big 70B pilot, and found something important via trace inspection. Trying to write it in order.

The supervisor sent a follow-up question asking about the determinism test and CloudWatch latency capture. Both items I hadn't done. Went back through past messages and found he'd sent a 7-item AWS setup checklist before Session 10 that I'd never actioned. Four items unmet — eu-west-1 region (I used us-east-1), 70B model access, S3 bucket, determinism test, CloudWatch latency. Sent an honest acknowledgement, took ownership, asked him to make the call on the region rather than unilaterally switching.

Ran the closure work in parallel while waiting for his region call.

**Determinism test.** Wrote `scripts/bedrock_determinism_test.py`. Two consecutive Bedrock Converse calls at temperature=0.0 with a non-trivial prompt ("List the first 5 prime numbers as a comma-separated list. Reply with the list and nothing else."). Both returned byte-identical: `'\n\n2, 3, 5, 7, 11'`. Identical token counts. AWS doesn't formally guarantee determinism at temp=0, so this is empirical evidence not proof. Mentioning it explicitly in the methodology as a limitation.

**CloudWatch latency.** Wrote `scripts/bedrock_cloudwatch_latency.py`. Queries `AWS/Bedrock` `InvocationLatency` metric — AWS auto-captures this on every Bedrock call. First run got AccessDenied because `bedrock-research-user` only had `AmazonBedrockFullAccess`. Added `CloudWatchReadOnlyAccess` policy. Re-ran, got mean 287.5ms across the two determinism-test calls.

Decision (finalised after supervisor's response): keep the existing pilot reports as Python local timing, switch to CloudWatch as primary source for the full experiment, with Python as sanity cross-check. Methodology footnote will explain the shift as a deliberate design choice, not a flaw.

**S3 bucket.** Created `bedrock-research-sanatan-25103130` in us-east-1. Added `AmazonS3FullAccess`. Verified with `aws s3 ls`.

**70B access.** Tested directly with a small Converse call. Returned `'\n\nOK.'` first try. AWS auto-enables 70B same as 8B; no manual request needed.

Sent full receipts package. Supervisor made three calls:
- Region: **stay us-east-1** (his eu-west-1 suggestion was about latency convenience, not correctness)
- CloudWatch: **Option 2** — pilot stays as Python timing, full experiment uses CloudWatch as primary with Python as sanity check
- **70B escalation authorised** — post-fix pilot showed both architectures under 30% Hard Success, satisfying the floor-effect criterion

He also asked two sanity-check questions I need to note here for the record: was the post-fix rerun on the same 20-task stratified sample (yes, deterministic from seed=42), and isn't the 5pp reactive drop within noise at n=20 (yes, exactly — one task flip = 5pp). His caution was correct. I noted it and won't over-interpret either the reactive drop or planning's 10pp improvement at that sample size.

Committed: `a34d27a` (infrastructure scripts).

---

## Session 16

70B pilot. Code changes were minimal because the LLM client was already set up to swap model IDs via `model_id`. Added a `--70b` CLI flag to `run_pilot.py` and a `latency_per_call_mean` column to the results aggregator (= wall-clock / llm_calls per run).

Renamed the 8B post-fix artefacts to `*_8b_postfix` so the 70B run wouldn't overwrite them. Now three preserved pilots in the repo: baseline (8B pre-fix), 8B post-fix, and 70B post-fix.

Ran the 70B pilot: 80 runs, ~30 minutes wall-clock, cost ~$2.50 (vs $0.24 for 8B — roughly 10× per-token cost).

### The three-way comparison

**Hard Success at noise=0:**

| | 8B baseline | 8B post-fix | 70B post-fix |
|---|---|---|---|
| Reactive | 15% | 10% | **65%** |
| Planning | 15% | 25% | **35%** |

**Hard Success at noise=0.2:**

| | 8B baseline | 8B post-fix | 70B post-fix |
|---|---|---|---|
| Reactive | 25% | 10% | **80%** |
| Planning | 0% | 0% | **25%** |

Floor effect lifted as the criterion predicted. Both architectures cleared 25%+ at noise=0. Reactive jumped to 65-80%. **Capacity was the binding constraint at 8B, not implementation.**

**Efficiency at noise=0:** Planning still uses 74% fewer tokens (5,689 vs 21,931) and is 1.9× faster total wall-clock. Latency-per-call shows planning is *slower per call* (6.12s vs 3.44s) because plans are longer outputs — planning wins on total only because it makes ~3× fewer calls.

Looking at the RQ predictions after this pilot:

| RQ | Prediction | 70B pilot |
|---|---|---|
| RQ1 (Hard Success) | Planning > Reactive | Reactive >> Planning (30-55pp gap) |
| RQ2 (Tokens) | Reactive > Planning | Planning >> Reactive (74% fewer tokens) |
| RQ3 (Robustness) | Planning > Reactive | Reactive > Planning (consistent at both scales) |

All three appear inverted. Effect sizes at 70B are well above n=20 sample noise. Full experiment with 150 runs per cell will settle it statistically.

### The malformed_limit finding

Post-fix pilot showed a new failure mode: 3 of 40 planning runs at 70B hit `malformed_limit`. Never happened at 8B. Supervisor asked to investigate the cause before the full experiment.

Ran a diagnostic to find the three failed runs (T005, T032 twice). All planning + 70B, all `parse_errors=0` — meaning the JSON parsed fine but failed *schema validation* downstream. Opened one trace (`T010__planning__noise0.2__seed42.jsonl`).

The failure was structural, not a bug in my code. The chaining instruction we added in Session 13 shows example syntax: `filter(candidate_asins=[<asins from step 1>])`. Reactive can fill in real ASINs at each step because it operates *after* each observation. Planning has to write the whole plan upfront, before it has any observations. So planning at 70B is smart enough to *try* to follow the chaining instruction — but has to invent placeholder values for `candidate_asins`. It tried `"previous_result"` (string), `"null"` (string), and stringified lists like `"['B001', 'B002']"`. The `FilterArgs` Pydantic schema rejects all three because it wants `list[str] | None`, not strings.

Three consecutive schema rejections → `malformed_limit` termination.

8B never hit this because 8B mostly ignored the chaining instruction. 70B reads it, tries to follow, and fails gracefully in a way our schema doesn't accommodate. This is a real architectural interaction, not a bug — and it demonstrates something the thesis should discuss: prompt-engineering interventions that work at one model scale can create novel failure modes at another.

Wrote up the cause carefully and sent to supervisor before applying any fix. He approved the fix and added an insight: when `candidate_asins` gets coerced to `None`, the filter runs on the whole catalogue rather than a narrowed list. Which means **planning is structurally unable to do progressive narrowing mid-plan** — it plans before it has any results to work with. That's a thesis-discussion goldmine that mechanically explains why planning underperforms on Hard Success and robustness. Not just a parser fix — a real architectural constraint being surfaced.

Committed: `679649e` (70B pilot results).

---

## Session 17

Applied the coercion fix. In `src/environment/models.py`, added a Pydantic `field_validator` to `FilterArgs.candidate_asins` (mode='before') that coerces:
- `"null"` → None
- `"previous_result"` → None
- `"['B001', 'B002']"` → parsed `['B001', 'B002']`
- Well-formed values pass through unchanged

Tool semantics don't change. The parser just tolerates common LLM output variants instead of rejecting on technicality. Same fix applies to both architectures for fairness.

Tested with a small in-script sanity check across 5 cases — all pass, all correctly coerced.

Ran the 40-run planning-only rerun (`--arch planning --70b`). Cost ~$1.20, ~16 minutes.

**Primary check:** `malformed_limit` failures went from 3/40 to **0/40**. Fix confirmed.

**Unexpected secondary finding:** Planning's Hard Success at noise=0 rose from 35% → 65%. That's much bigger than the ~7.5pp we'd expect from just resolving the malformed runs. Coercion is *also* unblocking runs previously stuck mid-plan on schema rejections — those runs now progress and sometimes succeed. Planning at noise=0.2 stayed at 20% (was 25%) — the coercion didn't rescue planning's noise robustness.

Revised three-way picture:
- Planning matches Reactive on Hard Success at noise=0 (both 65%). RQ1 inversion is **noise-conditional**, not absolute.
- Reactive still wins clearly on robustness: 80% vs 20% at noise=0.2.
- Planning still wins on efficiency (~7k vs ~22k tokens).

Committed: `4a2d486` (coercion fix) + `8ba256a` (planning-only rerun results).

---

## Session 18

Full-experiment infrastructure. Everything up to this point was pilot-scale — 80 runs, cheap-and-cheerful, easy to rerun if something broke. The full experiment is 1,200 runs at ~$30-45 cost and 10-12 hours wall-clock. Different threat model. Failure modes that were tolerable at pilot scale become expensive:
- Mid-run crash: 800 runs wasted unless we're checkpointing properly
- Bedrock throttling: 1,200 back-to-back calls might hit rate limits
- Cost overrun: a bug could balloon the projected $30-45
- Wall-clock over overnight window: sleep/network/VS-Code crashes all real risks

Built four safety mechanisms.

**Checkpoint/resume.** Extended the runner. On startup, checks if the results file exists and loads already-completed run keys (indexed by `(task_id, architecture, noise_level, seed)`). Iterates the matrix but skips keys that are already done. New file `src/experiments/full_runner.py`.

Unit-tested with 5 scenarios (nonexistent file, existing valid file, corrupted file, resume logic, iteration skip). 5/5 passed.

**Retry-with-backoff.** Modified `BedrockClient.complete()` to catch `ThrottlingException`, `ModelStreamErrorException`, `ServiceUnavailableException`, `ModelTimeoutException`. Exponential backoff: 1s, 2s, 4s, 8s, 16s across 5 attempts. Other exceptions surface immediately (we don't want to hide real errors).

**Cost abort threshold.** Added `CostThresholdExceeded` exception + `cost_threshold_usd` field to `BedrockClient`. Cumulative cost is computed after every call. Threshold set to $50 (well above projected $30-45). Runner catches the exception and shuts down gracefully with all results preserved.

**Post-experiment CloudWatch analysis.** Wrote `scripts/query_experiment_latency.py` — pulls Bedrock `InvocationLatency` metric across the experiment's time window and writes a CSV. Runs once after the experiment completes.

Also created `scripts/run_full_experiment.py` — separate entry point from the pilot script, so both remain available for future ablations. Locked matrix: 50 tasks × 2 architectures × 4 noise levels × 3 seeds = 1,200 runs. Seeds: `[42, 1, 2024]` (varied, memorable, three genuinely different values).

Updated 70B pricing constants: `PRICE_PER_1K_INPUT_TOKENS = 0.00072` (was 0.00022 for 8B).

Dry-run confirmed matrix dimensions. Committed: `76ee7c6`.

---

## Session 19

Full experiment run. Kicked off `uv run python scripts/run_full_experiment.py`, verified the "Starting fresh: 1200 runs" line, walked away.

Something happened partway through: I accidentally pressed the laptop's power button. Cancelled the shutdown dialog but the PowerShell window closed. Panic moment. Ran the check script: **917 runs preserved, 917 trace files on disk**, the results file intact. Checkpoint/resume worked exactly as designed. Restarted the same command, saw "Resuming from checkpoint: 917/1200 runs already completed," and it picked up from run 918. About 2.5 hours later it finished.

This is exactly the kind of end-to-end verification of the safety design that couldn't have been contrived — it just happened. Supervisor noted it belongs in the Reproducibility section of the Methodology chapter. Agreed.

### Full experiment results (1,200 runs, n=150 per cell)

**Hard Success:**

| Noise | Reactive | Planning | Δ |
|---|---|---|---|
| 0.0 | 62.0% | 58.0% | +4pp |
| 0.1 | 60.7% | 40.7% | +20pp |
| 0.2 | 64.0% | 35.3% | +29pp |
| 0.3 | 60.0% | 40.7% | +19pp |

**Preference Success:** Reactive at 24-27% across all noise; Planning at 9-16%. Roughly 2-3× advantage for reactive.

**Efficiency (noise=0):** Reactive 8.5 LLM calls, 19.3k tokens, 30.7s wall-clock. Planning 2.7 calls, 7.6k tokens, 17.9s. Planning uses 61% fewer tokens.

**Robustness pattern:**
- Reactive: essentially flat across noise (60-64% Hard Success)
- Planning: sharp drop from 58% (clean) to 35-41% (noisy)

**Failure modes (n=600 per architecture):**
- Reactive: 61.7% success, 19.5% wrong_product, 11.8% budget_exhausted
- Planning: 43.7% success, 24.2% replan_limit_exceeded, 21.7% wrong_product

Planning's dominant non-success mode is exhausting its replan budget — mechanistically consistent with the "structurally unable to do progressive narrowing mid-plan" insight from Session 16.

### CloudWatch latency

Ran the batch query. 7,177 total Bedrock calls captured across the experiment window. Mean latency 4,131.9 ms server-side. Python-timing cross-check agreed within ~130ms (roughly RTT + response transfer overhead). Both sources consistent — CloudWatch validated as the primary source for the thesis.

Sent supervisor the receipts. He confirmed the findings looked clean and asked about the failure-mode qualitative coding as the next step.

Committed: `7cc3ba5` (full experiment results).

---

## Session 20

Statistical analysis + qualitative coding setup + supervisor's substantive feedback.

### Statistical analysis

Built `src/experiments/stats_analysis.py`. For each (noise_level × success_metric) cell:
- Paired Wilcoxon signed-rank test on task-seed-paired differences
- Cliff's δ on paired data
- 95% percentile-bootstrap CI (10,000 resamples, seed=42) for mean difference
- Bonferroni correction across all 12 tests

Ran on the full experiment results. **10 of 12 tests reach significance after Bonferroni. All 10 favour reactive.**

The two non-significant tests are both at noise=0: Hard Success (Δ=+4pp, p=0.27) and Constraint Satisfaction (Δ=+3.3pp, p=0.27). Preference Success was significant even at noise=0 (Δ=+10pp).

Observation to note for the thesis methodology: Cliff's δ on binary paired data reduces to the paired proportion difference. So for Hard Success and Preference Success, the magnitude labels ("small", "medium", "large" from Romano et al. 2006) understate practical importance because they were calibrated for continuous outcomes. The continuous Constraint Satisfaction metric was the only one where δ registered as "medium" (0.338 at noise=0.2). Footnote it in the methodology.

Committed: `f267df0` (statistical analysis).

### Qualitative coding — setup

Designed the 10-category taxonomy in `docs/taxonomy_v1.md`. Categories cover the reasoning-level failure patterns I'd expect based on trace inspection so far — wrong_product_satisfying, search_blindness, failed_narrowing, non_commitment, plan_execution_mismatch, replan_treadmill, budget_exhaustion_mid_narrowing, malformed_action_recovery_failure, constraint_misinterpretation, other_uncoded.

Built three scripts:
- `sample_failed_traces.py` — stratified sample of 48 failed traces (12 per env-side failure_mode category), seeded at 42, locked in `data/qualitative_coding/sampled_traces.json`
- `code_failed_traces.py` — interactive tool for Pass 1 and Pass 2, saves to CSV as-you-go, resumable
- `compute_kappa.py` — Cohen's kappa computation with confusion matrix and disagreement report

Ran the sampler. Got exactly 12 per category, 48 total, all trace files existing.

Committed: `4280a7b` (qualitative coding tools + sample).

### Pass 1 partial

Started Pass 1 but only got through 24 of the 48 traces. Underestimated how time-consuming this is — each trace takes 3-5 minutes to read and categorise properly. Coded 24 in one session and stopped.

Messaged supervisor asking whether he'd accept 24 as the final sample size (with a methodology note about limited saturation) rather than pushing through the remaining 24 for a shallower reading of each. He was reasonable about it; awaiting his exact call. Fallback plan if he wants the full 48: dictate the remaining traces (say the observations aloud, capture as notes) rather than sit-and-read at pace. Meaningfully faster.

Something I want to be honest about here: I asked the AI collaborator to do the categorisation for me at one point. It refused — correctly. The kappa check measures *my* consistency, not the collaborator's; and submitting AI-generated qualitative analysis as my own would cross an academic integrity line that the code-and-scripting help doesn't. Recording it because it's the right kind of failure mode to notice: when the work becomes tedious, the temptation to offload is strong. The collaborator drew the line I should have drawn myself.

### Supervisor's feedback on the statistical analysis

Five points, all substantive, all going into the thesis structure:

1. **Report all 12 tests, not just the 10 significant ones.** Full table with both nulls named explicitly. Selective reporting is a red flag even when unintentional.
2. **Explain why no significance test for RQ2 (efficiency).** The token/wall-clock advantage was monotonic across all conditions, so a test adds no information. Say that explicitly rather than skip it silently. Report full descriptives (mean, median, SD).
3. **Separate effect size magnitude from practical significance.** The Cliff's δ footnote is good but needs to be extended in prose: the 29pp Hard Success gap at noise=0.2 is large in any applied sense regardless of what δ labels call it.
4. **Explain the noise=0 null result mechanistically.** Both architectures achieving equivalent Hard Success under clean conditions is a substantive finding, not a gap. The mechanistic answer likely lives in recovery-mechanism dormancy: under clean conditions there's nothing to trigger a replan, so planning's brittleness never manifests.
5. **RQ3 is the headline. Structure the thesis around it.** The story isn't "reactive beats planning" — it's "reactive and planning are equivalent under clean conditions but diverge under noise, and the divergence direction inverts the ReWOO prediction." Robustness is the finding; success and efficiency are measurements of it.

Point 5 in particular restructures the Discussion chapter. All five feed the writing phase.

Pass 2 in ~10 days after temporal decay. Meanwhile, thesis writing per supervisor's structure suggestion.

---

*Next: thesis writing per supervisor's structural feedback. Pass 2 of qualitative coding in ~10 days after temporal decay.*