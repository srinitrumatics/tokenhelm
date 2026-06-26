# Releasing TokenHelm

This guide covers cutting a release, validating on **TestPyPI**, and publishing to **PyPI**.
The automated path uses GitHub Actions with **Trusted Publishing (OIDC)** — no API tokens.

- CI: `.github/workflows/ci.yml` (lint, test matrix, build, security) on every push/PR.
- Release: `.github/workflows/release.yml` on `v*` tags — prerelease tags → TestPyPI, final
  version tags → PyPI, plus a GitHub Release with artifacts.

## Tag conventions

| Tag | Goes to | Example |
|-----|---------|---------|
| `vX.Y.Z` (final) | **PyPI** | `v0.1.0` |
| `vX.Y.Zrc/a/b/.devN` (prerelease) | **TestPyPI** | `v0.1.0rc1`, `v0.1.0a1` |

The release workflow classifies the tag and verifies it matches `project.version` in
`pyproject.toml`.

## Trusted Publishing (recommended — no tokens)

Configure once per index, then publishing needs no secrets:

1. **PyPI** → *Account → Publishing → Add a pending publisher*:
   - PyPI Project Name: `tokenhelm`
   - Owner: `quadkeys` · Repository: `tokenhelm`
   - Workflow filename: `release.yml`
   - Environment name: `pypi`
2. **TestPyPI** → same form at https://test.pypi.org, Environment name: `testpypi`.
3. In GitHub repo *Settings → Environments*, create `pypi` and `testpypi` (add required
   reviewers / branch protection as desired).

The workflow jobs request `id-token: write` and use `pypa/gh-action-pypi-publish`, which
exchanges the OIDC token for a short-lived upload credential at publish time.

## Manual upload (fallback)

Only if you must publish locally. Prefer tokens over a password; never commit them.

```bash
python -m pip install --upgrade build twine
python -m build
twine check dist/*

# TestPyPI first
twine upload --repository testpypi dist/*       # uses ~/.pypirc (see .pypirc.example)

# then PyPI
twine upload dist/*
```

## TestPyPI validation in a clean virtual environment

After a prerelease tag publishes (or a manual TestPyPI upload):

```bash
python -m venv /tmp/th && . /tmp/th/bin/activate          # Windows: \tmp\th\Scripts\activate

# TestPyPI doesn't host PyYAML — pull deps from real PyPI:
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            tokenhelm

python -c "import tokenhelm; print(tokenhelm.__version__)"
python -c "import importlib.resources as r; \
           assert (r.files('tokenhelm')/'data'/'pricing.yaml').is_file(); \
           assert (r.files('tokenhelm')/'py.typed').is_file(); print('data + py.typed OK')"
python -c "from tokenhelm.adapters import default_adapters; \
           print([a.provider.value for a in default_adapters()])"

# with all provider extras
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            "tokenhelm[all]"
python examples/openai_quickstart.py
```

Confirm: imports succeed, `pricing.yaml` and `py.typed` are packaged, all four adapters load,
and the examples run.

> **Local pre-flight already verified** (this repo, from the built wheel): `0.1.0`,
> `pricing.yaml` packaged ✅, `py.typed` packaged ✅, adapters
> `['openai','anthropic','gemini','ollama']` ✅, example runs ✅, lone runtime dep is PyYAML ✅.

## Security checklist (per release)

- **Dependency audit** — `pip-audit` (CI `security` job). Runtime dep surface is just PyYAML.
- **License scan** — MIT project; runtime dep PyYAML is MIT. Provider SDKs are optional extras.
- **Secret scan** — gitleaks (CI) + repo policy; no secrets in source (verified).
- **No credentials packaged** — wheel contains only `tokenhelm/**` + standard `dist-info`
  (verified: no `.env`/`.pypirc`/keys).
- **Wheel reproducibility** — builds set `SOURCE_DATE_EPOCH` for deterministic timestamps.
- **Metadata complete** — `twine check` passes; name, version, license, classifiers,
  `Requires-Python`, extras all present.
