"""Noise injector middleware.

Wraps tool calls to inject failures or observation corruption at probability p.
Critically: the noise injector is seeded so that the same (task, seed, p) cell
produces statistically identical noise patterns for both architectures, which
is what makes the robustness comparison fair.
"""
from __future__ import annotations

import logging
import random
from copy import deepcopy

from src.environment.models import Observation, Product

logger = logging.getLogger(__name__)


# Corruption bounds (locked during proposal design)
PRICE_PERTURB_PCT = 0.10      # ±10% on price
STARS_PERTURB = 0.3           # ±0.3 on stars
REVIEWS_PERTURB_PCT = 0.05    # ±5% on reviews


class NoiseInjector:
    """Middleware that may perturb an Observation before returning it to the agent.

    At each invocation, with probability `p`, applies one of two failure modes
    chosen with equal probability:
      (a) returns an error Observation simulating a transient tool failure;
      (b) returns a corrupted Observation with numeric fields perturbed.

    With probability 1 - p, returns the Observation untouched.
    """

    def __init__(self, p: float, rng: random.Random):
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"Noise probability p must be in [0, 1], got {p}")
        self.p = p
        self.rng = rng

    def maybe_perturb(self, obs: Observation) -> Observation:
        """Apply noise to an observation, or return it unchanged.

        Noise is never applied to terminal observations — those are the agent's
        final commitment and must propagate cleanly for scoring.
        """
        if obs.status == "terminal":
            return obs

        if self.p == 0.0:
            return obs

        if self.rng.random() >= self.p:
            return obs

        # Noise triggered — choose failure mode with equal probability
        if self.rng.random() < 0.5:
            return self._inject_error()
        else:
            return self._corrupt(obs)

    def _inject_error(self) -> Observation:
        """Return a structured error observation simulating transient tool failure."""
        return Observation(
            status="error",
            error_code="transient_failure",
            error_message="Transient tool failure. Retry or use a different approach.",
        )

    def _corrupt(self, obs: Observation) -> Observation:
        """Return a deep-copied observation with numeric product attrs perturbed.

        Only perturbs successful observations (status='ok') with non-empty products.
        Falls back to passthrough if there's nothing to corrupt.
        """
        if obs.status != "ok" or not obs.products:
            return obs

        out = deepcopy(obs)
        for product in out.products:
            product.price = self._perturb_price(product.price)
            product.stars = self._perturb_stars(product.stars)
            product.reviews = self._perturb_reviews(product.reviews)
        return out

    def _perturb_price(self, price: float) -> float:
        delta = self.rng.uniform(-PRICE_PERTURB_PCT, PRICE_PERTURB_PCT)
        return round(max(0.01, price * (1.0 + delta)), 2)

    def _perturb_stars(self, stars: float) -> float:
        delta = self.rng.uniform(-STARS_PERTURB, STARS_PERTURB)
        return round(max(0.0, min(5.0, stars + delta)), 1)

    def _perturb_reviews(self, reviews: int) -> int:
        if reviews == 0:
            return 0
        delta = self.rng.uniform(-REVIEWS_PERTURB_PCT, REVIEWS_PERTURB_PCT)
        return max(0, int(round(reviews * (1.0 + delta))))
