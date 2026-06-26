<!--
SYNC IMPACT REPORT
==================
Version change: (uninitialized template) → 0.1.0
Bump rationale: Initial ratification of the TokenHelm constitution. First concrete
  version replacing the unfilled template, establishing 10 core principles plus
  governance. Per semver this is the initial adoption (0.1.0).

Modified principles: N/A (initial adoption)
Added sections:
  - Vision
  - Core Principles I–X (Framework Agnostic, Provider Independence, Zero Vendor
    Lock-in, Developer Experience First, Lightweight Runtime, Extensibility,
    Standardized Data Model, Observability by Default, Testability, API Stability)
  - Additional Constraints
  - Development Workflow & Quality Gates
  - Governance
Removed sections: None

Templates requiring updates:
  - ✅ .specify/templates/plan-template.md  (Constitution Check is generic; gates
       derived from this file at plan time — no hardcoded principle names to edit)
  - ✅ .specify/templates/spec-template.md  (no constitution references; no change)
  - ✅ .specify/templates/tasks-template.md (no constitution references; no change)

Follow-up TODOs: None
-->

# TokenHelm Constitution

## Vision

TokenHelm is an open-source AI infrastructure library that provides standardized
token tracking, cost calculation, and provider abstraction for Large Language Model
applications. The library MUST remain lightweight, framework-agnostic,
provider-independent, and extensible.

## Core Principles

### I. Framework Agnostic

TokenHelm MUST NOT depend on any specific AI orchestration framework. Applications
MUST be able to integrate TokenHelm regardless of the framework they use. Supported
integration targets include, but are not limited to: OpenAI SDK, Google Gemini,
Anthropic, Ollama, LangGraph, LlamaIndex, CrewAI, Google ADK, and LangChain.

Rationale: Framework lock-in fragments the ecosystem and forces rewrites; a neutral
core maximizes reach and longevity.

### II. Provider Independence

All providers MUST expose a common interface. The core package MUST NOT contain
provider-specific business logic. Every provider MUST be implemented as a dedicated
adapter extending a shared `BaseAdapter` (e.g. `OpenAIAdapter`, `GeminiAdapter`,
`AnthropicAdapter`, `OllamaAdapter`).

Rationale: A single contract keeps the core stable and makes new providers additive
rather than invasive.

### III. Zero Vendor Lock-in

The SDK MUST allow applications to switch LLM providers without changing TokenHelm
APIs. Provider-specific implementation details MUST live only inside adapters and
MUST NOT leak into public APIs.

Rationale: Users adopt TokenHelm to gain portability; leaking provider specifics
would defeat the library's purpose.

### IV. Developer Experience First

Integration MUST require fewer than five lines of code for the common case.
Configuration MUST be simple and documented. The canonical usage pattern is:

```python
tracker = TokenHelm()
with tracker.trace():
    llm.invoke(...)
```

Rationale: Adoption is gated by first-run friction; a tiny surface area drives use.

### V. Lightweight Runtime

The SDK MUST introduce minimal runtime overhead. It MUST be async-compatible,
streaming-compatible, and thread-safe. Tracking overhead MUST target under 5 ms per
request.

Rationale: Observability that meaningfully slows inference will be disabled in
production; overhead must be negligible to stay on.

### VI. Extensibility

Every major component MUST be replaceable without modifying SDK core. This includes
at minimum: Logger, Storage, Pricing Provider, Event Exporter, and Adapter. Plugins
MUST NOT require forking or editing the core.

Rationale: A replaceable-component design lets teams meet their own infrastructure
constraints without maintaining a fork.

### VII. Standardized Data Model

Every LLM request MUST produce a normalized event. Each event MUST include at
minimum: `provider`, `model`, `input_tokens`, `output_tokens`, `total_tokens`,
`latency`, `cost`, and `timestamp`. Applications MUST NEVER receive provider-specific
usage objects from public APIs.

Rationale: A single schema makes downstream analytics, cost reporting, and tooling
portable across providers.

### VIII. Observability by Default

Every request MUST be observable. Exposed metrics MUST include token usage, latency,
provider, model, and estimated cost. Observability MUST be on by default, not an
opt-in afterthought.

Rationale: Cost and usage visibility is the core value proposition; it must require
no extra wiring.

### IX. Testability

Every module MUST have automated tests. Test coverage MUST include, at minimum:
adapter tests, cost calculator tests, token extraction tests, and configuration
tests. The project targets 90% coverage.

Rationale: Correct token and cost accounting is the product's promise; regressions
are unacceptable and must be caught automatically.

### X. API Stability

Public SDK APIs MUST remain backwards compatible within a major version. Breaking
changes to public APIs MUST be accompanied by a major version bump.

Rationale: Users build cost-critical pipelines on these APIs; predictable
compatibility is required for trust.

## Additional Constraints

- The core package MUST have a minimal dependency footprint; heavy or
  provider-specific dependencies belong to optional adapter extras.
- Provider-specific code MUST reside exclusively within its adapter module.
- The public API surface MUST be explicitly documented and versioned.

## Development Workflow & Quality Gates

- Every change MUST pass the automated test suite before merge.
- New providers MUST be added as adapters implementing the common interface; they
  MUST NOT introduce provider-specific logic into the core.
- New public API additions MUST include tests and documentation.
- Changes affecting the normalized event schema or public API MUST evaluate impact
  on API Stability (Principle X) and version accordingly.
- Pull requests MUST verify compliance with these principles; any deviation MUST be
  justified in the PR description.

## Governance

This constitution supersedes other development practices for the TokenHelm project.

- **Amendments**: Changes to this constitution MUST be documented in the Sync Impact
  Report at the top of this file and approved before merge.
- **Versioning policy**: This constitution follows semantic versioning.
  - MAJOR: Backward-incompatible governance or principle removals/redefinitions.
  - MINOR: A new principle/section is added, or guidance is materially expanded.
  - PATCH: Clarifications, wording, or non-semantic refinements.
- **Compliance review**: All PRs and reviews MUST verify compliance with the
  principles above. Complexity or deviations MUST be explicitly justified.

**Version**: 0.1.0 | **Ratified**: 2026-06-26 | **Last Amended**: 2026-06-26
