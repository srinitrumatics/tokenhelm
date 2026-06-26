"""AnthropicAdapter tests (T030) — offline, no anthropic import."""

from __future__ import annotations

from types import SimpleNamespace

from tokenhelm.adapters.anthropic import AnthropicAdapter
from tokenhelm.core.models import LLMProvider


def test_provider_is_anthropic():
    assert AnthropicAdapter().provider is LLMProvider.ANTHROPIC


def test_identifies_message(anthropic_response):
    assert AnthropicAdapter().identify(anthropic_response) is True


def test_extract_model(anthropic_response):
    assert AnthropicAdapter().extract_model(anthropic_response) == "claude-opus-4-8"


def test_extract_usage_derives_total(anthropic_response):
    usage = AnthropicAdapter().extract_usage(anthropic_response)
    assert usage.input_tokens == 1000
    assert usage.output_tokens == 500
    # Anthropic omits total -> derived
    assert usage.total_tokens == 1500
    assert usage.complete is True


def test_cache_tokens_kept_in_extra(anthropic_response):
    usage = AnthropicAdapter().extract_usage(anthropic_response)
    assert usage.extra.get("cache_read_input_tokens") == 200
    assert usage.extra.get("cache_creation_input_tokens") == 0


def test_identify_via_usage_and_stop_reason_without_type():
    resp = SimpleNamespace(
        model="claude-haiku-4-5",
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=10, output_tokens=20),
    )
    assert AnthropicAdapter().identify(resp) is True


def test_does_not_identify_openai_shape():
    openai_like = SimpleNamespace(
        object="chat.completion",
        model="gpt-4o",
        usage=SimpleNamespace(prompt_tokens=1, completion_tokens=2),
    )
    assert AnthropicAdapter().identify(openai_like) is False


def test_missing_usage_is_graceful():
    resp = SimpleNamespace(type="message", model="claude-opus-4-8")
    usage = AnthropicAdapter().extract_usage(resp)
    assert usage.complete is False
