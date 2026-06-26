"""Configuration constants and helpers (T012).

Kept intentionally small for v0.1 — the client holds the live configuration; this module
provides shared defaults so other modules don't hardcode them.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_CURRENCY = "USD"

#: Bundled pricing file shipped with the package (``tokenhelm/data/pricing.yaml``).
DEFAULT_PRICING_PATH = Path(__file__).resolve().parent.parent / "data" / "pricing.yaml"
