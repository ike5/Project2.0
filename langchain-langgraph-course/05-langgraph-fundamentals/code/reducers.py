"""Overwrite vs append: the same two nodes, with and without a reducer.

Run:
    python 05-langgraph-fundamentals/code/reducers.py

Shows: (A) a list key with NO reducer -> the second node OVERWRITES the first;
(B) the same key annotated with operator.add -> the lists are APPENDED;
(C) a tiny add_messages demo that grows a chat history.
"""

from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage


# -- The two worker nodes are identical in both graphs: each returns a one-item list.
def step_a(state) -> dict:
    return {"log": ["a ran"]}


def step_b(state) -> dict:
    return {"log": ["b ran"]}


def build(reducer: bool):
    """Build START -> a -> b -> END. `reducer` toggles whether 'log' appends."""
    if reducer:
        class State(TypedDict):
            log: Annotated[list, add]      # returned lists are concatenated
    else:
        class State(TypedDict):
            log: list                      # default: last write wins (overwrite)

    b = StateGraph(State)
    b.add_node("a", step_a)
    b.add_node("b", step_b)
    b.add_edge(START, "a")
    b.add_edge("a", "b")
    b.add_edge("b", END)
    return b.compile()


def main() -> None:
    print("=" * 56)
    print("A. No reducer  ->  OVERWRITE (last node wins)")
    print("=" * 56)
    overwrite = build(reducer=False)
    print("final log:", overwrite.invoke({"log": []})["log"])   # ['b ran']

    print("\n" + "=" * 56)
    print("B. Annotated[list, add]  ->  APPEND")
    print("=" * 56)
    append = build(reducer=True)
    print("final log:", append.invoke({"log": []})["log"])      # ['a ran', 'b ran']

    print("\n" + "=" * 56)
    print("C. add_messages  ->  chat history that grows")
    print("=" * 56)

    class ChatState(TypedDict):
        messages: Annotated[list, add_messages]

    def respond(state) -> dict:
        # A node just returns the NEW messages; the reducer appends them.
        return {"messages": [AIMessage("Hi! How can I help?")]}

    cb = StateGraph(ChatState)
    cb.add_node("respond", respond)
    cb.add_edge(START, "respond")
    cb.add_edge("respond", END)
    chat = cb.compile()

    out = chat.invoke({"messages": [HumanMessage("hello")]})
    for m in out["messages"]:
        print(f"  {m.type:6s}: {m.content}")
    print("  -> the human msg stayed; the AI reply was APPENDED, not replaced")


if __name__ == "__main__":
    main()
