"""Your first LangGraph: a single node over an integer state.

Run:
    python 05-langgraph-fundamentals/code/first_graph.py

Shows: a TypedDict State, a node that returns a PARTIAL update (only the key it
changes), START/END edges, compile + invoke, and the ASCII diagram of the graph.
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# 1. State is the data every node shares. Declare its shape as a TypedDict.
class State(TypedDict):
    value: int


# 2. A node receives the whole state and returns ONLY the keys it changes.
def increment(state: State) -> dict:
    return {"value": state["value"] + 1}


def main() -> None:
    # 3. Build the graph: register the node, wire START -> node -> END.
    builder = StateGraph(State)
    builder.add_node("inc", increment)
    builder.add_edge(START, "inc")        # where to begin
    builder.add_edge("inc", END)          # where to stop
    graph = builder.compile()

    # 4. Inspect the wiring.
    print("Graph structure:")
    graph.get_graph().print_ascii()

    # 5. Run it. invoke returns the FINAL state (a full dict).
    out = graph.invoke({"value": 0})
    print("\ninvoke({'value': 0}) ->", out)        # {'value': 1}
    print("invoke({'value': 41}) ->", graph.invoke({"value": 41}))  # {'value': 42}


if __name__ == "__main__":
    main()
