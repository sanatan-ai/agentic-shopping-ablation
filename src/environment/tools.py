"""Tool implementations.

Each tool is a pure function (catalogue + args) → Observation.
The catalogue is treated as read-only.
"""
from __future__ import annotations

import logging

import pandas as pd

from src.environment.models import (
    CompareArgs,
    FilterArgs,
    GetDetailsArgs,
    Observation,
    Product,
    PurchaseArgs,
    SearchArgs,
)

logger = logging.getLogger(__name__)

# Maximum products returned in any single observation (overflow signalled via `truncated`)
RESULT_CAP = 10


# --------------------------------------------------------------------- #
# Helpers                                                               #
# --------------------------------------------------------------------- #

def _to_product(row: pd.Series) -> Product:
    """Convert a catalogue row to a Product object."""
    return Product(
        asin=str(row["asin"]),
        bucket=str(row["bucket"]),
        title=str(row["title"]),
        brand=str(row["brand"]),
        price=float(row["price"]),
        stars=float(row["stars"]),
        reviews=int(row["reviews"]),
    )


def _cap_and_observe(
    matches: pd.DataFrame, tool_name: str, cap: int = RESULT_CAP
) -> Observation:
    """Cap a result DataFrame at `cap` rows and return an Observation."""
    total = len(matches)
    truncated = total > cap
    head = matches.head(cap)
    products = [_to_product(row) for _, row in head.iterrows()]
    return Observation(
        status="ok",
        tool=tool_name,  # type: ignore[arg-type]
        products=products,
        truncated=truncated,
        total_matches=total,
    )


# --------------------------------------------------------------------- #
# Tool: search                                                          #
# --------------------------------------------------------------------- #

def tool_search(catalogue: pd.DataFrame, args: SearchArgs) -> Observation:
    """Pure text matching: return products whose title contains all query words.

    Words are compared case-insensitively. Empty queries are rejected upstream
    by the SearchArgs schema (min_length=1).
    """
    query_words = [w.lower() for w in args.query.split() if w.strip()]
    if not query_words:
        return Observation(
            status="error",
            tool="search",
            error_code="invalid_query",
            error_message="Search query was empty after tokenization.",
        )

    title_lower = catalogue["title"].str.lower()
    mask = pd.Series(True, index=catalogue.index)
    for word in query_words:
        mask &= title_lower.str.contains(word, regex=False, na=False)

    matches = catalogue[mask]
    return _cap_and_observe(matches, "search")


# --------------------------------------------------------------------- #
# Tool: filter                                                          #
# --------------------------------------------------------------------- #

_NUMERIC_ATTRS = {"price", "stars", "reviews"}
_STRING_ATTRS = {"bucket", "brand"}


def tool_filter(catalogue: pd.DataFrame, args: FilterArgs) -> Observation:
    """Filter the catalogue (or a candidate subset) by a structured constraint."""
    # Determine the candidate pool
    if args.candidate_asins is not None:
        pool = catalogue[catalogue["asin"].isin(args.candidate_asins)]
    else:
        pool = catalogue

    attr = args.attribute
    op = args.operator
    val = args.value

    # Numeric vs string attribute handling
    if attr in _NUMERIC_ATTRS:
        try:
            val = float(val)
        except (TypeError, ValueError):
            return Observation(
                status="error",
                tool="filter",
                error_code="type_mismatch",
                error_message=f"Attribute '{attr}' is numeric but value '{val}' is not.",
            )
        col = pool[attr]
        if op == "<=":
            mask = col <= val
        elif op == ">=":
            mask = col >= val
        elif op == "<":
            mask = col < val
        elif op == ">":
            mask = col > val
        elif op == "==":
            mask = col == val
        elif op == "!=":
            mask = col != val
        else:
            return Observation(
                status="error",
                tool="filter",
                error_code="invalid_operator",
                error_message=f"Unknown operator '{op}'.",
            )
    elif attr in _STRING_ATTRS:
        if op not in ("==", "!="):
            return Observation(
                status="error",
                tool="filter",
                error_code="invalid_operator",
                error_message=f"String attribute '{attr}' only supports '==' or '!='; got '{op}'.",
            )
        val_str = str(val).lower()
        col_lower = pool[attr].str.lower()
        mask = (col_lower == val_str) if op == "==" else (col_lower != val_str)
    else:
        return Observation(
            status="error",
            tool="filter",
            error_code="invalid_attribute",
            error_message=f"Unknown attribute '{attr}'.",
        )

    matches = pool[mask]
    return _cap_and_observe(matches, "filter")


# --------------------------------------------------------------------- #
# Tool: compare                                                         #
# --------------------------------------------------------------------- #

def tool_compare(catalogue: pd.DataFrame, args: CompareArgs) -> Observation:
    """Return side-by-side details for 2-10 ASINs."""
    matches = catalogue[catalogue["asin"].isin(args.product_ids)]

    found_asins = set(matches["asin"])
    missing = [aid for aid in args.product_ids if aid not in found_asins]
    if missing:
        return Observation(
            status="error",
            tool="compare",
            error_code="unknown_asin",
            error_message=f"ASINs not found in catalogue: {missing}",
        )

    products = [_to_product(row) for _, row in matches.iterrows()]
    return Observation(
        status="ok",
        tool="compare",
        products=products,
        total_matches=len(products),
        truncated=False,
    )


# --------------------------------------------------------------------- #
# Tool: get_details                                                     #
# --------------------------------------------------------------------- #

def tool_get_details(catalogue: pd.DataFrame, args: GetDetailsArgs) -> Observation:
    """Return full metadata for a single product."""
    matches = catalogue[catalogue["asin"] == args.product_id]
    if matches.empty:
        return Observation(
            status="error",
            tool="get_details",
            error_code="unknown_asin",
            error_message=f"ASIN '{args.product_id}' not found in catalogue.",
        )
    return Observation(
        status="ok",
        tool="get_details",
        products=[_to_product(matches.iloc[0])],
        total_matches=1,
        truncated=False,
    )


# --------------------------------------------------------------------- #
# Tool: purchase                                                        #
# --------------------------------------------------------------------- #

def tool_purchase(catalogue: pd.DataFrame, args: PurchaseArgs) -> Observation:
    """Commit to a final product. Returns terminal observation.

    The episode controller treats this as the success terminal condition.
    """
    matches = catalogue[catalogue["asin"] == args.product_id]
    if matches.empty:
        return Observation(
            status="error",
            tool="purchase",
            error_code="unknown_asin",
            error_message=f"Cannot purchase '{args.product_id}': ASIN not in catalogue.",
        )
    return Observation(
        status="terminal",
        tool="purchase",
        purchased_asin=args.product_id,
        terminal_reason="purchased",
        products=[_to_product(matches.iloc[0])],
    )
