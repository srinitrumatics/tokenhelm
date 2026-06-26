"""FileLogger — append events as JSON lines to a file (T043).

Each event becomes one JSON object per line (the JSON Lines / ``.jsonl`` convention), making
the output trivially streamable and appendable. Receives only :class:`LLMEvent`.
"""

from __future__ import annotations

import json
from pathlib import Path


class FileLogger:
    """Append each event as a JSON line to ``path`` (created if missing)."""

    def __init__(self, path: str | Path, *, append: bool = True, encoding: str = "utf-8") -> None:
        self._path = Path(path)
        self._encoding = encoding
        if not append:
            # Truncate up front so a fresh run starts clean.
            self._path.write_text("", encoding=encoding)

    @property
    def path(self) -> Path:
        return self._path

    def log(self, event) -> None:
        line = json.dumps(event.to_dict())
        with open(self._path, "a", encoding=self._encoding) as fh:
            fh.write(line + "\n")
