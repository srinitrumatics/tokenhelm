<!--
Thanks for contributing! Please use a Conventional Commits PR title, e.g.:
  feat(adapters): add Mistral adapter
  fix(streaming): finalize once on cancellation
  docs: clarify pricing override precedence
-->

## Summary

What does this PR do and why?

## Type of change

- [ ] `fix` — bug fix (no API change)
- [ ] `feat` — additive feature (new adapter / logger / storage / pricing / kwarg)
- [ ] `docs` — documentation only
- [ ] `refactor` / `perf` / `test` / `chore`
- [ ] **Breaking change** (requires a MAJOR bump — explain below)

## Checklist

- [ ] Tests added/updated; `pytest` passes with coverage ≥ 90%.
- [ ] `ruff check src tests` and `ruff format --check src tests` pass.
- [ ] Public API changes (if any) are additive and documented in `docs/`.
- [ ] `CHANGELOG.md` updated under `[Unreleased]`.
- [ ] Dependency direction respected (adapters don't import loggers/storage; nothing imports `sdk`).

## Notes for reviewers

Anything that needs special attention, trade-offs, or follow-ups.
