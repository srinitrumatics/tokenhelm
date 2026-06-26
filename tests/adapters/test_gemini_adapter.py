"""GeminiAdapter tests (T029) — offline, no google-genai import."""

from __future__ import annotations

from types import SimpleNamespace

from tokenhelm.adapters.gemini import GeminiAdapter
from tokenhelm.core.models import LLMProvider


def test_provider_is_gemini():
    assert GeminiAdapter().provider is LLMProvider.GEMINI


def test_identifies_gemini_response(gemini_response):
    assert GeminiAdapter().identify(gemini_response) is True


def test_extract_model_from_model_version(gemini_response):
    assert GeminiAdapter().extract_model(gemini_response) == "gemini-2.5-pro"


def test_extract_usage(gemini_response):
    usage = GeminiAdapter().extract_usage(gemini_response)
    assert usage.input_tokens == 1000
    assert usage.output_tokens == 500
    assert usage.total_tokens == 1500
    assert usage.complete is True


def test_cache_tokens_kept_in_extra(gemini_response):
    usage = GeminiAdapter().extract_usage(gemini_response)
    assert usage.extra.get("cached_content_token_count") == 200


def test_missing_usage_is_graceful():
    resp = SimpleNamespace(model_version="gemini-2.5-flash")
    adapter = GeminiAdapter()
    assert adapter.identify(resp) is False
    usage = adapter.extract_usage(resp)
    assert usage.complete is False


def test_does_not_identify_openai_shape():
    openai_like = SimpleNamespace(
        object="chat.completion",
        model="gpt-4o",
        usage=SimpleNamespace(prompt_tokens=1, completion_tokens=2),
    )
    assert GeminiAdapter().identify(openai_like) is False
