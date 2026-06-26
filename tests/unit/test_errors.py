"""Error type tests (T013 coverage)."""

from __future__ import annotations

from tokenhelm.core.errors import ProviderNotInstalledError, TokenHelmError


def test_provider_not_installed_is_tokenhelm_error():
    err = ProviderNotInstalledError("openai")
    assert isinstance(err, TokenHelmError)
    assert err.provider == "openai"
    assert err.extra == "openai"
    assert 'pip install "tokenhelm[openai]"' in str(err)


def test_provider_not_installed_custom_extra():
    err = ProviderNotInstalledError("gemini", extra="gemini")
    assert "tokenhelm[gemini]" in str(err)
