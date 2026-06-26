"""InMemoryStorageBackend tests (T040) — StorageBackend extension point #5."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from tokenhelm.core.models import LLMEvent, LLMProvider
from tokenhelm.storage.base import StorageBackend
from tokenhelm.storage.memory import InMemoryStorageBackend


def _event(model: str = "gpt-4o") -> LLMEvent:
    return LLMEvent(
        provider=LLMProvider.OPENAI,
        model=model,
        input_tokens=1,
        output_tokens=1,
        total_tokens=2,
        latency=0.0,
        cost=Decimal("0"),
        timestamp=datetime.now(UTC),
    )


def test_satisfies_storage_backend_protocol():
    assert isinstance(InMemoryStorageBackend(), StorageBackend)


def test_save_and_all():
    store = InMemoryStorageBackend()
    store.save(_event("a"))
    store.save(_event("b"))

    models = [e.model for e in store.all()]
    assert models == ["a", "b"]


def test_all_returns_a_copy_not_the_backing_list():
    store = InMemoryStorageBackend()
    store.save(_event())

    snapshot = list(store.all())
    store.save(_event())
    assert len(snapshot) == 1  # earlier snapshot unaffected by later save
    assert len(list(store.all())) == 2


def test_len_and_clear():
    store = InMemoryStorageBackend()
    store.save(_event())
    store.save(_event())
    assert len(store) == 2
    store.clear()
    assert len(store) == 0
