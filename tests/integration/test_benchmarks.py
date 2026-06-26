"""Non-functional budget checks (T054) — SC-005, Constitution Principle V.

Marked ``benchmark`` so they can be deselected (``-m 'not benchmark'``). Thresholds are
deliberately generous relative to measured headroom (track() runs ~0.01 ms; the bar is 5 ms)
so the gate catches gross regressions, not noise.
"""

from __future__ import annotations

import time
import tracemalloc
from types import SimpleNamespace

import pytest

from tokenhelm import TokenHelm

pytestmark = pytest.mark.benchmark


def _response() -> SimpleNamespace:
    return SimpleNamespace(
        object="chat.completion",
        model="gpt-4o",
        usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=500, total_tokens=1500),
    )


def _stream(n_text_chunks: int):
    chunks = [
        SimpleNamespace(object="chat.completion.chunk", model="gpt-4o")
        for _ in range(n_text_chunks)
    ]
    chunks.append(
        SimpleNamespace(
            object="chat.completion.chunk",
            model="gpt-4o",
            usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=500, total_tokens=1500),
        )
    )
    return chunks


def test_track_overhead_under_5ms():
    tracker = TokenHelm(logger=lambda e: None)
    resp = _response()
    for _ in range(500):  # warmup
        tracker.track(resp)

    samples = []
    for _ in range(3000):
        t0 = time.perf_counter()
        tracker.track(resp)
        samples.append((time.perf_counter() - t0) * 1000.0)

    samples.sort()
    median = samples[len(samples) // 2]
    p99 = samples[int(len(samples) * 0.99)]
    assert median < 5.0, f"median {median:.4f} ms exceeds 5 ms budget"
    assert p99 < 5.0, f"p99 {p99:.4f} ms exceeds 5 ms budget"


def test_streaming_large_response_does_not_buffer_body():
    """A large streamed response must add < 20 MB (we pass chunks through, never buffer)."""
    tracker = TokenHelm(logger=lambda e: None)
    big = _stream(200_000)

    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    for _ in tracker.track_stream(iter(big)):
        pass
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    added_mib = (peak - base) / (1024 * 1024)
    assert added_mib < 20.0, f"streaming added {added_mib:.2f} MiB (budget 20 MB)"


def test_dispatcher_scales_with_sinks():
    """Per-track cost stays well under budget even with many sinks."""
    from tokenhelm import DefaultEventDispatcher

    sinks = [lambda e: None for _ in range(10)]
    tracker = TokenHelm(dispatcher=DefaultEventDispatcher(sinks))
    resp = _response()
    for _ in range(200):
        tracker.track(resp)

    t0 = time.perf_counter()
    for _ in range(2000):
        tracker.track(resp)
    per_track_ms = (time.perf_counter() - t0) / 2000 * 1000.0
    assert per_track_ms < 5.0, f"{per_track_ms:.4f} ms/track with 10 sinks exceeds budget"
