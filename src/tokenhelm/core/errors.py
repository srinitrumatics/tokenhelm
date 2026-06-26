"""Error types for TokenHelm (T013).

Tracking never raises on *missing data* — missing usage or missing pricing are represented
as flags on the event (FR-013). These exceptions cover structural problems only.
"""

from __future__ import annotations


class TokenHelmError(Exception):
    """Base error, e.g. no adapter recognized a response object."""


class ProviderNotInstalledError(TokenHelmError):
    """A matching provider adapter needs an optional extra that isn't installed."""

    def __init__(self, provider: str, extra: str | None = None) -> None:
        extra = extra or provider
        super().__init__(
            f"The '{provider}' provider requires the optional extra. "
            f'Install it with: pip install "tokenhelm[{extra}]"'
        )
        self.provider = provider
        self.extra = extra
