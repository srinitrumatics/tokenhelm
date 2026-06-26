# TokenHelm Roadmap

Guiding principle: every tier below is **additive on the v0.1 extension points** — new packages
and optional extras that consume the normalized `LLMEvent` or implement an existing interface
(`BaseAdapter`, `PricingProvider`, `EventDispatcher`, `Logger`, `StorageBackend`). The v0.1
core API does not change. Per [SemVer](https://semver.org) (Principle X), new modules,
implementations, and optional keyword arguments are **MINOR**; nothing here requires a breaking
change to existing code.

> Dates are sequencing, not commitments. Each release ships behind an optional extra so the
> lean core stays dependency-light.

## v0.1 — Core SDK ✅ (released)

Token tracking, cost calculation, four providers, streaming, async, five extension points.
Public API frozen as the v0.x contract.

## v0.2 — Analytics SDK

Aggregate and query tracked usage.

- **New extra:** `tokenhelm[analytics]`.
- **Builds on:** `StorageBackend` (read-back) + `EventDispatcher` (rollups).
- **Expected public API:**
  ```python
  from tokenhelm.analytics import UsageAnalytics, SQLiteStorageBackend
  analytics = UsageAnalytics(storage=SQLiteStorageBackend("usage.db"))
  analytics.summary(group_by="model", since="2026-01-01")   # tokens, cost, p50/p95 latency
  analytics.top_models(by="cost", limit=10)
  ```
- **Migration:** none. `TokenHelm(storage=SQLiteStorageBackend(...))` uses the existing kwarg;
  `InMemoryStorageBackend` keeps working. Adds `SQLiteStorageBackend` as a built-in.

## v0.3 — Prompt Intelligence

Per-prompt/template attribution and quality signals.

- **New extra:** `tokenhelm[prompt]`.
- **Builds on:** `LLMEvent.request` + `LLMUsage.extra` (cache/thinking tokens already preserved)
  and a new optional `metadata=` passthrough on `track()`/`trace()`.
- **Expected public API:**
  ```python
  with tracker.trace(metadata={"prompt_id": "summarize-v3"}) as scope:
      scope.track(response)
  from tokenhelm.prompt import PromptStats
  PromptStats(storage).by_prompt("summarize-v3")   # cost/tokens/cache-hit per template
  ```
- **Migration:** `metadata=` is an optional kwarg (additive). Events gain an optional
  `metadata` field (additive status data); existing consumers ignore it.

## v0.4 — RAG Intelligence

Retrieval-aware accounting (context tokens, retrieval cost, grounding ratio).

- **New extra:** `tokenhelm[rag]`.
- **Builds on:** a new `BaseAdapter`-style **retrieval adapter** family and `LLMUsage.extra`
  for context-token breakdowns; same `LLMEvent` pipeline.
- **Expected public API:**
  ```python
  from tokenhelm.rag import RagTracker
  rag = RagTracker(tracker)
  with rag.trace() as scope:
      scope.record_retrieval(chunks=8, context_tokens=4200)
      scope.track(llm_response)
  scope.events[-1].extra["context_tokens"]   # retrieval-aware metrics
  ```
- **Migration:** opt-in wrapper around the existing tracker; no change to core calls.

## v0.5 — AI FinOps

Budgets, alerts, chargeback, and live/remote pricing.

- **New extra:** `tokenhelm[finops]`.
- **Builds on:** `PricingProvider` (remote/dynamic rates) + `EventDispatcher`
  (budget/alert sinks).
- **Expected public API:**
  ```python
  from tokenhelm.finops import Budget, RemotePricingProvider, BudgetExceeded
  tracker = TokenHelm(
      pricing=RemotePricingProvider(url=...),
      dispatcher=Budget(limit_usd=500, on_exceeded=alert).as_dispatcher(),
  )
  ```
- **Migration:** `RemotePricingProvider` is just another `PricingProvider`; budgets are a
  dispatcher/logger. Both use existing kwargs. No breaking change.

## v1.0 — Enterprise Platform

Stabilize the v0.x surface as v1.0 and bundle the above behind a platform extra
(`tokenhelm[enterprise]`): multi-tenant storage, RBAC-aware exporters, dashboard server,
plugin registry.

- **Builds on:** all five extension points; the dashboard consumes `LLMEvent` via a
  `StorageBackend`/`EventDispatcher` — no core change.
- **Public API stability:** v1.0 promises backward compatibility within the 1.x line. Anything
  deprecated during 0.x (per the deprecation policy in `CONTRIBUTING.md`) is resolved before
  1.0. The eight `LLMEvent` fields and the five interfaces carry forward unchanged.
- **Migration:** v0.x → v1.0 is intended to be import-compatible; a `MIGRATING.md` will list any
  renamed-then-deprecated symbols with shims kept for one minor cycle.

## Cross-cutting (any release)

- Validate adapters against live provider SDK objects in CI.
- More providers (Bedrock, Vertex, Azure OpenAI, Mistral) as additional `BaseAdapter`s.
- Pricing freshness automation for bundled `pricing.yaml`.
