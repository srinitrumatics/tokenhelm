# Phase 0 Research: TokenHelm Core SDK

This document resolves the open design questions implied by the spec and constitution.
Each entry records the decision, the rationale, and the alternatives considered.

## R1 — How tracking captures a provider call (the `trace()` model)

**Decision**: TokenHelm **observes** objects the developer's own provider client returns,
rather than wrapping or patching the provider SDK. `tracker.trace()` opens a scope that
collects normalized events; inside it the developer either passes responses to
`tracker.track(response)` or returns them from a call the context manager is given a
handle to. Manual `tracker.track(response)` is always available and is the primitive that
`trace()` is built on.

**Rationale**: Constitution I/III forbid framework/provider coupling in the core.
Monkeypatching provider SDKs would couple us to each SDK's internals and break on their
upgrades. An observe-the-response model keeps the core neutral and the integration ≤5
lines (Principle IV). The developer keeps ownership of credentials and the actual API
call.

**Alternatives considered**:
- *Monkeypatch each provider client* — rejected: brittle, version-coupled, violates
  provider independence, hard to make thread-safe.
- *Proxy/wrapper client that makes the call for you* — rejected for v0.1: forces
  TokenHelm to manage credentials and request construction (vendor lock-in surface);
  can be added later as an optional convenience without changing the core.

## R2 — Normalizing usage across providers

**Decision**: Each adapter implements `extract_usage(response) -> LLMUsage` and
`identify(response) -> bool`. A `UsageParser` dispatch picks the adapter whose `identify`
matches the response object's type/shape. Provider field mappings for v0.1:

| Provider  | Input tokens | Output tokens | Notes |
|-----------|--------------|---------------|-------|
| OpenAI    | `usage.prompt_tokens` | `usage.completion_tokens` | `total_tokens` available; Responses API uses `input_tokens`/`output_tokens`. |
| Anthropic | `usage.input_tokens` | `usage.output_tokens` | Plus optional `cache_creation_input_tokens` / `cache_read_input_tokens` (captured as extra fields). |
| Gemini    | `usage_metadata.prompt_token_count` | `usage_metadata.candidates_token_count` | `total_token_count` available. |
| Ollama    | `prompt_eval_count` | `eval_count` | Local model; usage may be absent → degrade gracefully (FR-013). |

**Rationale**: Principle II/VII — a common interface and one normalized event; the
mapping table is the only place provider specifics live. Anthropic field names confirmed
against the Claude API reference (`usage.input_tokens` / `usage.output_tokens`, plus
cache token fields).

**Alternatives considered**: A single big `if/elif` parser in core — rejected: puts
provider logic in core (violates II). Per-adapter parsing keeps it isolated.

## R3 — Streaming token capture

**Decision**: `StreamingTracker` wraps the developer's stream iterator; it forwards chunks
unchanged and, on stream completion, reads the final usage. For providers that emit usage
only at the end of the stream (OpenAI requires `stream_options={"include_usage": True}`;
Anthropic carries it on the terminal `message_delta` / via `get_final_message()`;
Gemini on the final chunk's `usage_metadata`; Ollama on the final `done` chunk), the
single normalized event is produced once the stream is exhausted (User Story 4).

**Rationale**: Principle V (streaming-compatible) and FR-008 require exactly one event
with final aggregated totals. Wrapping the iterator avoids buffering the whole response in
memory (keeps the <20 MB target).

**Alternatives considered**: Summing per-chunk deltas ourselves — rejected: providers
already report authoritative end-of-stream totals; re-summing risks drift and double
counting. We document that callers enabling usage on the stream is required where the
provider gates it (e.g. OpenAI's `include_usage`).

## R4 — Pricing abstraction and cost math

**Decision**: Introduce a `PricingProvider` interface with one core method,
`get_rates(provider, model) -> RateEntry | None`. `CostCalculator` depends **only** on
this interface — it never reads YAML or any concrete source. v0.1 ships
`YamlPricingProvider` as the default implementation, which loads a per-provider/per-model
table of `input_rate`/`output_rate` (expressed as **cost per 1,000,000 tokens**) from a
bundled `pricing.yaml` plus optional user YAML/dict overrides. `RemotePricingProvider`
(fetch live rates) and `CustomPricingProvider` (developer-supplied logic) are named future
implementations that drop in without touching the calculator. `CostCalculator` computes
`input_cost = input_tokens / 1e6 * input_rate`, likewise output, `total = input + output`,
using `decimal.Decimal` to avoid float rounding error. A `None` rate (unknown model) →
event with token counts and a clearly-flagged "unpriced" cost (FR-013 / edge case).

**Rationale**: Principle VI explicitly names "Pricing Provider" as a replaceable component.
Coupling the calculator to YAML would make remote/custom pricing a core edit; depending on
an interface keeps the source swappable. Per-1M units keep the default config readable
(e.g. Opus 4.8 = 5.00 / 25.00); bundled defaults seeded from current public rates so the
common case needs no config (developer keeps rates current — spec Assumptions). PyYAML is
required only by `YamlPricingProvider`, not by core.

**Alternatives considered**: Calculator reads YAML directly — rejected: bakes the source
into core, blocking remote/custom providers (the user's explicit Decision 3). Per-token
float rates — rejected: unreadable and float-lossy.

## R5 — Event pipeline: EventDispatcher → Logger(s)/Storage

**Decision**: The tracker emits each `LLMEvent` to an `EventDispatcher`
(`dispatch(event: LLMEvent) -> None`) and is otherwise unaware of where events go. The
default `DefaultEventDispatcher` fans an event out to one or more `Logger`s and,
optionally, a `StorageBackend`. `Logger` is a one-method protocol
(`log(event) -> None`) with built-ins `ConsoleLogger`, `JSONLogger`, `FileLogger`; any
protocol-conforming object or `Callable[[LLMEvent], None]` qualifies. Flow:
`Tracker → LLMEvent → EventDispatcher → {ConsoleLogger, JSONLogger, FileLogger, custom}`
(+ optional `StorageBackend`).

**Rationale**: Principle VI names both "Event Exporter" and "Logger" as separate
replaceable components; the dispatcher is the exporter seam. Separating dispatch from
logging lets the tracker stay ignorant of sinks (the user's Decision 4) and lets multiple
sinks receive one event without the tracker fanning out itself. A structural `Protocol`
for `Logger` lets plain functions or third-party sinks qualify without inheritance.

**Alternatives considered**: Tracker holding a logger list and fanning out directly —
rejected: couples the tracker to sink management (violates Decision 4). A single logger
only — rejected: can't tee to console + file + metrics simultaneously.

## R8 — Storage backend

**Decision**: A `StorageBackend` interface (`save(event: LLMEvent) -> None`, plus a basic
`query`/iteration affordance) for persisting normalized events. v0.1 ships
`InMemoryStorageBackend` (keeps events in a list) as the basic implementation; it is
optional and off by default (events still flow to loggers). The `DefaultEventDispatcher`
forwards to a `StorageBackend` when one is configured. Durable backends (SQLite, file,
remote) are future implementations behind the same interface.

**Rationale**: Principle VI names "Storage" as a replaceable component. Defining the
interface now — even with only an in-memory impl — keeps later persistence additive and
non-breaking (Principle X). Off-by-default preserves the <5 ms / <20 MB budget for users
who only want logging.

**Alternatives considered**: Deferring storage entirely to a later version — rejected: the
user asked to define the extension point now; a stub interface costs little and prevents a
future API change. A mandatory always-on store — rejected: would add overhead and memory
the lightweight-runtime principle forbids by default.

## R6 — Async, thread-safety, and overhead budget

**Decision**: `trace()` provides both `__enter__/__exit__` and `__aenter__/__aexit__`.
Per-trace state lives in a context-local (`contextvars.ContextVar`) so concurrent traces
across threads and async tasks never share counters (edge case: concurrent tracked
requests). Latency is measured with `time.perf_counter()`. The hot path does only
arithmetic and a dataclass construction — no I/O — to stay under 5 ms; logging is the
only side effect and can be made async/deferred by a custom logger.

**Rationale**: Principle V (async, streaming, thread-safe, <5 ms) and FR-011/FR-012.
`contextvars` is the standard mechanism that works correctly under both threads and
asyncio.

**Alternatives considered**: Thread-local storage — rejected: does not propagate
correctly across `asyncio` tasks. A global lock around shared counters — rejected:
contention and avoidable; isolation via contextvars is cleaner and faster.

## R7 — Packaging and optional provider dependencies

**Decision**: One distribution `tokenhelm` with optional extras:
`tokenhelm[openai]`, `[gemini]`, `[anthropic]`, `[ollama]`, and `[all]`. Adapters import
their provider SDK **lazily inside the adapter module**, raising a clear, actionable error
if the extra isn't installed and that provider is used. Core import pulls in only PyYAML.

**Rationale**: Principle I/V (framework-agnostic, lightweight) and the Additional
Constraints in the constitution (minimal core footprint; provider-specific deps in extras).

**Alternatives considered**: Hard-depending on all four SDKs — rejected: heavy install,
violates the lightweight-core constraint. Separate distributions per adapter — rejected as
overkill for v0.1's four providers; extras give the same isolation with one package.

## R9 — The five extension-point interfaces

**Decision**: v0.1 defines all five Constitution-Principle-VI components as first-class
interfaces, each with at least one concrete implementation now:

| Interface | v0.1 default impl | Future impls (named, not built) |
|-----------|-------------------|----------------------------------|
| `BaseAdapter` | `OpenAIAdapter`, `GeminiAdapter`, `AnthropicAdapter`, `OllamaAdapter` | LangChain/CrewAI/etc. adapters |
| `PricingProvider` | `YamlPricingProvider` | `RemotePricingProvider`, `CustomPricingProvider` |
| `EventDispatcher` | `DefaultEventDispatcher` | async/batched dispatchers |
| `Logger` | `ConsoleLogger`, `JSONLogger`, `FileLogger` | OTel/metrics sinks |
| `StorageBackend` | `InMemoryStorageBackend` | SQLite/file/remote |

**Rationale**: Defining the seams now (per the user's "additional interfaces" request and
Principle VI) makes later capability additive rather than breaking (Principle X), at the
cost of a few thin interface modules. Core depends on the interfaces only.

**Alternatives considered**: Defining interfaces lazily as each feature lands — rejected:
risks a breaking API change when storage/remote-pricing arrive; the user explicitly asked
for the extension points up front.

## Resolved unknowns

All `NEEDS CLARIFICATION` items implied by the spec/constitution are resolved above. No
open questions block Phase 1.
