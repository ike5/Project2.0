"""Build a ChatPromptTemplate and see what .invoke() produces (no model call).

Run:
    python 02-prompts-and-lcel/code/prompt_template.py

A template separates the *shape* of a prompt from the *values* you fill it with.
Invoking it returns a PromptValue — a bundle of real messages — without ever
calling the model. This script makes that concrete by printing the messages.
"""

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def section(title: str) -> None:
    print("\n" + "-" * 56)
    print(title)
    print("-" * 56)


def main() -> None:
    section("1. A translation template")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You translate English to {language}. Reply with only the translation."),
        ("human", "{text}"),
    ])
    print("input_variables:", prompt.input_variables)  # ['language', 'text'] (order may vary)

    section("2. Fill it -> a PromptValue (NO model called yet)")
    pv = prompt.invoke({"language": "French", "text": "good morning"})
    print("type:", type(pv).__name__)
    for msg in pv.to_messages():
        print(f"  {type(msg).__name__:14s} {msg.content!r}")

    section("3. Same template, different values (reuse!)")
    pv2 = prompt.invoke({"language": "Spanish", "text": "see you tomorrow"})
    for msg in pv2.to_messages():
        print(f"  {type(msg).__name__:14s} {msg.content!r}")

    section("4. MessagesPlaceholder injects a running history")
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])
    pv3 = chat_prompt.invoke({
        "history": [HumanMessage("I'm Ada."), AIMessage("Nice to meet you, Ada!")],
        "input": "What's my name?",
    })
    for msg in pv3.to_messages():
        print(f"  {type(msg).__name__:14s} {msg.content!r}")

    print("\nDone. Notice: no API call happened — a template only formats messages.")


if __name__ == "__main__":
    main()
