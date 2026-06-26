---
description: "Task list for TokenHelm Core SDK implementation"
---

# Tasks: TokenHelm Core SDK

**Input**: Design documents from `specs/001-core-sdk/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public-api.md, quickstart.md

**Tests**: INCLUDED — required by Constitution Principle IX (automated tests for adapters,
cost calculator, token extraction, configuration; 90% coverage target) and the spec's
Acceptance Criteria.

**Organization**: Tasks are grouped by user story (US1–US4 from spec.md) for independent
implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps the task to a user story (US1, US2, US3, US4)
- Exact file paths are included in each description

## Path Conventions

Single Python package, src-layout: `src/tokenhelm/`, tests at `tests/`, per plan.md.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and structure

- [X] T001 Create the source/test/docs tree per plan.md: `src/tokenhelm/{core,adapters,pricing,dispatch,logging,storage,sdk,data}/`, `tests/{unit,adapters/fixtures,integration}/`, `examples/`, `docs/` (add `__init__.py` to each `src` subpackage)
- [X] T002 Author `pyproject.toml` (src-layout, Python 3.11+, runtime dep `PyYAML`; optional extras `openai`, `gemini`, `anthropic`, `ollama`, `all`, `dev`) at repo root
- [X] T003 [P] Configure Ruff lint+format settings in `pyproject.toml`
- [X] T004 [P] Configure pytest (with `pytest-asyncio`) and `pytest-cov` (fail-under 90, `benchmark` marker) in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provider-neutral core and the five extension-point interfaces that every user
story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement core data models (`LLMProvider`, `LLMUsage`, `LLMCost`, `RateEntry`, `LLMRequest`, `LLMEvent` with `to_dict()`, status flags `usage_complete`/`priced`) in `src/tokenhelm/core/models.py`
- [X] T006 [P] Define `BaseAdapter` interface (`provider`, `identify`, `extract_usage`, `extract_model`, optional `wrap_stream`) in `src/tokenhelm/adapters/base.py`
- [X] T007 [P] Define `PricingProvider` interface (`get_rates(provider, model) -> RateEntry | None`) in `src/tokenhelm/pricing/base.py`
- [X] T008 [P] Define `EventDispatcher` interface (`dispatch(event)`) in `src/tokenhelm/dispatch/base.py`
- [X] T009 [P] Define `Logger` protocol (`log(event)`) in `src/tokenhelm/logging/base.py`
- [X] T010 [P] Define `StorageBackend` interface (`save(event)`, `all()`) in `src/tokenhelm/storage/base.py`
- [X] T011 [P] Implement `LatencyTracker` (`time.perf_counter`) in `src/tokenhelm/core/tracker.py`
- [X] T012 [P] Implement configuration loading/defaults in `src/tokenhelm/core/config.py`
- [X] T013 [P] Define error types (`TokenHelmError`, `ProviderNotInstalledError`) in `src/tokenhelm/core/errors.py`

**Checkpoint**: Models + all five interfaces exist — user stories can begin.

---

## Phase 3: User Story 1 - Track usage and cost across one provider (Priority: P1) 🎯 MVP

**Goal**: A developer tracks one (non-streaming) provider call and receives a normalized
`LLMEvent` with all eight fields and a correctly computed cost.

**Independent Test**: Configure `TokenHelm()` with the OpenAI adapter, call
`tracker.track(openai_response)`, and assert the event has all 8 fields, `total = input +
output`, and `cost` matches configured pricing.

### Tests for User Story 1 ⚠️ (write first, ensure they FAIL)

- [X] T014 [P] [US1] Unit test `CostCalculator` (priced math with `Decimal`; unpriced → `priced=False`, cost 0) against a fake `PricingProvider` in `tests/unit/test_calculator.py`
- [X] T015 [P] [US1] Unit test `YamlPricingProvider` (bundled lookup + user override + miss→None) in `tests/unit/test_pricing_provider.py`
- [X] T016 [P] [US1] Adapter test for OpenAI (captured fixture → `LLMUsage`/model; `identify`) in `tests/adapters/test_openai_adapter.py` (fixture: `tests/adapters/fixtures/openai_response.json`)
- [X] T017 [P] [US1] Unit test extraction dispatch + missing-usage degradation (`usage_complete=False`) in `tests/unit/test_extraction.py`
- [X] T018 [P] [US1] Integration test single-`track()` event shape, 8-field presence, total invariant in `tests/integration/test_trace_context.py`

### Implementation for User Story 1

- [X] T019 [P] [US1] Bundled default per-provider/model rates (per-1M-token units) in `src/tokenhelm/data/pricing.yaml`
- [X] T020 [US1] Implement `YamlPricingProvider` (bundled `pricing.yaml` + optional YAML/dict overrides) in `src/tokenhelm/pricing/yaml_provider.py` (depends T007, T019)
- [X] T021 [US1] Implement `CostCalculator` + `CurrencyFormatter` depending ONLY on `PricingProvider` in `src/tokenhelm/core/calculator.py` (depends T005, T007)
- [X] T022 [P] [US1] Implement `ConsoleLogger` in `src/tokenhelm/logging/console.py` (depends T009)
- [X] T023 [US1] Implement `DefaultEventDispatcher` (fan-out to loggers + optional storage) in `src/tokenhelm/dispatch/default.py` (depends T008, T009, T010)
- [X] T024 [P] [US1] Implement `OpenAIAdapter` (lazy `openai` import; `identify`/`extract_usage`/`extract_model`) in `src/tokenhelm/adapters/openai.py` (depends T006)
- [X] T025 [US1] Implement `UsageParser` extraction dispatch/adapter registry in `src/tokenhelm/core/extraction.py` (depends T006, T024)
- [X] T026 [US1] Implement `TokenTracker` (build `LLMEvent` via adapter + calculator + latency; per-scope `contextvars` state; emit to dispatcher) in `src/tokenhelm/core/tracker.py` (depends T005, T011, T021, T023, T025)
- [X] T027 [US1] Implement `TokenHelm` client `__init__`/`configure`/`track()` and sync `trace()` context manager in `src/tokenhelm/sdk/client.py` and `src/tokenhelm/sdk/context.py` (depends T026)
- [X] T028 [US1] Wire public exports (`TokenHelm`, `LLMEvent`, `LLMProvider`, interfaces, default impls, errors) in `src/tokenhelm/__init__.py` (depends T027)

**Checkpoint**: One provider tracked end-to-end; MVP is testable and demoable.

---

## Phase 4: User Story 2 - Switch providers without changing tracking code (Priority: P2)

**Goal**: The same tracking workflow runs against any of OpenAI, Gemini, Anthropic, Ollama
and yields events of identical shape; switching is configuration only.

**Independent Test**: Run `tracker.track()` against fixtures for all four providers and
assert identical field sets; assert Ollama zero-rate model → `cost == 0` without error.

### Tests for User Story 2 ⚠️

- [X] T029 [P] [US2] Adapter test for Gemini (fixture → usage/model) in `tests/adapters/test_gemini_adapter.py` (fixture: `tests/adapters/fixtures/gemini_response.json`)
- [X] T030 [P] [US2] Adapter test for Anthropic (`usage.input_tokens`/`output_tokens`, cache extras) in `tests/adapters/test_anthropic_adapter.py` (fixture: `tests/adapters/fixtures/anthropic_response.json`)
- [X] T031 [P] [US2] Adapter test for Ollama (`prompt_eval_count`/`eval_count`; missing-usage path) in `tests/adapters/test_ollama_adapter.py` (fixture: `tests/adapters/fixtures/ollama_response.json`)
- [X] T032 [P] [US2] Integration test: identical event shape across all four providers + Ollama zero-rate cost in `tests/integration/test_provider_parity.py`

### Implementation for User Story 2

- [X] T033 [P] [US2] Implement `GeminiAdapter` (`usage_metadata.*`; duck-typed, no SDK import) in `src/tokenhelm/adapters/gemini.py` (depends T006)
- [X] T034 [P] [US2] Implement `AnthropicAdapter` (`usage.input_tokens`/`output_tokens` + cache token extras into `LLMUsage.extra`) in `src/tokenhelm/adapters/anthropic.py` (depends T006)
- [X] T035 [P] [US2] Implement `OllamaAdapter` (`prompt_eval_count`/`eval_count`; graceful missing-usage) in `src/tokenhelm/adapters/ollama.py` (depends T006)
- [X] T036 [US2] Register the three new adapters in the default adapter set in `src/tokenhelm/adapters/__init__.py` (`default_adapters()` — relocated here from `core/extraction.py` during the MVP decoupling review so core depends only on `BaseAdapter`) (depends T025, T033, T034, T035)
- [X] T037 [US2] Bundled rates for the new providers/models present in `src/tokenhelm/data/pricing.yaml` (depends T019)

**Checkpoint**: All four providers produce identical-shape events; provider switch is config-only.

---

## Phase 5: User Story 3 - Choose how usage is recorded (Priority: P2)

**Goal**: Events can be delivered to console/JSON/file or a custom sink, to multiple sinks
at once via the dispatcher, and optionally persisted — without modifying the library.

**Independent Test**: Track a request with each built-in logger, a custom callable, and a
multi-logger + storage configuration; confirm each records the event and storage holds it.

### Tests for User Story 3 ⚠️

- [X] T038 [P] [US3] Unit test `ConsoleLogger`/`JSONLogger`/`FileLogger` output formats in `tests/unit/test_loggers.py`
- [X] T039 [P] [US3] Unit test `DefaultEventDispatcher` multi-logger fan-out + storage forwarding + custom callable sink + ordering + isolation + event immutability in `tests/unit/test_dispatch.py`
- [X] T040 [P] [US3] Unit test `InMemoryStorageBackend` (`save`/`all`) in `tests/unit/test_storage.py`
- [X] T041 [P] [US3] Unit test client accepts a `PricingProvider` instance, logger list/callable, custom `adapters`, and `configure()` wiring in `tests/unit/test_config.py`

### Implementation for User Story 3

- [X] T042 [P] [US3] Implement `JSONLogger` (one JSON object per event) in `src/tokenhelm/logging/json.py` (depends T009)
- [X] T043 [P] [US3] Implement `FileLogger` (JSON lines, append mode) in `src/tokenhelm/logging/file.py` (depends T009)
- [X] T044 [P] [US3] Implement `InMemoryStorageBackend` in `src/tokenhelm/storage/memory.py` (depends T010)
- [X] T045 [US3] Extend `TokenHelm.__init__`/`configure` to accept `logger` list/callable, `pricing` as `PricingProvider`, `dispatcher`, `storage` (single or list), and `adapters`; build `DefaultEventDispatcher` from them in `src/tokenhelm/sdk/client.py` (depends T027, T042, T043, T044)
- [X] T046 [US3] Export `JSONLogger`, `FileLogger`, `InMemoryStorageBackend` in `src/tokenhelm/__init__.py` (depends T028, T042, T043, T044)

**Checkpoint**: Output is fully pluggable; multiple sinks + storage + pricing swap work.

---

## Phase 6: User Story 4 - Track streaming responses (Priority: P3)

**Goal**: A streamed response, once fully consumed, produces exactly one normalized event
with final aggregated totals; async tracking behaves identically.

**Independent Test**: Wrap a streamed fixture with `track_stream()`, consume it fully, and
assert exactly one `LLMEvent` with final totals; run the async `trace()` path.

### Tests for User Story 4 ⚠️

- [X] T047 [P] [US4] Integration test streaming → single final event with aggregated totals (per provider's end-of-stream usage) + provider parity in `tests/integration/test_streaming.py`
- [X] T048 [P] [US4] Integration test async `trace()`/`track_stream()` parity, concurrent isolation, nested scopes, cancellation/exception cleanup in `tests/integration/test_streaming.py`

### Implementation for User Story 4

- [X] T049 [US4] Implement streaming emit path: `TokenTracker.emit_stream` (one immutable event on finalization) + provider-agnostic `StreamSession` (wrap/manual, sync/async) in `src/tokenhelm/core/tracker.py` and `src/tokenhelm/sdk/context.py` (depends T026)
- [X] T050 [P] [US4] Add per-adapter `StreamAggregator` + `identify_stream` (OpenAI `include_usage` chunk, Anthropic `message_start`/`message_delta`, Gemini final-chunk `usage_metadata`, Ollama final `done`) in `src/tokenhelm/adapters/{openai,gemini,anthropic,ollama}.py` (depends T024, T033, T034, T035)
- [X] T051 [US4] Add `track_stream()` to the client and async `__aenter__`/`__aexit__` to `trace()` (+ `StreamSession` async iteration) in `src/tokenhelm/sdk/client.py` and `src/tokenhelm/sdk/context.py` (depends T027, T049, T050)

**Checkpoint**: Streaming and async paths produce correct single events.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Concerns spanning all stories; non-functional gates; release.

- [X] T052 [P] [US1] Capture provider response fixtures for all four providers (response + stream) in `tests/adapters/fixtures/`
- [X] T053 Integration test thread/async concurrency isolation (no cross-contamination of counts) in `tests/integration/test_thread_safety.py`
- [X] T054 [P] Benchmark: per-`track()` overhead < 5 ms and streaming memory < 20 MB (marker `benchmark`) in `tests/integration/test_benchmarks.py`
- [X] T055 [P] Write `docs/installation.md`, `docs/quickstart.md`, `docs/configuration.md`, `docs/api-reference.md`
- [X] T056 [P] Add runnable examples `examples/openai_quickstart.py`, `examples/anthropic_quickstart.py`, `examples/custom_logger.py`
- [X] T057 [P] Author `README.md` and `CHANGELOG.md` at repo root (+ `LICENSE`, `CONTRIBUTING.md`)
- [X] T058 Verify coverage ≥ 90% (`pytest --cov=tokenhelm --cov-report=term-missing`) — 95.62%
- [X] T059 Finalize PyPI packaging metadata/classifiers + `py.typed` in `pyproject.toml`; `python -m build` produces sdist + wheel (twine upload pending credentials)
- [X] T060 Run `specs/001-core-sdk/quickstart.md` validation end-to-end and check off its acceptance checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (P1)**: no dependencies.
- **Foundational (P2)**: depends on Setup — BLOCKS all user stories.
- **US1 (P3)**: depends on Foundational. The shared engine (calculator, dispatcher,
  tracker, client) is built here, so **US2/US3/US4 depend on US1**.
- **US2 (P4)**: depends on US1 (adapter pattern + extraction registry + client).
- **US3 (P5)**: depends on US1 (dispatcher/logger seams + client).
- **US4 (P6)**: depends on US1 (tracker/client); touches all adapters.
- **Polish (P7)**: depends on all targeted stories.

### User Story Dependencies

- US1 = MVP, standalone after Foundational.
- US2, US3 build on US1 but are independently testable and mutually independent (different
  files: adapters vs loggers/dispatch/storage) — can proceed in parallel after US1.
- US4 builds on US1 and edits adapter files US2 created — sequence US4 after US2 (or
  coordinate the shared adapter files).

### Within Each User Story

- Tests written first and failing, then implementation.
- Models/interfaces (Foundational) → providers/pricing → tracker/dispatcher → client/wiring.

### Parallel Opportunities

- Setup: T003, T004 in parallel.
- Foundational: T006–T013 in parallel (distinct files) after T005.
- US1 tests T014–T018 in parallel; impl T019/T022/T024 in parallel.
- US2 adapters T033–T035 in parallel; tests T029–T032 in parallel.
- US3 impls T042–T044 in parallel; tests T038–T041 in parallel.
- Polish: T054–T057 in parallel.

---

## Parallel Example: User Story 2

```bash
# Adapter implementations (independent files):
Task: "Implement GeminiAdapter in src/tokenhelm/adapters/gemini.py"
Task: "Implement AnthropicAdapter in src/tokenhelm/adapters/anthropic.py"
Task: "Implement OllamaAdapter in src/tokenhelm/adapters/ollama.py"

# Adapter tests (independent fixtures/files):
Task: "Adapter test for Gemini in tests/adapters/test_gemini_adapter.py"
Task: "Adapter test for Anthropic in tests/adapters/test_anthropic_adapter.py"
Task: "Adapter test for Ollama in tests/adapters/test_ollama_adapter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1 → **STOP & VALIDATE** (track one
   OpenAI response, get a correct normalized event) → demo.

### Incremental Delivery

- US1 (MVP: one provider) → US2 (all four providers) → US3 (pluggable output + storage) →
  US4 (streaming + async) → Polish (docs, benchmarks, coverage, PyPI). Each story adds value
  without breaking prior stories.

### Parallel Team Strategy

After US1 lands, one developer takes US2 (adapters) while another takes US3
(loggers/dispatch/storage); US4 follows US2 to avoid adapter-file contention.

---

## Notes

- [P] = different files, no incomplete dependencies.
- Tests are required (Constitution IX); verify they fail before implementing.
- Adapters lazy-import their provider SDK and raise `ProviderNotInstalledError` if the
  extra is absent — adapter tests use offline fixtures, no API keys.
- `CostCalculator` must depend only on `PricingProvider`; the tracker must emit only to an
  `EventDispatcher` — keep these seams clean (Decisions 3 & 4).
- Commit after each task or logical group; stop at any checkpoint to validate.
