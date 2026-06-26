"""OpenAIAdapter — normalize OpenAI responses (T024).

Observe-don't-patch: this reads attributes off whatever response object the developer's own
OpenAI client returned. It identifies responses by shape (duck typing), so the core does not
need the ``openai`` package installed to normalize a response. Supports both the Chat
Completions shape (``usage.prompt_tokens`` / ``completion_tokens``) and the Responses API
shape (``usage.input_tokens`` / ``output_tokens``).
"""

from __future__ import annotations

from ..core.models import LLMProvider, LLMUsage
from .base import BaseAdapter, StreamAggregator

# OpenAI response objects carry an ``object`` discriminator, e.g. "chat.completion",
# "response", or "text_completion". We use it (when present) to disambiguate from other
# providers that also expose input/output token counts (notably Anthropic).
_OPENAI_OBJECT_PREFIXES = ("chat.completion", "response", "text_completion")


class OpenAIAdapter(BaseAdapter):
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENAI

    def identify(self, response: object) -> bool:
        obj = getattr(response, "object", None)
        if isinstance(obj, str) and obj.startswith(_OPENAI_OBJECT_PREFIXES):
            return True
        usage = getattr(response, "usage", None)
        # Chat Completions usage has the OpenAI-specific ``prompt_tokens`` field.
        return usage is not None and hasattr(usage, "prompt_tokens")

    def extract_model(self, response: object) -> str:
        return str(getattr(response, "model", "") or "")

    def extract_usage(self, response: object) -> LLMUsage:
        usage = getattr(response, "usage", None)
        if usage is None:
            return LLMUsage()
        return _usage_from_openai(usage)

    def new_stream_aggregator(self) -> StreamAggregator:
        return _OpenAIStreamAggregator()


def _usage_from_openai(usage: object) -> LLMUsage:
    """Normalize an OpenAI ``usage`` object (Chat Completions or Responses API naming)."""
    input_tokens = getattr(usage, "prompt_tokens", None)
    output_tokens = getattr(usage, "completion_tokens", None)
    if input_tokens is None and output_tokens is None:
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    return LLMUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


class _OpenAIStreamAggregator(StreamAggregator):
    """OpenAI streaming: final usage arrives in a late chunk's ``usage`` (include_usage)."""

    def __init__(self) -> None:
        self._model = ""
        self._usage = LLMUsage()

    def consume(self, chunk: object) -> None:
        model = getattr(chunk, "model", None)
        if model:
            self._model = str(model)
        usage = getattr(chunk, "usage", None)
        if usage is not None:
            self._usage = _usage_from_openai(usage)

    def model(self) -> str:
        return self._model

    def usage(self) -> LLMUsage:
        return self._usage
