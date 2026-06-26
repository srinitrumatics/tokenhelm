"""Concurrency isolation tests (T053) — SC-007, FR-012.

Many tracked requests across threads and asyncio tasks simultaneously must each produce their
own correct event with no cross-contamination of counts or scope membership.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from tokenhelm import TokenHelm
from tokenhelm.core.models import LLMProvider


def _response(prompt: int, completion: int) -> SimpleNamespace:
    return SimpleNamespace(
        object="chat.completion",
        model="gpt-4o",
        usage=SimpleNamespace(
            prompt_tokens=prompt, completion_tokens=completion, total_tokens=prompt + completion
        ),
    )


def test_threaded_traces_do_not_cross_contaminate():
    tracker = TokenHelm(logger=lambda e: None)

    def work(n: int) -> tuple[int, int]:
        # Each thread opens its own scope and tracks n events; contextvars isolate scopes.
        with tracker.trace() as scope:
            for _ in range(n):
                scope.track(_response(n, n))
        # All events in this scope must carry this thread's token counts only.
        distinct_inputs = {e.input_tokens for e in scope.events}
        return len(scope.events), len(distinct_inputs)

    counts = list(range(1, 25))
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(work, counts))

    for expected_n, (got_n, distinct) in zip(counts, results, strict=True):
        assert got_n == expected_n  # no missing or leaked events
        assert distinct == 1  # all events in a scope share that thread's counts


async def test_concurrent_async_tasks_isolated():
    tracker = TokenHelm(logger=lambda e: None)

    async def task(marker: int) -> int:
        async with tracker.trace() as scope:
            for _ in range(marker):
                await asyncio.sleep(0)  # interleave aggressively
                scope.track(_response(marker, 1))
        assert len({e.input_tokens for e in scope.events}) == 1
        assert all(e.input_tokens == marker for e in scope.events)
        return len(scope.events)

    markers = list(range(1, 21))
    results = await asyncio.gather(*(task(m) for m in markers))
    assert results == markers


async def test_mixed_sync_and_async_share_one_model():
    tracker = TokenHelm(logger=lambda e: None)

    # sync trace and async trace use the same ContextVar without interfering.
    with tracker.trace() as sync_scope:
        sync_scope.track(_response(10, 10))

        async def inner():
            async with tracker.trace() as async_scope:
                async_scope.track(_response(20, 20))
            return async_scope

        async_scope = await inner()

    assert len(sync_scope.events) == 1
    assert sync_scope.events[0].input_tokens == 10
    assert len(async_scope.events) == 1
    assert async_scope.events[0].input_tokens == 20
    assert async_scope.events[0].provider is LLMProvider.OPENAI
