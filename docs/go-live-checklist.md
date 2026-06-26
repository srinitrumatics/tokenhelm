# Release Procedure & Go-Live Checklist (canonical)

This is the **canonical, end-to-end release procedure** for TokenHelm — follow it for every
release.

- **First release (v0.1.0):** complete every section, including the one-time infrastructure
  setup (sections 1–3).
- **Subsequent releases:** sections 1–3 become a quick **re-verification** that the publishing
  and protection infrastructure is still in place; then run the per-version quality gates in
  [`release-checklist.md`](release-checklist.md) and proceed through sections 5–8.

Supporting detail: [`releasing.md`](releasing.md) (how publishing works),
[`repository-setup.md`](repository-setup.md) (GitHub settings),
[`release-checklist.md`](release-checklist.md) (per-version quality gates).

Maintainer: `@srinitrumatics` · Repo: https://github.com/srinitrumatics/tokenhelm

---

## 1. Trusted Publishers (PyPI + TestPyPI)

- [ ] **TestPyPI** pending publisher added (https://test.pypi.org → Account → Publishing):
      project `tokenhelm`, owner `srinitrumatics`, repo `tokenhelm`, workflow `release.yml`,
      environment `testpypi`.
- [ ] **PyPI** pending publisher added (https://pypi.org → Account → Publishing) with the same
      values and environment `pypi`.
- [ ] Project name `tokenhelm` is available / owned on both indexes (no name conflict).
  - *Verify:* https://pypi.org/project/tokenhelm/ and https://test.pypi.org/project/tokenhelm/
    return 404 (unclaimed) or are owned by you.

## 2. GitHub Environments

- [ ] Environment **`testpypi`** created (Settings → Environments).
- [ ] Environment **`pypi`** created, with **required reviewer(s)** so production publish needs
      manual approval.
- [ ] No long-lived PyPI API tokens stored as secrets (OIDC only).
  - *Verify:* Settings → Secrets and variables → Actions shows no `PYPI_*`/`TWINE_*` secrets.

## 3. Repository Security & Protection

- [ ] Branch protection on `main`: require PR, 1 approval, **require Code Owner review**,
      dismiss stale approvals, require conversation resolution, linear history, no bypass.
- [ ] **Required status checks** selected (names appear after the first CI run):
      `Lint (ruff)`, `Test (py3.11/3.12/3.13 × ubuntu)` + at least `windows`/`macos` on 3.12,
      `Build & verify distribution`, `PR Title (Conventional Commits) / validate`.
- [ ] Squash-merge only; "Default to PR title" for the squash message.
- [ ] **Dependabot alerts** + **security updates** enabled.
- [ ] **Secret scanning** + **push protection** enabled.
- [ ] **Private vulnerability reporting** enabled (powers `SECURITY.md`).
- [ ] **CodeQL** enabled / running (workflow `codeql.yml` present).

## 4. GitHub Actions green on `main`

- [ ] **CI** (`ci.yml`) — lint, full 3×3 test matrix, build & clean-venv install, security all ✅.
- [ ] **CodeQL** (`codeql.yml`) — completes; no unexpected high-severity alerts.
- [ ] **Sync labels** (`labels.yml`) — applied the label set from `.github/labels.yml`.
- [ ] **PR Title** check active on PRs.
  - *Verify:* Actions tab shows the latest `main` runs green.

## 5. Release Please operating

- [ ] `release-please` (`.github/workflows/release-please.yml`) ran on the push to `main` and
      **opened a release PR** titled like `chore(main): release 0.1.0`.
- [ ] The release PR's proposed `CHANGELOG.md` and version bump look correct.
- [ ] Decision made on cut path:
  - **Option A (recommended):** validate via a manual `v0.1.0rc1` tag first (below), then merge
    the release PR to cut `v0.1.0`.
  - **Option B:** merge the release PR to tag `v0.1.0` directly (skips the rc validation).

## 6. Cut the prerelease tag (only after 1–5 are ✅)

- [ ] Working tree clean, `main` up to date locally.
- [ ] Create + push annotated tag:
      `git tag -a v0.1.0rc1 -m "v0.1.0rc1" && git push origin v0.1.0rc1`
- [ ] `release.yml` runs: build → twine check → classify as **prerelease** → publish to
      **TestPyPI** via OIDC → GitHub prerelease created with artifacts. All ✅.

## 7. Validate from TestPyPI (clean virtual environment)

- [ ] Fresh venv install (TestPyPI doesn't host PyYAML — add the real-PyPI extra index):
      ```bash
      python -m venv /tmp/th && . /tmp/th/bin/activate
      pip install --index-url https://test.pypi.org/simple/ \
                  --extra-index-url https://pypi.org/simple/ tokenhelm
      ```
- [ ] `python -c "import tokenhelm; print(tokenhelm.__version__)"` → `0.1.0rc1`.
- [ ] `pricing.yaml` + `py.typed` packaged; four adapters load.
- [ ] `pip install ... "tokenhelm[all]"` succeeds.
- [ ] All three `examples/*.py` run successfully.
  - *(All of these were already verified locally against the built wheel.)*

## 8. Publish v0.1.0 to PyPI (only after 7 is ✅)

- [ ] Merge the release PR (or push `v0.1.0`) → `release.yml` classifies as **final** → publish
      to **PyPI** via OIDC (approve the `pypi` environment when prompted).
- [ ] GitHub Release `v0.1.0` published with generated notes + artifacts.
- [ ] Final smoke test from PyPI in a clean venv: `pip install tokenhelm` → `track()` works.
- [ ] Announce; open a fresh `[Unreleased]` section in `CHANGELOG.md`.

---

### Status summary

| # | Gate | Status |
|---|------|--------|
| 1 | Trusted Publishers (PyPI + TestPyPI) | ⬜ pending |
| 2 | GitHub environments (`testpypi`, `pypi`) | ⬜ pending |
| 3 | Branch protection + security features | ⬜ pending |
| 4 | All Actions green on `main` | ⬜ pending |
| 5 | Release Please release PR open & correct | ⬜ pending |
| 6 | `v0.1.0rc1` tag → TestPyPI publish ✅ | ⬜ pending |
| 7 | Clean-venv install from TestPyPI ✅ | ⬜ pending |
| 8 | `v0.1.0` → PyPI publish ✅ | ⬜ pending |

> Do not push `v0.1.0rc1` until rows 1–5 are ✅. Do not publish `v0.1.0` until row 7 is ✅.
