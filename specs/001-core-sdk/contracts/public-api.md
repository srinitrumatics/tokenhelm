# Public API Contract: TokenHelm Core SDK v0.1

This is the **versioned public surface** (Principle X — backwards compatible within a major
version). Anything not listed here is internal and may change. Signatures are descriptive
Python; types reference the entities in `data-model.md`.

## Package exports (`from tokenhelm import ...`)

```python
TokenHelm          # the client
LLMEvent           # the normalized event (read-only consumer type)
LLMProvider        # provider enum

# Extension-point interfaces (Constitution Principle VI)
BaseAdapter        # provider adapter contract
PricingProvider    # pricing source contract
EventDispatcher    # event-exporter contract
Logger             # output-mechanism protocol
StorageBackend     # persistence contract

# Default implementations
YamlPricingProvider                      # default PricingProvider
DefaultEventDispatcher                   # default EventDispatcher
ConsoleLogger, JSONLogger, FileLogger    # built-in Loggers
InMemoryStorageBackend                   # default StorageBackend

TokenHelmError, ProviderNotInstalledError   # error types
```

## `TokenHelm` client

```python
class TokenHelm:
    def __init__(
        self,
        *,
        # Logger(s): one, many, or a callable. Wrapped in the default dispatcher.
        logger: Logger | Callable[[LLMEvent], None]
              | list[Logger | Callable[[LLMEvent], None]] | None = None,
        # Pricing source. A str/Path/dict is sugar for the default YamlPricingProvider;
        # pass a PricingProvider to fully swap the source (remote/custom).
        pricing: PricingProvider | str | Path | dict | None = None,
        # Full control of the event pipeline; overrides `logger`/`storage` if given.
        dispatcher: EventDispatcher | None = None,
        # Optional persistence; off by default. Added to the default dispatcher.
        storage: StorageBackend | None = None,
        currency: str = "USD",
    ) -> None: ...
```

- Construct with zero arguments for the common case (`tracker = TokenHelm()`), satisfying
  the ≤5-line integration goal (SC-001). Defaults: a `ConsoleLogger` wrapped in a
  `DefaultEventDispatcher`, a `YamlPricingProvider` over bundled rates, no storage.
- `pricing` as `str`/`Path`/`dict` configures the default `YamlPricingProvider`; passing a
  `PricingProvider` instance swaps the source entirely (Decision 3). Unknown models remain
  "unpriced".
- `dispatcher` lets advanced users replace the whole event pipeline; otherwise the client
  builds a `DefaultEventDispatcher` from `logger` + `storage` (Decision 4). The tracker
  only ever talks to the dispatcher.

### `configure()`

```python
def configure(
    self,
    *,
    logger: ... = ...,
    pricing: PricingProvider | str | Path | dict | None = ...,
    dispatcher: EventDispatcher | None = ...,
    storage: StorageBackend | None = ...,
    currency: str | None = ...,
) -> None: ...
```

Post-construction reconfiguration of the same knobs. Only provided arguments change
(FR-005 — pricing configurable; FR-010 — logger selectable).

### `track()` — manual tracking (FR-007)

```python
def track(self, response: object) -> LLMEvent: ...
```

- Accepts a completed provider response object from any supported provider.
- Auto-detects the provider via adapter `identify()`, normalizes usage, computes cost,
  builds and emits an `LLMEvent`, and returns it.
- Degrades gracefully (FR-013): missing usage → `usage_complete=False`; missing pricing →
  `priced=False`. Never raises on missing data; raises `ProviderNotInstalledError` only if
  the matching provider's extra isn't installed, and `TokenHelmError` if no adapter
  recognizes the object.

### `trace()` — scoped tracking (FR-006)

```python
def trace(self) -> TraceScope: ...        # usable as sync OR async context manager
```

Usage:

```python
with tracker.trace() as scope:
    response = client.responses.create(...)   # developer's own call
    scope.track(response)                      # or scope returns events it collected
# scope.events -> list[LLMEvent] available after exit
```

- Supports `with` and `async with` (FR-011).
- Each scope is isolated via context-local state so concurrent traces across threads/tasks
  never cross-contaminate (FR-012, SC-007).
- `scope.events` exposes the `LLMEvent`s tracked within the scope.

### `track_stream()` — streaming (FR-008)

```python
def track_stream(self, stream: Iterable | AsyncIterable) -> Iterable | AsyncIterable: ...
```

- Wraps a provider stream; yields each chunk unchanged; on exhaustion emits exactly one
  `LLMEvent` with final aggregated totals (User Story 4). Works inside or outside a
  `trace()` scope.

## Normalized event (consumer-facing)

`LLMEvent` exposes the eight mandated fields plus status flags (see `data-model.md`):
`provider, model, input_tokens, output_tokens, total_tokens, latency, cost, timestamp`,
plus `usage_complete`, `priced`, and `cost_detail`. It is read-only for consumers and
serializes to a plain dict via `event.to_dict()` (JSON-safe).

**Guarantee**: consumers never receive a provider-specific usage object — only `LLMEvent`
(Principle VII / FR-003).

## Extension-point interfaces (Principle VI)

All five are public and stable. Each has a default implementation; core depends only on
the interfaces.

### `BaseAdapter` (provider adapter — extension point #1)

```python
class BaseAdapter(Protocol):
    @property
    def provider(self) -> LLMProvider: ...
    def identify(self, response: object) -> bool: ...
    def extract_usage(self, response: object) -> LLMUsage: ...
    def extract_model(self, response: object) -> str: ...
    def wrap_stream(self, stream): ...   # optional; capture final usage
```

Built-ins: `OpenAIAdapter`, `GeminiAdapter`, `AnthropicAdapter`, `OllamaAdapter`.

### `PricingProvider` (pricing source — extension point #2)

```python
class PricingProvider(Protocol):
    def get_rates(self, provider: LLMProvider, model: str) -> RateEntry | None: ...
```

- `CostCalculator` depends only on this (Decision 3). `None` → unpriced.
- Default: `YamlPricingProvider(path=None, overrides=None)` (bundled `pricing.yaml` +
  optional user YAML/dict). Future: `RemotePricingProvider`, `CustomPricingProvider`.

### `EventDispatcher` (event exporter — extension point #3)

```python
class EventDispatcher(Protocol):
    def dispatch(self, event: LLMEvent) -> None: ...
```

- The tracker emits here and is unaware of sinks (Decision 4).
- Default: `DefaultEventDispatcher(loggers, storage=None)` fans out to loggers + storage.

### `Logger` (output mechanism — extension point #4, FR-010)

```python
class Logger(Protocol):
    def log(self, event: LLMEvent) -> None: ...
```

- Any object with `log(event)`, or any `Callable[[LLMEvent], None]`, qualifies.
- Built-ins: `ConsoleLogger()`, `JSONLogger(stream=...)`, `FileLogger(path, *, append=True)`.

### `StorageBackend` (persistence — extension point #5)

```python
class StorageBackend(Protocol):
    def save(self, event: LLMEvent) -> None: ...
    def all(self) -> Iterable[LLMEvent]: ...
```

- Optional; off by default. Default: `InMemoryStorageBackend()`. Future: SQLite/file/remote.

## Errors

```python
class TokenHelmError(Exception): ...                 # base; e.g. unrecognized response
class ProviderNotInstalledError(TokenHelmError): ... # adapter's extra not installed
```

- Tracking never raises on missing usage or missing pricing — those are represented as
  flags on the event, not exceptions (FR-013).

## Stability statement

These names, call shapes, the eight event fields, and the five extension-point interfaces
(`BaseAdapter`, `PricingProvider`, `EventDispatcher`, `Logger`, `StorageBackend`) are the
v0.x public contract. Additive changes (new adapters, new pricing/storage/dispatcher
implementations, new optional kwargs, new event status flags) are minor; removing or
renaming any of the above, changing an interface method signature, or changing the eight
required event fields, requires a major version bump (Principle X).
