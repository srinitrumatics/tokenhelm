"""Track an Anthropic Messages call with TokenHelm.

Run after `pip install "tokenhelm[anthropic]"`. The same `tracker.track(...)` call works for
every provider — only the response object differs.
"""

from types import SimpleNamespace

from tokenhelm import TokenHelm


def main() -> None:
    # import anthropic
    # client = anthropic.Anthropic()
    # response = client.messages.create(
    #     model="claude-opus-4-8",
    #     max_tokens=1024,
    #     messages=[{"role": "user", "content": "Hello!"}],
    # )

    tracker = TokenHelm()

    # Stand-in Message for an offline demo; replace with your real `response`.
    response = SimpleNamespace(
        type="message",
        role="assistant",
        model="claude-opus-4-8",
        stop_reason="end_turn",
        usage=SimpleNamespace(
            input_tokens=1000, output_tokens=500, cache_read_input_tokens=200
        ),
    )

    event = tracker.track(response)
    print(event.to_dict())
    # Anthropic reports no combined total; TokenHelm derives total_tokens = input + output.


if __name__ == "__main__":
    main()
