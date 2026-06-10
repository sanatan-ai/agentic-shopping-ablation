from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# -------------------------------------------------------------------- #
# Paths                                                                #
# -------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

RAW_PRODUCTS_CSV = DATA_RAW / "amazon_products.csv"
RAW_CATEGORIES_CSV = DATA_RAW / "amazon_categories.csv"
PROCESSED_CATALOGUE_PARQUET = DATA_PROCESSED / "catalogue.parquet"

BRANDS_YAML = Path(__file__).resolve().parent / "brands.yaml"

# -------------------------------------------------------------------- #
# Reproducibility                                                      #
# -------------------------------------------------------------------- #
RANDOM_SEED = 42

# -------------------------------------------------------------------- #
# Bucket mapping: raw category_id -> our final bucket label            #
# -------------------------------------------------------------------- #
# Locked during EDA (Section 7):
# - Phones bucket renamed to PhoneAccessories (no actual smartphones)
# - Laptops substituted with LaptopAccessories (no actual laptops)
# - Men's + Women's watches merged into a single Watches bucket
BUCKET_MAP: dict[int, str] = {
    71:  "Headphones",
    79:  "Cameras",
    75:  "PhoneAccessories",
    113: "Watches",
    121: "Watches",
    65:  "LaptopAccessories",
}

BUCKET_NAMES: list[str] = sorted(set(BUCKET_MAP.values()))

# -------------------------------------------------------------------- #
# Cleaning thresholds                                                  #
# -------------------------------------------------------------------- #
# Locked during EDA (Section 3):
# - Drop rows where price <= 0 (no valid price)
# - Drop rows where stars <= 0 (no rating)
# - Drop rows where title is null/empty
# - Reviews kept in catalogue but NOT used as a constraint
#   (~70% of dataset has reviews=0 due to scrape sparsity)
MIN_PRICE = 0.0
MIN_STARS = 0.0

# -------------------------------------------------------------------- #
# Sampling                                                             #
# -------------------------------------------------------------------- #
# Locked during EDA (overall plan): stratified ~100 per bucket, ~500 total.
PRODUCTS_PER_BUCKET = 100
TARGET_TOTAL_PRODUCTS = PRODUCTS_PER_BUCKET * len(BUCKET_NAMES)  # 500

# -------------------------------------------------------------------- #
# Task constraint tiers (for downstream task generation, not used here)#
# -------------------------------------------------------------------- #
# Documented here for reference; the task generator (next phase) will use these.
STAR_TIERS = {"loose": 4.3, "standard": 4.5, "tight": 4.7}
PRICE_QUANTILE_TIERS = {"loose": 0.50, "standard": 0.30, "tight": 0.15}


# -------------------------------------------------------------------- #
# Pipeline run config (passed around as a single object)               #
# -------------------------------------------------------------------- #
@dataclass(frozen=True)
class PipelineConfig:
    """Immutable configuration object passed through the pipeline."""

    raw_products_csv: Path = RAW_PRODUCTS_CSV
    raw_categories_csv: Path = RAW_CATEGORIES_CSV
    output_parquet: Path = PROCESSED_CATALOGUE_PARQUET
    brands_yaml: Path = BRANDS_YAML

    bucket_map: dict[int, str] = field(default_factory=lambda: dict(BUCKET_MAP))
    products_per_bucket: int = PRODUCTS_PER_BUCKET
    random_seed: int = RANDOM_SEED

    min_price: float = MIN_PRICE
    min_stars: float = MIN_STARS

    def validate(self) -> None:
        """Sanity-check the configuration."""
        if not self.raw_products_csv.exists():
            raise FileNotFoundError(f"Raw products CSV not found: {self.raw_products_csv}")
        if not self.raw_categories_csv.exists():
            raise FileNotFoundError(f"Raw categories CSV not found: {self.raw_categories_csv}")
        if not self.brands_yaml.exists():
            raise FileNotFoundError(f"Brands YAML not found: {self.brands_yaml}")
        if self.products_per_bucket < 1:
            raise ValueError(f"products_per_bucket must be >= 1, got {self.products_per_bucket}")