"""JSONLogger — one JSON object per event to a text stream (T042).

Receives only :class:`LLMEvent` and serializes it via ``event.to_dict()`` (JSON-safe). A
logger never sees a provider-specific response object, adapters, or pricing — only the
normalized event.
"""

from __future__ import annotations

import json
import sys
from typing import TextIO

from ..core.models import LLMEvent


class JSONLogger:
    """Write each event as a single JSON object (one line) to a stream (stdout by default)."""

    def __init__(self, stream: TextIO | None = None, *, indent: int | None = None) -> None:
        self._stream = stream if stream is not None else sys.stdout
        self._indent = indent

    def log(self, event: LLMEvent) -> None:
        self._stream.write(json.dumps(event.to_dict(), indent=self._indent))
        self._stream.write("\n")
        flush = getattr(self._stream, "flush", None)
        if callable(flush):
            flush()
