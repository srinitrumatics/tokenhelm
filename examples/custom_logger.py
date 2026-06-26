"""Custom output: a callable sink, multiple loggers, and storage at once.

Shows that recording is fully pluggable without modifying the library — the tracker emits one
immutable event to whatever sinks you configure.
"""

from types import SimpleNamespace

from tokenhelm import (
    ConsoleLogger,
    InMemoryStorageBackend,
    JSONLogger,
    TokenHelm,
)


def push_to_metrics(event) -> None:
    # Any Callable[[LLMEvent], None] qualifies as a logger.
    print(f"[metrics] {event.provider.value}.{event.model} cost={event.cost}")


def main() -> None:
    store = InMemoryStorageBackend()
    tracker = TokenHelm(
        logger=[ConsoleLogger(), JSONLogger(), push_to_metrics],
        storage=store,
    )

    response = SimpleNamespace(
        object="chat.completion",
        model="gpt-4o",
        usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=500, total_tokens=1500),
    )
    tracker.track(response)

    print("persisted events:", len(list(store.all())))


if __name__ == "__main__":
    main()
