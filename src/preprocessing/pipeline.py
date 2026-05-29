"""Top-level pipeline orchestrator.

Composes the cleaning and sampling steps to transform the raw Amazon Products
Dataset into the curated ~500-product catalogue, written to Parquet.
"""
from __future__ import annotations

import logging

import pandas as pd

from src.preprocessing.clean import (
    deduplicate_on_asin,
    drop_missing_essentials,
    extract_brand,
    filter_to_target_categories,
    load_brands,
    select_final_columns,
)
from src.preprocessing.config import PipelineConfig
from src.preprocessing.sample import stratified_sample

logger = logging.getLogger(__name__)


def run_pipeline(cfg: PipelineConfig) -> pd.DataFrame:
    """Run the full preprocessing pipeline and write the curated catalogue.

    Args:
        cfg: Pipeline configuration.

    Returns:
        The curated catalogue DataFrame (also written to disk as Parquet).
    """
    cfg.validate()

    logger.info("Loading raw products from %s", cfg.raw_products_csv)
    df = pd.read_csv(cfg.raw_products_csv)
    logger.info("Loaded %d raw rows, %d columns", len(df), df.shape[1])

    logger.info("Loading brand allowlist from %s", cfg.brands_yaml)
    brands = load_brands(cfg.brands_yaml)

    # Pipeline stages
    df = filter_to_target_categories(df, cfg.bucket_map)
    df = drop_missing_essentials(df, min_price=cfg.min_price, min_stars=cfg.min_stars)
    df = deduplicate_on_asin(df)
    df = extract_brand(df, brands)
    df = stratified_sample(
        df,
        products_per_bucket=cfg.products_per_bucket,
        random_seed=cfg.random_seed,
    )
    df = select_final_columns(df)

    # Write artefact
    cfg.output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cfg.output_parquet, index=False)
    logger.info("Wrote curated catalogue to %s (%d rows)", cfg.output_parquet, len(df))

    # Quick post-write summary
    _log_summary(df)

    return df


def _log_summary(df: pd.DataFrame) -> None:
    """Log a per-bucket summary of the curated catalogue."""
    logger.info("Final catalogue summary:")
    for bucket, group in df.groupby("bucket"):
        known_brands = (group["brand"] != "Unknown").sum()
        logger.info(
            "  %-20s n=%3d  price[median=%.2f, p75=%.2f]  stars[median=%.2f]  "
            "brand_known=%d/%d",
            bucket,
            len(group),
            group["price"].median(),
            group["price"].quantile(0.75),
            group["stars"].median(),
            known_brands,
            len(group),
        )