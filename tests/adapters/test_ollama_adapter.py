"""OllamaAdapter tests (T031) — offline, no ollama import."""

from __future__ import annotations

from types import SimpleNamespace

from tokenhelm.adapters.ollama import OllamaAdapter
from tokenhelm.core.models import LLMProvider


def test_provider_is_ollama():
    assert OllamaAdapter().provider is LLMProvider.OLLAMA


def test_identifies_ollama_response(ollama_response):
    assert OllamaAdapter().identify(ollama_response) is True


def test_extract_model(ollama_response):
    assert OllamaAdapter().extract_model(ollama_response) == "llama3.3"


def test_extract_usage_derives_total(ollama_response):
    usage = OllamaAdapter().extract_usage(ollama_response)
    assert usage.input_tokens == 1000
    assert usage.output_tokens == 500
    assert usage.total_tokens == 1500
    assert usage.complete is True


def test_missing_usage_is_graceful():
    """An intermediate streaming chunk (not yet done) has no eval counts."""
    resp = SimpleNamespace(model="llama3.3", done=False, prompt_eval_count=10)
    adapter = OllamaAdapter()
    assert adapter.identify(resp) is True
    usage = adapter.extract_usage(resp)
    assert usage.input_tokens == 10
    assert usage.output_tokens is None
    assert usage.complete is False


def test_does_not_identify_openai_shape():
    openai_like = SimpleNamespace(
        object="chat.completion",
        model="gpt-4o",
        usage=SimpleNamespace(prompt_tokens=1, completion_tokens=2),
    )
    assert OllamaAdapter().identify(openai_like) is False
