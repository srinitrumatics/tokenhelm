"""Track an OpenAI call with TokenHelm.

Run after `pip install "tokenhelm[openai]"`. You bring your own client and credentials;
TokenHelm only observes the response object your client returns.
"""

from types import SimpleNamespace

from tokenhelm import TokenHelm


def main() -> None:
    # from openai import OpenAI
    # client = OpenAI()
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[{"role": "user", "content": "Hello!"}],
    # )

    tracker = TokenHelm()  # zero-config

    # Stand-in response for an offline demo; replace with your real `response`.
    response = SimpleNamespace(
        object="chat.completion",
        model="gpt-4o",
        usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=500, total_tokens=1500),
    )

    event = tracker.track(response)
    print(event.to_dict())


if __name__ == "__main__":
    main()
