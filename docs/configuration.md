# Configuration

`TokenHelm` takes a single keyword-only knob set, shared by the constructor and `configure()`:

```python
TokenHelm(
    logger=...,       # a Logger, a Callable[[LLMEvent], None], or a list of them
    pricing=...,      # a PricingProvider, or str/Path/dict sugar for YamlPricingProvider
    dispatcher=...,   # an EventDispatcher (replaces the whole pipeline)
    storage=...,      # a StorageBackend or list of them (opt-in persistence)
    adapters=...,     # an iterable of BaseAdapter (replaces the built-in set)
    currency="USD",
)
```

`configure(**same)` reconfigures post-construction; only the arguments you pass change, the
rest are preserved.

## Loggers

```python
from tokenhelm import TokenHelm, ConsoleLogger, JSONLogger, FileLogger

TokenHelm(logger=JSONLogger())                      # JSON per line to stdout
TokenHelm(logger=FileLogger("usage.jsonl"))         # JSON lines appended to a file
TokenHelm(logger=lambda e: metrics.push(e.to_dict()))   # any callable
TokenHelm(logger=[ConsoleLogger(), FileLogger("usage.jsonl")])  # multiple at once
```

A logger receives only the normalized `LLMEvent` — never a provider response object.

## Storage

```python
from tokenhelm import TokenHelm, InMemoryStorageBackend

store = InMemoryStorageBackend()
tracker = TokenHelm(logger=ConsoleLogger(), storage=store)
tracker.track(response)
list(store.all())          # persisted events
```

Storage is off by default. Implement `StorageBackend` (`save`, `all`) for SQLite/Postgres/Redis.

## Pricing

```python
from tokenhelm import TokenHelm, YamlPricingProvider

TokenHelm(pricing="my_rates.yaml")                                   # file override
TokenHelm(pricing={"openai": {"gpt-4o": {"input": 2.5, "output": 10.0}}})  # dict override
TokenHelm(pricing=YamlPricingProvider(path="my_rates.yaml"))         # explicit provider
# TokenHelm(pricing=MyRemotePricingProvider())                       # any PricingProvider
```

Rates are per 1,000,000 tokens. Unknown models are "unpriced" (`priced=False`, `cost=0`) — no
error. `CostCalculator` depends only on the `PricingProvider` interface.

## Custom adapters

```python
from tokenhelm import TokenHelm, BaseAdapter
from tokenhelm.adapters import default_adapters

class MyAdapter(BaseAdapter):
    ...   # provider, identify, extract_model, extract_usage [+ streaming]

# Replace the built-in set:
TokenHelm(adapters=[MyAdapter()])
# Extend it (keep the built-ins):
TokenHelm(adapters=[*default_adapters(), MyAdapter()])
```

## Full control of the pipeline

```python
from tokenhelm import DefaultEventDispatcher, ConsoleLogger, InMemoryStorageBackend

dispatcher = DefaultEventDispatcher(
    loggers=[ConsoleLogger(), JSONLogger()],
    storage=InMemoryStorageBackend(),
)
TokenHelm(dispatcher=dispatcher)   # the tracker only ever talks to the dispatcher
```
