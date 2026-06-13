"""Reactive (ReAct-style) agent.

Single-episode loop:
  1. Build the system prompt and initial user message from the task NL.
  2. Repeatedly:
     a. Call the LLM → get a JSON thought/action
     b. Parse the JSON; on failure, feed an error observation back
     c. Execute the action via the environment
     d. Append the observation to the conversation history
  3. Stop when the environment returns a terminal observation
     (purchase / budget / malformed-limit).

The agent does NOT have any episodic memory beyond the current conversation
history — this is the pure single-episode ReAct as locked in the proposal.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from src.agents.llm_client import LLMClient, LLMResponse
from src.agents.parser import ParseError, parse_llm_output
from src.agents.prompts import (
    REACTIVE_SYSTEM_PROMPT,
    build_initial_user_message,
    build_observation_message,
)
from src.environment.environment import Environment
from src.environment.models import Action, Observation

logger = logging.getLogger(__name__)


def _observation_to_text(obs: Observation) -> str:
    """Render an Observation back to text for the agent's next turn.

    Compact format: status, tool, any products (asin/title/brand/price/stars),
    overflow signal, errors, terminal reason.
    """
    lines: list[str] = []
    lines.append(f"status: {obs.status}")
    if obs.tool:
        lines.append(f"tool: {obs.tool}")
    if obs.error_code:
        lines.append(f"error_code: {obs.error_code}")
        if obs.error_message:
            lines.append(f"error_message: {obs.error_message}")
    if obs.products:
        lines.append(f"products ({len(obs.products)} returned, total_matches={obs.total_matches}):")
        for p in obs.products:
            lines.append(
                f"  - asin={p.asin} | bucket={p.bucket} | brand={p.brand} | "
                f"price=${p.price:.2f} | stars={p.stars} | reviews={p.reviews} | "
                f"title={p.title[:80]}"
            )
        if obs.truncated:
            lines.append(
                f"NOTE: results truncated at 10; total_matches={obs.total_matches}. "
                "Refine your query/filter to narrow further."
            )
    if obs.status == "terminal":
        lines.append(f"terminal_reason: {obs.terminal_reason}")
        if obs.purchased_asin:
            lines.append(f"purchased_asin: {obs.purchased_asin}")
    return "\n".join(lines)


@dataclass
class ReactiveAgentResult:
    """Aggregated outcome of one reactive-agent episode."""

    task_id: str
    steps_taken: int
    terminated: bool
    terminal_reason: Optional[str]
    purchased_asin: Optional[str]
    total_input_tokens: int
    total_output_tokens: int
    wall_clock_seconds: float
    llm_calls: int
    parse_errors: int = 0


@dataclass
class ReactiveAgent:
    """Single-episode ReAct-style agent."""

    llm: LLMClient
    env: Environment
    max_tokens_per_step: int = 256
    temperature: float = 0.0

    # Episode-local state (reset per task)
    _messages: list[dict[str, str]] = field(default_factory=list)
    _llm_calls: int = 0
    _input_tokens: int = 0
    _output_tokens: int = 0
    _parse_errors: int = 0

    def run_episode(self, task_id: str, task_nl: str) -> ReactiveAgentResult:
        """Run a single episode against the configured environment + task.

        The environment is expected to have been reset with the appropriate
        task-specific configuration (e.g. noise seed) before calling this.
        """
        self._reset_episode_state()
        self._messages = [{"role": "user", "content": build_initial_user_message(task_nl)}]

        start = time.time()

        while not self.env.terminated:
            # 1. Call the LLM
            try:
                response: LLMResponse = self.llm.complete(
                    system=REACTIVE_SYSTEM_PROMPT,
                    messages=self._messages,
                    max_tokens=self.max_tokens_per_step,
                    temperature=self.temperature,
                )
            except Exception as exc:
                logger.exception("LLM call failed during episode %s", task_id)
                # Treat LLM failure as a hard episode end (no point continuing)
                break

            self._llm_calls += 1
            self._input_tokens += response.input_tokens
            self._output_tokens += response.output_tokens

            # 2. Append the assistant's response to the history
            self._messages.append({"role": "assistant", "content": response.text})

            # 3. Parse the JSON
            try:
                parsed = parse_llm_output(response.text)
            except ParseError as exc:
                self._parse_errors += 1
                # Feed an error observation back to the agent for self-correction
                error_text = (
                    f"status: error\n"
                    f"error_code: parse_failure\n"
                    f"error_message: Your previous response could not be parsed as JSON. "
                    f"Details: {exc}. Respond with a single JSON object only."
                )
                self._messages.append(
                    {"role": "user", "content": build_observation_message(error_text)}
                )
                # Don't count as an environment step — but environment doesn't see this either
                # If the agent keeps emitting bad JSON, parse_errors accumulates; we cap below
                if self._parse_errors >= 5:
                    logger.warning(
                        "Episode %s: 5+ parse errors. Terminating to avoid runaway.", task_id
                    )
                    break
                continue

            # 4. Send the action to the environment
            obs = self.env.step(action=parsed.action, thought=parsed.thought)

            # 5. Render the observation back to text and append to history
            obs_text = _observation_to_text(obs)
            self._messages.append(
                {"role": "user", "content": build_observation_message(obs_text)}
            )

            if obs.status == "terminal":
                break

        elapsed = time.time() - start

        return ReactiveAgentResult(
            task_id=task_id,
            steps_taken=self.env.step_index,
            terminated=self.env.terminated,
            terminal_reason=self.env.terminal_reason,
            purchased_asin=self.env.purchased_asin,
            total_input_tokens=self._input_tokens,
            total_output_tokens=self._output_tokens,
            wall_clock_seconds=elapsed,
            llm_calls=self._llm_calls,
            parse_errors=self._parse_errors,
        )

    def _reset_episode_state(self) -> None:
        self._messages = []
        self._llm_calls = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._parse_errors = 0
