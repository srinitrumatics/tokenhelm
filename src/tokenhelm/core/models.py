"""Core data model for TokenHelm (T005).

Every tracked LLM request is normalized into these provider-agnostic dataclasses. The
public, consumer-facing record is :class:`LLMEvent`; the rest are building blocks. All
monetary values use :class:`decimal.Decimal`; token counts are ``int``; timestamps are
timezone-aware UTC ``datetime``.

See ``specs/001-core-sdk/data-model.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class LLMProvider(str, Enum):
    """Source provider of a tracked request. Serialized as its lowercase value."""

    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.value


@dataclass
class LLMUsage:
    """Normalized token usage extracted by an adapter.

    ``total_tokens`` defaults to ``input_tokens + output_tokens`` when the provider does not
    supply it and both are present. A missing usage object leaves the counts ``None`` and is
    surfaced via :attr:`complete` / the event's ``usage_complete`` flag.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            self.total_tokens is None
            and self.input_tokens is not None
            and self.output_tokens is not None
        ):
            self.total_tokens = self.input_tokens + self.output_tokens

    @property
    def complete(self) -> bool:
        """True when both input and output token counts are present."""
        return self.input_tokens is not None and self.output_tokens is not None


@dataclass(frozen=True)
class LLMCost:
    """Computed cost for a single request.

    An unpriced request (model absent from the pricing source) still yields a valid
    ``LLMCost`` with ``priced=False`` and zero costs — never an error (FR-013).

    Frozen: a built event (and its cost breakdown) is immutable, so every dispatcher sink
    receives the exact same value with no risk of one sink mutating it for the others.
    """

    input_cost: Decimal = Decimal("0")
    output_cost: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    currency: str = "USD"
    priced: bool = True


@dataclass(frozen=True)
class RateEntry:
    """A single pricing record returned by a :class:`PricingProvider`. Per-1M-token units."""

    provider: LLMProvider
    model: str
    input_rate: Decimal
    output_rate: Decimal


@dataclass(frozen=True)
class LLMRequest:
    """Lightweight descriptor of the tracked request context. Frozen (immutable)."""

    provider: LLMProvider
    model: str
    streamed: bool = False
    started_at: datetime | None = None
    #: Exception type name when a stream ended abnormally (error/cancellation); else None.
    #: Partial metrics are preserved on the event; ``usage_complete`` still signals partiality.
    error: str | None = None


@dataclass(frozen=True)
class LLMEvent:
    """The single normalized record every tracked request produces (Principle VII).

    Consumers never receive a provider-specific usage object — only this event. The eight
    constitution-mandated fields are always present as keys; token values may be ``None`` in
    the degraded case, with ``usage_complete=False`` signalling it.

    Frozen: the event is immutable once built. The tracker emits one instance through the
    dispatcher and every sink (loggers, storage) receives that same immutable object.
    """

    provider: LLMProvider
    model: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    latency: float
    cost: Decimal
    timestamp: datetime
    usage_complete: bool = True
    priced: bool = True
    cost_detail: LLMCost | None = None
    request: LLMRequest | None = None

    @property
    def currency(self) -> str:
        return self.cost_detail.currency if self.cost_detail else "USD"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain, JSON-safe dict. Loggers rely on this."""
        provider = self.provider.value if isinstance(self.provider, LLMProvider) else self.provider
        return {
            "provider": provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency": self.latency,
            "cost": str(self.cost),
            "timestamp": self.timestamp.isoformat(),
            "usage_complete": self.usage_complete,
            "priced": self.priced,
            "currency": self.currency,
        }
