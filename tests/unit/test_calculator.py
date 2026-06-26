"""CostCalculator tests (T014) — FR-004, FR-013, Decision 3."""

from __future__ import annotations

from decimal import Decimal

from tokenhelm.core.calculator import CostCalculator, CurrencyFormatter
from tokenhelm.core.models import LLMProvider, LLMUsage, RateEntry


class StubPricing:
    """A PricingProvider stub — proves CostCalculator depends only on the interface."""

    def __init__(self, entry: RateEntry | None) -> None:
        self._entry = entry

    def get_rates(self, provider: LLMProvider, model: str) -> RateEntry | None:
        return self._entry


def test_compute_input_output_total():
    entry = RateEntry(LLMProvider.OPENAI, "gpt-4o", Decimal("2.5"), Decimal("10.0"))
    calc = CostCalculator(StubPricing(entry))

    cost = calc.compute(LLMProvider.OPENAI, "gpt-4o", LLMUsage(1_000_000, 500_000))

    assert cost.priced is True
    assert cost.input_cost == Decimal("2.5")  # 1M tokens * $2.5/1M
    assert cost.output_cost == Decimal("5.0")  # 0.5M tokens * $10/1M
    assert cost.total_cost == Decimal("7.5")
    assert cost.currency == "USD"


def test_compute_uses_decimal_no_float_drift():
    entry = RateEntry(LLMProvider.OPENAI, "gpt-4o", Decimal("0.15"), Decimal("0.6"))
    calc = CostCalculator(StubPricing(entry))

    cost = calc.compute(LLMProvider.OPENAI, "gpt-4o", LLMUsage(1234, 567))

    assert isinstance(cost.total_cost, Decimal)
    expected = (Decimal(1234) / Decimal(1_000_000) * Decimal("0.15")) + (
        Decimal(567) / Decimal(1_000_000) * Decimal("0.6")
    )
    assert cost.total_cost == expected


def test_unpriced_model():
    """FR-013: unknown model -> priced=False, cost 0, no error."""
    calc = CostCalculator(StubPricing(None))

    cost = calc.compute(LLMProvider.OPENAI, "mystery-model", LLMUsage(10, 20))

    assert cost.priced is False
    assert cost.total_cost == Decimal("0")


def test_zero_rate_local_model_no_error():
    """Edge case: zero-rate (local) model yields cost 0 without error."""
    entry = RateEntry(LLMProvider.OLLAMA, "llama3.3", Decimal("0"), Decimal("0"))
    calc = CostCalculator(StubPricing(entry))

    cost = calc.compute(LLMProvider.OLLAMA, "llama3.3", LLMUsage(100, 200))

    assert cost.priced is True
    assert cost.total_cost == Decimal("0")


def test_partial_usage_does_not_crash():
    entry = RateEntry(LLMProvider.OPENAI, "gpt-4o", Decimal("2.5"), Decimal("10.0"))
    calc = CostCalculator(StubPricing(entry))

    cost = calc.compute(LLMProvider.OPENAI, "gpt-4o", LLMUsage(input_tokens=1_000_000))

    assert cost.input_cost == Decimal("2.5")
    assert cost.output_cost == Decimal("0")


def test_currency_passthrough():
    entry = RateEntry(LLMProvider.OPENAI, "gpt-4o", Decimal("2.5"), Decimal("10.0"))
    calc = CostCalculator(StubPricing(entry), currency="EUR")

    cost = calc.compute(LLMProvider.OPENAI, "gpt-4o", LLMUsage(1, 1))

    assert cost.currency == "EUR"


def test_currency_formatter_symbol_and_fallback():
    assert CurrencyFormatter("USD", places=2).format(Decimal("7.5")) == "$7.50"
    assert CurrencyFormatter("XYZ", places=2).format(Decimal("7.5")) == "7.50 XYZ"


def test_decimal_precision_is_exact_not_float():
    """3 tokens at $0.15/1M = exactly 0.00000045 — a value float cannot represent."""
    entry = RateEntry(LLMProvider.OPENAI, "gpt-4o-mini", Decimal("0.15"), Decimal("0.6"))
    calc = CostCalculator(StubPricing(entry))

    cost = calc.compute(LLMProvider.OPENAI, "gpt-4o-mini", LLMUsage(3, 0))

    assert cost.input_cost == Decimal("0.00000045")
    # The naive float computation differs — proving we are not silently using floats.
    assert cost.input_cost != Decimal(3 / 1_000_000 * 0.15)


def test_total_cost_equals_sum_exactly():
    entry = RateEntry(LLMProvider.ANTHROPIC, "claude-opus-4-8", Decimal("5"), Decimal("25"))
    calc = CostCalculator(StubPricing(entry))

    cost = calc.compute(LLMProvider.ANTHROPIC, "claude-opus-4-8", LLMUsage(333_333, 777_777))

    assert cost.total_cost == cost.input_cost + cost.output_cost
    assert isinstance(cost.total_cost, Decimal)
