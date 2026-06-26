"""End-to-end US1 tests (T018) — quickstart Scenarios 1, 4 (sync scope), 6.

Exercises the full client path: TokenHelm.track() / trace() over a captured OpenAI response,
asserting the normalized event shape, cost, scope collection, and graceful degradation.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from tokenhelm import TokenHelm
from tokenhelm.core.models import LLMProvider
from tokenhelm.sdk.context import active_scope

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


def _silent() -> TokenHelm:
    """A client with no console noise during tests."""
    return TokenHelm(logger=lambda event: None)


def test_single_track_event_shape(openai_response):
    tracker = _silent()
    event = tracker.track(openai_response)

    assert EIGHT_FIELDS <= event.to_dict().keys()
    assert event.provider is LLMProvider.OPENAI
    assert event.model == "gpt-4o"
    assert event.input_tokens == 1000
    assert event.output_tokens == 500
    assert event.total_tokens == 1500
    assert event.total_tokens == event.input_tokens + event.output_tokens
    assert event.usage_complete is True
    assert event.priced is True
    # gpt-4o: $2.5/1M in + $10/1M out -> 1000/1e6*2.5 + 500/1e6*10
    assert event.cost == Decimal("0.0025") + Decimal("0.005")


def test_to_dict_is_json_safe(openai_response):
    import json

    event = _silent().track(openai_response)
    payload = json.dumps(event.to_dict())  # must not raise
    assert "gpt-4o" in payload


def test_scope_collects_events(openai_response):
    tracker = _silent()
    with tracker.trace() as scope:
        scope.track(openai_response)
        scope.track(openai_response)
    assert len(scope.events) == 2
    assert all(e.provider is LLMProvider.OPENAI for e in scope.events)


def test_bare_track_inside_scope_is_attributed(openai_response):
    tracker = _silent()
    with tracker.trace() as scope:
        tracker.track(openai_response)  # bare client.track, no scope.* call
    assert len(scope.events) == 1


def test_scope_latency_is_measured(openai_response):
    tracker = _silent()
    with tracker.trace() as scope:
        event = scope.track(openai_response)
    assert event.latency >= 0.0
    assert event.request is not None and event.request.started_at is not None


def test_unpriced_model_degrades(openai_response):
    """FR-013: model absent from pricing -> priced False, cost 0, no error."""
    resp = SimpleNamespace(object="chat.completion", model="gpt-unknown-9000",
                           usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20,
                                                 total_tokens=30))
    event = _silent().track(resp)
    assert event.priced is False
    assert event.cost == Decimal("0")
    assert event.total_tokens == 30


def test_missing_usage_degrades():
    """FR-013: missing usage -> usage_complete False, no error."""
    resp = SimpleNamespace(object="chat.completion", model="gpt-4o")
    event = _silent().track(resp)
    assert event.usage_complete is False
    assert event.input_tokens is None


# -- trace context isolation (FR-012 / SC-007 foundations) -----------------------------


def test_no_active_scope_outside_trace():
    assert active_scope() is None


def test_scope_cleared_after_exit(openai_response):
    tracker = _silent()
    with tracker.trace() as scope:
        assert active_scope() is scope
    assert active_scope() is None


def test_scope_reset_even_on_exception(openai_response):
    """A raised exception inside the block must not leak the active scope."""
    tracker = _silent()
    with pytest.raises(ValueError):
        with tracker.trace():
            assert active_scope() is not None
            raise ValueError("boom")
    assert active_scope() is None


def test_sequential_scopes_do_not_cross_contaminate(openai_response):
    tracker = _silent()
    with tracker.trace() as first:
        first.track(openai_response)
    with tracker.trace() as second:
        second.track(openai_response)
        second.track(openai_response)
    assert len(first.events) == 1
    assert len(second.events) == 2


def test_nested_scopes_restore_outer(openai_response):
    tracker = _silent()
    with tracker.trace() as outer:
        with tracker.trace() as inner:
            assert active_scope() is inner
            inner.track(openai_response)
        # exiting inner restores outer as the active scope
        assert active_scope() is outer
        outer.track(openai_response)
    assert len(inner.events) == 1
    assert len(outer.events) == 1
