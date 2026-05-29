"""Stratified sampling for the curated catalogue."""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def stratified_sample(
    df: pd.DataFrame,
    products_per_bucket: int,
    random_seed: int,
) -> pd.DataFrame:
    """Sample N products per bucket with a fixed random seed.

    If a bucket has fewer than `products_per_bucket` rows after cleaning,
    all of its rows are kept (no oversampling).

    Args:
        df: Cleaned DataFrame with a 'bucket' column.
        products_per_bucket: Target sample size per bucket.
        random_seed: Seed for reproducibility.

    Returns:
        DataFrame with up to `products_per_bucket * num_buckets` rows.
    """
    sampled_frames: list[pd.DataFrame] = []

    for bucket, group in df.groupby("bucket"):
        n_available = len(group)
        n_take = min(products_per_bucket, n_available)
        if n_available < products_per_bucket:
            logger.warning(
                "stratified_sample [%s]: only %d available (target %d) -- taking all",
                bucket,
                n_available,
                products_per_bucket,
            )
        else:
            logger.info(
                "stratified_sample [%s]: sampling %d of %d", bucket, n_take, n_available
            )
        sampled = group.sample(n=n_take, random_state=random_seed)
        sampled_frames.append(sampled)

    out = pd.concat(sampled_frames, ignore_index=True)
    # Shuffle the final catalogue once so buckets aren't grouped contiguously
    out = out.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)
    logger.info("stratified_sample: final catalogue has %d products", len(out))
    return out