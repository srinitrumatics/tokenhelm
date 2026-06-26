"""Scoped + streaming tracking via context-local state (T027, T049, T051).

A :class:`TraceScope` isolates the events tracked within a ``with``/``async with``
``tracker.trace()`` block. The active scope is stored in a :class:`contextvars.ContextVar`,
which is both thread-safe and asyncio-safe — each thread and each asyncio task gets its own
view, so concurrent and nested traces never cross-contaminate (FR-012, SC-007).

A :class:`StreamSession` (``tracker.track_stream``) wraps a streamed response. It delegates all
provider-specific chunk parsing to the recognized adapter's :class:`StreamAggregator` and emits
**exactly one** immutable :class:`LLMEvent` when the stream finalizes — never a partial event.
The same object supports both sync and async use (wrap-iteration or manual ``consume``), so
there is a single programming model across sync and async.
"""

from __future__ import annotations

import contextvars
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from ..core.models import LLMEvent
from ..core.tracker import LatencyTracker

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..core.extraction import UsageParser
    from ..core.tracker import TokenTracker

_active_scope: contextvars.ContextVar[TraceScope | None] = contextvars.ContextVar(
    "tokenhelm_active_scope", default=None
)


def active_scope() -> TraceScope | None:
    """The trace scope active in the current context, if any."""
    return _active_scope.get()


def _error_name(exc: BaseException | None) -> str | None:
    """Exception type name to record on the event, or None for a clean / early-stop end.

    ``GeneratorExit`` (consumer stopped iterating early) is treated as a clean stop — the
    event still carries whatever partial usage was aggregated, flagged via ``usage_complete``.
    """
    if exc is None or isinstance(exc, GeneratorExit):
        return None
    return type(exc).__name__


class TraceScope:
    """Collects the events tracked inside a ``with``/``async with`` trace block."""

    def __init__(self, tracker: TokenTracker) -> None:
        self._tracker = tracker
        self.events: list[LLMEvent] = []
        self.started_perf: float = 0.0
        self.started_at: datetime | None = None
        self._token: contextvars.Token | None = None

    def _enter(self) -> TraceScope:
        self.started_perf = LatencyTracker.now()
        self.started_at = datetime.now(UTC)
        self._token = _active_scope.set(self)
        return self

    def _exit(self) -> None:
        if self._token is not None:
            _active_scope.reset(self._token)
            self._token = None

    # sync context manager
    def __enter__(self) -> TraceScope:
        return self._enter()

    def __exit__(self, *exc: object) -> bool:
        self._exit()
        return False

    # async context manager — mirrors the sync API (no separate programming model)
    async def __aenter__(self) -> TraceScope:
        return self._enter()

    async def __aexit__(self, *exc: object) -> bool:
        self._exit()
        return False

    def track(self, response: object) -> LLMEvent:
        """Track a response and attribute it to this scope."""
        return self._tracker.track(response, scope=self)

    def add(self, event: LLMEvent) -> None:
        self.events.append(event)


class StreamSession:
    """Tracks a streamed response and emits exactly one event on finalization (US4).

    Lifecycle: start -> consume chunks (adapter aggregates) -> finalize -> emit one event.
    Usable four ways, all single-emit and scope-aware:

    - sync wrap:    ``for chunk in tracker.track_stream(stream): ...``
    - async wrap:   ``async for chunk in tracker.track_stream(astream): ...``
    - sync manual:  ``with tracker.track_stream() as s: s.consume(chunk)``
    - async manual: ``async with tracker.track_stream() as s: s.consume(chunk)``
    """

    def __init__(
        self,
        tracker: TokenTracker,
        registry: UsageParser,
        *,
        stream: object | None = None,
    ) -> None:
        self._tracker = tracker
        self._registry = registry
        self._raw = stream
        self._adapter = None
        self._aggregator = None
        self._scope: TraceScope | None = None
        self._started: float = 0.0
        self._finalized = False
        self._event: LLMEvent | None = None

    @property
    def event(self) -> LLMEvent | None:
        """The emitted event (available after the stream finalizes)."""
        return self._event

    def consume(self, chunk: object) -> object:
        """Feed one provider chunk to the adapter aggregator; returns the chunk unchanged."""
        if self._aggregator is None:
            self._adapter = self._registry.find_stream(chunk)
            self._aggregator = self._adapter.new_stream_aggregator()
        self._aggregator.consume(chunk)
        return chunk

    # -- lifecycle --------------------------------------------------------------------

    def _start(self) -> None:
        # Capture the active trace scope at start so the final event is attributed to it.
        self._scope = active_scope()
        self._started = LatencyTracker.now()

    def _finalize(self, exc: BaseException | None = None) -> LLMEvent | None:
        if self._finalized:
            return self._event  # idempotent — never emit twice
        self._finalized = True
        if self._aggregator is None or self._adapter is None:
            return None  # nothing was consumed -> no event
        usage = self._aggregator.usage()
        model = self._aggregator.model()
        self._event = self._tracker.emit_stream(
            self._adapter.provider,
            model,
            usage,
            started_perf=self._started,
            scope=self._scope,
            error=_error_name(exc),
        )
        return self._event

    # sync context manager (manual consume)
    def __enter__(self) -> StreamSession:
        self._start()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._finalize(exc)
        return False

    # async context manager (manual consume)
    async def __aenter__(self) -> StreamSession:
        self._start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        self._finalize(exc)
        return False

    # sync wrap-iteration
    def __iter__(self):
        if self._raw is None:
            raise TypeError("track_stream() has no stream to iterate; use it as a context manager")
        self._start()
        try:
            for chunk in self._raw:  # type: ignore[union-attr]
                yield self.consume(chunk)
        except BaseException as exc:  # noqa: BLE001 - finalize on any termination, then re-raise
            self._finalize(exc)
            raise
        else:
            self._finalize()

    # async wrap-iteration
    async def __aiter__(self):
        if self._raw is None:
            raise TypeError("track_stream() has no stream to iterate; use it as a context manager")
        self._start()
        try:
            async for chunk in self._raw:  # type: ignore[union-attr]
                yield self.consume(chunk)
        except BaseException as exc:  # noqa: BLE001 - includes CancelledError; finalize then re-raise
            self._finalize(exc)
            raise
        else:
            self._finalize()
