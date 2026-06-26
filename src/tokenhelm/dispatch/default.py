"""DefaultEventDispatcher — fan one event out to many sinks (T023, T045).

The tracker emits exactly one immutable :class:`LLMEvent` here and is unaware of where it
goes (Decision 4). The dispatcher fans that single instance out to every configured sink.

Ordering guarantee: loggers receive the event first, in registration order; then storage
backends, in registration order. The *same* immutable event object is delivered to all sinks.

Isolation guarantee: a sink that raises does not stop delivery to the others — observability
must never break the developer's request path (FR-013 spirit).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from ..core.models import LLMEvent
from ..logging.base import Logger
from ..storage.base import StorageBackend

LoggerLike = Logger | Callable[[LLMEvent], None]


def _as_list(value: object) -> list:
    """Normalize ``None`` | single | iterable into a list (strings/bytes treated as single)."""
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value]
    if isinstance(value, Iterable):
        return list(value)
    return [value]


class DefaultEventDispatcher:
    """Default :class:`EventDispatcher`: loggers first (in order), then storage (in order)."""

    def __init__(
        self,
        loggers: LoggerLike | Iterable[LoggerLike] | None = None,
        storage: StorageBackend | Iterable[StorageBackend] | None = None,
    ) -> None:
        self._loggers: list[LoggerLike] = _as_list(loggers)
        self._storages: list[StorageBackend] = _as_list(storage)

    @property
    def loggers(self) -> tuple[LoggerLike, ...]:
        return tuple(self._loggers)

    @property
    def storages(self) -> tuple[StorageBackend, ...]:
        return tuple(self._storages)

    def dispatch(self, event: LLMEvent) -> None:
        for logger in self._loggers:
            try:
                self._emit(logger, event)
            except Exception:
                # One failing sink must not block the rest.
                continue
        for storage in self._storages:
            try:
                storage.save(event)
            except Exception:
                continue

    @staticmethod
    def _emit(logger: LoggerLike, event: LLMEvent) -> None:
        log_method = getattr(logger, "log", None)
        if callable(log_method):
            log_method(event)
        elif callable(logger):
            logger(event)
        else:  # pragma: no cover - misconfiguration
            raise TypeError(f"{logger!r} is neither a Logger nor a callable")
