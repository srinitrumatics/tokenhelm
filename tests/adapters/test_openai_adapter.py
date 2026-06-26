"""OpenAIAdapter tests (T016) — FR-002, FR-003, observe-don't-patch.

Runs offline against a captured response shape; the ``openai`` package is not imported.
"""

from __future__ import annotations

from types import SimpleNamespace

from tokenhelm.adapters.openai import OpenAIAdapter
from tokenhelm.core.models import LLMProvider


def test_identifies_chat_completion(openai_response):
    assert OpenAIAdapter().identify(openai_response) is True


def test_provider_is_openai():
    assert OpenAIAdapter().provider is LLMProvider.OPENAI


def test_extract_model(openai_response):
    assert OpenAIAdapter().extract_model(openai_response) == "gpt-4o"


def test_extract_usage_chat_completion(openai_response):
    usage = OpenAIAdapter().extract_usage(openai_response)
    assert usage.input_tokens == 1000
    assert usage.output_tokens == 500
    assert usage.total_tokens == 1500
    assert usage.complete is True


def test_extract_usage_responses_api_shape():
    """Responses API uses input_tokens/output_tokens; identified via the ``object`` marker."""
    resp = SimpleNamespace(
        object="response",
        model="gpt-4.1",
        usage=SimpleNamespace(input_tokens=200, output_tokens=80, total_tokens=280),
    )
    adapter = OpenAIAdapter()
    assert adapter.identify(resp) is True
    usage = adapter.extract_usage(resp)
    assert usage.input_tokens == 200
    assert usage.output_tokens == 80


def test_missing_usage_is_graceful():
    resp = SimpleNamespace(object="chat.completion", model="gpt-4o")
    usage = OpenAIAdapter().extract_usage(resp)
    assert usage.input_tokens is None
    assert usage.complete is False


def test_does_not_identify_foreign_object():
    foreign = SimpleNamespace(model="x", usage=SimpleNamespace(input_tokens=1, output_tokens=2))
    # No ``object`` marker and no ``prompt_tokens`` -> not an OpenAI chat-completion shape.
    assert OpenAIAdapter().identify(foreign) is False
