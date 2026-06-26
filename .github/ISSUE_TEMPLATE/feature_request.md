---
name: Feature request
about: Suggest an idea or enhancement
title: "[Feature]: "
labels: ["enhancement", "triage"]
assignees: []
---

## Problem / motivation

What are you trying to do that TokenHelm doesn't support today?

## Proposed solution

What you'd like to see. If it touches the public API, sketch the call shape:

```python
# proposed usage
```

## Which extension point does this fit?

TokenHelm favors additive change via its extension points. If applicable, note which one:

- [ ] `BaseAdapter` (new/changed provider)
- [ ] `PricingProvider` (pricing source)
- [ ] `EventDispatcher` (event routing)
- [ ] `Logger` (output)
- [ ] `StorageBackend` (persistence)
- [ ] Core API change (please explain why an extension point isn't sufficient)

## Alternatives considered

Other approaches you thought about.

## Additional context

Links, references, or prior art.
