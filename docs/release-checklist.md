# Release Checklist

Copy this list into the release PR / issue and tick each item. See `docs/releasing.md` for the
commands behind each step.

## Pre-release

- [ ] **CHANGELOG updated** — move `[Unreleased]` entries under the new `[X.Y.Z]` heading with date.
- [ ] **Version bumped** — `project.version` in `pyproject.toml` set to `X.Y.Z` (and `__version__`).
- [ ] **Tests passing** — `pytest` green on the supported matrix (3.11/3.12/3.13 × Linux/Win/macOS).
- [ ] **Coverage gate** — `pytest --cov=tokenhelm --cov-fail-under=90` passes (currently ~95%).
- [ ] **Benchmarks** — `pytest -m benchmark` passes (track() < 5 ms, streaming < 20 MB).
- [ ] **Lint** — `ruff check src tests` and `ruff format --check src tests` clean.
- [ ] **Docs reviewed** — quickstart / configuration / api-reference reflect any API changes.

## Build verification

- [ ] **Build** — `python -m build` produces sdist + wheel.
- [ ] **Metadata** — `twine check dist/*` passes.
- [ ] **Clean-venv install** — fresh venv installs the wheel; `import tokenhelm` works;
      `pricing.yaml` + `py.typed` packaged; four adapters load; an example runs.
- [ ] **Security** — `pip-audit` clean; secret scan clean; no credentials in the wheel.

## TestPyPI validation

- [ ] **Prerelease tag pushed** — e.g. `vX.Y.Zrc1` → CI publishes to TestPyPI via OIDC.
- [ ] **Install from TestPyPI** in a clean venv (with `--extra-index-url` for PyYAML).
- [ ] **`tokenhelm[all]`** installs and `import` of each adapter path succeeds.
- [ ] **Examples run** against the TestPyPI install.

## PyPI publication

- [ ] **Final tag pushed** — `vX.Y.Z` → CI publishes to PyPI via OIDC.
- [ ] **Install from PyPI** in a clean venv; smoke-test `track()`.
- [ ] **GitHub Release created** — artifacts attached, notes generated, prerelease flag correct.
- [ ] **Version tag** — `vX.Y.Z` annotated tag present and pushed.

## Post-release

- [ ] Open a new `[Unreleased]` section in `CHANGELOG.md`.
- [ ] Bump to the next dev version if you use one.
- [ ] Announce / update the roadmap status.
