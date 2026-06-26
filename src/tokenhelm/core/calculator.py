"""Cost calculation and currency formatting (T021).

``CostCalculator`` depends ONLY on the :class:`PricingProvider` interface (Decision 3). A
``None`` rate lookup yields an unpriced ``LLMCost`` (``priced=False``, zero cost) — never an
error (FR-013).
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from .config import DEFAULT_CURRENCY
from .models import LLMCost, LLMProvider, LLMUsage

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..pricing.base import PricingProvider

_PER_MILLION = Decimal(1_000_000)


class CostCalculator:
    """Compute :class:`LLMCost` from usage + a pricing source."""

    def __init__(self, pricing: PricingProvider, currency: str = DEFAULT_CURRENCY) -> None:
        self._pricing = pricing
        self.currency = currency

    def compute(self, provider: LLMProvider, model: str, usage: LLMUsage) -> LLMCost:
        rate = self._pricing.get_rates(provider, model)
        if rate is None:
            return LLMCost(currency=self.currency, priced=False)

        input_tokens = usage.input_tokens or 0
        output_tokens = usage.output_tokens or 0
        input_cost = (Decimal(input_tokens) / _PER_MILLION) * rate.input_rate
        output_cost = (Decimal(output_tokens) / _PER_MILLION) * rate.output_rate
        return LLMCost(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            currency=self.currency,
            priced=True,
        )


class CurrencyFormatter:
    """Human-readable money formatting for loggers/CLI output."""

    _SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}

    def __init__(self, currency: str = DEFAULT_CURRENCY, *, places: int = 6) -> None:
        self.currency = currency
        self.places = places

    def format(self, amount: Decimal) -> str:
        symbol = self._SYMBOLS.get(self.currency, "")
        value = f"{amount:.{self.places}f}"
        if symbol:
            return f"{symbol}{value}"
        return f"{value} {self.currency}"
