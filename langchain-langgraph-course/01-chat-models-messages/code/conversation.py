"""A multi-turn conversation is just a Python list you grow and re-send.

Run:
    python 01-chat-models-messages/code/conversation.py

Needs a running local Ollama server (ollama serve). The API is STATELESS: the model remembers nothing between
calls. It "remembers" the number below ONLY because we append each AIMessage and
re-send the whole list every time.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


def print_transcript(messages: list) -> None:
    print("\n--- running transcript ---")
    for m in messages:
        role = type(m).__name__.replace("Message", "").upper()
        print(f"  {role:7s}: {m.content}")
    print("--------------------------")


def main() -> None:
    model = ChatOllama(model="llama3.1", num_predict=1024)

    # The conversation: a list we own and manage ourselves.
    messages = [SystemMessage("You are a concise assistant. Keep replies to one sentence.")]

    # --- Turn 1: give the model a fact to remember ---
    messages.append(HumanMessage("My favorite number is 7. Please remember it."))
    ai = model.invoke(messages)
    messages.append(ai)                      # <-- keep the reply in history!
    print_transcript(messages)

    # --- Turn 2: an unrelated turn, so the fact isn't in the immediate question ---
    messages.append(HumanMessage("Name a fruit that is the color red."))
    ai = model.invoke(messages)
    messages.append(ai)
    print_transcript(messages)

    # --- Turn 3: recall the fact from turn 1 ---
    messages.append(HumanMessage("What is my favorite number?"))
    ai = model.invoke(messages)
    messages.append(ai)
    print_transcript(messages)

    print("\nFinal answer:", ai.content)
    assert "7" in ai.content, "Model should recall 7 because we re-sent the history."
    print("\nIt recalled 7 — NOT because of server memory, but because the whole")
    print("list (including turn 1) was re-sent on every invoke. That's all 'memory' is.")
    print(f"\nThe history is now {len(messages)} messages long and grows each turn.")
    assert isinstance(messages[-1], AIMessage)


if __name__ == "__main__":
    main()
