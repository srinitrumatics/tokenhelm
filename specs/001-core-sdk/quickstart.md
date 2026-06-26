# Quickstart & Validation Guide: TokenHelm Core SDK

This guide is a runnable validation path that proves the feature works end-to-end. It maps
each user story / success criterion to a concrete check. It is **not** the implementation —
see `tasks.md` for build steps.

## Prerequisites

- Python 3.11+
- The package installed in editable mode with the providers you want to validate:
  ```bash
  pip install -e ".[all]"        # or .[openai], .[anthropic], etc.
  pip install -e ".[dev]"        # pytest, pytest-asyncio, pytest-cov
  ```
- No provider API keys are required to run the test suite — adapter tests use captured
  response fixtures under `tests/adapters/fixtures/`.

## Scenario 1 — Track one request, get a normalized event (US1, SC-001/SC-002/SC-003)

Goal: ≤5 lines to add tracking; event has all 8 fields; cost matches pricing.

```python
from tokenhelm import TokenHelm

tracker = TokenHelm()                       # zero-config
response = client.responses.create(...)     # your own OpenAI call
event = tracker.track(response)             # normalized event
print(event.to_dict())
```

**Expected**: `event` has `provider, model, input_tokens, output_tokens, total_tokens,
latency, cost, timestamp` populated; `total_tokens == input_tokens + output_tokens`;
`event.cost` equals configured rate × tokens. See `contracts/public-api.md`.

**Automated check**: `tests/integration/test_trace_context.py::test_single_track_event_shape`.

## Scenario 2 — Same code, different provider (US2, SC-004)

Goal: switch providers with no change to tracking code.

```python
tracker = TokenHelm()
for response in (openai_response, anthropic_response, gemini_response, ollama_response):
    event = tracker.track(response)
    assert {"provider","model","input_tokens","output_tokens",
            "total_tokens","latency","cost","timestamp"} <= event.to_dict().keys()
```

**Expected**: identical event shape across all four providers; provider field differs;
each priced from its own rates. Zero-rate/local model (Ollama) yields `cost == 0` without
error (edge case).

**Automated check**: `tests/adapters/test_*_adapter.py` (one per provider) +
`test_trace_context.py::test_provider_switch_identical_shape`.

## Scenario 3 — Choose how events are recorded (US3, FR-010, Decisions 3 & 4)

```python
from tokenhelm import (
    TokenHelm, JSONLogger, FileLogger, ConsoleLogger,
    InMemoryStorageBackend, YamlPricingProvider,
)

TokenHelm(logger=JSONLogger())                       # JSON to stdout
TokenHelm(logger=FileLogger("usage.jsonl"))          # JSON lines to file
TokenHelm(logger=lambda e: my_metrics.push(e.to_dict()))   # custom sink, no lib change

# Multiple sinks at once — the EventDispatcher fans out; the tracker stays unaware
store = InMemoryStorageBackend()
tracker = TokenHelm(logger=[ConsoleLogger(), FileLogger("usage.jsonl")], storage=store)
tracker.track(response)
assert list(store.all())                            # event also persisted

# Swap the pricing source entirely (not just YAML) — CostCalculator is unchanged
TokenHelm(pricing=YamlPricingProvider(path="my_rates.yaml"))
# TokenHelm(pricing=MyRemotePricingProvider())      # future: same interface
```

**Expected**: each mechanism records the event in its format; the custom callable receives
the event without modifying the library; multiple loggers + storage all receive one event
via the dispatcher; pricing source is swappable behind `PricingProvider` (Principle VI,
Decisions 3 & 4).

**Automated check**: `tests/unit/test_loggers.py`, `tests/unit/test_dispatch.py`,
`tests/unit/test_storage.py`, `tests/unit/test_pricing_provider.py`.

## Scenario 4 — Scoped + streaming + async (US4, FR-006/FR-008/FR-011)

```python
# scoped, sync
with tracker.trace() as scope:
    resp = client.responses.create(...)
    scope.track(resp)
assert len(scope.events) == 1

# streaming — one event after the stream is exhausted
for chunk in tracker.track_stream(client.responses.create(..., stream=True)):
    ...   # consume chunks
# exactly one LLMEvent emitted with final totals

# async
async with tracker.trace() as scope:
    resp = await aclient.responses.create(...)
    scope.track(resp)
```

**Expected**: scope collects events; streaming yields one final event with aggregated
totals; async path behaves identically.

**Automated check**: `test_trace_context.py::{test_streaming_single_event, test_async_trace}`.

## Scenario 5 — Concurrency isolation (SC-007, FR-012)

Run many tracked requests across threads/tasks simultaneously; assert each produces its own
correct event with no cross-contamination of counts.

**Automated check**: `tests/integration/test_thread_safety.py`.

## Scenario 6 — Graceful degradation (FR-013, edge cases)

- Response with missing usage → event present, `usage_complete == False`, no exception.
- Model absent from pricing → event present, `priced == False`, `cost == 0`, no exception.

**Automated check**: `test_calculator.py::test_unpriced_model`,
`test_extraction.py::test_missing_usage`.

## Non-functional validation (SC-005)

- **Overhead**: a microbenchmark asserts per-`track()` overhead < 5 ms on the fixture path.
- **Memory**: streaming a large response does not buffer the full body (< 20 MB added).

**Automated check**: `tests/integration/` benchmark markers (run with `-m benchmark`).

## Coverage gate (SC-008, Principle IX)

```bash
pytest --cov=tokenhelm --cov-report=term-missing
```

**Expected**: adapters, cost calculator, token extraction, and configuration covered;
overall coverage meets the 90% target.

## Acceptance checklist (from spec)

- [X] OpenAI / Gemini / Anthropic / Ollama adapters produce normalized events
- [X] Cost calculation passes unit tests
- [X] Streaming supported (one final event)
- [X] Context manager supported (sync + async)
- [X] Documentation completed (`docs/`)
- [ ] Published to PyPI — package builds (sdist + wheel via `python -m build`); upload pending credentials
