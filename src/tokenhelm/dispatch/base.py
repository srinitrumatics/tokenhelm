"""Extension point #3 — event exporter contract (T008).

The tracker emits one event here and knows nothing about sinks (Decision 4).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..core.models import LLMEvent


@runtime_checkable
class EventDispatcher(Protocol):
    """Route one normalized event to all configured sinks."""

    def dispatch(self, event: LLMEvent) -> None:
        """Deliver ``event`` to every sink. Must not raise on a single sink failure."""
        ...
