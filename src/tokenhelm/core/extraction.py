"""Adapter registry / usage parser (T025).

Holds the ordered list of provider adapters and resolves which one recognizes a given
response object via :meth:`BaseAdapter.identify`. The tracker depends on this rather than on
any concrete adapter.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..adapters.base import BaseAdapter
from .errors import TokenHelmError


class UsageParser:
    """Ordered registry of adapters; finds the one that can parse a response."""

    def __init__(self, adapters: Iterable[BaseAdapter] | None = None) -> None:
        self._adapters: list[BaseAdapter] = list(adapters) if adapters is not None else []

    def register(self, adapter: BaseAdapter) -> None:
        self._adapters.append(adapter)

    @property
    def adapters(self) -> tuple[BaseAdapter, ...]:
        return tuple(self._adapters)

    def find(self, response: object) -> BaseAdapter:
        return self._find(response, lambda a, r: a.identify(r), "response object")

    def find_stream(self, chunk: object) -> BaseAdapter:
        """Resolve the adapter that recognizes a streaming *chunk* (US4)."""
        return self._find(chunk, lambda a, c: a.identify_stream(c), "stream chunk")

    def _find(self, obj: object, predicate, label: str) -> BaseAdapter:
        for adapter in self._adapters:
            try:
                if predicate(adapter, obj):
                    return adapter
            except Exception:
                # A misbehaving identify() must not block other adapters.
                continue
        raise TokenHelmError(
            f"No registered adapter recognized the {label} "
            f"(type={type(obj).__name__}). Supported providers: "
            f"{', '.join(a.provider.value for a in self._adapters) or 'none'}."
        )
