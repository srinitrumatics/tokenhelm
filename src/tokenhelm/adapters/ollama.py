"""OllamaAdapter — normalize Ollama (local) responses (T035).

Observe-don't-patch: reads attributes off the response object the developer's own ``ollama``
client returns. Ollama reports usage as ``prompt_eval_count`` (input) and ``eval_count``
(output); there is no combined total (LLMUsage derives it). Local inference is typically
zero-cost — unlisted models simply resolve as "unpriced" (cost 0) without error.
"""

from __future__ import annotations

from ..core.models import LLMProvider, LLMUsage
from .base import BaseAdapter, StreamAggregator


def _usage_of(response: object) -> LLMUsage:
    # Ollama provides no combined total; LLMUsage derives input + output.
    return LLMUsage(
        input_tokens=getattr(response, "prompt_eval_count", None),
        output_tokens=getattr(response, "eval_count", None),
    )


class OllamaAdapter(BaseAdapter):
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OLLAMA

    def identify(self, response: object) -> bool:
        # eval_count / prompt_eval_count are distinctive to Ollama responses.
        return hasattr(response, "eval_count") or hasattr(response, "prompt_eval_count")

    def extract_model(self, response: object) -> str:
        return str(getattr(response, "model", "") or "")

    def extract_usage(self, response: object) -> LLMUsage:
        return _usage_of(response)

    def identify_stream(self, chunk: object) -> bool:
        # Intermediate stream chunks lack eval counts but carry model + done.
        return self.identify(chunk) or (hasattr(chunk, "done") and hasattr(chunk, "model"))

    def new_stream_aggregator(self) -> StreamAggregator:
        return _OllamaStreamAggregator()


class _OllamaStreamAggregator(StreamAggregator):
    """Ollama streaming: the final ``done`` chunk carries prompt_eval_count / eval_count."""

    def __init__(self) -> None:
        self._model = ""
        self._input: int | None = None
        self._output: int | None = None

    def consume(self, chunk: object) -> None:
        model = getattr(chunk, "model", None)
        if model:
            self._model = str(model)
        prompt_eval = getattr(chunk, "prompt_eval_count", None)
        if prompt_eval is not None:
            self._input = prompt_eval
        eval_count = getattr(chunk, "eval_count", None)
        if eval_count is not None:
            self._output = eval_count

    def model(self) -> str:
        return self._model

    def usage(self) -> LLMUsage:
        return LLMUsage(input_tokens=self._input, output_tokens=self._output)
