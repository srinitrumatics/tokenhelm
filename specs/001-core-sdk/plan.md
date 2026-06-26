# Implementation Plan: TokenHelm Core SDK

**Branch**: `001-core-sdk` | **Date**: 2026-06-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-core-sdk/spec.md`

**Note**: This plan was produced by `/speckit-plan`. Phase 2 (`tasks.md`) is generated separately by `/speckit-tasks`.

## Summary

TokenHelm Core SDK v0.1 is a lightweight, framework-agnostic Python library that gives
developers token tracking, normalized usage events, and LLM cost calculation through a
single unified API across four providers (OpenAI, Gemini, Anthropic, Ollama). The
technical approach is a small dependency-light core (models, tracker, cost calculator,
event plumbing) with all variation isolated behind five replaceable extension-point
interfaces — `BaseAdapter`, `PricingProvider`, `EventDispatcher`, `Logger`, and
`StorageBackend` — and optional install extras. The `CostCalculator` depends only on the
`PricingProvider` abstraction (YAML is merely the default implementation); the tracker
emits events to an `EventDispatcher` and is unaware of where they are written; the
dispatcher fans out to one or more `Logger`s and, optionally, a `StorageBackend`.
Tracking is exposed both as a context manager (`tracker.trace()`) and as explicit manual
tracking (`tracker.track(response)`), supports streaming and async, and is thread-safe
with sub-5ms overhead. The user's milestone breakdown (M1 models → M8 docs) maps directly
onto the build order below.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Core has a minimal footprint — `PyYAML` is required only by the
default `YamlPricingProvider`, not by the core calculator (which depends on the
`PricingProvider` interface). Provider SDKs (`openai`, `google-genai`, `anthropic`,
`ollama`) are **optional extras**, imported lazily inside their adapters so the core never
hard-depends on them. TokenHelm observes/normalizes objects the developer's own provider
client returns; it does not call providers itself.

**Storage**: N/A for the runtime path. Pricing rates load from a bundled default
`pricing.yaml` plus optional user-supplied YAML. Event output destination is pluggable
(console / JSON / file / custom) and not a database.

**Testing**: `pytest` with `pytest-asyncio`; coverage via `pytest-cov` (target 90%).
Provider responses are captured as fixtures so adapter tests run offline with no network
or API keys.

**Target Platform**: Cross-platform pure-Python library (Linux, macOS, Windows),
importable from sync and async code. Distributed on PyPI.

**Project Type**: Library (single package, `packages/`-style layout with `core`,
`adapters`, `sdk`).

**Performance Goals**: <5 ms tracking overhead per request; <20 MB additional memory.

**Constraints**: Thread-safe; async-compatible; streaming-compatible; no provider-specific
logic in core; every major component (logger, storage, pricing provider, event exporter,
adapter) replaceable without editing the core; public API backwards-compatible within a
major version.

**Scale/Scope**: v0.1 = four adapters, one normalized event schema, sync + async +
streaming code paths. Additional providers are future adapters, not API changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` (v0.1.0):

| # | Principle | How this plan satisfies it | Status |
|---|-----------|----------------------------|--------|
| I | Framework Agnostic | Core depends on no AI framework; integration is by observing the developer's own provider client. | ✅ Pass |
| II | Provider Independence | All providers implement a shared `BaseAdapter`; no provider logic in core. | ✅ Pass |
| III | Zero Vendor Lock-in | Public API is provider-neutral; switching providers is configuration only. | ✅ Pass |
| IV | Developer Experience First | `tracker = TokenHelm()` + `with tracker.trace():` is ≤5 lines; YAML/config documented. | ✅ Pass |
| V | Lightweight Runtime | <5 ms / <20 MB targets; async + streaming + thread-safe by design; minimal deps. | ✅ Pass |
| VI | Extensibility | The five constitution-named components are first-class interfaces: `Logger`, `StorageBackend`, `PricingProvider`, `EventDispatcher` (event exporter), `BaseAdapter` — each replaceable without editing core. | ✅ Pass |
| VII | Standardized Data Model | Single normalized event with the 8 required fields; provider usage objects never leak. | ✅ Pass |
| VIII | Observability by Default | Tracking is on within the trace scope by default; metrics = tokens, latency, provider, model, cost. | ✅ Pass |
| IX | Testability | Adapter / cost / extraction / config tests; 90% coverage target; offline fixtures. | ✅ Pass |
| X | API Stability | Public surface is explicitly enumerated in `contracts/` and versioned (semver). | ✅ Pass |

No violations. Complexity Tracking section below is intentionally empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-core-sdk/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Feature spec (/speckit-specify output)
├── research.md          # Phase 0 output (/speckit-plan)
├── data-model.md        # Phase 1 output (/speckit-plan)
├── quickstart.md        # Phase 1 output (/speckit-plan)
├── contracts/           # Phase 1 output (/speckit-plan)
│   └── public-api.md    # Public SDK surface + normalized event contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (/speckit-specify)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/tokenhelm/
├── __init__.py              # Public exports: TokenHelm, LLMEvent, interfaces, impls, errors
├── core/
│   ├── models.py            # LLMProvider, LLMRequest, LLMUsage, LLMCost, LLMEvent
│   ├── tracker.py           # TokenTracker, StreamingTracker, LatencyTracker (emits to EventDispatcher)
│   ├── extraction.py        # UsageParser dispatch over adapters
│   ├── calculator.py        # CostCalculator (depends ONLY on PricingProvider), CurrencyFormatter
│   └── config.py            # Configuration loading + defaults
├── adapters/                # Extension point #1 — BaseAdapter
│   ├── base.py              # BaseAdapter (the common provider interface)
│   ├── openai.py            # OpenAIAdapter
│   ├── gemini.py            # GeminiAdapter
│   ├── anthropic.py         # AnthropicAdapter
│   └── ollama.py            # OllamaAdapter
├── pricing/                 # Extension point #2 — PricingProvider
│   ├── base.py              # PricingProvider interface
│   └── yaml_provider.py     # YamlPricingProvider (default impl; RemotePricingProvider/CustomPricingProvider future)
├── dispatch/                # Extension point #3 — EventDispatcher (the "event exporter")
│   ├── base.py              # EventDispatcher interface
│   └── default.py           # DefaultEventDispatcher (fans out to loggers + optional storage)
├── logging/                 # Extension point #4 — Logger
│   ├── base.py              # Logger protocol
│   ├── console.py           # ConsoleLogger
│   ├── json.py              # JSONLogger
│   └── file.py              # FileLogger
├── storage/                 # Extension point #5 — StorageBackend
│   ├── base.py              # StorageBackend interface
│   └── memory.py            # InMemoryStorageBackend (basic v0.1 impl)
├── sdk/
│   ├── client.py            # TokenHelm client: configure(), track(), trace(); wires the defaults
│   └── context.py           # trace() context manager (sync + async)
└── data/
    └── pricing.yaml         # Bundled default per-provider/model rates (loaded by YamlPricingProvider)

tests/
├── unit/
│   ├── test_models.py
│   ├── test_calculator.py        # CostCalculator against a fake PricingProvider
│   ├── test_pricing_provider.py  # YamlPricingProvider lookup + miss
│   ├── test_dispatch.py          # DefaultEventDispatcher fan-out
│   ├── test_extraction.py
│   ├── test_config.py
│   ├── test_loggers.py
│   └── test_storage.py           # InMemoryStorageBackend
├── adapters/
│   ├── fixtures/            # Captured provider response objects (offline)
│   ├── test_openai_adapter.py
│   ├── test_gemini_adapter.py
│   ├── test_anthropic_adapter.py
│   └── test_ollama_adapter.py
└── integration/
    ├── test_trace_context.py     # sync + async + streaming end-to-end
    └── test_thread_safety.py

examples/
├── openai_quickstart.py
├── anthropic_quickstart.py
└── custom_logger.py

docs/
├── installation.md
├── quickstart.md
├── configuration.md
└── api-reference.md

pyproject.toml               # Package metadata + optional extras (openai/gemini/anthropic/ollama/all)
```

**Structure Decision**: Single Python package `tokenhelm` under `src/` (src-layout for
clean test isolation). The five replaceable extension points each get their own
subpackage with an interface module plus a default implementation —
`adapters/` (BaseAdapter), `pricing/` (PricingProvider), `dispatch/` (EventDispatcher),
`logging/` (Logger), `storage/` (StorageBackend). `core/` holds provider-neutral logic
(models, tracker, calculator, config) and depends only on those interfaces, never on a
concrete implementation; `sdk/` is the developer-facing client that wires defaults
together. This realizes the user's proposed `packages/{core,adapters,sdk}` tree as Python
subpackages while keeping a single installable distribution, and makes Constitution
Principle VI structurally explicit.

## Complexity Tracking

> No Constitution Check violations. No entries required.
