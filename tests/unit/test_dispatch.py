"""DefaultEventDispatcher tests (T039) — multi-sink fan-out, isolation, ordering, immutability.

Covers the US3 dispatcher requirements: multiple loggers receive the same event, storage
receives every event, a failing sink does not stop the others, the event is immutable during
dispatch, and ordering is loggers-in-order then storage-in-order.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tokenhelm.core.models import LLMCost, LLMEvent, LLMProvider
from tokenhelm.dispatch.default import DefaultEventDispatcher
from tokenhelm.storage.memory import InMemoryStorageBackend


def _event() -> LLMEvent:
    return LLMEvent(
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        latency=0.01,
        cost=Decimal("0.0075"),
        timestamp=datetime.now(UTC),
        cost_detail=LLMCost(currency="USD"),
    )


def test_multiple_loggers_receive_the_same_event():
    a, b, c = [], [], []
    dispatcher = DefaultEventDispatcher([a.append, b.append, c.append])

    event = _event()
    dispatcher.dispatch(event)

    assert a == [event] and b == [event] and c == [event]
    # Same object identity delivered to every sink (one immutable instance).
    assert a[0] is event and b[0] is event and c[0] is event


def test_storage_receives_every_event():
    store = InMemoryStorageBackend()
    dispatcher = DefaultEventDispatcher([], storage=store)

    for _ in range(3):
        dispatcher.dispatch(_event())

    assert len(list(store.all())) == 3


def test_multiple_storage_backends_all_receive():
    s1, s2 = InMemoryStorageBackend(), InMemoryStorageBackend()
    dispatcher = DefaultEventDispatcher([], storage=[s1, s2])

    dispatcher.dispatch(_event())

    assert len(list(s1.all())) == 1
    assert len(list(s2.all())) == 1


def test_custom_callable_sink():
    received = []
    dispatcher = DefaultEventDispatcher([lambda e: received.append(e.to_dict())])
    dispatcher.dispatch(_event())
    assert received[0]["provider"] == "openai"


def test_logger_failure_does_not_stop_other_sinks():
    good_before, good_after = [], []
    store = InMemoryStorageBackend()

    def boom(event):
        raise RuntimeError("sink down")

    dispatcher = DefaultEventDispatcher(
        [good_before.append, boom, good_after.append], storage=store
    )
    dispatcher.dispatch(_event())  # must not raise

    assert len(good_before) == 1
    assert len(good_after) == 1  # sink after the failing one still ran
    assert len(list(store.all())) == 1  # storage still ran


def test_storage_failure_does_not_stop_logging():
    seen = []

    class BoomStorage:
        def save(self, event):
            raise RuntimeError("disk full")

        def all(self):
            return []

    dispatcher = DefaultEventDispatcher([seen.append], storage=BoomStorage())
    dispatcher.dispatch(_event())
    assert len(seen) == 1


def test_dispatch_ordering_loggers_then_storage_in_registration_order():
    order = []

    class RecordingStorage:
        def __init__(self, tag):
            self.tag = tag

        def save(self, event):
            order.append(self.tag)

        def all(self):
            return []

    dispatcher = DefaultEventDispatcher(
        loggers=[lambda e: order.append("log1"), lambda e: order.append("log2")],
        storage=[RecordingStorage("store1"), RecordingStorage("store2")],
    )
    dispatcher.dispatch(_event())

    assert order == ["log1", "log2", "store1", "store2"]


def test_event_is_immutable_during_dispatch():
    event = _event()

    def mutator(e):
        # A misbehaving sink must not be able to mutate the shared event.
        with pytest.raises(dataclasses.FrozenInstanceError):
            e.model = "tampered"  # type: ignore[misc]

    DefaultEventDispatcher([mutator]).dispatch(event)
    assert event.model == "gpt-4o"
