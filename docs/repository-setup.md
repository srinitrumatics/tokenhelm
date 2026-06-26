# Repository Configuration (maintainer setup)

One-time GitHub settings to apply after pushing the repo. These complement the in-repo files
(`.github/CODEOWNERS`, `.github/dependabot.yml`, the workflows, and the Trusted Publisher setup
in `docs/releasing.md`).

## Branch protection (`main`)

*Settings → Branches → Add rule* for `main`:

- ✅ Require a pull request before merging
  - ✅ Require approvals: **1** (CODEOWNERS reviews enforced)
  - ✅ Require review from Code Owners
  - ✅ Dismiss stale approvals on new commits
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date
  - Required checks (see next section)
- ✅ Require conversation resolution before merging
- ✅ Require linear history (pairs well with squash-merge + Conventional Commit PR titles)
- ✅ Do not allow bypassing the above settings
- ✅ Restrict who can push to matching branches (maintainers only)

Recommended repo-wide: *Settings → General → Pull Requests* → **Allow squash merging only**,
and "Default to PR title" for the squash commit message (feeds release-please).

## Required status checks

Use these job names from `ci.yml` (names appear after the first CI run):

- `Lint (ruff)`
- `Test (py3.11 / ubuntu-latest)`, `Test (py3.12 / ubuntu-latest)`, `Test (py3.13 / ubuntu-latest)`
- `Test (py3.12 / windows-latest)`, `Test (py3.12 / macos-latest)` (at minimum one of each OS)
- `Build & verify distribution`
- `PR Title (Conventional Commits)` → `validate`

> Tip: require the full 3×3 matrix for maximum safety, or a representative subset (all
> Pythons on Linux + py3.12 on Windows/macOS) to balance latency.

## CODEOWNERS

`.github/CODEOWNERS` routes reviews. Replace `@quadkeys` with the org/team handle (e.g.
`@quadkeys/maintainers`) once a team exists. Enable "Require review from Code Owners" above.

## Dependency updates: Dependabot vs Renovate

| | **Dependabot** (chosen) | **Renovate** |
|---|---|---|
| Setup | Native to GitHub, zero extra app | Install GitHub App + `renovate.json` |
| Config power | Good (grouping, schedules, labels) | Excellent (very granular, monorepo-savvy) |
| Security alerts | Native (GitHub Advisory DB) | Via integration |
| Best for | Small/medium libraries like TokenHelm | Large/monorepo or complex policies |

**Recommendation: Dependabot** (`.github/dependabot.yml` already added) — native, low-maintenance,
and more than sufficient for a single-package library with one runtime dependency. Revisit
Renovate only if the project grows into a monorepo or needs fine-grained update policies.

## Automatic security updates

*Settings → Code security and analysis* → enable:

- ✅ Dependabot alerts
- ✅ Dependabot security updates (auto-PRs for vulnerable deps)
- ✅ Secret scanning + Push protection
- ✅ Private vulnerability reporting (powers `SECURITY.md`'s advisory link)
- ✅ Code scanning (optional: add CodeQL for Python)

## Environments (for Trusted Publishing)

Create `pypi` and `testpypi` environments (*Settings → Environments*) and register the
matching Trusted Publishers on PyPI/TestPyPI — full steps in `docs/releasing.md`. Add required
reviewers on the `pypi` environment so production publishes need a human approval.
