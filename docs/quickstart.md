# Quick Start

## Track one request

```python
from tokenhelm import TokenHelm

tracker = TokenHelm()                          # zero-config: console logging + bundled pricing
response = client.chat.completions.create(...)  # your own OpenAI call
event = tracker.track(response)                # normalized LLMEvent
print(event.to_dict())
```

`event` carries the eight mandated fields — `provider, model, input_tokens, output_tokens,
total_tokens, latency, cost, timestamp` — plus `usage_complete` and `priced` flags.

## Scoped tracking

```python
with tracker.trace() as scope:
    response = client.chat.completions.create(...)
    scope.track(response)
print(scope.events)        # [LLMEvent(...)]

# async mirrors the sync API
async with tracker.trace() as scope:
    response = await aclient.chat.completions.create(...)
    scope.track(response)
```

## Streaming

```python
# wrap a provider stream — exactly one event after the stream is exhausted
for chunk in tracker.track_stream(client.chat.completions.create(..., stream=True)):
    ...   # consume chunks as usual

# or drive it yourself
with tracker.track_stream() as stream:
    for chunk in client.chat.completions.create(..., stream=True):
        stream.consume(chunk)
print(stream.event)        # the single aggregated LLMEvent

# async streaming
async for chunk in tracker.track_stream(aclient.chat.completions.create(..., stream=True)):
    ...
```

> For OpenAI streaming, request usage with `stream_options={"include_usage": True}` so the
> final chunk carries token counts.

## Switch providers — no code change

```python
tracker = TokenHelm()
for response in (openai_resp, anthropic_resp, gemini_resp, ollama_resp):
    event = tracker.track(response)            # identical event shape across all four
```

See [configuration.md](configuration.md) for loggers, storage, pricing, and custom adapters,
and [api-reference.md](api-reference.md) for the full public surface.
