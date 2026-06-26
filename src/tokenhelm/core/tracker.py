"""Latency measurement and the token tracker (T011, T026).

``LatencyTracker`` is the foundational timing primitive (Phase 2). ``TokenTracker`` (added in
Phase 3 / US1) orchestrates the per-request flow: adapter -> usage -> cost -> event ->
dispatcher. The tracker only ever talks to the :class:`EventDispatcher` (Decision 4).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .models import LLMEvent, LLMProvider, LLMRequest, LLMUsage

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..dispatch.base import EventDispatcher
    from .calculator import CostCalculator
    from .extraction import UsageParser


class LatencyTracker:
    """Context manager measuring wall-clock latency with :func:`time.perf_counter`.

    Usage::

        with LatencyTracker() as lt:
            ...
        lt.elapsed  # seconds (float)
    """

    __slots__ = ("_start", "elapsed")

    def __init__(self) -> None:
        self._start: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> LatencyTracker:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> bool:
        self.elapsed = time.perf_counter() - self._start
        return False

    @staticmethod
    def now() -> float:
        """A monotonic timestamp suitable for diffing into a latency (seconds)."""
        return time.perf_counter()


class TokenTracker:
    """Builds and emits one :class:`LLMEvent` per tracked response (Phase 3 / US1).

    Depends only on abstractions: a :class:`UsageParser` (adapter registry), a
    :class:`CostCalculator`, and an :class:`EventDispatcher`.
    """

    def __init__(
        self,
        registry: UsageParser,
        calculator: CostCalculator,
        dispatcher: EventDispatcher,
    ) -> None:
        self._registry = registry
        self._calculator = calculator
        self._dispatcher = dispatcher

    def track(
        self,
        response: object,
        *,
        scope: _ScopeLike | None = None,
        streamed: bool = False,
    ) -> LLMEvent:
        adapter = self._registry.find(response)
        provider = adapter.provider
        model = adapter.extract_model(response)
        usage = adapter.extract_usage(response)

        latency = 0.0
        if scope is not None:
            latency = max(0.0, LatencyTracker.now() - scope.started_perf)

        return self._emit(provider, model, usage, latency=latency, streamed=streamed, scope=scope)

    def emit_stream(
        self,
        provider: LLMProvider,
        model: str,
        usage: LLMUsage,
        *,
        started_perf: float,
        scope: _ScopeLike | None = None,
        error: str | None = None,
    ) -> LLMEvent:
        """Build and emit the single event for a finished stream (US4).

        The provider/model/usage come from an adapter's :class:`StreamAggregator`; this method
        never inspects chunks. ``error`` (an exception type name) marks an abnormal end while
        still preserving whatever partial usage was aggregated.
        """
        latency = max(0.0, LatencyTracker.now() - started_perf) if started_perf else 0.0
        return self._emit(
            provider, model, usage, latency=latency, streamed=True, scope=scope, error=error
        )

    def _emit(
        self,
        provider: LLMProvider,
        model: str,
        usage: LLMUsage,
        *,
        latency: float,
        streamed: bool,
        scope: _ScopeLike | None,
        error: str | None = None,
    ) -> LLMEvent:
        cost = self._calculator.compute(provider, model, usage)
        started_at = scope.started_at if scope is not None else None
        event = LLMEvent(
            provider=provider,
            model=model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            latency=latency,
            cost=cost.total_cost,
            timestamp=datetime.now(UTC),
            usage_complete=usage.complete,
            priced=cost.priced,
            cost_detail=cost,
            request=LLMRequest(
                provider=provider,
                model=model,
                streamed=streamed,
                started_at=started_at,
                error=error,
            ),
        )
        self._dispatcher.dispatch(event)
        if scope is not None:
            scope.add(event)
        return event


class _ScopeLike:  # pragma: no cover - structural typing helper
    """Structural description of what ``track`` needs from a trace scope."""

    started_perf: float
    started_at: datetime | None

    def add(self, event: LLMEvent) -> None: ...
