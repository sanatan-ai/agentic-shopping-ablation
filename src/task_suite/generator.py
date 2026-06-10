"""Task suite generator.

Produces a deterministic set of constrained multi-step shopping tasks against
the curated catalogue. See `config.py` for parameters and `models.py` for schemas.
"""
from __future__ import annotations

import logging
import random
from collections import Counter, defaultdict
from typing import Optional

import pandas as pd

from src.task_suite.config import TaskSuiteConfig
from src.task_suite.models import (
    BucketName,
    Constraints,
    DifficultyTier,
    PreferenceFunction,
    Task,
    TaskSuite,
)

logger = logging.getLogger(__name__)


# ===================================================================== #
# Natural-language templates                                            #
# ===================================================================== #
# Three surface-variant templates per (preference, has_stars, has_brand)
# combination. Placeholders: {bucket}, {price}, {stars}, {brand}.

# Map internal bucket names to display strings for natural-language output
_BUCKET_DISPLAY: dict[BucketName, str] = {
    "Cameras": "camera",
    "Headphones": "pair of headphones",
    "Watches": "watch",
    "LaptopAccessories": "laptop accessory",
    "PhoneAccessories": "phone accessory",
}

# Templates keyed by (preference, has_min_stars, has_brand) -> 3 surface variants
_TEMPLATES: dict[tuple[str, bool, bool], list[str]] = {
    # ------ cheapest, no stars, no brand ------
    ("cheapest", False, False): [
        "Find a {bucket} under ${price}, and choose the cheapest option.",
        "I need a {bucket} priced below ${price}. Pick the cheapest one.",
        "Looking for the cheapest {bucket} under ${price}.",
    ],
    # ------ cheapest, with stars, no brand ------
    ("cheapest", True, False): [
        "Find a {bucket} under ${price} with at least {stars} stars, and choose the cheapest option.",
        "I need a {bucket} priced below ${price}, rated at least {stars} stars. Pick the cheapest one.",
        "Looking for the cheapest {bucket} under ${price} with {stars}+ stars.",
    ],
    # ------ cheapest, with stars, with brand ------
    ("cheapest", True, True): [
        "Find a {bucket} under ${price} with at least {stars} stars from {brand}, and choose the cheapest option.",
        "I need a {bucket} by {brand}, priced below ${price}, rated at least {stars} stars. Pick the cheapest one.",
        "Looking for the cheapest {brand} {bucket} under ${price} with {stars}+ stars.",
    ],
    # ------ highest_rated, no stars, no brand ------
    ("highest_rated", False, False): [
        "Find a {bucket} under ${price}, and choose the highest-rated option.",
        "I need a {bucket} priced below ${price}. Pick the highest-rated one.",
        "Looking for the best-rated {bucket} under ${price}.",
    ],
    # ------ highest_rated, with stars, no brand ------
    ("highest_rated", True, False): [
        "Find a {bucket} under ${price} with at least {stars} stars, and choose the highest-rated option.",
        "I need a {bucket} priced below ${price}, rated at least {stars} stars. Pick the highest-rated one.",
        "Looking for the best-rated {bucket} under ${price} with {stars}+ stars.",
    ],
    # ------ highest_rated, with stars, with brand ------
    ("highest_rated", True, True): [
        "Find a {bucket} under ${price} with at least {stars} stars from {brand}, and choose the highest-rated option.",
        "I need a {bucket} by {brand}, priced below ${price}, rated at least {stars} stars. Pick the highest-rated one.",
        "Looking for the best-rated {brand} {bucket} under ${price} with {stars}+ stars.",
    ],
}


def _render(
    constraints: Constraints,
    preference: PreferenceFunction,
    rng: random.Random,
) -> str:
    """Render a natural-language prompt from a constraint spec by sampling a surface variant."""
    has_stars = constraints.min_stars is not None
    has_brand = constraints.brand is not None
    templates = _TEMPLATES[(preference, has_stars, has_brand)]
    template = rng.choice(templates)
    return template.format(
        bucket=_BUCKET_DISPLAY[constraints.bucket],
        price=f"{constraints.max_price:.2f}",
        stars=f"{constraints.min_stars:.1f}" if has_stars else "",
        brand=constraints.brand if has_brand else "",
    )


# ===================================================================== #
# Catalogue helpers                                                     #
# ===================================================================== #


def _bucket_subset(catalogue: pd.DataFrame, bucket: BucketName) -> pd.DataFrame:
    """Return just the rows in the named bucket."""
    return catalogue[catalogue["bucket"] == bucket]


def _price_threshold(catalogue: pd.DataFrame, bucket: BucketName, quantile: float) -> float:
    """Return a price cap at the given quantile of the bucket's price distribution."""
    sub = _bucket_subset(catalogue, bucket)
    val = float(sub["price"].quantile(quantile))
    # Round to a "natural" number for the natural-language prompt
    if val < 30:
        return round(val, 0)
    if val < 100:
        return round(val / 5) * 5  # round to nearest 5
    return round(val / 10) * 10  # round to nearest 10


def _known_brands_for_bucket(catalogue: pd.DataFrame, bucket: BucketName) -> list[str]:
    """Return the list of known (non-'Unknown') brands present in the bucket."""
    sub = _bucket_subset(catalogue, bucket)
    brands = sub.loc[sub["brand"] != "Unknown", "brand"].unique().tolist()
    return sorted(brands)


# ===================================================================== #
# Valid-set + optimal computation                                       #
# ===================================================================== #


def _compute_valid_set(catalogue: pd.DataFrame, c: Constraints) -> pd.DataFrame:
    """Return the subset of the catalogue satisfying all hard constraints."""
    mask = (catalogue["bucket"] == c.bucket) & (catalogue["price"] <= c.max_price)
    if c.min_stars is not None:
        mask &= catalogue["stars"] >= c.min_stars
    if c.brand is not None:
        mask &= catalogue["brand"].str.lower() == c.brand.lower()
    return catalogue[mask]


def _compute_optimal(valid: pd.DataFrame, preference: PreferenceFunction) -> list[str]:
    """Return ASINs that are optimal under the preference function (handles ties)."""
    if preference == "cheapest":
        best = valid["price"].min()
        return valid.loc[valid["price"] == best, "asin"].tolist()
    elif preference == "highest_rated":
        best = valid["stars"].max()
        return valid.loc[valid["stars"] == best, "asin"].tolist()
    else:
        raise ValueError(f"Unknown preference: {preference}")


# ===================================================================== #
# Constraint sampling per difficulty                                    #
# ===================================================================== #


def _sample_constraints(
    catalogue: pd.DataFrame,
    bucket: BucketName,
    difficulty: DifficultyTier,
    cfg: TaskSuiteConfig,
    rng: random.Random,
) -> Optional[Constraints]:
    """Sample a constraint set for the given bucket and difficulty.

    Returns None if the bucket cannot support the difficulty (e.g. 'hard'
    requires brand but the bucket has no known brands).
    """
    # Pick price tier and translate to threshold
    price_tier = rng.choice(list(cfg.price_quantile_tiers.keys()))
    max_price = _price_threshold(catalogue, bucket, cfg.price_quantile_tiers[price_tier])

    # Easy: bucket + price only
    if difficulty == "easy":
        return Constraints(bucket=bucket, max_price=max_price)

    # Medium: bucket + price + stars
    star_tier = rng.choice(list(cfg.star_tiers.keys()))
    min_stars = cfg.star_tiers[star_tier]
    if difficulty == "medium":
        return Constraints(bucket=bucket, max_price=max_price, min_stars=min_stars)

    # Hard: bucket + price + stars + brand
    if difficulty == "hard":
        if bucket not in cfg.brand_eligible_buckets:
            return None  # signal: cannot generate hard task for this bucket
        brands = _known_brands_for_bucket(catalogue, bucket)
        if not brands:
            return None
        brand = rng.choice(brands)
        return Constraints(
            bucket=bucket,
            max_price=max_price,
            min_stars=min_stars,
            brand=brand,
        )

    raise ValueError(f"Unknown difficulty: {difficulty}")


# ===================================================================== #
# Per-bucket difficulty allocation                                      #
# ===================================================================== #


def _allocate_difficulties(cfg: TaskSuiteConfig) -> dict[BucketName, list[DifficultyTier]]:
    """Allocate 10 difficulty slots per bucket so that the global mix is 15/20/15.

    Buckets eligible for 'hard' tasks (brand-constrained) get more hard slots.
    Brand-ineligible buckets get their would-be-hard slots redistributed to medium.

    Target global: 15 easy / 20 medium / 15 hard
    Eligible buckets (3): get all hard slots → 5 hard each
    Ineligible buckets (2): no hard slots → 3 easy, 7 medium each
    Eligible buckets: 3 easy, 2 medium, 5 hard each

    Verification:
      easy:   3*3 + 2*3 = 9+6 = 15 ✓
      medium: 3*2 + 2*7 = 6+14 = 20 ✓
      hard:   3*5 + 2*0 = 15 ✓
    """
    allocation: dict[BucketName, list[DifficultyTier]] = {}
    for bucket in cfg.brand_eligible_buckets:
        # 3 easy + 2 medium + 5 hard = 10
        allocation[bucket] = (
            ["easy"] * 3 + ["medium"] * 2 + ["hard"] * 5  # type: ignore
        )

    other_buckets = [b for b in ["Cameras", "Headphones", "Watches", "LaptopAccessories", "PhoneAccessories"]
                     if b not in cfg.brand_eligible_buckets]
    for bucket in other_buckets:
        # 3 easy + 7 medium = 10
        allocation[bucket] = (
            ["easy"] * 3 + ["medium"] * 7  # type: ignore
        )

    return allocation


# ===================================================================== #
# Generator main loop                                                   #
# ===================================================================== #


def generate_tasks(cfg: TaskSuiteConfig) -> TaskSuite:
    """Generate the full task suite. Deterministic given the random seed."""
    cfg.validate()

    rng = random.Random(cfg.random_seed)
    catalogue = pd.read_parquet(cfg.catalogue_parquet)
    logger.info("Loaded catalogue: %d products across %d buckets", len(catalogue), catalogue["bucket"].nunique())

    difficulty_per_bucket = _allocate_difficulties(cfg)

    tasks: list[Task] = []
    next_id = 1

    for bucket, difficulties in difficulty_per_bucket.items():
        for difficulty in difficulties:
            task = _generate_one(
                catalogue=catalogue,
                bucket=bucket,
                difficulty=difficulty,
                cfg=cfg,
                rng=rng,
                task_id=f"T{next_id:03d}",
            )
            if task is None:
                logger.warning(
                    "Could not generate %s task for bucket %s after %d attempts",
                    difficulty,
                    bucket,
                    cfg.max_generation_attempts,
                )
                continue
            tasks.append(task)
            next_id += 1

    logger.info("Generated %d tasks total", len(tasks))

    # Shuffle final order so buckets aren't grouped contiguously
    rng.shuffle(tasks)
    # Re-assign sequential task_ids after shuffle for cleaner indexing
    for i, t in enumerate(tasks, start=1):
        t.task_id = f"T{i:03d}"

    return TaskSuite(
        catalogue_source=str(cfg.catalogue_parquet.relative_to(cfg.catalogue_parquet.parents[2])),
        random_seed=cfg.random_seed,
        tasks=tasks,
    )


def _generate_one(
    catalogue: pd.DataFrame,
    bucket: BucketName,
    difficulty: DifficultyTier,
    cfg: TaskSuiteConfig,
    rng: random.Random,
    task_id: str,
) -> Optional[Task]:
    """Resample constraints until we find a task with a valid set in the acceptable range."""
    for _attempt in range(cfg.max_generation_attempts):
        constraints = _sample_constraints(catalogue, bucket, difficulty, cfg, rng)
        if constraints is None:
            return None  # this difficulty isn't possible for this bucket

        valid = _compute_valid_set(catalogue, constraints)
        n_valid = len(valid)
        if not (cfg.min_valid_set_size <= n_valid <= cfg.max_valid_set_size):
            continue

        preference: PreferenceFunction = rng.choice(["cheapest", "highest_rated"])  # type: ignore
        optimal = _compute_optimal(valid, preference)
        nl = _render(constraints, preference, rng)

        return Task(
            task_id=task_id,
            bucket=bucket,
            difficulty=difficulty,
            constraints=constraints,
            preference=preference,
            natural_language=nl,
            valid_set=valid["asin"].tolist(),
            optimal_asins=optimal,
        )

    return None  # gave up


# ===================================================================== #
# Persistence + summary                                                 #
# ===================================================================== #


def write_task_suite(suite: TaskSuite, cfg: TaskSuiteConfig) -> None:
    """Write the task suite to JSON and a human-readable summary report to Markdown."""
    # JSON output
    cfg.output_json.parent.mkdir(parents=True, exist_ok=True)
    cfg.output_json.write_text(suite.model_dump_json(indent=2), encoding="utf-8")
    logger.info("Wrote task suite to %s (%d tasks)", cfg.output_json, len(suite.tasks))

    # Markdown summary
    _write_summary(suite, cfg)


def _write_summary(suite: TaskSuite, cfg: TaskSuiteConfig) -> None:
    """Write a human-readable summary report."""
    cfg.summary_report.parent.mkdir(parents=True, exist_ok=True)

    # Aggregate stats
    by_bucket = Counter(t.bucket for t in suite.tasks)
    by_difficulty = Counter(t.difficulty for t in suite.tasks)
    by_preference = Counter(t.preference for t in suite.tasks)
    crosstab: dict[tuple[str, str], int] = defaultdict(int)
    for t in suite.tasks:
        crosstab[(t.bucket, t.difficulty)] += 1

    valid_sizes = [len(t.valid_set) for t in suite.tasks]
    optimal_sizes = [len(t.optimal_asins) for t in suite.tasks]

    lines: list[str] = []
    lines.append("# Task Suite Summary\n")
    lines.append(f"- **Total tasks:** {len(suite.tasks)}")
    lines.append(f"- **Catalogue source:** `{suite.catalogue_source}`")
    lines.append(f"- **Random seed:** {suite.random_seed}\n")

    lines.append("## Distribution\n")
    lines.append("**By bucket:**\n")
    for b, n in sorted(by_bucket.items()):
        lines.append(f"- {b}: {n}")
    lines.append("\n**By difficulty:**\n")
    for d in ["easy", "medium", "hard"]:
        lines.append(f"- {d.capitalize()}: {by_difficulty.get(d, 0)}")
    lines.append("\n**By preference:**\n")
    for p, n in sorted(by_preference.items()):
        lines.append(f"- {p}: {n}")

    lines.append("\n**Crosstab (bucket × difficulty):**\n")
    lines.append("| Bucket | Easy | Medium | Hard | Total |")
    lines.append("|---|---|---|---|---|")
    for b in sorted(by_bucket.keys()):
        easy = crosstab.get((b, "easy"), 0)
        med = crosstab.get((b, "medium"), 0)
        hard = crosstab.get((b, "hard"), 0)
        lines.append(f"| {b} | {easy} | {med} | {hard} | {easy + med + hard} |")

    lines.append("\n## Valid-set statistics\n")
    lines.append(f"- Min valid-set size: {min(valid_sizes)}")
    lines.append(f"- Max valid-set size: {max(valid_sizes)}")
    lines.append(f"- Median valid-set size: {sorted(valid_sizes)[len(valid_sizes) // 2]}")
    lines.append(f"- Tasks with multiple optima (ties): {sum(1 for s in optimal_sizes if s > 1)}")

    lines.append("\n## Sample tasks (one per difficulty)\n")
    for diff in ["easy", "medium", "hard"]:
        sample = next((t for t in suite.tasks if t.difficulty == diff), None)
        if sample is None:
            continue
        lines.append(f"### {diff.capitalize()} ({sample.task_id}, {sample.bucket})\n")
        lines.append(f"**Prompt:** *{sample.natural_language}*\n")
        lines.append(f"- Constraints: bucket={sample.constraints.bucket}, max_price=${sample.constraints.max_price}, "
                     f"min_stars={sample.constraints.min_stars}, brand={sample.constraints.brand}")
        lines.append(f"- Preference: {sample.preference}")
        lines.append(f"- Valid-set size: {len(sample.valid_set)}; optimal: {sample.optimal_asins}\n")

    cfg.summary_report.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote summary to %s", cfg.summary_report)
