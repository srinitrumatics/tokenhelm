"""TokenHelm — lightweight, framework-agnostic LLM token tracking and cost calculation.

Public surface per ``specs/001-core-sdk/contracts/public-api.md``. Names exported here are the
v0.x stable contract (Principle X). This slice (User Story 1) ships the OpenAI vertical;
additional providers, loggers, storage, and streaming land in later phases.
"""

from __future__ import annotations

# Errors
# Extension-point interfaces (Principle VI)
from .adapters.anthropic import AnthropicAdapter
from .adapters.base import BaseAdapter, StreamAggregator
from .adapters.gemini import GeminiAdapter
from .adapters.ollama import OllamaAdapter
from .adapters.openai import OpenAIAdapter
from .core.calculator import CostCalculator
from .core.errors import ProviderNotInstalledError, TokenHelmError

# Core data model
from .core.models import (
    LLMCost,
    LLMEvent,
    LLMProvider,
    LLMRequest,
    LLMUsage,
    RateEntry,
)
from .dispatch.base import EventDispatcher
from .dispatch.default import DefaultEventDispatcher
from .logging.base import Logger
from .logging.console import ConsoleLogger
from .logging.file import FileLogger
from .logging.json import JSONLogger
from .pricing.base import PricingProvider
from .pricing.yaml_provider import YamlPricingProvider

# Client + scope
from .sdk.client import TokenHelm
from .sdk.context import StreamSession, TraceScope
from .storage.base import StorageBackend
from .storage.memory import InMemoryStorageBackend

__version__ = "0.1.0"  # x-release-please-version

__all__ = [
    "__version__",
    # client
    "TokenHelm",
    "TraceScope",
    "StreamSession",
    # event + enum
    "LLMEvent",
    "LLMProvider",
    "LLMUsage",
    "LLMCost",
    "LLMRequest",
    "RateEntry",
    # interfaces
    "BaseAdapter",
    "StreamAggregator",
    "PricingProvider",
    "EventDispatcher",
    "Logger",
    "StorageBackend",
    # built-in adapters
    "OpenAIAdapter",
    "AnthropicAdapter",
    "GeminiAdapter",
    "OllamaAdapter",
    # default implementations
    "YamlPricingProvider",
    "DefaultEventDispatcher",
    "ConsoleLogger",
    "JSONLogger",
    "FileLogger",
    "InMemoryStorageBackend",
    "CostCalculator",
    # errors
    "TokenHelmError",
    "ProviderNotInstalledError",
]
