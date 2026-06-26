"""Extension point #2 — pricing source contract (T007).

``CostCalculator`` depends only on this interface (Decision 3), never on a concrete source.
A ``None`` result means the model is unpriced.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..core.models import LLMProvider, RateEntry


@runtime_checkable
class PricingProvider(Protocol):
    """Resolve per-1M-token rates for a (provider, model) pair."""

    def get_rates(self, provider: LLMProvider, model: str) -> RateEntry | None:
        """Return the :class:`RateEntry` for the pair, or ``None`` if unpriced."""
        ...
