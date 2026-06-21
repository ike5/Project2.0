"""Messages 101: build System+Human messages, invoke, read content and token usage.

Run:
    python 01-chat-models-messages/code/messages_basics.py

Needs a running local Ollama server (ollama serve). Shows that a chat model takes a LIST
of role-tagged messages and returns an AIMessage carrying both text and metadata,
and that passing a bare string is shorthand for one HumanMessage.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


def section(title: str) -> None:
    print("\n" + "-" * 56)
    print(title)
    print("-" * 56)


def main() -> None:
    model = ChatOllama(model="llama3.1", num_predict=1024)

    section("1. A list of role-tagged messages -> an AIMessage")
    messages = [
        SystemMessage("You are a terse assistant. Answer in one short sentence."),
        HumanMessage("Why is the sky blue?"),
    ]
    reply = model.invoke(messages)
    print("type(reply) :", type(reply).__name__)          # AIMessage
    assert isinstance(reply, AIMessage)
    print("reply.content:", reply.content)

    section("2. Token usage lives on the AIMessage")
    print("usage_metadata :", reply.usage_metadata)
    print("model     :", reply.response_metadata.get("model"))
    print("done_reason    :", reply.response_metadata.get("done_reason"))
    # input + output should sum to total
    u = reply.usage_metadata
    assert u["input_tokens"] + u["output_tokens"] == u["total_tokens"]

    section("3. A bare string == a single HumanMessage")
    from_string = model.invoke("Say the word 'pong'.")
    from_list = model.invoke([HumanMessage("Say the word 'pong'.")])
    print("from string:", from_string.content)
    print("from list  :", from_list.content)
    print("(both forms are equivalent inputs)")

    print("\nDone. Inspect every printed field — you'll read usage like this all course.")


if __name__ == "__main__":
    main()
