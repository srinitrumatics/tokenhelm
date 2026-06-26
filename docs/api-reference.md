# API Reference

The public surface is everything exported from `tokenhelm`. These names, their call shapes, the
eight `LLMEvent` fields, and the five extension interfaces are the v0.x stable contract
(see `specs/001-core-sdk/contracts/public-api.md`).

## Client — `TokenHelm`

| Member | Signature | Notes |
|--------|-----------|-------|
| `__init__` | `(*, logger=None, pricing=None, dispatcher=None, storage=None, adapters=None, currency="USD")` | All keyword-only. Zero-config default = `ConsoleLogger` + bundled `YamlPricingProvider`. |
| `track` | `(response) -> LLMEvent` | Auto-detects provider, normalizes, prices, emits, returns the event. Attributes to the active `trace()` scope if any. |
| `trace` | `() -> TraceScope` | Scoped tracking; usable as `with` or `async with`. |
| `track_stream` | `(stream=None) -> StreamSession` | Wrap a provider stream (`for`/`async for`) or use as `with`/`async with` + `consume(chunk)`. Emits exactly one event on finalization. |
| `configure` | `(*, logger=…, pricing=…, dispatcher=…, storage=…, adapters=…, currency=…) -> None` | Reconfigure; only passed args change. |
| `currency` | `property -> str` | Active currency. |

`track()` is synchronous (pure-CPU normalization, no I/O) and is safe to call from async code.

## Event — `LLMEvent` (immutable)

Fields: `provider, model, input_tokens, output_tokens, total_tokens, latency, cost, timestamp`,
plus `usage_complete`, `priced`, `cost_detail` (`LLMCost`), `request` (`LLMRequest`).
`currency` property and `to_dict()` (JSON-safe) are provided. Frozen — every dispatcher sink
receives the same immutable instance.

Related models: `LLMProvider` (enum), `LLMUsage`, `LLMCost`, `LLMRequest` (`streamed`, `error`),
`RateEntry`.

## Extension interfaces

| Interface | Method(s) | Default impl |
|-----------|-----------|--------------|
| `BaseAdapter` | `provider`, `identify`, `extract_model`, `extract_usage`, `identify_stream`, `new_stream_aggregator` | `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`, `OllamaAdapter` |
| `StreamAggregator` | `consume`, `model`, `usage` | per-adapter aggregators |
| `PricingProvider` | `get_rates(provider, model) -> RateEntry \| None` | `YamlPricingProvider` |
| `EventDispatcher` | `dispatch(event) -> None` | `DefaultEventDispatcher` |
| `Logger` | `log(event) -> None` | `ConsoleLogger`, `JSONLogger`, `FileLogger` |
| `StorageBackend` | `save(event)`, `all()` | `InMemoryStorageBackend` |

## Sessions

- `TraceScope` — `events: list[LLMEvent]`, `track(response)`; sync + async context manager.
- `StreamSession` — `consume(chunk)`, `event`; sync/async, wrap or manual.

## Advanced

- `CostCalculator(pricing: PricingProvider, currency="USD")` — the costing engine used
  internally by the client. Exposed for standalone cost computation
  (`calc.compute(provider, model, usage) -> LLMCost`); it depends only on the
  `PricingProvider` interface. Most users should use `TokenHelm` instead.

## Errors

- `TokenHelmError` — base; e.g. no adapter recognized the object.
- `ProviderNotInstalledError` — a provider extra isn't installed.

Tracking never raises on missing data: missing usage → `usage_complete=False`; missing pricing
→ `priced=False`; a stream that ends abnormally → `request.error` set, partial metrics kept.
