"""Episode controller and top-level Environment class.

The Environment is the agent-facing API:
    env.reset(task) → initial state
    env.step(action) → Observation

It composes:
  - the catalogue (read-only data layer)
  - the tools (action dispatch)
  - the noise injector (middleware)
  - the episode controller (step budget, termination, malformed-action tracking)
"""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
from pydantic import ValidationError

from src.environment.models import (
    Action,
    Observation,
    TraceStep,
)
from src.environment.noise import NoiseInjector
from src.environment.tools import (
    tool_compare,
    tool_filter,
    tool_get_details,
    tool_purchase,
    tool_search,
)

logger = logging.getLogger(__name__)

# Locked during proposal design
STEP_BUDGET = 15
MALFORMED_ACTION_LIMIT = 3  # 3 consecutive malformed actions terminates the episode


@dataclass
class Environment:
    """Top-level environment: holds catalogue, noise, and episode state."""

    catalogue: pd.DataFrame
    noise: NoiseInjector
    step_budget: int = STEP_BUDGET
    malformed_action_limit: int = MALFORMED_ACTION_LIMIT

    # Episode state (mutated as episode progresses)
    _step_index: int = 0
    _consecutive_malformed: int = 0
    _terminated: bool = False
    _terminal_reason: Optional[str] = None
    _purchased_asin: Optional[str] = None
    _trace: list[TraceStep] = field(default_factory=list)

    def reset(self) -> None:
        """Reset episode state. Call before each new task."""
        self._step_index = 0
        self._consecutive_malformed = 0
        self._terminated = False
        self._terminal_reason = None
        self._purchased_asin = None
        self._trace = []

    def step(self, action: Action, thought: Optional[str] = None) -> Observation:
        """Execute one action and return the (possibly noisy) observation.

        Args:
            action: The agent's structured action.
            thought: Optional reasoning string from the agent, logged with the step.

        Returns:
            The Observation. May be terminal (purchase / budget / malformed limit).
        """
        if self._terminated:
            raise RuntimeError("Episode already terminated. Call reset() before next episode.")

        self._step_index += 1

        # Check step budget
        if self._step_index > self.step_budget:
            return self._terminate("budget_exhausted")

        # Validate the action shape
        try:
            validated_args = action.validated_args()
        except (ValidationError, KeyError) as exc:
            obs = Observation(
                status="error",
                tool=action.tool if hasattr(action, "tool") else None,
                error_code="malformed_action",
                error_message=f"Action validation failed: {exc}",
            )
            self._consecutive_malformed += 1
            self._log_step(action, obs, thought)
            if self._consecutive_malformed >= self.malformed_action_limit:
                return self._terminate("malformed_limit")
            return obs

        # Dispatch to the appropriate tool
        try:
            if action.tool == "search":
                raw_obs = tool_search(self.catalogue, validated_args)  # type: ignore
            elif action.tool == "filter":
                raw_obs = tool_filter(self.catalogue, validated_args)  # type: ignore
            elif action.tool == "compare":
                raw_obs = tool_compare(self.catalogue, validated_args)  # type: ignore
            elif action.tool == "get_details":
                raw_obs = tool_get_details(self.catalogue, validated_args)  # type: ignore
            elif action.tool == "purchase":
                raw_obs = tool_purchase(self.catalogue, validated_args)  # type: ignore
            else:
                raw_obs = Observation(
                    status="error",
                    error_code="unknown_tool",
                    error_message=f"Unknown tool '{action.tool}'.",
                )
        except Exception as exc:  # tools should not raise, but be defensive
            logger.exception("Tool '%s' raised unexpectedly", action.tool)
            raw_obs = Observation(
                status="error",
                tool=action.tool,
                error_code="tool_exception",
                error_message=str(exc),
            )

        # Reset malformed counter on a successfully-validated action
        if raw_obs.status != "error" or raw_obs.error_code != "malformed_action":
            self._consecutive_malformed = 0

        # Apply noise to non-terminal observations
        obs = self.noise.maybe_perturb(raw_obs)

        # If the (noised) observation is terminal, commit the purchase and end the episode
        if obs.status == "terminal":
            self._purchased_asin = obs.purchased_asin
            self._terminated = True
            self._terminal_reason = obs.terminal_reason

        self._log_step(action, obs, thought)
        return obs

    # ----------------------------------------------------------------- #
    # Termination helpers                                               #
    # ----------------------------------------------------------------- #

    def _terminate(self, reason: str) -> Observation:
        """Mark episode as terminated, log a synthetic terminal step, and return the obs."""
        self._terminated = True
        self._terminal_reason = reason
        obs = Observation(status="terminal", terminal_reason=reason)
        # Log a synthetic step (no action — terminated by environment-side condition)
        self._trace.append(
            TraceStep(step_index=self._step_index, action=None, observation=obs, thought=None)
        )
        return obs

    # ----------------------------------------------------------------- #
    # Trace & state inspection                                          #
    # ----------------------------------------------------------------- #

    def _log_step(self, action: Action, obs: Observation, thought: Optional[str]) -> None:
        self._trace.append(
            TraceStep(
                step_index=self._step_index,
                action=action,
                observation=obs,
                thought=thought,
            )
        )

    @property
    def trace(self) -> list[TraceStep]:
        return list(self._trace)

    @property
    def step_index(self) -> int:
        return self._step_index

    @property
    def terminated(self) -> bool:
        return self._terminated

    @property
    def terminal_reason(self) -> Optional[str]:
        return self._terminal_reason

    @property
    def purchased_asin(self) -> Optional[str]:
        return self._purchased_asin


def build_environment(
    catalogue: pd.DataFrame,
    noise_probability: float,
    seed: int,
    step_budget: int = STEP_BUDGET,
) -> Environment:
    """Convenience factory: catalogue + noise level + seed → ready-to-use Environment."""
    rng = random.Random(seed)
    noise = NoiseInjector(p=noise_probability, rng=rng)
    env = Environment(catalogue=catalogue, noise=noise, step_budget=step_budget)
    env.reset()
    return env
