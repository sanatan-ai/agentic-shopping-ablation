from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------- #
# Category filtering                                                   #
# -------------------------------------------------------------------- #
def filter_to_target_categories(
    df: pd.DataFrame, bucket_map: dict[int, str]
) -> pd.DataFrame:
    """Keep only rows whose category_id is in bucket_map; attach a 'bucket' column.

    Args:
        df: Raw products DataFrame.
        bucket_map: Mapping of raw category_id (int) -> bucket label (str).

    Returns:
        Filtered DataFrame with an added 'bucket' column.
    """
    n_in = len(df)
    out = df[df["category_id"].isin(bucket_map.keys())].copy()
    out["bucket"] = out["category_id"].map(bucket_map)
    logger.info(
        "filter_to_target_categories: %d -> %d rows (%.2f%% kept)",
        n_in,
        len(out),
        100 * len(out) / n_in if n_in else 0.0,
    )
    return out


# -------------------------------------------------------------------- #
# Missing-value handling                                               #
# -------------------------------------------------------------------- #
def drop_missing_essentials(
    df: pd.DataFrame, min_price: float = 0.0, min_stars: float = 0.0
) -> pd.DataFrame:
    """Drop rows with effectively missing essential attributes.

    Per EDA finding: 'missing' values in this dataset are encoded as zeros,
    not nulls. We treat price<=0 and stars<=0 as missing. Reviews is kept
    as-is regardless of value (the field is sparsely populated by the scrape
    and is not used as a constraint).

    Args:
        df: DataFrame after category filtering.
        min_price: Drop rows with price <= this value (default 0.0).
        min_stars: Drop rows with stars <= this value (default 0.0).

    Returns:
        DataFrame with rows missing essentials dropped.
    """
    n_in = len(df)
    out = df[
        df["title"].notna()
        & (df["title"].str.strip() != "")
        & (df["price"] > min_price)
        & (df["stars"] > min_stars)
    ].copy()
    logger.info(
        "drop_missing_essentials: %d -> %d rows (dropped %d)",
        n_in,
        len(out),
        n_in - len(out),
    )
    return out


# -------------------------------------------------------------------- #
# Deduplication                                                        #
# -------------------------------------------------------------------- #
def deduplicate_on_asin(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only one row per ASIN (no-op for our data — ASIN is already unique).

    Retained as an explicit pipeline step for safety and future-proofing.

    Args:
        df: DataFrame after cleaning.

    Returns:
        DataFrame deduplicated on the 'asin' column.
    """
    n_in = len(df)
    out = df.drop_duplicates(subset="asin", keep="first").copy()
    logger.info(
        "deduplicate_on_asin: %d -> %d rows (dropped %d duplicates)",
        n_in,
        len(out),
        n_in - len(out),
    )
    return out


# -------------------------------------------------------------------- #
# Brand extraction                                                     #
# -------------------------------------------------------------------- #
def load_brands(brands_yaml: Path) -> dict[str, list[str]]:
    """Load the per-bucket brand allowlist from YAML."""
    with brands_yaml.open("r", encoding="utf-8") as f:
        brands = yaml.safe_load(f)
    if not isinstance(brands, dict):
        raise ValueError(f"Expected dict in {brands_yaml}, got {type(brands)}")
    return brands


def _build_brand_pattern(brand_list: list[str]) -> re.Pattern:
    """Compile a regex matching any brand in the list as a whole word, longest-first."""
    # Sort by length descending so 'TAG Heuer' wins over 'TAG' when both present.
    sorted_brands = sorted(brand_list, key=len, reverse=True)
    escaped = [re.escape(b) for b in sorted_brands]
    pattern = r"\b(" + "|".join(escaped) + r")\b"
    return re.compile(pattern, flags=re.IGNORECASE)


def extract_brand(
    df: pd.DataFrame, brands: dict[str, list[str]]
) -> pd.DataFrame:
    out = df.copy()
    out["brand"] = "Unknown"

    for bucket, brand_list in brands.items():
        if bucket not in out["bucket"].unique():
            continue
        pattern = _build_brand_pattern(brand_list)
        mask = out["bucket"] == bucket
        # Extract the first regex match per title; NaN if no match.
        matches = out.loc[mask, "title"].str.extract(pattern, expand=False)
        # Canonicalise: where matched, take the canonical-case form from the brand list.
        canonical_map = {b.lower(): b for b in brand_list}
        canonical = matches.str.lower().map(canonical_map)
        out.loc[mask, "brand"] = canonical.fillna("Unknown")

    # Log per-bucket coverage
    coverage = out.groupby("bucket")["brand"].apply(
        lambda s: (s != "Unknown").mean() * 100
    )
    for bucket, pct in coverage.items():
        logger.info("brand coverage [%s]: %.1f%% known", bucket, pct)

    return out


# -------------------------------------------------------------------- #
# Column selection / final shape                                       #
# -------------------------------------------------------------------- #
FINAL_COLUMNS = [
    "asin",
    "bucket",
    "title",
    "brand",
    "price",
    "stars",
    "reviews",
    "category_id",
    "isBestSeller",
    "boughtInLastMonth",
]


def select_final_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce the DataFrame to the final catalogue schema."""
    missing = set(FINAL_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in final shape: {missing}")
    return df[FINAL_COLUMNS].copy()