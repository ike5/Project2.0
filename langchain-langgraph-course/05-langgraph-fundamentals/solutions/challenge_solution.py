"""Reference solution for Challenge 05. Run:
    python 05-langgraph-fundamentals/solutions/challenge_solution.py

Covers: a reducer-accumulated log (vs overwrite), a fixed-count loop accumulating
into a list, a conditional edge to one of two terminal nodes, and (stretch) a node
that calls the model. The model task needs your local Ollama server running.
"""

from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END


def task1_reducer_log() -> None:
    print("\n[1] Reducer-accumulated log")

    class State(TypedDict):
        log: Annotated[list, add]

    def first(s):  return {"log": ["first"]}
    def second(s): return {"log": ["second"]}
    def third(s):  return {"log": ["third"]}

    b = StateGraph(State)
    b.add_node("first", first); b.add_node("second", second); b.add_node("third", third)
    b.add_edge(START, "first")
    b.add_edge("first", "second")
    b.add_edge("second", "third")
    b.add_edge("third", END)
    g = b.compile()
    out = g.invoke({"log": []})
    print("  with reducer   :", out["log"])
    assert out["log"] == ["first", "second", "third"]

    # Same graph, but the key has NO reducer -> last node overwrites.
    class PlainState(TypedDict):
        log: list

    b2 = StateGraph(PlainState)
    b2.add_node("first", first); b2.add_node("second", second); b2.add_node("third", third)
    b2.add_edge(START, "first")
    b2.add_edge("first", "second")
    b2.add_edge("second", "third")
    b2.add_edge("third", END)
    plain = b2.compile().invoke({"log": []})
    print("  without reducer:", plain["log"])
    assert plain["log"] == ["third"]


def task2_fixed_loop() -> None:
    print("\n[2] Loop exactly N times, accumulating")
    N = 5

    class State(TypedDict):
        count: int
        results: Annotated[list, add]

    def work(s):
        c = s["count"] + 1
        return {"count": c, "results": [c]}

    def keep_going(s) -> str:
        return "work" if s["count"] < N else END

    b = StateGraph(State)
    b.add_node("work", work)
    b.add_edge(START, "work")
    b.add_conditional_edges("work", keep_going, {"work": "work", END: END})
    g = b.compile()

    print("  streamed per-node updates:")
    for step in g.stream({"count": 0, "results": []}):
        print("   ", step)

    out = g.invoke({"count": 0, "results": []})
    print("  final:", out)
    assert out["count"] == N
    assert out["results"] == [1, 2, 3, 4, 5]


def task3_branch() -> None:
    print("\n[3] Conditional edge to one of two terminal nodes")

    class State(TypedDict):
        category: str
        answer: str

    def handle_question(s): return {"answer": "answered a question"}
    def handle_command(s):  return {"answer": "ran a command"}

    def route(s) -> str:
        return "handle_question" if s["category"] == "q" else "handle_command"

    b = StateGraph(State)
    b.add_node("handle_question", handle_question)
    b.add_node("handle_command", handle_command)
    b.add_conditional_edges(START, route,
                            {"handle_question": "handle_question",
                             "handle_command": "handle_command"})
    b.add_edge("handle_question", END)
    b.add_edge("handle_command", END)
    g = b.compile()

    q = g.invoke({"category": "q", "answer": ""})
    c = g.invoke({"category": "c", "answer": ""})
    print("  category 'q' ->", q["answer"])
    print("  category 'c' ->", c["answer"])
    assert q["answer"] == "answered a question"
    assert c["answer"] == "ran a command"


def task4_model_node() -> None:
    print("\n[4] Stretch: a node that calls the model")
    # Needs your local Ollama server running (ollama serve) with llama3.1 pulled.
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage
    from langgraph.graph.message import add_messages

    class ChatState(TypedDict):
        messages: Annotated[list, add_messages]

    model = ChatOllama(model="llama3.1", num_predict=512)

    def chat(s) -> dict:
        return {"messages": [model.invoke(s["messages"])]}

    b = StateGraph(ChatState)
    b.add_node("chat", chat)
    b.add_edge(START, "chat")
    b.add_edge("chat", END)
    g = b.compile()

    out = g.invoke({"messages": [HumanMessage("Reply with exactly: pong")]})
    for m in out["messages"]:
        print(f"  {m.type:6s}: {m.content}")
    assert len(out["messages"]) >= 2   # human + AI reply both present


def main() -> None:
    task1_reducer_log()
    task2_fixed_loop()
    task3_branch()
    task4_model_node()
    print("\nAll checks passed ✅")


if __name__ == "__main__":
    main()
