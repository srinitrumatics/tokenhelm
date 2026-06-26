# TokenHelm

**Lightweight, framework-agnostic token tracking and LLM cost calculation across providers.**

TokenHelm gives you one normalized usage/cost event for every LLM call — OpenAI, Gemini,
Anthropic, or Ollama — without locking you into any framework, patching any provider SDK, or
ever touching your credentials. It simply **observes** the response object your own client
already returns.

```python
from tokenhelm import TokenHelm

tracker = TokenHelm()                      # zero-config
response = client.chat.completions.create(...)   # your own OpenAI call
event = tracker.track(response)            # normalized LLMEvent
print(event.to_dict())
# {'provider': 'openai', 'model': 'gpt-4o', 'input_tokens': 1000,
#  'output_tokens': 500, 'total_tokens': 1500, 'latency': 0.0,
#  'cost': '0.00750', 'timestamp': '...', 'usage_complete': True,
#  'priced': True, 'currency': 'USD'}
```

---

## Installation

```bash
pip install tokenhelm                  # core (only dependency: PyYAML)
pip install "tokenhelm[openai]"        # + OpenAI extras (for your own client)
pip install "tokenhelm[anthropic]"     # + Anthropic
pip install "tokenhelm[gemini]"        # + Google Gemini
pip install "tokenhelm[ollama]"        # + Ollama
pip install "tokenhelm[all]"           # all provider extras
pip install "tokenhelm[dev]"           # test/lint toolchain
```

Requires **Python 3.11+**. The extras only pull in the provider SDKs *you* call — TokenHelm
itself never imports them to read a response.

---

## Quick Start

```python
from tokenhelm import TokenHelm

tracker = TokenHelm()

# 1. Manual tracking — track any completed response
event = tracker.track(response)

# 2. Scoped tracking — collect every event in a block
with tracker.trace() as scope:
    response = client.chat.completions.create(...)
    scope.track(response)
print(scope.events)           # [LLMEvent(...)]

# 3. Choose where events go (any logger, callable, or storage)
from tokenhelm import ConsoleLogger
tracker = TokenHelm(logger=[ConsoleLogger(), lambda e: metrics.push(e.to_dict())])

# 4. Bring your own pricing (file, dict, or a full PricingProvider)
tracker = TokenHelm(pricing="my_rates.yaml")
tracker = TokenHelm(pricing={"openai": {"gpt-4o": {"input": 2.5, "output": 10.0}}})

# 5. Reconfigure later without rebuilding
tracker.configure(currency="EUR")

# 6. Streaming — exactly one event after the stream is exhausted
for chunk in tracker.track_stream(client.chat.completions.create(..., stream=True)):
    ...   # consume chunks as usual

# 7. Async — same API with `async with` / `async for`
async with tracker.trace() as scope:
    scope.track(await aclient.chat.completions.create(...))
```

Every tracked request yields the same normalized **`LLMEvent`** with the eight mandated
fields — `provider, model, input_tokens, output_tokens, total_tokens, latency, cost,
timestamp` — plus `usage_complete` / `priced` status flags. Consumers never see a
provider-specific usage object. Costs use `decimal.Decimal` (no float drift). Missing usage or
unknown pricing degrade gracefully via the flags — tracking never raises on missing data.

---

## Architecture

TokenHelm is built around five replaceable extension points; the core depends only on their
interfaces, never on a concrete implementation.

```
            ┌──────────────────────────────────────────────────────────┐
            │                     Your Application                       │
            └───────────────────────────┬──────────────────────────────┘
                                         │  track() / trace() / configure()
                                         ▼
                              ┌────────────────────┐
                              │      TokenHelm      │   (sdk: client + TraceScope)
                              └─────────┬──────────┘
                                        ▼
                              ┌────────────────────┐
                              │    TokenTracker     │   builds the normalized LLMEvent
                              └───┬────────────┬───┘
                  extract usage  │            │  compute cost
                                 ▼            ▼
                   ┌──────────────────┐   ┌──────────────────┐
                   │   BaseAdapter ①  │   │ CostCalculator   │
                   │ OpenAI/Gemini/   │   └────────┬─────────┘
                   │ Anthropic/Ollama │            ▼
                   └──────────────────┘   ┌──────────────────┐
                                          │ PricingProvider ② │  (YAML default)
                                          └──────────────────┘
                                        │
                                        ▼  emit (tracker is unaware of sinks)
                              ┌────────────────────┐
                              │  EventDispatcher ③ │
                              └───┬────────────┬───┘
                                  ▼            ▼
                        ┌──────────────┐  ┌──────────────────┐
                        │   Logger ④   │  │ StorageBackend ⑤ │  (optional)
                        │ Console/...  │  └──────────────────┘
                        └──────────────┘
```

**Extension points** (all public & stable — Constitution Principle VI):

| # | Interface | Default | Swap it to… |
|---|-----------|---------|-------------|
| ① | `BaseAdapter` | OpenAI, Gemini, Anthropic, Ollama | add a new provider |
| ② | `PricingProvider` | `YamlPricingProvider` | remote/dynamic pricing, AI FinOps |
| ③ | `EventDispatcher` | `DefaultEventDispatcher` | custom routing/batching/export |
| ④ | `Logger` | `ConsoleLogger` | JSON/file/metrics/dashboards |
| ⑤ | `StorageBackend` | none (opt-in) | in-memory/SQLite/warehouse/analytics |

**Dependency direction is strictly one-way** (no reverse dependencies):

```
Application → TokenHelm → TokenTracker → EventDispatcher → Logger / StorageBackend
                              └────────→ CostCalculator → PricingProvider
                              └────────→ UsageParser → BaseAdapter
```

`CostCalculator` depends *only* on `PricingProvider`; `TokenTracker` emits *only* through
`EventDispatcher`. Analytics, dashboards, and FinOps are downstream consumers of `LLMEvent`
behind these interfaces — they require no change to the core.

---

## Supported Providers

All four providers are supported, with streaming and async, in v0.1.0.

| Provider | Status | Usage fields read |
|----------|--------|-------------------|
| **OpenAI** | ✅ supported | `usage.prompt_tokens` / `completion_tokens` (Chat); `input_tokens` / `output_tokens` (Responses) |
| **Google Gemini** | ✅ supported | `usage_metadata.prompt_token_count` / `candidates_token_count` |
| **Anthropic** | ✅ supported | `usage.input_tokens` / `output_tokens` (+ cache token extras) |
| **Ollama** (local) | ✅ supported | `prompt_eval_count` / `eval_count` |

All providers normalize into the **same** `LLMEvent` schema — switching providers is a
configuration change, not a code change. Each adapter handles both completed responses and
streaming.

---

## Roadmap

**v0.1.0 — Core SDK ✅ (current)**

- [x] Track usage and cost across one provider (MVP): cost calculation, normalized event,
      scoped `trace()`, console logging, graceful degradation.
- [x] Provider parity: OpenAI, Gemini, Anthropic, Ollama adapters; identical event shape.
- [x] Output choice: `JSONLogger`, `FileLogger`, `InMemoryStorageBackend`, full `configure()`
      and multi-sink dispatch.
- [x] Streaming & async: `track_stream()` (one final event), async `trace()`.
- [x] Hardening: <5 ms / <20 MB budgets, thread/async isolation suite, docs, packaging.

**Beyond v0.1** — each tier is additive on the five extension points; the v0.1 core API does
not change. See [`ROADMAP.md`](ROADMAP.md).

- [ ] **v0.2 — Analytics SDK** (`SQLiteStorageBackend` + usage queries)
- [ ] **v0.3 — Prompt Intelligence** (per-prompt/template attribution)
- [ ] **v0.4 — RAG Intelligence** (retrieval-aware accounting)
- [ ] **v0.5 — AI FinOps** (budgets, alerts, remote pricing)
- [ ] **v1.0 — Enterprise Platform** (stabilize the v0.x surface; dashboard, plugins)

---

## Design principles

Framework-agnostic · provider-independent · zero vendor lock-in · <5 ms overhead ·
observe-don't-patch · one standardized event · everything replaceable.

See `specs/001-core-sdk/` for the constitution, spec, plan, data model, and public API
contract.

## Release Process

Releases follow a documented, automated procedure (Conventional Commits → release-please →
Trusted Publishing on PyPI via OIDC). The canonical, end-to-end release procedure is the
**[Go-Live & Release checklist](docs/go-live-checklist.md)** — follow it for every release.

Supporting docs:

- [`docs/releasing.md`](docs/releasing.md) — how publishing works (TestPyPI → PyPI, OIDC).
- [`docs/repository-setup.md`](docs/repository-setup.md) — branch protection, required checks,
  Dependabot, security features.
- [`docs/release-checklist.md`](docs/release-checklist.md) — per-version quality gates.

Contributors: see [`CONTRIBUTING.md`](CONTRIBUTING.md) for the dev workflow, versioning, and
deprecation policy.

## License

MIT

