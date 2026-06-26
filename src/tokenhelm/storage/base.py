"""Extension point #5 — persistence contract (T010).

Optional persistence of normalized events; off by default. Future impls (SQLite/file/remote)
sit behind this same interface.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from ..core.models import LLMEvent


@runtime_checkable
class StorageBackend(Protocol):
    """Persist and read back normalized events."""

    def save(self, event: LLMEvent) -> None:
        """Persist one event."""
        ...

    def all(self) -> Iterable[LLMEvent]:
        """Read back stored events (basic query affordance)."""
        ...
