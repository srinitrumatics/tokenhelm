"""Default PricingProvider — YAML-backed (T020).

Loads ``(provider, model) -> {input, output}`` rates from the bundled ``data/pricing.yaml``,
then layers optional user YAML (``path``) and/or a dict override on top (user entries win by
key). Rates are per-1,000,000 tokens, parsed via ``Decimal(str(...))`` to avoid float drift.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from ..core.config import DEFAULT_PRICING_PATH
from ..core.models import LLMProvider, RateEntry

RatesMapping = Mapping[str, Mapping[str, Mapping[str, Any]]]


class YamlPricingProvider:
    """Bundled rates + optional user overrides, behind the :class:`PricingProvider` contract."""

    def __init__(
        self,
        path: str | Path | None = None,
        overrides: RatesMapping | None = None,
        *,
        include_bundled: bool = True,
    ) -> None:
        # key: (provider_value, model) -> RateEntry
        self._rates: dict[tuple[str, str], RateEntry] = {}
        if include_bundled and DEFAULT_PRICING_PATH.exists():
            self._load_mapping(self._read_yaml(DEFAULT_PRICING_PATH))
        if path is not None:
            self._load_mapping(self._read_yaml(Path(path)))
        if overrides is not None:
            self._load_mapping(overrides)

    @staticmethod
    def _read_yaml(path: Path) -> RatesMapping:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, Mapping):
            raise ValueError(f"Pricing file {path} must be a mapping of provider -> models")
        return data

    def _load_mapping(self, data: RatesMapping) -> None:
        for provider_name, models in data.items():
            try:
                provider = LLMProvider(str(provider_name).lower())
            except ValueError:
                # Unknown provider name in a user file — skip rather than crash.
                continue
            if not isinstance(models, Mapping):
                continue
            for model, rates in models.items():
                if not isinstance(rates, Mapping):
                    continue
                input_rate = Decimal(str(rates.get("input", "0")))
                output_rate = Decimal(str(rates.get("output", "0")))
                self._rates[(provider.value, str(model))] = RateEntry(
                    provider=provider,
                    model=str(model),
                    input_rate=input_rate,
                    output_rate=output_rate,
                )

    def get_rates(self, provider: LLMProvider, model: str) -> RateEntry | None:
        provider_value = provider.value if isinstance(provider, LLMProvider) else str(provider)
        return self._rates.get((provider_value, model))
