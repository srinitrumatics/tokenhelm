"""UsageParser registry tests (T017) — adapter resolution + graceful degradation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tokenhelm.adapters import default_adapters
from tokenhelm.adapters.openai import OpenAIAdapter
from tokenhelm.core.errors import TokenHelmError
from tokenhelm.core.extraction import UsageParser


def test_find_resolves_openai(openai_response):
    parser = UsageParser(default_adapters())
    adapter = parser.find(openai_response)
    assert isinstance(adapter, OpenAIAdapter)


def test_unrecognized_response_raises_tokenhelm_error():
    parser = UsageParser(default_adapters())
    with pytest.raises(TokenHelmError):
        parser.find(SimpleNamespace(nothing="useful"))


def test_misbehaving_adapter_does_not_block_others(openai_response):
    class Boom:
        @property
        def provider(self):
            from tokenhelm.core.models import LLMProvider

            return LLMProvider.GEMINI

        def identify(self, response):
            raise RuntimeError("boom")

        def extract_usage(self, response):  # pragma: no cover - not reached
            raise NotImplementedError

        def extract_model(self, response):  # pragma: no cover - not reached
            raise NotImplementedError

    parser = UsageParser([Boom(), OpenAIAdapter()])
    assert isinstance(parser.find(openai_response), OpenAIAdapter)


def test_register_appends_adapter():
    parser = UsageParser()
    assert parser.adapters == ()
    parser.register(OpenAIAdapter())
    assert len(parser.adapters) == 1


def test_missing_usage_event_flag(openai_response):
    """FR-013: a response missing usage still parses; usage marked incomplete."""
    resp = SimpleNamespace(object="chat.completion", model="gpt-4o")
    parser = UsageParser(default_adapters())
    adapter = parser.find(resp)
    usage = adapter.extract_usage(resp)
    assert usage.complete is False
