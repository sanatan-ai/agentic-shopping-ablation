"""Oracle agent — cheats by knowing the task's ground truth.

This is NOT a real agent. It exists solely to sanity-check the environment:
- Hand-crafts a sequence of valid tool calls
- Uses the task's ground truth to purchase the optimal product
- Expected outcome: 100% Hard Success and 100% Preference Success on noise=0

If the oracle scores less than 100%, there is a bug in the environment,
not the agent.
"""
from __future__ import annotations

import logging

from src.environment.environment import Environment
from src.environment.models import Action
from src.task_suite.models import Task

logger = logging.getLogger(__name__)


def run_oracle_episode(env: Environment, task: Task) -> str | None:
    """Run a single oracle episode against the given task on the given environment.

    The oracle:
      1. searches with the bucket display name to verify search works
      2. compares the valid set products to verify compare works
      3. purchases an optimal product

    Returns:
        The purchased ASIN, or None if termination was abnormal.
    """
    env.reset()

    # Step 1: search (to verify the search tool works in the pipeline)
    obs = env.step(Action(tool="search", args={"query": task.bucket}))
    if obs.status == "terminal":
        return None

    # Step 2: compare a small subset of valid products (verify compare tool)
    sample_for_compare = task.valid_set[: min(3, len(task.valid_set))]
    if len(sample_for_compare) >= 2:
        obs = env.step(Action(tool="compare", args={"product_ids": sample_for_compare}))
        if obs.status == "terminal":
            return None

    # Step 3: get details of the optimal product (verify get_details)
    optimal = task.optimal_asins[0]
    obs = env.step(Action(tool="get_details", args={"product_id": optimal}))
    if obs.status == "terminal":
        return None

    # Step 4: purchase the optimal product (terminal)
    obs = env.step(Action(tool="purchase", args={"product_id": optimal}))
    if obs.status == "terminal" and obs.terminal_reason == "purchased":
        return obs.purchased_asin
    return None
