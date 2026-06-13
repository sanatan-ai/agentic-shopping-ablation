"""Parser for LLM JSON output into Thought + Action.

Small open-weight models (Llama 3.1 8B) frequently emit JSON wrapped in
markdown fences or with leading prose. We attempt several extraction strategies
before giving up.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from src.environment.models import Action


class ParseError(Exception):
    """Raised when LLM output cannot be parsed into a valid action."""


@dataclass
class ParsedStep:
    thought: str
    action: Action


# Regex to extract the first JSON object found in text. Handles nested braces
# via balanced-bracket counting since plain regex can't do nesting.
def _extract_json_object(text: str) -> str | None:
    """Find the first balanced { ... } JSON object in the text, if any."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start=start):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` and ``` ... ``` fences if present."""
    # ```json ... ``` or just ``` ... ```
    fence_pattern = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
    m = fence_pattern.search(text)
    if m:
        return m.group(1).strip()
    return text


def parse_llm_output(text: str) -> ParsedStep:
    """Parse a raw LLM response string into a ParsedStep.

    Strategy:
      1. Strip whitespace + markdown fences.
      2. Try to parse the whole thing as JSON.
      3. If that fails, extract the first balanced { ... } and parse it.
      4. Validate keys + types via the Action Pydantic schema.

    Raises ParseError on any failure (caller treats as a malformed action).
    """
    raw = text.strip()
    raw = _strip_markdown_fences(raw)
    raw = raw.strip()

    # Try direct parse
    obj = None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract a balanced JSON object
        extracted = _extract_json_object(raw)
        if extracted is None:
            raise ParseError(f"No JSON object found in LLM output. Got: {text[:200]!r}")
        try:
            obj = json.loads(extracted)
        except json.JSONDecodeError as exc:
            raise ParseError(f"Extracted text isn't valid JSON: {exc}. Extracted: {extracted[:200]!r}")

    if not isinstance(obj, dict):
        raise ParseError(f"Parsed JSON isn't an object. Got: {type(obj).__name__}")

    thought = obj.get("thought", "")
    action_dict = obj.get("action")

    if not isinstance(action_dict, dict):
        raise ParseError(f"'action' key missing or not an object. Got: {obj!r}")

    tool = action_dict.get("tool")
    args = action_dict.get("args", {})

    if tool is None:
        raise ParseError(f"'tool' missing from action. Got: {action_dict!r}")

    try:
        action = Action(tool=tool, args=args if isinstance(args, dict) else {})
    except Exception as exc:
        raise ParseError(f"Action schema validation failed: {exc}")

    return ParsedStep(thought=str(thought), action=action)
