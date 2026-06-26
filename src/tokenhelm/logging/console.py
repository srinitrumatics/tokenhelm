"""ConsoleLogger — human-readable event output (T022)."""

from __future__ import annotations

import sys
from typing import TextIO

from ..core.calculator import CurrencyFormatter
from ..core.models import LLMEvent


class ConsoleLogger:
    """Print a one-line summary of each event to a text stream (stdout by default)."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream if stream is not None else sys.stdout

    def log(self, event: LLMEvent) -> None:
        money = CurrencyFormatter(event.currency).format(event.cost)
        usage = "usage=partial" if not event.usage_complete else ""
        priced = "" if event.priced else "unpriced"
        flags = " ".join(f for f in (usage, priced) if f)
        flags = f" [{flags}]" if flags else ""
        provider = event.provider.value if hasattr(event.provider, "value") else event.provider
        print(
            f"[tokenhelm] {provider}/{event.model} "
            f"in={event.input_tokens} out={event.output_tokens} "
            f"total={event.total_tokens} latency={event.latency:.4f}s cost={money}{flags}",
            file=self._stream,
        )
