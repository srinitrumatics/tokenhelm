# Contributing to TokenHelm

Thanks for your interest in improving TokenHelm. This guide covers the development workflow,
the API-stability rules, and how new providers/extensions are added.

## Development setup

```bash
python -m pip install -e ".[dev]"     # editable install + test/lint toolchain
pytest                                # run the suite (90% coverage gate enforced)
pytest -m "not benchmark"             # skip the perf/memory budget checks
ruff check src tests                  # lint
ruff format src tests                 # format
```

Requires Python 3.11+.

## Project layout

```
src/tokenhelm/
  core/        models, tracker, extraction, calculator, config, errors
  adapters/    BaseAdapter + StreamAggregator and the four provider adapters
  pricing/     PricingProvider + YamlPricingProvider
  dispatch/    EventDispatcher + DefaultEventDispatcher
  logging/     Logger + Console/JSON/File loggers
  storage/     StorageBackend + InMemoryStorageBackend
  sdk/         TokenHelm client + TraceScope/StreamSession
  data/        bundled pricing.yaml
```

**Dependency direction is strictly one-way:** `sdk → core → interfaces`. Concrete
implementations are assembled only at the `sdk` layer. Adapters must never import loggers,
storage, or the dispatcher.

## Adding a provider adapter

1. Subclass `BaseAdapter` in `src/tokenhelm/adapters/<provider>.py`. Implement `provider`,
   `identify`, `extract_model`, `extract_usage`. For streaming, add `identify_stream` and a
   `StreamAggregator` via `new_stream_aggregator`.
2. Observe-don't-patch: read attributes off the response object by duck typing. Do **not**
   import the provider SDK to normalize a response.
3. Register it in `default_adapters()` (`src/tokenhelm/adapters/__init__.py`).
4. Add a captured fixture under `tests/adapters/fixtures/` and an adapter test.
5. Add bundled rates to `src/tokenhelm/data/pricing.yaml`.

Custom adapters need not live in this repo — pass `adapters=[...]` to `TokenHelm(...)`.

## Versioning & public API stability (Principle X)

TokenHelm follows [Semantic Versioning](https://semver.org). The **public contract** is the
names exported from `tokenhelm/__init__.py`, their call shapes, the eight `LLMEvent` fields,
and the five extension-point interfaces (`BaseAdapter`, `PricingProvider`, `EventDispatcher`,
`Logger`, `StorageBackend`). See `specs/001-core-sdk/contracts/public-api.md`.

- **PATCH** — bug fixes, docs, internal refactors with no API change.
- **MINOR** — additive only: new adapters, new logger/storage/dispatcher/pricing
  implementations, new optional keyword arguments, new event status flags.
- **MAJOR** — removing or renaming a public name, changing an interface method signature, or
  changing the eight required event fields.

Anything not exported from the top-level package is internal and may change without notice.

## Deprecation policy

- A public API slated for removal is marked deprecated in a MINOR release: a
  `DeprecationWarning` at runtime, a `Deprecated:` note in the docstring, and a CHANGELOG
  entry under **Deprecated**.
- A deprecated API is kept working for at least one subsequent MINOR release before removal,
  and is only removed in a MAJOR release.
- New behavior ships side-by-side with the old where feasible, so users can migrate
  incrementally.

## Pull requests

- Add or update tests; keep coverage ≥ 90%.
- Run `ruff check` and `ruff format` before pushing.
- Update `CHANGELOG.md` under `[Unreleased]`.
- Keep changes within the dependency direction described above.

## License

By contributing you agree your contributions are licensed under the project's MIT License.
