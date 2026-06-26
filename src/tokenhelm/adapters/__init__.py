"""Provider adapters (extension point #1).

``default_adapters()`` is the built-in adapter set the client registers by default. It lives
here (not in ``core``) so the core stays decoupled from concrete adapter implementations —
``core.extraction.UsageParser`` depends only on :class:`BaseAdapter`.
"""

from __future__ import annotations

from .base import BaseAdapter


def default_adapters() -> list[BaseAdapter]:
    """Built-in adapters, in resolution order (US1 ships OpenAI; US2 adds the rest)."""
    from .anthropic import AnthropicAdapter
    from .gemini import GeminiAdapter
    from .ollama import OllamaAdapter
    from .openai import OpenAIAdapter

    return [OpenAIAdapter(), AnthropicAdapter(), GeminiAdapter(), OllamaAdapter()]
