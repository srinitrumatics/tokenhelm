"""Minimal US1 example — track one OpenAI call and print the normalized event.

You bring your own OpenAI client and credentials; TokenHelm only observes the response object
your client returns (observe-don't-patch). Run after `pip install "tokenhelm[openai]"`.
"""

from tokenhelm import TokenHelm


def main() -> None:
    # from openai import OpenAI
    # client = OpenAI()
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[{"role": "user", "content": "Hello!"}],
    # )

    tracker = TokenHelm()  # zero-config: ConsoleLogger + bundled pricing

    # For a runnable, offline demo we stand in a response-shaped object. Replace with the
    # `response` from your own client call above.
    from types import SimpleNamespace

    response = SimpleNamespace(
        object="chat.completion",
        model="gpt-4o",
        usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=500, total_tokens=1500),
    )

    event = tracker.track(response)
    print(event.to_dict())


if __name__ == "__main__":
    main()
