# TokenHelm v0.1.0 — Release Notes

**Lightweight, framework-agnostic token tracking and LLM cost calculation across providers.**

TokenHelm gives you one normalized usage/cost event for every LLM call — OpenAI, Gemini,
Anthropic, or Ollama — without locking you into a framework, patching any provider SDK, or ever
touching your credentials. It **observes** the response object your own client returns.

```python
from tokenhelm import TokenHelm

tracker = TokenHelm()                          # zero-config
event = tracker.track(response)                # normalized, immutable LLMEvent
print(event.to_dict())
```

## Architecture overview

```
Application → TokenHelm (sdk) → TokenTracker (core) → EventDispatcher → Logger(s) / Storage
                                       └────────────→ CostCalculator → PricingProvider
                                       └────────────→ UsageParser → BaseAdapter
```

- **Observe-don't-patch:** adapters read attributes off whatever response object your client
  returns (duck typing) — no provider SDK is imported to normalize a response.
- **Strictly one-way dependencies:** `sdk → core → interfaces`. Concrete implementations are
  assembled only at the `sdk` layer; adapters never import loggers/storage; nothing imports
  `sdk`. No cycles.
- **Immutable event:** `LLMEvent`/`LLMCost`/`LLMRequest` are frozen — the tracker emits one
  instance and every sink receives that same object.
- **Decisions enforced:** `CostCalculator` depends only on `PricingProvider`; `TokenTracker`
  emits only through `EventDispatcher` and is unaware of sinks.

## Public API

| Surface | Signature |
|---|---|
| `TokenHelm(*, logger, pricing, dispatcher, storage, adapters, currency="USD")` | client; all keyword-only |
| `track(response) -> LLMEvent` | manual tracking (sync; safe in async code) |
| `trace() -> TraceScope` | scoped tracking; `with` **and** `async with` |
| `track_stream(stream=None) -> StreamSession` | streaming; wrap (`for`/`async for`) or manual (`consume`) |
| `configure(**knobs)` | reconfigure; only passed args change |

Plus the data model (`LLMEvent`, `LLMProvider`, `LLMUsage`, `LLMCost`, `LLMRequest`,
`RateEntry`), the five extension interfaces, built-in implementations, and error types — 29
exported names, all documented and audited (`scripts/check_public_api.py`).

The eight mandated event fields — `provider, model, input_tokens, output_tokens, total_tokens,
latency, cost, timestamp` — plus `usage_complete`/`priced` flags are the stable contract.

## Supported providers

| Feature | OpenAI | Gemini | Anthropic | Ollama |
|---|---|---|---|---|
| Token tracking | ✅ | ✅ | ✅ | ✅ |
| Cost calculation | ✅ | ✅ | ✅ | ✅ (0 local) |
| Streaming (one final event) | ✅ | ✅ | ✅ | ✅ |
| Async | ✅ | ✅ | ✅ | ✅ |
| Bundled pricing | ✅ | ✅ | ✅ | ✅ (0-rate) |
| Usage-metadata extras | — | cached/thoughts/tool | cache tokens | — |
| Error/cancellation recovery | ✅ | ✅ | ✅ | ✅ |

## Extension points (all public & stable)

`BaseAdapter` · `PricingProvider` · `EventDispatcher` · `Logger` · `StorageBackend`. The core
depends only on these interfaces; future Analytics/Prompt/RAG/FinOps/Dashboard modules are
downstream consumers requiring no core change.

## Test results

- **127 tests passing** (unit + adapter + integration + streaming + thread/async + benchmark).
- Coverage: unit (calculator, pricing, extraction, dispatch, storage, loggers, config),
  adapters (4 providers, response + stream fixtures), integration (event shape, provider
  parity, trace isolation, concurrency, streaming lifecycle, cancellation/exception cleanup).

## Coverage

**95.62%** line+branch (gate: 90%, enforced in CI and locally).

## Performance (measured — Python 3.13, single core)

| Metric | Result | Budget |
|---|---|---|
| `track()` overhead | median **0.011 ms**, p99 0.028 ms | < 5 ms ✅ |
| Dispatcher 1→10 sinks | 0.014 → 0.016 ms/track (flat) | — |
| Streaming a 200k-chunk response | **+0.00 MiB** (passthrough, no buffering) | < 20 MB ✅ |

## Known limitations

- Provider identification is **duck-typed**; a novel/ambiguous response could misclassify —
  mitigated by `adapters=[...]` to override the registry.
- Streaming aggregation is validated against **captured fixtures**, not live SDK objects
  (live-SDK CI is a pre-1.0 item).
- Bundled `pricing.yaml` is a **static snapshot**; override via file/dict/`PricingProvider`.
- `track()` is synchronous by design (pure-CPU; no `await` needed). No mid-stream/progress
  events in v0.1.
- Storage is opt-in and in-memory only in v0.1 (SQLite/remote come via the interface later).

## Roadmap

v0.2 Analytics → v0.3 Prompt Intelligence → v0.4 RAG Intelligence → v0.5 AI FinOps →
v1.0 Enterprise Platform — all additive on the v0.1 extension points. See
[`ROADMAP.md`](../ROADMAP.md).

## Install

```bash
pip install tokenhelm                  # core (only dependency: PyYAML)
pip install "tokenhelm[all]"           # + all provider SDKs
```

Requires Python 3.11+. MIT licensed.
