"""InMemoryStorageBackend — default StorageBackend (T044).

The v0.1 persistence implementation: appends events to an in-memory list. Future backends
(SQLite/PostgreSQL/Redis/remote) implement the same :class:`StorageBackend` interface, so the
dispatcher and client never change to support them.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..core.models import LLMEvent


class InMemoryStorageBackend:
    """Store events in a list; read them back via :meth:`all`."""

    def __init__(self) -> None:
        self._events: list[LLMEvent] = []

    def save(self, event: LLMEvent) -> None:
        self._events.append(event)

    def all(self) -> Iterable[LLMEvent]:
        # Return a copy so callers cannot mutate the backing store.
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)
