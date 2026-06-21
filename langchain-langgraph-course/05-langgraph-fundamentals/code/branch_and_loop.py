"""Branching with a conditional edge, and a loop built from a counter + router.

Run:
    python 05-langgraph-fundamentals/code/branch_and_loop.py

Shows: (A) a router that BRANCHES to an even-node or an odd-node based on state;
(B) a LOOP: a node bumps a counter, a router edges back to it until count >= N,
then to END. Both are streamed so you can watch each per-node update.
"""

from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# A. Branching: route to one of two terminal nodes based on parity.
# ---------------------------------------------------------------------------
class BranchState(TypedDict):
    value: int
    label: str


def even_node(state) -> dict:
    return {"label": f"{state['value']} is even"}


def odd_node(state) -> dict:
    return {"label": f"{state['value']} is odd"}


def parity_router(state) -> str:
    # A router does NOT do work — it returns the NAME of the next node.
    return "even_node" if state["value"] % 2 == 0 else "odd_node"


def build_branch():
    b = StateGraph(BranchState)
    b.add_node("even_node", even_node)
    b.add_node("odd_node", odd_node)
    # Branch straight out of START using a conditional edge with an explicit map.
    b.add_conditional_edges(START, parity_router,
                            {"even_node": "even_node", "odd_node": "odd_node"})
    b.add_edge("even_node", END)
    b.add_edge("odd_node", END)
    return b.compile()


# ---------------------------------------------------------------------------
# B. Looping: a counter node + a router that loops back until done.
# ---------------------------------------------------------------------------
class LoopState(TypedDict):
    count: int
    history: Annotated[list, add]   # accumulate each tick (append, not overwrite)


N = 3


def tick(state) -> dict:
    new_count = state["count"] + 1
    return {"count": new_count, "history": [new_count]}


def keep_going(state) -> str:
    # Loop back to "tick" until we hit N, then stop.
    return "tick" if state["count"] < N else END


def build_loop():
    b = StateGraph(LoopState)
    b.add_node("tick", tick)
    b.add_edge(START, "tick")
    b.add_conditional_edges("tick", keep_going, {"tick": "tick", END: END})
    return b.compile()


def main() -> None:
    print("=" * 56)
    print("A. Branch on even/odd")
    print("=" * 56)
    branch = build_branch()
    for v in (4, 7):
        print(f"value={v} -> {branch.invoke({'value': v, 'label': ''})['label']}")

    print("\n" + "=" * 56)
    print(f"B. Loop until count >= {N} (streaming per-node updates)")
    print("=" * 56)
    loop = build_loop()
    for step in loop.stream({"count": 0, "history": []}):
        print("  step:", step)          # {'tick': {'count': 1, 'history': [1]}}, ...

    final = loop.invoke({"count": 0, "history": []})
    print("  final state:", final)      # {'count': 3, 'history': [1, 2, 3]}

    print("\n  same run with stream_mode='values' (FULL state each step):")
    for step in loop.stream({"count": 0, "history": []}, stream_mode="values"):
        print("  values:", step)


if __name__ == "__main__":
    main()
