"""LLM client abstraction.

Defines a Protocol that the agent calls against, with two implementations:
  - BedrockClient: real AWS Bedrock + Llama 3.1 8B
  - MockClient: canned responses for testing without AWS spend

The Protocol layer means the agent code never imports boto3 directly —
sanity tests use the mock; pilot/full runs use Bedrock. Same agent code.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# AWS Bedrock pricing for Llama 3.1 8B Instruct (us-east-1, as of late 2025)
# Used for cost tracking only; not authoritative
PRICE_PER_1K_INPUT_TOKENS = 0.00022   # USD
PRICE_PER_1K_OUTPUT_TOKENS = 0.00022  # USD


@dataclass
class LLMResponse:
    """A single LLM completion + its accounting info."""

    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        in_cost = (self.input_tokens / 1000.0) * PRICE_PER_1K_INPUT_TOKENS
        out_cost = (self.output_tokens / 1000.0) * PRICE_PER_1K_OUTPUT_TOKENS
        return in_cost + out_cost


class LLMClient(Protocol):
    """The contract the agent calls against. Any implementation must complete()."""

    def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Issue a completion request and return the LLM's response.

        Args:
            system: System message (tool spec, role description)
            messages: Conversation history. Each dict: {'role': 'user'|'assistant', 'content': str}
            max_tokens: Max tokens to generate
            temperature: Sampling temperature (0.0 for determinism)

        Returns:
            LLMResponse with text + accounting.
        """
        ...


# ===================================================================== #
# BedrockClient — real AWS Bedrock                                      #
# ===================================================================== #

# Llama 3.1 8B Instruct via the us-* inference profile (required as of 2025-09).
# Direct on-demand calls to `meta.llama3-1-8b-instruct-v1:0` now return
# ValidationException; must invoke via the inference profile prefix `us.`.
BEDROCK_MODEL_ID = "us.meta.llama3-1-8b-instruct-v1:0"


@dataclass
class BedrockClient:
    """Real Bedrock client. Lazily creates the boto3 client on first use."""

    model_id: str = BEDROCK_MODEL_ID
    region: str = "us-east-1"

    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    _client: Any = field(default=None, init=False, repr=False)

    def _ensure_client(self) -> Any:
        if self._client is None:
            import boto3
            self._client = boto3.client("bedrock-runtime", region_name=self.region)
            logger.info("BedrockClient initialised: model=%s, region=%s",
                        self.model_id, self.region)
        return self._client

    def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> LLMResponse:
        client = self._ensure_client()

        # Bedrock Converse expects messages with 'content' as a list of blocks
        converse_messages = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in messages
        ]

        response = client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=converse_messages,
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        )

        text = response["output"]["message"]["content"][0]["text"]
        usage = response["usage"]
        stop = response["stopReason"]

        self.total_calls += 1
        self.total_input_tokens += usage["inputTokens"]
        self.total_output_tokens += usage["outputTokens"]

        return LLMResponse(
            text=text,
            input_tokens=usage["inputTokens"],
            output_tokens=usage["outputTokens"],
            stop_reason=stop,
        )

    def cost_summary(self) -> str:
        total_cost = (
            (self.total_input_tokens / 1000.0) * PRICE_PER_1K_INPUT_TOKENS
            + (self.total_output_tokens / 1000.0) * PRICE_PER_1K_OUTPUT_TOKENS
        )
        return (
            f"BedrockClient: {self.total_calls} calls, "
            f"{self.total_input_tokens} in tokens, "
            f"{self.total_output_tokens} out tokens, "
            f"${total_cost:.6f} USD"
        )


# ===================================================================== #
# MockClient — canned responses for testing                             #
# ===================================================================== #

@dataclass
class MockClient:
    """Returns pre-scripted responses. For testing the agent loop without LLM calls."""

    responses: list[str]
    _call_index: int = field(default=0, init=False)

    total_calls: int = field(default=0, init=False)
    total_input_tokens: int = field(default=0, init=False)
    total_output_tokens: int = field(default=0, init=False)

    def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> LLMResponse:
        if self._call_index >= len(self.responses):
            raise RuntimeError(
                f"MockClient exhausted: agent made {self._call_index + 1} calls, "
                f"only {len(self.responses)} responses scripted."
            )
        text = self.responses[self._call_index]
        self._call_index += 1

        # Fake token counts proportional to text length (rough)
        in_tokens = sum(len(m["content"]) for m in messages) // 4 + len(system) // 4
        out_tokens = len(text) // 4

        self.total_calls += 1
        self.total_input_tokens += in_tokens
        self.total_output_tokens += out_tokens

        return LLMResponse(
            text=text,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            stop_reason="end_turn",
        )

    def cost_summary(self) -> str:
        return f"MockClient (no real cost): {self.total_calls} canned responses returned"
