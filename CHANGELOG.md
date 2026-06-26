# Changelog

All notable changes to TokenHelm are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-26

First public release. Lightweight, framework-agnostic token tracking and LLM cost calculation.

### Added

- **Core SDK** — `TokenHelm` client with `track()`, `trace()` (sync + async context manager),
  `track_stream()` (sync/async, wrap or manual `consume`), and `configure()`.
- **Normalized event** — immutable `LLMEvent` with the eight mandated fields
  (`provider, model, input_tokens, output_tokens, total_tokens, latency, cost, timestamp`)
  plus `usage_complete` / `priced` status flags and `to_dict()` JSON serialization.
- **Provider adapters** (observe-don't-patch, no SDK import required to normalize):
  OpenAI, Anthropic, Gemini, Ollama — non-streaming and streaming.
- **Cost calculation** — `CostCalculator` (depends only on `PricingProvider`) with
  `decimal.Decimal` precision; default `YamlPricingProvider` over bundled rates with
  file/dict overrides.
- **Event pipeline** — `EventDispatcher` abstraction; `DefaultEventDispatcher` fans one
  immutable event out to multiple loggers and storage backends with ordering and
  per-sink failure isolation.
- **Loggers** — `ConsoleLogger`, `JSONLogger`, `FileLogger`, plus any `Callable[[LLMEvent], None]`.
- **Storage** — `StorageBackend` interface + `InMemoryStorageBackend` (opt-in).
- **Five extension points** — `BaseAdapter`, `PricingProvider`, `EventDispatcher`, `Logger`,
  `StorageBackend` — all public and stable; the core depends only on the interfaces.
- **Streaming aggregation** — per-adapter `StreamAggregator`; exactly one event per stream,
  graceful finalize on error/cancellation with partial metrics preserved (`request.error`).
- **Concurrency** — `contextvars`-based trace isolation across threads and asyncio tasks.

### Performance (measured, Python 3.13, single core)

- `track()` overhead: median ~0.011 ms, p99 ~0.028 ms (budget: < 5 ms).
- Streaming a 200k-chunk response: ~0 MiB added (chunks are passed through, never buffered).

[Unreleased]: https://github.com/quadkeys/tokenhelm/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/quadkeys/tokenhelm/releases/tag/v0.1.0
