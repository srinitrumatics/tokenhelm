"""Shared test helpers and fixtures.

Adapter tests run fully offline against captured response shapes — no provider SDKs, no API
keys (quickstart Prerequisites). JSON fixtures under ``tests/adapters/fixtures/`` are loaded
and wrapped into attribute-access objects that mimic provider response objects, since
TokenHelm adapters observe attributes (duck typing) rather than SDK classes.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "adapters" / "fixtures"


def _objectify(value: Any) -> Any:
    """Recursively turn dicts into attribute-access namespaces (lists handled element-wise)."""
    if isinstance(value, dict):
        return SimpleNamespace(**{k: _objectify(v) for k, v in value.items()})
    if isinstance(value, list):
        return [_objectify(v) for v in value]
    return value


def load_fixture(name: str) -> Any:
    """Load a JSON fixture file and wrap it as a response-like object."""
    with open(FIXTURES / name, encoding="utf-8") as fh:
        return _objectify(json.load(fh))


@pytest.fixture
def openai_response() -> Any:
    """A captured OpenAI Chat Completions response (object form)."""
    return load_fixture("openai_response.json")


@pytest.fixture
def gemini_response() -> Any:
    """A captured Google Gemini GenerateContentResponse (object form)."""
    return load_fixture("gemini_response.json")


@pytest.fixture
def anthropic_response() -> Any:
    """A captured Anthropic Message (object form)."""
    return load_fixture("anthropic_response.json")


@pytest.fixture
def ollama_response() -> Any:
    """A captured Ollama chat response (object form)."""
    return load_fixture("ollama_response.json")


# -- streaming chunk sequences (object form) -------------------------------------------


@pytest.fixture
def openai_stream() -> list:
    return load_fixture("openai_stream.json")


@pytest.fixture
def anthropic_stream() -> list:
    return load_fixture("anthropic_stream.json")


@pytest.fixture
def gemini_stream() -> list:
    return load_fixture("gemini_stream.json")


@pytest.fixture
def ollama_stream() -> list:
    return load_fixture("ollama_stream.json")
