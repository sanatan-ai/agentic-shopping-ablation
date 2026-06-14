"""Parser for plan-format LLM output.

Expects JSON with structure:
{
  "plan_summary": "...",
  "plan": [
    {"tool": "...", "args": {...}},
    ...
  ]
}

Returns a list of validated Action objects. Reuses the JSON-extraction logic
from the reactive parser for robustness against markdown fences / leading prose.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from src.agents.parser import ParseError, _extract_json_object, _strip_markdown_fences
from src.environment.models import Action

# Maximum plan length (matches step budget; longer plans get rejected)
MAX_PLAN_ACTIONS = 10


@dataclass
class ParsedPlan:
    plan_summary: str
    actions: list[Action]


def parse_plan(text: str) -> ParsedPlan:
    """Parse a plan-format LLM response into a list of Actions.

    Raises ParseError on any failure.
    """
    raw = text.strip()
    raw = _strip_markdown_fences(raw)
    raw = raw.strip()

    # Try direct parse, fall back to balanced-bracket extraction
    obj = None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        extracted = _extract_json_object(raw)
        if extracted is None:
            raise ParseError(f"No JSON object found in plan output. Got: {text[:200]!r}")
        try:
            obj = json.loads(extracted)
        except json.JSONDecodeError as exc:
            raise ParseError(f"Extracted plan isn't valid JSON: {exc}")

    if not isinstance(obj, dict):
        raise ParseError(f"Parsed plan isn't an object. Got type {type(obj).__name__}")

    plan_summary = str(obj.get("plan_summary", ""))
    plan_raw = obj.get("plan")

    if not isinstance(plan_raw, list):
        raise ParseError(f"'plan' key missing or not a list. Got: {obj!r}")

    if len(plan_raw) == 0:
        raise ParseError("Plan is empty (must contain at least 1 action).")

    if len(plan_raw) > MAX_PLAN_ACTIONS:
        raise ParseError(
            f"Plan too long: {len(plan_raw)} actions, max is {MAX_PLAN_ACTIONS}."
        )

    actions: list[Action] = []
    for i, item in enumerate(plan_raw):
        if not isinstance(item, dict):
            raise ParseError(f"Plan action #{i} is not an object. Got: {item!r}")
        tool = item.get("tool")
        args = item.get("args", {})
        if tool is None:
            raise ParseError(f"Plan action #{i} missing 'tool' key. Got: {item!r}")
        try:
            actions.append(Action(tool=tool, args=args if isinstance(args, dict) else {}))
        except Exception as exc:
            raise ParseError(f"Plan action #{i} schema validation failed: {exc}")

    return ParsedPlan(plan_summary=plan_summary, actions=actions)
