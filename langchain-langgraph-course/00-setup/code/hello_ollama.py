"""Your friendly first script: call a local model with messages, then stream the same prompt.

Run:
    python 00-setup/code/hello_ollama.py

Shows the difference between invoke (one block + token usage) and stream (token by token).
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


def main() -> None:
    # Small num_predict keeps these demo calls cheap and fast.
    model = ChatOllama(model="llama3.1", num_predict=128)

    messages = [
        SystemMessage("You are a concise, friendly assistant."),
        HumanMessage("In one sentence, what is LangChain?"),
    ]

    # (a) invoke: run once, get the whole AIMessage back.
    print("=== invoke (batched) ===")
    reply = model.invoke(messages)
    print(reply.content)

    # .usage_metadata reports how many tokens went in and came out.
    usage = reply.usage_metadata or {}
    print(
        f"\ntokens -> input: {usage.get('input_tokens')}  "
        f"output: {usage.get('output_tokens')}"
    )

    # (b) stream: same prompt, but tokens arrive one chunk at a time.
    print("\n=== stream (token by token) ===")
    for chunk in model.stream(messages):
        print(chunk.content, end="", flush=True)
    print("\n\nSame prompt, two delivery modes. Move on to the lab!")


if __name__ == "__main__":
    main()
