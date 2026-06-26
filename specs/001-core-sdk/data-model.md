# Phase 1 Data Model: TokenHelm Core SDK

Entities are realized as Python dataclasses in `src/tokenhelm/core/models.py` unless noted.
Field types are descriptive (implementation may refine). All monetary values use
`decimal.Decimal`; token counts are `int`; timestamps are timezone-aware `datetime` (UTC).

## LLMProvider (enum)

Identifies the source provider of a tracked request.

| Value | Meaning |
|-------|---------|
| `OPENAI` | OpenAI |
| `GEMINI` | Google Gemini |
| `ANTHROPIC` | Anthropic |
| `OLLAMA` | Ollama (local) |

- Open for extension: new providers add a member without changing the event schema.
- Serialized as its lowercase string name in events.

## LLMUsage

Normalized token usage extracted by an adapter. Provider-agnostic.

| Field | Type | Rules |
|-------|------|-------|
| `input_tokens` | int ≥ 0 | Prompt/input tokens. `None` only if the provider omitted usage (degraded). |
| `output_tokens` | int ≥ 0 | Completion/output tokens. Same nullability rule. |
| `total_tokens` | int ≥ 0 | Defaults to `input_tokens + output_tokens` if the provider doesn't supply it. |
| `extra` | dict | Optional provider extras kept out of the core schema (e.g. Anthropic `cache_read_input_tokens`). Never required by consumers. |

- Validation: `total_tokens == input_tokens + output_tokens` when all are present.
- Missing usage → fields may be `None` and the event flags `usage_complete = False`.

## LLMCost

Computed cost for a single request.

| Field | Type | Rules |
|-------|------|-------|
| `input_cost` | Decimal ≥ 0 | `input_tokens / 1e6 * input_rate`. |
| `output_cost` | Decimal ≥ 0 | `output_tokens / 1e6 * output_rate`. |
| `total_cost` | Decimal ≥ 0 | `input_cost + output_cost`. |
| `currency` | str | ISO 4217 code; defaults to `USD`. |
| `priced` | bool | `False` when the model had no pricing entry; costs are then `Decimal('0')` and flagged. |

- An unpriced request still yields a valid `LLMCost` (`priced = False`), never an error.

## LLMRequest

Lightweight descriptor of the tracked request context (what was tracked).

| Field | Type | Rules |
|-------|------|-------|
| `provider` | LLMProvider | Required. |
| `model` | str | Required; the model identifier reported by the response. |
| `streamed` | bool | True if produced via `StreamingTracker`. |
| `started_at` | datetime | Set when tracking begins (for latency). |

## LLMEvent (the normalized event — primary output)

The single standardized record every tracked request produces. This is the public
contract consumers receive (FR-003, Principle VII). Provider usage objects are **never**
exposed here.

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `provider` | str (LLMProvider value) | ✅ | Adapter |
| `model` | str | ✅ | Response |
| `input_tokens` | int \| None | ✅* | LLMUsage |
| `output_tokens` | int \| None | ✅* | LLMUsage |
| `total_tokens` | int \| None | ✅* | LLMUsage |
| `latency` | float (seconds) | ✅ | LatencyTracker |
| `cost` | Decimal | ✅ | LLMCost.total_cost |
| `timestamp` | datetime (UTC) | ✅ | Event creation time |
| `usage_complete` | bool | ✅ | False when provider omitted usage |
| `priced` | bool | ✅ | False when model pricing was missing |
| `cost_detail` | LLMCost | — | Full breakdown (input/output/currency) for consumers that want it |
| `request` | LLMRequest | — | Context (streamed flag, started_at) |

\* The eight constitution-mandated fields are always present as keys; token values may be
`None` in the degraded case, with `usage_complete = False` signalling it.

- Serializable to a plain dict / JSON (loggers rely on this).
- `total = input + output` invariant holds whenever all token values are present.

## BaseAdapter (interface, `adapters/base.py`)

Extension point #1 — not a data record but the contract every provider adapter satisfies.

| Member | Signature | Purpose |
|--------|-----------|---------|
| `provider` | property → LLMProvider | Which provider this adapter handles. |
| `identify(response)` | (object) → bool | True if this adapter can parse the response. |
| `extract_usage(response)` | (object) → LLMUsage | Normalize tokens. |
| `extract_model(response)` | (object) → str | Read the model id. |
| `wrap_stream(stream)` | (iterator) → iterator | Optional; yields chunks, captures final usage. |

- Adapters import their provider SDK lazily; absence raises a clear install error.

## RateEntry

A single pricing record returned by a `PricingProvider`.

| Field | Type | Rules |
|-------|------|-------|
| `provider` | LLMProvider | Required. |
| `model` | str | Required. |
| `input_rate` | Decimal ≥ 0 | Cost per 1,000,000 input tokens. |
| `output_rate` | Decimal ≥ 0 | Cost per 1,000,000 output tokens. |

## PricingProvider (interface, `pricing/base.py`)

Extension point #2. `CostCalculator` depends only on this — never on a concrete source.

| Member | Signature | Purpose |
|--------|-----------|---------|
| `get_rates(provider, model)` | (LLMProvider, str) → RateEntry \| None | Resolve rates; `None` = unpriced. |

- Default impl `YamlPricingProvider`: loads `(provider, model) -> {input_rate, output_rate}`
  from bundled `data/pricing.yaml` plus optional user YAML/dict overrides (user entries
  override/extend bundled by key). Per-1M-token units.
- Future impls (named, not built in v0.1): `RemotePricingProvider`, `CustomPricingProvider`.
- `CostCalculator` calls `get_rates`; a `None` result → `LLMCost(priced=False)`.

## EventDispatcher (interface, `dispatch/base.py`)

Extension point #3 — the "event exporter" seam. The tracker emits here and knows nothing
about sinks (Decision 4).

| Member | Signature | Purpose |
|--------|-----------|---------|
| `dispatch(event)` | (LLMEvent) → None | Route one event to all configured sinks. |

- Default impl `DefaultEventDispatcher(loggers, storage=None)`: fans `event` out to each
  `Logger`, then to the optional `StorageBackend`.

## Logger (interface, `logging/base.py`)

Extension point #4.

| Member | Signature | Purpose |
|--------|-----------|---------|
| `log(event)` | (LLMEvent) → None | Record/forward the normalized event. |

- Built-ins: `ConsoleLogger`, `JSONLogger`, `FileLogger`. Any callable `(LLMEvent) -> None`
  or protocol-conforming object is accepted (Principle VI).

## StorageBackend (interface, `storage/base.py`)

Extension point #5. Optional persistence of normalized events; off by default.

| Member | Signature | Purpose |
|--------|-----------|---------|
| `save(event)` | (LLMEvent) → None | Persist one event. |
| `all()` | () → Iterable[LLMEvent] | Read back stored events (basic query affordance). |

- Default impl `InMemoryStorageBackend`: appends events to an in-memory list.
- Future impls (not built in v0.1): SQLite / file / remote backends behind this interface.

## Relationships

```
LLMEvent ──contains──> LLMCost ──priced-by──> CostCalculator ──depends-on──> PricingProvider ──(RateEntry)
   │                                                                              (YamlPricingProvider default)
   ├──describes──> LLMRequest
   ├──derived-from──> LLMUsage <──extract_usage── BaseAdapter (OpenAI/Gemini/Anthropic/Ollama)
   └──emitted-to──> EventDispatcher ──fans-out──> Logger(s)  [+ optional StorageBackend]
```

A tracked request flows: provider response → `BaseAdapter.extract_usage/model` →
`LLMUsage` + `LLMRequest` → `CostCalculator` (via `PricingProvider.get_rates`) → `LLMCost`
→ `LLMEvent` → `EventDispatcher.dispatch` → `Logger`(s) and optional `StorageBackend`.
