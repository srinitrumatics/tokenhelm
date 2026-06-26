# TokenHelm v0.1.0rc1 — Release Candidate

> ⚠️ **This is a release candidate, not a final release.** It is published to **TestPyPI only**
> for final pre-publication validation. Do not use it in production. If validation passes, the
> identical code ships as **v0.1.0** on public PyPI.

## Purpose of this RC

`v0.1.0rc1` is the last gate before the public release. It exists to verify, end-to-end, that:

- the package **builds and publishes** through the automated OIDC pipeline (`release.yml`),
- it **installs cleanly** from an index into a fresh virtual environment,
- the **packaged data** (`pricing.yaml`, `py.typed`) and **all four adapters** are present,
- the **examples run** against the installed package.

No code changes are expected between `v0.1.0rc1` and `v0.1.0`.

## Install (TestPyPI)

TestPyPI does not host runtime dependencies, so add real PyPI as an extra index for PyYAML:

```bash
python -m venv .venv && . .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            "tokenhelm==0.1.0rc1"

# with all provider extras
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            "tokenhelm[all]==0.1.0rc1"
```

## Validation checklist

```bash
python -c "import tokenhelm; print(tokenhelm.__version__)"          # -> 0.1.0rc1
python -c "import importlib.resources as r; \
           assert (r.files('tokenhelm')/'data'/'pricing.yaml').is_file(); \
           assert (r.files('tokenhelm')/'py.typed').is_file(); print('data + py.typed OK')"
python -c "from tokenhelm.adapters import default_adapters; \
           print([a.provider.value for a in default_adapters()])"   # openai, anthropic, gemini, ollama
python examples/openai_quickstart.py
python examples/anthropic_quickstart.py
python examples/custom_logger.py
```

Expected: imports succeed, data files packaged, four adapters load, examples print a normalized
event. (All of this is already verified locally against the built wheel.)

## What's in this release

The full feature set and detailed notes are in
**[release-notes-v0.1.0.md](release-notes-v0.1.0.md)**. In brief:

- Core SDK: `track()`, `trace()` (sync **and** async), `track_stream()` (sync/async, wrap or
  manual), `configure()`.
- Immutable, normalized `LLMEvent` (eight mandated fields + `usage_complete`/`priced` flags).
- Four provider adapters — **OpenAI, Anthropic, Gemini, Ollama** — non-streaming and streaming.
- Five extension points: `BaseAdapter`, `PricingProvider`, `EventDispatcher`, `Logger`,
  `StorageBackend`.
- 127 tests, 95.62% coverage; `track()` ≈ 0.011 ms, streaming adds ≈ 0 MiB.

## Known limitations

See the *Known limitations* section of
[release-notes-v0.1.0.md](release-notes-v0.1.0.md#known-limitations): duck-typed provider
identification, streaming validated against captured fixtures, static bundled pricing, and
sync-only `track()`.

## Feedback

Found a problem with the RC? Please open an issue
(https://github.com/srinitrumatics/tokenhelm/issues) or start a discussion
(https://github.com/srinitrumatics/tokenhelm/discussions) and mention `v0.1.0rc1`.

## After validation

If the checklist above passes from TestPyPI, we cut **v0.1.0** and publish to public PyPI via
the same OIDC pipeline. See [go-live-checklist.md](go-live-checklist.md) for the full procedure.
