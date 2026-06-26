"""AnthropicAdapter — normalize Anthropic Messages responses (T034).

Observe-don't-patch: reads attributes off the ``Message`` object the developer's own
``anthropic`` client returns. Anthropic reports usage under ``usage.input_tokens`` /
``output_tokens`` and does **not** supply a combined total (LLMUsage derives it). Prompt-cache
counts (``cache_creation_input_tokens`` / ``cache_read_input_tokens``) are preserved in
``LLMUsage.extra`` rather than folded into the core schema.
"""

from __future__ import annotations

from ..core.models import LLMProvider, LLMUsage
from .base import BaseAdapter, StreamAggregator

_CACHE_FIELDS = ("cache_creation_input_tokens", "cache_read_input_tokens")

_STREAM_EVENT_TYPES = frozenset(
    {
        "message_start",
        "content_block_start",
        "content_block_delta",
        "content_block_stop",
        "message_delta",
        "message_stop",
        "ping",
    }
)


class AnthropicAdapter(BaseAdapter):
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.ANTHROPIC

    def identify(self, response: object) -> bool:
        # Anthropic Message objects carry type == "message"; their usage uses input_tokens.
        if getattr(response, "type", None) == "message":
            return True
        usage = getattr(response, "usage", None)
        return (
            usage is not None
            and hasattr(usage, "input_tokens")
            and hasattr(response, "stop_reason")
        )

    def extract_model(self, response: object) -> str:
        return str(getattr(response, "model", "") or "")

    def extract_usage(self, response: object) -> LLMUsage:
        usage = getattr(response, "usage", None)
        if usage is None:
            return LLMUsage()
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        # Anthropic does not report a combined total; LLMUsage derives input + output.
        return LLMUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            extra=_cache_extra(usage),
        )

    def identify_stream(self, chunk: object) -> bool:
        return getattr(chunk, "type", None) in _STREAM_EVENT_TYPES

    def new_stream_aggregator(self) -> StreamAggregator:
        return _AnthropicStreamAggregator()


def _cache_extra(usage: object) -> dict[str, int]:
    extra: dict[str, int] = {}
    for name in _CACHE_FIELDS:
        value = getattr(usage, name, None)
        if value is not None:
            extra[name] = value
    return extra


class _AnthropicStreamAggregator(StreamAggregator):
    """Anthropic streaming: input + model from ``message_start``; output from ``message_delta``.

    ``message_start`` carries ``message.usage.input_tokens`` (and the model); subsequent
    ``message_delta`` events carry the running ``usage.output_tokens``.
    """

    def __init__(self) -> None:
        self._model = ""
        self._input: int | None = None
        self._output: int | None = None
        self._extra: dict[str, int] = {}

    def consume(self, chunk: object) -> None:
        ctype = getattr(chunk, "type", None)
        if ctype == "message_start":
            message = getattr(chunk, "message", None)
            if message is not None:
                self._model = str(getattr(message, "model", "") or "")
                usage = getattr(message, "usage", None)
                if usage is not None:
                    self._input = getattr(usage, "input_tokens", None)
                    self._output = getattr(usage, "output_tokens", None)
                    self._extra = _cache_extra(usage)
        elif ctype == "message_delta":
            usage = getattr(chunk, "usage", None)
            if usage is not None:
                output = getattr(usage, "output_tokens", None)
                if output is not None:
                    self._output = output

    def model(self) -> str:
        return self._model

    def usage(self) -> LLMUsage:
        return LLMUsage(input_tokens=self._input, output_tokens=self._output, extra=self._extra)
