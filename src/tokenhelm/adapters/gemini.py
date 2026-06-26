"""GeminiAdapter — normalize Google Gemini responses (T033).

Observe-don't-patch: reads attributes off the ``GenerateContentResponse`` object the
developer's own ``google-genai`` client returns. Gemini reports usage under
``usage_metadata`` (``prompt_token_count`` / ``candidates_token_count`` / ``total_token_count``)
and the resolved model under ``model_version``.
"""

from __future__ import annotations

from ..core.models import LLMProvider, LLMUsage
from .base import BaseAdapter, StreamAggregator

_GEMINI_EXTRA_FIELDS = (
    "cached_content_token_count",
    "thoughts_token_count",
    "tool_use_prompt_token_count",
)


def _model_of(response: object) -> str:
    return str(getattr(response, "model_version", None) or getattr(response, "model", "") or "")


def _usage_from_metadata(meta: object) -> LLMUsage:
    extra: dict[str, int] = {}
    # Gemini may report cached / tool / thinking tokens; keep them out of the core schema.
    for name in _GEMINI_EXTRA_FIELDS:
        value = getattr(meta, name, None)
        if value is not None:
            extra[name] = value
    return LLMUsage(
        input_tokens=getattr(meta, "prompt_token_count", None),
        output_tokens=getattr(meta, "candidates_token_count", None),
        total_tokens=getattr(meta, "total_token_count", None),
        extra=extra,
    )


class GeminiAdapter(BaseAdapter):
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GEMINI

    def identify(self, response: object) -> bool:
        # The ``usage_metadata`` container with Gemini's token-count fields is distinctive.
        meta = getattr(response, "usage_metadata", None)
        return meta is not None and (
            hasattr(meta, "prompt_token_count") or hasattr(meta, "candidates_token_count")
        )

    def extract_model(self, response: object) -> str:
        return _model_of(response)

    def extract_usage(self, response: object) -> LLMUsage:
        meta = getattr(response, "usage_metadata", None)
        if meta is None:
            return LLMUsage()
        return _usage_from_metadata(meta)

    def identify_stream(self, chunk: object) -> bool:
        # Streaming chunks are GenerateContentResponse objects; earliest chunks may carry
        # candidates before usage_metadata is populated.
        return self.identify(chunk) or hasattr(chunk, "candidates")

    def new_stream_aggregator(self) -> StreamAggregator:
        return _GeminiStreamAggregator()


class _GeminiStreamAggregator(StreamAggregator):
    """Gemini streaming: keep the latest ``usage_metadata`` / ``model_version`` seen.

    Gemini reports cumulative usage on each chunk, with the final chunk holding the totals.
    """

    def __init__(self) -> None:
        self._model = ""
        self._usage = LLMUsage()

    def consume(self, chunk: object) -> None:
        model = _model_of(chunk)
        if model:
            self._model = model
        meta = getattr(chunk, "usage_metadata", None)
        if meta is not None:
            self._usage = _usage_from_metadata(meta)

    def model(self) -> str:
        return self._model

    def usage(self) -> LLMUsage:
        return self._usage
