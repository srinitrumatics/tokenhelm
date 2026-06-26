"""Client configuration / wiring tests (T041) — __init__ + configure() public surface.

Verifies the stable knob set (logger / pricing / dispatcher / storage / adapters / currency),
including custom adapter registration (extension point #1) and configure() preserving the
arguments you don't pass.
"""

from __future__ import annotations

from decimal import Decimal

from tokenhelm import (
    ConsoleLogger,
    DefaultEventDispatcher,
    InMemoryStorageBackend,
    JSONLogger,
    TokenHelm,
    YamlPricingProvider,
)
from tokenhelm.adapters import default_adapters
from tokenhelm.adapters.base import BaseAdapter
from tokenhelm.core.models import LLMEvent, LLMProvider, LLMUsage


def test_accepts_pricing_provider_instance(openai_response):
    provider = YamlPricingProvider(overrides={"openai": {"gpt-4o": {"input": 1.0, "output": 1.0}}})
    tracker = TokenHelm(logger=lambda e: None, pricing=provider)
    event = tracker.track(openai_response)
    assert event.cost == Decimal("0.001") + Decimal("0.0005")  # 1000/1e6 + 500/1e6


def test_accepts_logger_list_and_callable(openai_response):
    a, b = [], []
    tracker = TokenHelm(logger=[ConsoleLogger(), a.append, b.append])
    tracker.track(openai_response)
    assert len(a) == 1 and len(b) == 1


def test_multi_sink_dispatcher_example(openai_response):
    """The reviewer's example: many loggers + storage at once, all receive one event."""
    store = InMemoryStorageBackend()
    captured: list[LLMEvent] = []
    dispatcher = DefaultEventDispatcher(
        loggers=[JSONLogger(stream=_DevNull()), captured.append],
        storage=store,
    )
    tracker = TokenHelm(dispatcher=dispatcher)
    tracker.track(openai_response)

    assert len(captured) == 1
    assert len(list(store.all())) == 1


class _DevNull:
    def write(self, *_a):  # swallow JSONLogger output in tests
        pass

    def flush(self):
        pass


# -- custom adapter registration (extension point #1) ----------------------------------


class _FakeProviderAdapter(BaseAdapter):
    """A plugin-style adapter for a hypothetical response object."""

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENAI

    def identify(self, response: object) -> bool:
        return getattr(response, "_fake", False) is True

    def extract_model(self, response: object) -> str:
        return "fake-model"

    def extract_usage(self, response: object) -> LLMUsage:
        return LLMUsage(input_tokens=7, output_tokens=3)


def test_custom_adapters_replace_defaults():
    from types import SimpleNamespace

    tracker = TokenHelm(logger=lambda e: None, adapters=[_FakeProviderAdapter()])
    event = tracker.track(SimpleNamespace(_fake=True))
    assert event.model == "fake-model"
    assert event.input_tokens == 7


def test_extend_defaults_by_prepending_default_adapters(openai_response):
    from types import SimpleNamespace

    tracker = TokenHelm(
        logger=lambda e: None,
        adapters=[*default_adapters(), _FakeProviderAdapter()],
    )
    # Built-ins still work...
    assert tracker.track(openai_response).model == "gpt-4o"
    # ...and the custom adapter is also registered.
    assert tracker.track(SimpleNamespace(_fake=True)).model == "fake-model"


# -- configure() wiring ----------------------------------------------------------------


def test_configure_changes_currency_only(openai_response):
    tracker = TokenHelm(logger=lambda e: None)
    tracker.configure(currency="EUR")
    assert tracker.currency == "EUR"
    assert tracker.track(openai_response).currency == "EUR"


def test_configure_preserves_unspecified_args(openai_response):
    """Changing currency must NOT drop a previously configured storage backend."""
    store = InMemoryStorageBackend()
    tracker = TokenHelm(logger=lambda e: None, storage=store)
    tracker.configure(currency="GBP")  # storage not mentioned -> preserved

    tracker.track(openai_response)
    assert len(list(store.all())) == 1
    assert tracker.currency == "GBP"


def test_configure_swaps_logger(openai_response):
    first, second = [], []
    tracker = TokenHelm(logger=first.append)
    tracker.configure(logger=second.append)
    tracker.track(openai_response)
    assert len(first) == 0 and len(second) == 1


def test_configure_swaps_adapters():
    from types import SimpleNamespace

    tracker = TokenHelm(logger=lambda e: None)
    tracker.configure(adapters=[_FakeProviderAdapter()])
    event = tracker.track(SimpleNamespace(_fake=True))
    assert event.model == "fake-model"
