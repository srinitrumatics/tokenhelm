"""Logger tests (T038) — ConsoleLogger / JSONLogger / FileLogger formats + independence.

A logger receives ONLY an LLMEvent — never a provider response object, adapter, or pricing
(FR-010, Principle VI). These tests build events directly, with no adapter/pricing involved.
"""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from decimal import Decimal

from tokenhelm.core.models import LLMCost, LLMEvent, LLMProvider
from tokenhelm.logging.console import ConsoleLogger
from tokenhelm.logging.file import FileLogger
from tokenhelm.logging.json import JSONLogger


def _event(*, priced: bool = True, usage_complete: bool = True) -> LLMEvent:
    return LLMEvent(
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        input_tokens=1000 if usage_complete else None,
        output_tokens=500 if usage_complete else None,
        total_tokens=1500 if usage_complete else None,
        latency=0.0123,
        cost=Decimal("0.0075"),
        timestamp=datetime.now(UTC),
        usage_complete=usage_complete,
        priced=priced,
        cost_detail=LLMCost(currency="USD", priced=priced),
    )


def test_console_logger_writes_human_summary():
    stream = io.StringIO()
    ConsoleLogger(stream).log(_event())
    out = stream.getvalue()
    assert "openai/gpt-4o" in out
    assert "in=1000" in out and "out=500" in out
    assert "cost=$" in out


def test_console_logger_flags_unpriced_and_partial():
    stream = io.StringIO()
    ConsoleLogger(stream).log(_event(priced=False, usage_complete=False))
    out = stream.getvalue()
    assert "unpriced" in out and "partial" in out


def test_json_logger_emits_one_json_object_per_line():
    stream = io.StringIO()
    logger = JSONLogger(stream)
    logger.log(_event())
    logger.log(_event())

    lines = stream.getvalue().strip().splitlines()
    assert len(lines) == 2
    payload = json.loads(lines[0])
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt-4o"
    assert payload["cost"] == "0.0075"


def test_json_logger_receives_only_event_dict_keys():
    """The serialized payload is exactly the normalized event — no provider object leaks."""
    stream = io.StringIO()
    JSONLogger(stream).log(_event())
    payload = json.loads(stream.getvalue())
    assert set(payload.keys()) == {
        "provider", "model", "input_tokens", "output_tokens", "total_tokens",
        "latency", "cost", "timestamp", "usage_complete", "priced", "currency",
    }


def test_file_logger_appends_json_lines(tmp_path):
    path = tmp_path / "usage.jsonl"
    logger = FileLogger(path)
    logger.log(_event())
    logger.log(_event())

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[1])["model"] == "gpt-4o"


def test_file_logger_truncates_when_append_false(tmp_path):
    path = tmp_path / "usage.jsonl"
    path.write_text("STALE\n", encoding="utf-8")
    logger = FileLogger(path, append=False)
    logger.log(_event())

    content = path.read_text(encoding="utf-8")
    assert "STALE" not in content
    assert content.strip().count("\n") == 0  # exactly one line
