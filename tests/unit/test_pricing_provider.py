"""YamlPricingProvider tests (T015) — FR-005, Decision 3."""

from __future__ import annotations

from decimal import Decimal

from tokenhelm.core.models import LLMProvider
from tokenhelm.pricing.base import PricingProvider
from tokenhelm.pricing.yaml_provider import YamlPricingProvider


def test_bundled_rates_loaded():
    provider = YamlPricingProvider()

    entry = provider.get_rates(LLMProvider.OPENAI, "gpt-4o")
    assert entry is not None
    assert entry.input_rate == Decimal("2.5")
    assert entry.output_rate == Decimal("10.0")


def test_satisfies_pricing_provider_protocol():
    assert isinstance(YamlPricingProvider(), PricingProvider)


def test_unknown_model_returns_none():
    provider = YamlPricingProvider()
    assert provider.get_rates(LLMProvider.OPENAI, "does-not-exist") is None


def test_dict_override_extends_and_wins():
    overrides = {
        "openai": {
            "gpt-4o": {"input": 99.0, "output": 199.0},  # override bundled
            "custom-model": {"input": 1.0, "output": 2.0},  # extend
        }
    }
    provider = YamlPricingProvider(overrides=overrides)

    overridden = provider.get_rates(LLMProvider.OPENAI, "gpt-4o")
    assert overridden is not None
    assert overridden.input_rate == Decimal("99.0")

    extended = provider.get_rates(LLMProvider.OPENAI, "custom-model")
    assert extended is not None
    assert extended.output_rate == Decimal("2.0")


def test_user_yaml_file_override(tmp_path):
    rates_file = tmp_path / "my_rates.yaml"
    rates_file.write_text(
        "anthropic:\n  claude-opus-4-8:\n    input: 7.0\n    output: 35.0\n",
        encoding="utf-8",
    )
    provider = YamlPricingProvider(path=rates_file)

    entry = provider.get_rates(LLMProvider.ANTHROPIC, "claude-opus-4-8")
    assert entry is not None
    assert entry.input_rate == Decimal("7.0")


def test_unknown_provider_in_file_is_skipped(tmp_path):
    rates_file = tmp_path / "weird.yaml"
    rates_file.write_text("notaprovider:\n  some-model:\n    input: 1\n", encoding="utf-8")

    # Should not raise; bundled rates still resolve.
    provider = YamlPricingProvider(path=rates_file)
    assert provider.get_rates(LLMProvider.OPENAI, "gpt-4o") is not None
