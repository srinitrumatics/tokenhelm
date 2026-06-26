"""Extension point #1 — provider adapter contract (T006, T050).

An adapter *observes* a response object the developer's own client returned; it never patches
or wraps the provider SDK. Adapters identify a response by its shape (duck typing) so the core
needs no provider SDK installed to normalize a response.

Streaming (US4): each adapter owns its provider-specific chunk-aggregation logic behind a
:class:`StreamAggregator`. The core tracker never understands streaming payloads — it only asks
the aggregator for a final :class:`LLMUsage` and model. ``identify_stream`` recognizes a
streaming *chunk* (whose shape may differ from a full response).
"""

from __future__ import annotations

import abc

from ..core.models import LLMProvider, LLMUsage


class StreamAggregator(abc.ABC):
    """Accumulates provider-specific stream chunks into a normalized usage/model.

    One aggregator instance handles one stream. ``consume`` is called once per chunk (in
    order); ``model`` and ``usage`` are read once at finalization. Implementations must
    tolerate partial streams — returning whatever usage was seen so far, with missing counts
    left as ``None`` (so the event flags ``usage_complete=False``).
    """

    @abc.abstractmethod
    def consume(self, chunk: object) -> None:
        """Accumulate one stream chunk. Must not raise on a chunk lacking usage."""

    @abc.abstractmethod
    def model(self) -> str:
        """Best-known model id from the chunks seen so far."""

    @abc.abstractmethod
    def usage(self) -> LLMUsage:
        """The aggregated usage so far (final once the stream is exhausted)."""


class BaseAdapter(abc.ABC):
    """Contract every provider adapter satisfies."""

    @property
    @abc.abstractmethod
    def provider(self) -> LLMProvider:
        """Which provider this adapter handles."""

    @abc.abstractmethod
    def identify(self, response: object) -> bool:
        """True if this adapter can parse a completed (non-streaming) ``response``."""

    @abc.abstractmethod
    def extract_usage(self, response: object) -> LLMUsage:
        """Normalize token usage into an :class:`LLMUsage`."""

    @abc.abstractmethod
    def extract_model(self, response: object) -> str:
        """Read the model identifier reported by the response."""

    # -- streaming (optional per adapter) --------------------------------------------

    def identify_stream(self, chunk: object) -> bool:
        """True if this adapter recognizes a streaming *chunk*. Defaults to ``identify``.

        Override when a provider's streaming chunk shape differs from its full response.
        """
        return self.identify(chunk)

    def new_stream_aggregator(self) -> StreamAggregator:
        """Return a fresh :class:`StreamAggregator` for one stream. v0.1 default: unsupported."""
        raise NotImplementedError(f"{type(self).__name__} does not support streaming aggregation.")
