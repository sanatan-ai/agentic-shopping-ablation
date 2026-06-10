"""Configuration for task suite generation.

All design decisions locked during the design session are encoded here as a
single source of truth for the task generator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# -------------------------------------------------------------------- #
# Paths                                                                #
# -------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

CATALOGUE_PARQUET = DATA_PROCESSED / "catalogue.parquet"
TASK_SUITE_JSON = DATA_PROCESSED / "task_suite.json"
SUMMARY_REPORT = PROJECT_ROOT / "reports" / "task_suite_summary.md"

# -------------------------------------------------------------------- #
# Reproducibility                                                      #
# -------------------------------------------------------------------- #
RANDOM_SEED = 42

# -------------------------------------------------------------------- #
# Task suite composition                                               #
# -------------------------------------------------------------------- #
TOTAL_TASKS = 50

# Per-difficulty allocation: 15 easy + 20 medium + 15 hard = 50
DIFFICULTY_ALLOCATION: dict[str, int] = {
    "easy": 15,
    "medium": 20,
    "hard": 15,
}

# Per-bucket allocation: 10 tasks per bucket × 5 buckets = 50
TASKS_PER_BUCKET = 10
BUCKETS: list[str] = ["Cameras", "Headphones", "Watches", "LaptopAccessories", "PhoneAccessories"]

# -------------------------------------------------------------------- #
# Brand-gating: which buckets are eligible for brand-constrained tasks #
# -------------------------------------------------------------------- #
# Based on observed brand-coverage from the catalogue (EDA findings):
#   Cameras 56%, LaptopAccessories 53%, PhoneAccessories 52% --> eligible
#   Headphones 27%, Watches 8% --> not eligible (insufficient known brands)
BRAND_ELIGIBLE_BUCKETS: set[str] = {"Cameras", "LaptopAccessories", "PhoneAccessories"}

# -------------------------------------------------------------------- #
# Constraint tiers (locked during EDA)                                 #
# -------------------------------------------------------------------- #
# Star-rating tiers: loose / standard / tight
STAR_TIERS: dict[str, float] = {"loose": 4.3, "standard": 4.5, "tight": 4.7}

# Price-cap tiers expressed as quantile of bucket price distribution
# (lower quantile = tighter, fewer products satisfy)
PRICE_QUANTILE_TIERS: dict[str, float] = {"loose": 0.50, "standard": 0.30, "tight": 0.15}

# -------------------------------------------------------------------- #
# Valid-set bounds                                                     #
# -------------------------------------------------------------------- #
# Tasks whose valid set falls outside these bounds are discarded and
# re-sampled. Lower bound ensures the task is meaningfully solvable;
# upper bound ensures it is non-trivial.
MIN_VALID_SET_SIZE = 2
MAX_VALID_SET_SIZE = 30

# Maximum number of resampling attempts before giving up on a task slot
MAX_GENERATION_ATTEMPTS = 200

# -------------------------------------------------------------------- #
# Preferences                                                          #
# -------------------------------------------------------------------- #
PREFERENCES: list[str] = ["cheapest", "highest_rated"]


@dataclass(frozen=True)
class TaskSuiteConfig:
    """Immutable configuration object."""

    catalogue_parquet: Path = CATALOGUE_PARQUET
    output_json: Path = TASK_SUITE_JSON
    summary_report: Path = SUMMARY_REPORT

    random_seed: int = RANDOM_SEED
    total_tasks: int = TOTAL_TASKS
    tasks_per_bucket: int = TASKS_PER_BUCKET

    difficulty_allocation: dict[str, int] = field(
        default_factory=lambda: dict(DIFFICULTY_ALLOCATION)
    )
    brand_eligible_buckets: set[str] = field(
        default_factory=lambda: set(BRAND_ELIGIBLE_BUCKETS)
    )
    star_tiers: dict[str, float] = field(default_factory=lambda: dict(STAR_TIERS))
    price_quantile_tiers: dict[str, float] = field(
        default_factory=lambda: dict(PRICE_QUANTILE_TIERS)
    )

    min_valid_set_size: int = MIN_VALID_SET_SIZE
    max_valid_set_size: int = MAX_VALID_SET_SIZE
    max_generation_attempts: int = MAX_GENERATION_ATTEMPTS

    def validate(self) -> None:
        if not self.catalogue_parquet.exists():
            raise FileNotFoundError(f"Catalogue not found: {self.catalogue_parquet}")
        total_diff = sum(self.difficulty_allocation.values())
        if total_diff != self.total_tasks:
            raise ValueError(
                f"Difficulty allocation sums to {total_diff}, expected {self.total_tasks}"
            )
