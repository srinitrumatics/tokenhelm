"""Extension point #4 — output mechanism contract (T009, FR-010).

Any object with a ``log(event)`` method, or any ``Callable[[LLMEvent], None]``, qualifies as
a logger. The default dispatcher accepts both forms.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..core.models import LLMEvent


@runtime_checkable
class Logger(Protocol):
    """Record or forward a normalized event."""

    def log(self, event: LLMEvent) -> None:
        """Handle one event (write, forward, aggregate, ...)."""
        ...
