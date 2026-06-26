"""Streaming + async tests (T047, T048) — US4.

Covers the reviewer's matrix: exactly one event per stream, sync/async parity, concurrent
stream isolation, nested stream scopes, cancellation cleanup, exception cleanup, and provider
parity for streaming. All offline against captured chunk-sequence fixtures.
"""

from __future__ import annotations

import asyncio

import pytest

from tokenhelm import TokenHelm
from tokenhelm.core.models import LLMProvider

ALL_STREAMS = ("openai_stream", "anthropic_stream", "gemini_stream", "ollama_stream")
PROVIDER_OF = {
    "openai_stream": LLMProvider.OPENAI,
    "anthropic_stream": LLMProvider.ANTHROPIC,
    "gemini_stream": LLMProvider.GEMINI,
    "ollama_stream": LLMProvider.OLLAMA,
}


def _sync_iter(chunks):
    yield from chunks


async def _async_iter(chunks):
    for chunk in chunks:
        yield chunk


def _failing_iter(chunks, *, at):
    for index, chunk in enumerate(chunks):
        if index == at:
            raise RuntimeError("stream broke")
        yield chunk


def _capturing_tracker():
    seen = []
    return TokenHelm(logger=seen.append), seen


# -- exactly one event ----------------------------------------------------------------


def test_sync_wrap_emits_exactly_one_event(openai_stream):
    tracker, seen = _capturing_tracker()
    chunks = list(tracker.track_stream(_sync_iter(openai_stream)))

    assert len(chunks) == len(openai_stream)  # every chunk passed through unchanged
    assert len(seen) == 1
    event = seen[0]
    assert event.input_tokens == 1000
    assert event.output_tokens == 500
    assert event.total_tokens == 1500
    assert event.request.streamed is True
    assert event.request.error is None


def test_sync_manual_consume_emits_one_event(openai_stream):
    tracker, seen = _capturing_tracker()
    with tracker.track_stream() as session:
        for chunk in openai_stream:
            session.consume(chunk)
    assert len(seen) == 1
    assert session.event is not None
    assert session.event.output_tokens == 500


def test_empty_stream_emits_no_event():
    tracker, seen = _capturing_tracker()
    chunks = list(tracker.track_stream(_sync_iter([])))
    assert chunks == []
    assert seen == []


# -- async + parity -------------------------------------------------------------------


async def test_async_wrap_emits_one_event(openai_stream):
    tracker, seen = _capturing_tracker()
    chunks = [c async for c in tracker.track_stream(_async_iter(openai_stream))]
    assert len(chunks) == len(openai_stream)
    assert len(seen) == 1
    assert seen[0].total_tokens == 1500


async def test_async_manual_consume_emits_one_event(openai_stream):
    tracker, seen = _capturing_tracker()
    async with tracker.track_stream() as session:
        async for chunk in _async_iter(openai_stream):
            session.consume(chunk)
    assert len(seen) == 1
    assert session.event.input_tokens == 1000


async def test_sync_async_parity(openai_stream):
    sync_tracker, sync_seen = _capturing_tracker()
    list(sync_tracker.track_stream(_sync_iter(openai_stream)))

    async_tracker, async_seen = _capturing_tracker()
    [c async for c in async_tracker.track_stream(_async_iter(openai_stream))]

    def comparable(event):
        d = event.to_dict()
        d.pop("timestamp")
        d.pop("latency")
        return d

    assert comparable(sync_seen[0]) == comparable(async_seen[0])


async def test_async_trace_is_context_manager(openai_response):
    """async with tracker.trace() mirrors the sync API."""
    tracker, _ = _capturing_tracker()
    async with tracker.trace() as scope:
        scope.track(openai_response)
    assert len(scope.events) == 1


# -- provider parity ------------------------------------------------------------------


@pytest.mark.parametrize("stream_name", ALL_STREAMS)
def test_provider_parity_streaming(stream_name, request):
    chunks = request.getfixturevalue(stream_name)
    tracker, seen = _capturing_tracker()

    list(tracker.track_stream(_sync_iter(chunks)))

    assert len(seen) == 1
    event = seen[0]
    assert event.provider is PROVIDER_OF[stream_name]
    assert event.input_tokens == 1000
    assert event.output_tokens == 500
    assert event.total_tokens == 1500
    assert event.usage_complete is True
    assert event.request.streamed is True


# -- scope integration + isolation ----------------------------------------------------


def test_stream_event_attributed_to_active_scope(openai_stream):
    tracker, _ = _capturing_tracker()
    with tracker.trace() as scope:
        for _ in tracker.track_stream(_sync_iter(openai_stream)):
            pass
    assert len(scope.events) == 1
    assert scope.events[0].request.streamed is True


def test_nested_stream_scopes_do_not_cross_contaminate(openai_stream, ollama_stream):
    tracker, _ = _capturing_tracker()
    with tracker.trace() as outer:
        for _ in tracker.track_stream(_sync_iter(openai_stream)):
            pass
        with tracker.trace() as inner:
            for _ in tracker.track_stream(_sync_iter(ollama_stream)):
                pass
    assert len(inner.events) == 1
    assert inner.events[0].provider is LLMProvider.OLLAMA
    assert len(outer.events) == 1  # only the openai stream ran under outer
    assert outer.events[0].provider is LLMProvider.OPENAI


async def test_concurrent_async_stream_isolation(
    openai_stream, anthropic_stream, gemini_stream, ollama_stream
):
    tracker, _ = _capturing_tracker()
    work = {
        LLMProvider.OPENAI: openai_stream,
        LLMProvider.ANTHROPIC: anthropic_stream,
        LLMProvider.GEMINI: gemini_stream,
        LLMProvider.OLLAMA: ollama_stream,
    }

    async def worker(provider, chunks):
        async with tracker.trace() as scope:
            # Yield control between chunks to interleave tasks aggressively.
            async for _ in tracker.track_stream(_async_iter(chunks)):
                await asyncio.sleep(0)
        assert len(scope.events) == 1  # each task sees only its own event
        assert scope.events[0].provider is provider
        return scope.events[0].provider

    providers = await asyncio.gather(*(worker(p, c) for p, c in work.items()))
    assert set(providers) == set(work)


# -- error / cancellation cleanup -----------------------------------------------------


def test_exception_midstream_finalizes_once_and_marks_event(openai_stream):
    tracker, seen = _capturing_tracker()
    with pytest.raises(RuntimeError):
        for _ in tracker.track_stream(_failing_iter(openai_stream, at=2)):
            pass

    assert len(seen) == 1  # exactly one event, no duplicate
    event = seen[0]
    assert event.request.error == "RuntimeError"
    # Failed before the usage chunk -> partial usage, flagged.
    assert event.usage_complete is False


async def test_async_cancellation_cleanup(openai_stream):
    tracker, seen = _capturing_tracker()

    async def cancelling():
        yield openai_stream[0]
        yield openai_stream[1]
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        async for _ in tracker.track_stream(cancelling()):
            pass

    assert len(seen) == 1
    assert seen[0].request.error == "CancelledError"


def test_no_duplicate_event_on_manual_finalize_then_exit(openai_stream):
    tracker, seen = _capturing_tracker()
    with tracker.track_stream() as session:
        for chunk in openai_stream:
            session.consume(chunk)
        first = session._finalize()  # explicit finalize inside the block
    # __exit__ also calls _finalize -> must be idempotent
    assert len(seen) == 1
    assert session.event is first
