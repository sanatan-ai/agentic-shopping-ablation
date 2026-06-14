"""Planning (plan-then-execute + replan-on-failure) agent.

Architecture:
  - Phase 1: LLM emits a complete plan (list of actions) for the task.
  - Phase 2: System executes the plan action-by-action against the environment.
  - Replan trigger: if execution hits an error OR plan finishes without purchase,
    LLM is called again with execution history to emit a new plan.
  - Max 3 replans per episode (locked in proposal).

Key contrast with reactive agent: planning agent has FEWER LLM calls (1 per plan,
not 1 per environment step), which is the central efficiency hypothesis we are
testing (RQ2).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from src.agents.llm_client import LLMClient, LLMResponse
from src.agents.parser import ParseError
from src.agents.planning_parser import parse_plan
from src.agents.planning_prompts import (
    PLANNING_SYSTEM_PROMPT,
    build_initial_plan_prompt,
    build_replan_prompt,
)
from src.agents.reactive_agent import _observation_to_text  # reuse the rendering logic
from src.environment.environment import Environment
from src.environment.models import Action, Observation

logger = logging.getLogger(__name__)

# Locked in proposal
MAX_REPLANS = 3


@dataclass
class PlanningAgentResult:
    """Aggregated outcome of one planning-agent episode."""

    task_id: str
    steps_taken: int           # env steps consumed
    terminated: bool
    terminal_reason: Optional[str]
    purchased_asin: Optional[str]
    total_input_tokens: int
    total_output_tokens: int
    wall_clock_seconds: float
    llm_calls: int             # number of plan/replan calls
    replans_used: int
    parse_errors: int = 0


@dataclass
class PlanningAgent:
    """Plan-then-execute + replan-on-failure agent."""

    llm: LLMClient
    env: Environment
    max_tokens_per_plan: int = 512
    temperature: float = 0.0
    max_replans: int = MAX_REPLANS

    # Episode-local state
    _execution_history: list[str] = field(default_factory=list)
    _llm_calls: int = 0
    _input_tokens: int = 0
    _output_tokens: int = 0
    _parse_errors: int = 0
    _replans_used: int = 0

    def run_episode(self, task_id: str, task_nl: str) -> PlanningAgentResult:
        """Run a single episode against the configured environment + task."""
        self._reset_episode_state()
        start = time.time()

        # ----- Phase 1: initial plan ----- #
        plan = self._call_llm_for_plan(
            user_prompt=build_initial_plan_prompt(task_nl),
            attempt_label="initial",
        )

        # ----- Execute / replan loop ----- #
        while plan is not None and not self.env.terminated:
            replan_reason = self._execute_plan(plan)

            if self.env.terminated:
                break

            # Plan finished and we haven't terminated → must replan
            if self._replans_used >= self.max_replans:
                # Out of replans; force termination
                logger.info("Episode %s: exhausted %d replans. Ending.", task_id, self.max_replans)
                self.env._terminate("replan_limit_exceeded")  # access internal helper
                break

            self._replans_used += 1
            history_text = "\n".join(self._execution_history) if self._execution_history else "(no actions yet)"
            plan = self._call_llm_for_plan(
                user_prompt=build_replan_prompt(task_nl, history_text, replan_reason),
                attempt_label=f"replan_{self._replans_used}",
            )

        elapsed = time.time() - start

        return PlanningAgentResult(
            task_id=task_id,
            steps_taken=self.env.step_index,
            terminated=self.env.terminated,
            terminal_reason=self.env.terminal_reason,
            purchased_asin=self.env.purchased_asin,
            total_input_tokens=self._input_tokens,
            total_output_tokens=self._output_tokens,
            wall_clock_seconds=elapsed,
            llm_calls=self._llm_calls,
            replans_used=self._replans_used,
            parse_errors=self._parse_errors,
        )

    # ----------------------------------------------------------------- #
    # LLM call wrapper                                                  #
    # ----------------------------------------------------------------- #

    def _call_llm_for_plan(self, user_prompt: str, attempt_label: str):
        """Call the LLM for a plan. Returns ParsedPlan or None on parse failure."""
        try:
            response: LLMResponse = self.llm.complete(
                system=PLANNING_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=self.max_tokens_per_plan,
                temperature=self.temperature,
            )
        except Exception:
            logger.exception("LLM call (%s) failed", attempt_label)
            return None

        self._llm_calls += 1
        self._input_tokens += response.input_tokens
        self._output_tokens += response.output_tokens

        try:
            plan = parse_plan(response.text)
            logger.info("Plan (%s): %d actions — %s",
                        attempt_label, len(plan.actions), plan.plan_summary[:80])
            return plan
        except ParseError as exc:
            self._parse_errors += 1
            logger.warning("Plan parse failure (%s): %s", attempt_label, exc)
            return None

    # ----------------------------------------------------------------- #
    # Plan execution                                                    #
    # ----------------------------------------------------------------- #

    def _execute_plan(self, plan) -> str:
        """Execute a plan's actions sequentially. Returns the replan-reason string.

        Stops execution when:
          - env terminates (purchase or budget exhausted), OR
          - an action returns an error observation (replan trigger).
        Returns a human-readable reason for replanning if the episode is not yet
        terminated.
        """
        for i, action in enumerate(plan.actions):
            if self.env.terminated:
                return "Episode terminated mid-plan."

            obs: Observation = self.env.step(action=action, thought=plan.plan_summary)
            obs_text = _observation_to_text(obs)

            # Append to execution history for the next replan prompt
            self._execution_history.append(
                f"STEP {self.env.step_index}: action={{'tool': '{action.tool}', 'args': {action.args}}}\n"
                f"  → {obs_text}"
            )

            if obs.status == "terminal":
                return "Plan reached a terminal state."

            if obs.status == "error":
                # Replan trigger
                return (
                    f"Action #{i+1} (tool='{action.tool}') returned error: "
                    f"{obs.error_code} — {obs.error_message}."
                )

        # Plan finished without termination → need to replan for purchase
        return "Plan finished without purchasing. Now make the final purchase decision."

    # ----------------------------------------------------------------- #
    # State reset                                                       #
    # ----------------------------------------------------------------- #

    def _reset_episode_state(self) -> None:
        self._execution_history = []
        self._llm_calls = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._parse_errors = 0
        self._replans_used = 0
