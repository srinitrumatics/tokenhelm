# Feature Specification: TokenHelm Core SDK

**Feature Branch**: `001-core-sdk`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "TokenHelm Core SDK v0.1 — a lightweight Python library that enables developers to track token usage and calculate LLM costs using a unified API across multiple providers (OpenAI, Gemini, Anthropic, Ollama)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track usage and cost across one provider (Priority: P1)

A developer building an LLM application wraps their existing LLM call with TokenHelm
so that, after the call returns, they receive a normalized record of how many input
and output tokens were used, how long the call took, and what it cost — without
having to parse provider-specific usage objects themselves.

**Why this priority**: This is the core value proposition. Without normalized
token/cost tracking for at least one provider, the library delivers nothing. It is
the smallest slice that is independently shippable and demonstrable.

**Independent Test**: Configure TokenHelm with a single provider, issue one
(non-streaming) LLM request inside the tracker, and verify a normalized event is
produced containing provider, model, input/output/total tokens, latency, cost, and
timestamp — with cost matching the configured pricing.

**Acceptance Scenarios**:

1. **Given** a configured TokenHelm client and a provider with known pricing,
   **When** a developer makes a tracked LLM request and it completes,
   **Then** a normalized event is produced with all required fields populated and a
   correctly computed total cost.
2. **Given** a tracked LLM request,
   **When** the response is received,
   **Then** the reported input, output, and total token counts match the provider's
   reported usage, and total = input + output.

---

### User Story 2 - Switch providers without changing tracking code (Priority: P2)

A developer who already tracks usage for one provider points TokenHelm at a different
supported provider (e.g. from OpenAI to Anthropic). The tracking API they call and
the shape of the event they receive stay identical; only configuration changes.

**Why this priority**: Provider portability is the differentiator over per-vendor
tooling, but it depends on P1 existing first. It proves the abstraction holds.

**Independent Test**: Run the same tracking workflow against two different supported
providers and confirm both yield events of the same shape with all required fields,
using each provider's pricing.

**Acceptance Scenarios**:

1. **Given** the same tracking workflow,
   **When** it is run against any of OpenAI, Gemini, Anthropic, or Ollama,
   **Then** the resulting normalized event has the identical field set and the
   developer's tracking code is unchanged between providers.
2. **Given** a provider whose request returns no billable usage (e.g. a local
   model with zero-rate pricing),
   **When** the request is tracked,
   **Then** an event is still produced with a cost of zero rather than an error.

---

### User Story 3 - Choose how usage is recorded (Priority: P2)

A developer wants tracked events delivered somewhere useful — printed to the console
during development, written as JSON, or appended to a file — and can select or supply
the recording mechanism without modifying the library.

**Why this priority**: Observability output is what makes tracking actionable, and
the pluggable-logger requirement is a constitutional commitment (extensibility). It
builds on P1 but is not required for the first demonstrable slice.

**Independent Test**: Track a request with each provided output mechanism (console,
JSON, file) and confirm the event is recorded in the expected form for each.

**Acceptance Scenarios**:

1. **Given** a selected output mechanism,
   **When** a tracked request completes,
   **Then** the normalized event is recorded via that mechanism in its expected
   format.
2. **Given** a custom output mechanism supplied by the developer,
   **When** a tracked request completes,
   **Then** the event is delivered to the custom mechanism without any change to the
   library itself.

---

### User Story 4 - Track streaming responses (Priority: P3)

A developer using streamed responses tracks the request through TokenHelm and, once
the stream is exhausted, receives the same normalized event (with final token counts,
latency, and cost) as for a non-streaming call.

**Why this priority**: Streaming is common in production but is an extension of the
core tracking behavior; it can ship after non-streaming tracking is proven.

**Independent Test**: Issue a streamed request inside the tracker, consume the full
stream, and verify a single normalized event with complete final totals is produced.

**Acceptance Scenarios**:

1. **Given** a streamed LLM response,
   **When** the developer consumes the entire stream within the tracker,
   **Then** exactly one normalized event is produced with final aggregated token
   counts, total latency, and computed cost.

---

### Edge Cases

- **Missing usage data**: A provider response omits token usage. The system records
  an event with the fields it can determine and flags the missing usage rather than
  crashing the developer's request.
- **Unknown model pricing**: A request uses a model absent from the pricing
  configuration. The system produces an event with token counts and a clearly
  identifiable "unpriced" cost (e.g. zero or null with an indicator) instead of
  failing.
- **Concurrent tracked requests**: Multiple requests are tracked simultaneously from
  different threads or async tasks. Each produces its own correct event with no
  cross-contamination of counts.
- **Stream abandoned early**: A streamed response is only partially consumed. The
  system reports usage based on what was consumed without raising on cleanup.
- **Manual tracking of an already-completed response**: A developer passes a finished
  response object directly; the system normalizes it into an event the same as an
  in-context tracked call.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a single client entry point that a developer can
  instantiate to begin tracking.
- **FR-002**: System MUST support tracking for OpenAI, Gemini, Anthropic, and Ollama
  through provider adapters, with each provider isolated behind a common interface.
- **FR-003**: System MUST normalize every tracked response into a common event
  containing: provider, model, input_tokens, output_tokens, total_tokens, latency,
  cost, and timestamp. Developers MUST NOT need to handle provider-specific usage
  objects.
- **FR-004**: System MUST calculate input cost, output cost, and total cost for each
  tracked request based on its token usage and configured pricing.
- **FR-005**: System MUST allow pricing to be configured per provider and model
  (input rate and output rate), via external configuration, without code changes.
- **FR-006**: System MUST provide a context-manager style of tracking that captures
  any LLM requests made within its scope.
- **FR-007**: System MUST provide a manual tracking entry point that accepts a
  response object and produces a normalized event.
- **FR-008**: System MUST support tracking of streaming responses, producing a single
  normalized event with final aggregated totals once the stream is consumed.
- **FR-009**: System MUST emit tracked usage as structured events suitable for
  programmatic consumption.
- **FR-010**: System MUST allow developers to select among provided output mechanisms
  (console, JSON, file) and to supply a custom output mechanism without modifying the
  library.
- **FR-011**: System MUST remain usable from both synchronous and asynchronous code.
- **FR-012**: System MUST handle concurrent tracked requests safely, keeping each
  request's usage and event independent.
- **FR-013**: System MUST degrade gracefully when usage data or model pricing is
  missing, producing a best-effort event rather than failing the developer's request.

### Out of Scope (v0.1)

- Dashboard or analytics UI
- Prompt optimization
- RAG optimization
- Response caching
- Recommendation engine
- Budget forecasting

### Key Entities *(include if feature involves data)*

- **Tracking Client**: The developer-facing entry point that opens tracking scopes,
  accepts manual tracking calls, and routes resulting events to the configured output
  mechanism.
- **Provider Adapter**: A per-provider component that translates a provider's response
  and usage into the common normalized form. All adapters share one interface.
- **Normalized Usage Event**: The standardized record of a single LLM request —
  provider, model, input_tokens, output_tokens, total_tokens, latency, cost,
  timestamp — plus any indicators for missing usage or pricing.
- **Pricing Configuration**: The set of per-provider, per-model input and output rates
  used to compute cost; externally configurable.
- **Output Mechanism (Logger)**: The replaceable component that records or forwards
  normalized events (console, JSON, file, or custom).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can add usage and cost tracking to an existing single
  LLM call in five lines of code or fewer.
- **SC-002**: For every supported provider (OpenAI, Gemini, Anthropic, Ollama), a
  tracked request produces a normalized event containing all eight required fields.
- **SC-003**: Reported total cost matches the expected cost derived from the
  configured pricing and observed token counts for 100% of priced requests in the
  test suite.
- **SC-004**: Switching the tracked provider requires no change to the developer's
  tracking code — only configuration.
- **SC-005**: Tracking adds under 5 ms of overhead per request and under 20 MB of
  additional memory.
- **SC-006**: Tracking works for both streaming and non-streaming responses, and from
  both synchronous and asynchronous code.
- **SC-007**: Concurrent tracked requests each produce correct, independent events
  with no cross-contamination under multi-threaded execution.
- **SC-008**: The four adapters, cost calculation, and token extraction are covered by
  automated tests meeting the project's 90% coverage target.

## Assumptions

- Target users are developers integrating LLM calls in Python applications (Python
  3.11+), comfortable configuring the library in code or via a configuration file.
- TokenHelm wraps or observes calls the developer makes using each provider's own
  client; it does not make LLM calls on the developer's behalf and does not manage
  provider credentials.
- Pricing rates are supplied by the developer (defaults may be provided) and are
  expressed per token unit consistent with how providers report usage; keeping rates
  current is the developer's responsibility for v0.1.
- "Cost" is an estimate computed from configured rates and reported token counts, not
  a billed amount reconciled with any provider invoice.
- The four named providers are the complete supported set for v0.1; additional
  providers are added later as new adapters without changing the public API.
- Distribution to a public package index is an acceptance goal but external to the
  library's runtime behavior.
