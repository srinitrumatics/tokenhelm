"""Provider-parity integration tests (T032) — US2, SC-004.

The same tracking workflow runs against all four providers and yields events of identical
shape; switching providers is configuration only (here: just a different response object).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from tokenhelm import TokenHelm
from tokenhelm.core.models import LLMProvider

EIGHT_FIELDS = {
    "provider",
    "model",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "latency",
    "cost",
    "timestamp",
}

ALL_FIXTURES = ("openai_response", "anthropic_response", "gemini_response", "ollama_response")


def _silent() -> TokenHelm:
    return TokenHelm(logger=lambda event: None)


@pytest.mark.parametrize("fixture_name", ALL_FIXTURES)
def test_each_provider_yields_full_event_shape(fixture_name, request):
    response = request.getfixturevalue(fixture_name)
    event = _silent().track(response)

    assert EIGHT_FIELDS <= event.to_dict().keys()
    assert event.input_tokens == 1000
    assert event.output_tokens == 500
    assert event.total_tokens == 1500
    assert event.usage_complete is True


def test_provider_switch_identical_shape(
    openai_response, anthropic_response, gemini_response, ollama_response
):
    tracker = _silent()
    events = [
        tracker.track(openai_response),
        tracker.track(anthropic_response),
        tracker.track(gemini_response),
        tracker.track(ollama_response),
    ]

    # Identical key sets across every provider.
    shapes = {frozenset(e.to_dict().keys()) for e in events}
    assert len(shapes) == 1

    # Provider field differs and is correctly attributed.
    assert [e.provider for e in events] == [
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.GEMINI,
        LLMProvider.OLLAMA,
    ]


def test_priced_from_own_rates(openai_response, anthropic_response, gemini_response):
    tracker = _silent()
    # gpt-4o: 1000/1e6*2.5 + 500/1e6*10
    assert tracker.track(openai_response).cost == Decimal("0.0025") + Decimal("0.005")
    # claude-opus-4-8: 1000/1e6*5 + 500/1e6*25
    assert tracker.track(anthropic_response).cost == Decimal("0.005") + Decimal("0.0125")
    # gemini-2.5-pro: 1000/1e6*1.25 + 500/1e6*10
    assert tracker.track(gemini_response).cost == Decimal("0.00125") + Decimal("0.005")


def test_ollama_zero_rate_cost_is_zero_without_error(ollama_response):
    """Edge case: local zero-rate model yields cost == 0, priced True, no error."""
    event = _silent().track(ollama_response)
    assert event.cost == Decimal("0")
    assert event.priced is True  # llama3.3 is listed at 0/0 in bundled pricing
    assert event.provider is LLMProvider.OLLAMA


def test_unlisted_ollama_model_is_unpriced(ollama_response):
    from types import SimpleNamespace

    resp = SimpleNamespace(model="some-random-local-model", done=True,
                           prompt_eval_count=10, eval_count=20)
    event = _silent().track(resp)
    assert event.provider is LLMProvider.OLLAMA
    assert event.priced is False
    assert event.cost == Decimal("0")
