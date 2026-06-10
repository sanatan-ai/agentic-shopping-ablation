"""Pydantic schemas for environment interactions.

Defines the typed action/observation contract between an agent and the environment.
All agent-environment communication flows through these models.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# Tool names
ToolName = Literal["search", "filter", "compare", "get_details", "purchase"]
FilterOperator = Literal["<=", ">=", "==", "<", ">", "!="]


# ===================================================================== #
# Action schemas — agent → environment                                  #
# ===================================================================== #

class SearchArgs(BaseModel):
    query: str = Field(min_length=1, description="Free-text search query")


class FilterArgs(BaseModel):
    attribute: Literal["price", "stars", "reviews", "bucket", "brand"]
    operator: FilterOperator
    value: Any  # number for price/stars/reviews; string for bucket/brand
    candidate_asins: list[str] | None = Field(
        default=None,
        description="Optional subset of ASINs to filter; if None, filters whole catalogue",
    )


class CompareArgs(BaseModel):
    product_ids: list[str] = Field(min_length=2, max_length=10, description="2-10 ASINs to compare")


class GetDetailsArgs(BaseModel):
    product_id: str = Field(min_length=1)


class PurchaseArgs(BaseModel):
    product_id: str = Field(min_length=1)


class Action(BaseModel):
    """An agent action: tool name + typed args.

    The agent emits one of these per step. Malformed actions are rejected
    by the environment and counted toward the malformed-action limit.
    """

    tool: ToolName
    args: dict[str, Any] = Field(default_factory=dict)

    def validated_args(self) -> BaseModel:
        """Return the args parsed as the appropriate typed model. Raises on invalid args."""
        schemas: dict[str, type[BaseModel]] = {
            "search": SearchArgs,
            "filter": FilterArgs,
            "compare": CompareArgs,
            "get_details": GetDetailsArgs,
            "purchase": PurchaseArgs,
        }
        return schemas[self.tool](**self.args)


# ===================================================================== #
# Observation schemas — environment → agent                             #
# ===================================================================== #

class Product(BaseModel):
    """Compact product representation in observations."""

    asin: str
    bucket: str
    title: str
    brand: str
    price: float
    stars: float
    reviews: int


class Observation(BaseModel):
    """The environment's response to an action.

    Always returns one of three states: ok with content, ok with error, or terminal.
    """

    status: Literal["ok", "error", "terminal"]
    tool: ToolName | None = None
    products: list[Product] = Field(default_factory=list)
    truncated: bool = Field(default=False, description="True if result was capped (more available)")
    total_matches: int | None = Field(default=None, description="Total before truncation, if applicable")
    error_code: str | None = None
    error_message: str | None = None
    terminal_reason: str | None = None  # 'purchased' | 'budget_exhausted' | 'malformed_limit'
    purchased_asin: str | None = None  # set only when status=terminal and reason=purchased

    @field_validator("status")
    @classmethod
    def _status_consistency(cls, v: str, info) -> str:
        # Light validator; deep checks happen in the env
        return v


# ===================================================================== #
# Episode trace                                                         #
# ===================================================================== #

class TraceStep(BaseModel):
    """One step in an episode's trace."""

    step_index: int
    action: Action | None = None  # None on terminal step from environment side
    observation: Observation
    thought: str | None = None  # populated by the agent if it emits reasoning


class EpisodeResult(BaseModel):
    """The final outcome of an episode."""

    task_id: str
    architecture: str
    noise_level: float
    seed: int
    steps_taken: int
    terminated: bool
    terminal_reason: str | None = None
    purchased_asin: str | None = None
    tokens_used: int = 0
    wall_clock_seconds: float = 0.0
    trace: list[TraceStep] = Field(default_factory=list)
