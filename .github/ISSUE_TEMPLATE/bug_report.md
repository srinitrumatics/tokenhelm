---
name: Bug report
about: Report a problem so we can fix it
title: "[Bug]: "
labels: ["bug", "triage"]
assignees: []
---

## Description

A clear and concise description of what the bug is.

## Reproduction

Minimal code that triggers the issue (please remove credentials):

```python
from tokenhelm import TokenHelm

tracker = TokenHelm()
# ...
```

## Expected behavior

What you expected to happen.

## Actual behavior

What actually happened, including the full traceback if any.

```text
<paste traceback here>
```

## Environment

- TokenHelm version: <!-- python -c "import tokenhelm; print(tokenhelm.__version__)" -->
- Python version: <!-- python --version -->
- OS:
- Provider(s) involved: <!-- openai / anthropic / gemini / ollama / custom -->
- Installed extras: <!-- e.g. tokenhelm[openai] -->

## Additional context

Anything else that helps — a normalized event `to_dict()`, a redacted response shape, etc.
