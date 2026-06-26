"""The TokenHelm client — public entry point (T027, T045).

Wires the abstractions together: a :class:`PricingProvider` feeds a :class:`CostCalculator`;
an adapter registry feeds a :class:`TokenTracker`; events flow to an :class:`EventDispatcher`
built from the configured logger(s) + optional storage. The tracker only ever talks to the
dispatcher (Decision 4), and the calculator only ever talks to the pricing interface
(Decision 3).

The constructor and :meth:`configure` share one knob set — ``logger``, ``pricing``,
``dispatcher``, ``storage``, ``adapters``, ``currency`` — so the public surface stays stable as
new sinks, pricing sources, and provider adapters are added (no signature churn). Future
Analytics / FinOps / Dashboard modules plug in as custom adapters, pricing providers,
dispatchers, loggers, or storage backends behind these existing interfaces.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from ..adapters import default_adapters
from ..adapters.base import BaseAdapter
from ..core.calculator import CostCalculator
from ..core.config import DEFAULT_CURRENCY
from ..core.extraction import UsageParser
from ..core.models import LLMEvent
from ..core.tracker import TokenTracker
from ..dispatch.base import EventDispatcher
from ..dispatch.default import DefaultEventDispatcher
from ..logging.base import Logger
from ..logging.console import ConsoleLogger
from ..pricing.base import PricingProvider
from ..pricing.yaml_provider import YamlPricingProvider
from ..storage.base import StorageBackend
from .context import StreamSession, TraceScope, active_scope

LoggerLike = Logger | Callable[[LLMEvent], None]
LoggerArg = LoggerLike | Iterable[LoggerLike] | None
PricingArg = PricingProvider | str | Path | dict | None
StorageArg = StorageBackend | Iterable[StorageBackend] | None
AdaptersArg = Iterable[BaseAdapter] | None

_UNSET = object()


class TokenHelm:
    """Track token usage and compute LLM cost across providers (FR-001)."""

    def __init__(
        self,
        *,
        logger: LoggerArg = None,
        pricing: PricingArg = None,
        dispatcher: EventDispatcher | None = None,
        storage: StorageArg = None,
        adapters: AdaptersArg = None,
        currency: str = DEFAULT_CURRENCY,
    ) -> None:
        # Remember the raw knobs so configure() can change one without dropping the others.
        self._logger_arg: LoggerArg = logger
        self._pricing_arg: PricingArg = pricing
        self._dispatcher_arg: EventDispatcher | None = dispatcher
        self._storage_arg: StorageArg = storage
        self._adapters_arg: AdaptersArg = adapters
        self._currency = currency
        self._rebuild()

    # -- configuration ----------------------------------------------------------------

    def configure(
        self,
        *,
        logger: object = _UNSET,
        pricing: object = _UNSET,
        dispatcher: object = _UNSET,
        storage: object = _UNSET,
        adapters: object = _UNSET,
        currency: object = _UNSET,
    ) -> None:
        """Reconfigure post-construction. Only the arguments you pass change; the rest are
        preserved (FR-005 pricing configurable; FR-010 logger selectable)."""
        if logger is not _UNSET:
            self._logger_arg = logger  # type: ignore[assignment]
        if pricing is not _UNSET:
            self._pricing_arg = pricing  # type: ignore[assignment]
        if dispatcher is not _UNSET:
            self._dispatcher_arg = dispatcher  # type: ignore[assignment]
        if storage is not _UNSET:
            self._storage_arg = storage  # type: ignore[assignment]
        if adapters is not _UNSET:
            self._adapters_arg = adapters  # type: ignore[assignment]
        if currency is not _UNSET:
            self._currency = currency  # type: ignore[assignment]
        self._rebuild()

    def _rebuild(self) -> None:
        self._registry = UsageParser(self._coerce_adapters(self._adapters_arg))
        self._pricing = self._coerce_pricing(self._pricing_arg)
        self._calculator = CostCalculator(self._pricing, self._currency)
        # An explicit dispatcher replaces the whole pipeline; otherwise build the default
        # from logger(s) + storage (Decision 4).
        self._dispatcher: EventDispatcher = self._dispatcher_arg or DefaultEventDispatcher(
            self._coerce_loggers(self._logger_arg), self._storage_arg
        )
        self._tracker = TokenTracker(self._registry, self._calculator, self._dispatcher)

    @staticmethod
    def _coerce_adapters(adapters: AdaptersArg) -> list[BaseAdapter]:
        # None -> built-in set; an explicit iterable replaces it (prepend default_adapters()
        # yourself to extend rather than replace).
        return default_adapters() if adapters is None else list(adapters)

    @staticmethod
    def _coerce_pricing(pricing: PricingArg) -> PricingProvider:
        if pricing is None:
            return YamlPricingProvider()
        if isinstance(pricing, (str, Path)):
            return YamlPricingProvider(path=pricing)
        if isinstance(pricing, dict):
            return YamlPricingProvider(overrides=pricing)
        return pricing  # already a PricingProvider

    @staticmethod
    def _coerce_loggers(logger: LoggerArg) -> list[LoggerLike]:
        if logger is None:
            return [ConsoleLogger()]
        if isinstance(logger, (list, tuple)):
            return list(logger)
        return [logger]

    # -- tracking ---------------------------------------------------------------------

    def track(self, response: object) -> LLMEvent:
        """Manually track a completed response (FR-007). Attributes to the active scope."""
        return self._tracker.track(response, scope=active_scope())

    def trace(self) -> TraceScope:
        """Open a scoped tracking block (FR-006). Usable as ``with`` or ``async with``."""
        return TraceScope(self._tracker)

    def track_stream(self, stream: object | None = None) -> StreamSession:
        """Track a streamed response, emitting exactly one event on finalization (FR-008).

        Pass a provider stream to wrap-iterate it (``for``/``async for``), or call with no
        argument and use it as a ``with``/``async with`` block, feeding chunks via
        ``session.consume(chunk)``. Provider-specific aggregation lives entirely in the
        adapter; this client method is provider-agnostic.
        """
        return StreamSession(self._tracker, self._registry, stream=stream)

    @property
    def currency(self) -> str:
        return self._currency
