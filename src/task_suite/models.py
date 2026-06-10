"""Pydantic schemas for the task suite."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Type aliases
BucketName = Literal["Cameras", "Headphones", "Watches", "LaptopAccessories", "PhoneAccessories"]
PreferenceFunction = Literal["cheapest", "highest_rated"]
DifficultyTier = Literal["easy", "medium", "hard"]


class Constraints(BaseModel):
    """Structured hard-constraint specification for a task.

    Reviews are deliberately excluded as a constraint type — see EDA report
    (scrape-side sparsity makes them unreliable).
    """

    bucket: BucketName
    max_price: float = Field(gt=0, description="Maximum price cap")
    min_stars: float | None = Field(default=None, ge=0, le=5, description="Minimum star rating")
    brand: str | None = Field(default=None, description="Required brand (case-insensitive)")

    @field_validator("brand")
    @classmethod
    def _brand_not_unknown(cls, v: str | None) -> str | None:
        if v is not None and v.strip().lower() == "unknown":
            raise ValueError("Cannot constrain on 'Unknown' brand")
        return v

    def num_constraints(self) -> int:
        """Count of active hard constraints (always >=2 because bucket + price are required)."""
        n = 2  # bucket + max_price
        if self.min_stars is not None:
            n += 1
        if self.brand is not None:
            n += 1
        return n


class Task(BaseModel):
    """A single benchmark task."""

    task_id: str
    bucket: BucketName
    difficulty: DifficultyTier
    constraints: Constraints
    preference: PreferenceFunction
    natural_language: str = Field(description="The prompt presented to the agent")
    valid_set: list[str] = Field(description="ASINs satisfying all hard constraints")
    optimal_asins: list[str] = Field(description="ASINs optimal under the preference function")

    @field_validator("valid_set")
    @classmethod
    def _valid_set_nonempty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("valid_set must be non-empty")
        return v

    @field_validator("optimal_asins")
    @classmethod
    def _optimal_subset_of_valid(cls, v: list[str], info) -> list[str]:
        valid = info.data.get("valid_set")
        if valid is not None and not set(v).issubset(set(valid)):
            raise ValueError("optimal_asins must be a subset of valid_set")
        return v


class TaskSuite(BaseModel):
    """The complete benchmark task suite."""

    catalogue_source: str = Field(description="Path or identifier of the catalogue the tasks were built against")
    random_seed: int
    tasks: list[Task]

    def summary(self) -> dict[str, int]:
        """Per-(bucket, difficulty) task counts."""
        from collections import Counter

        return dict(Counter((t.bucket, t.difficulty) for t in self.tasks))
