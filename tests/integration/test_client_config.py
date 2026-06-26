"""Client construction + reconfiguration tests (T027 coverage) — FR-005/FR-010, Decision 3/4."""

from __future__ import annotations

from decimal import Decimal

from tokenhelm import ConsoleLogger, DefaultEventDispatcher, TokenHelm
from tokenhelm.core.models import LLMEvent


class ListStorage:
    def __init__(self) -> None:
        self.events: list[LLMEvent] = []

    def save(self, event: LLMEvent) -> None:
        self.events.append(event)

    def all(self):
        return list(self.events)


def test_storage_receives_event(openai_response):
    store = ListStorage()
    tracker = TokenHelm(logger=lambda e: None, storage=store)
    tracker.track(openai_response)
    assert len(store.all()) == 1


def test_multiple_loggers_all_receive(openai_response):
    a: list[LLMEvent] = []
    b: list[LLMEvent] = []
    tracker = TokenHelm(logger=[a.append, b.append])
    tracker.track(openai_response)
    assert len(a) == 1 and len(b) == 1


def test_dict_pricing_override_applied(openai_response):
    tracker = TokenHelm(
        logger=lambda e: None,
        pricing={"openai": {"gpt-4o": {"input": 100.0, "output": 100.0}}},
    )
    event = tracker.track(openai_response)
    # 1000/1e6*100 + 500/1e6*100
    assert event.cost == Decimal("0.1") + Decimal("0.05")


def test_explicit_dispatcher_overrides_logger(openai_response):
    seen: list[LLMEvent] = []
    dispatcher = DefaultEventDispatcher([seen.append])
    tracker = TokenHelm(dispatcher=dispatcher)
    tracker.track(openai_response)
    assert len(seen) == 1


def test_configure_changes_currency(openai_response):
    tracker = TokenHelm(logger=lambda e: None)
    tracker.configure(currency="EUR")
    event = tracker.track(openai_response)
    assert event.currency == "EUR"


def test_configure_swaps_logger(openai_response):
    first: list[LLMEvent] = []
    tracker = TokenHelm(logger=first.append)
    second: list[LLMEvent] = []
    tracker.configure(logger=second.append)
    tracker.track(openai_response)
    assert len(first) == 0
    assert len(second) == 1


def test_default_logger_is_console(capsys, openai_response):
    tracker = TokenHelm()  # zero-config -> ConsoleLogger
    tracker.track(openai_response)
    captured = capsys.readouterr()
    assert "[tokenhelm]" in captured.out
    assert isinstance(ConsoleLogger(), ConsoleLogger)
