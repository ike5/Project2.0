"""The same agent in a few lines, using the create_agent shortcut.

Run:
    python 06-agents-with-langgraph/code/react_prebuilt.py

Needs a running local Ollama server (ollama serve).

create_agent wires up exactly what agent_graph.py + agent_memory.py build by
hand — an agent node, a ToolNode, the conditional loop, and (optionally) a
checkpointer for memory. Reach for it when you DON'T need custom nodes, branching,
or human-in-the-loop. Build the graph yourself when you do.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent

from tools import TOOLS


def main() -> None:
    model = ChatOllama(model="llama3.1", num_predict=1024)

    # One line: model + tools + loop + memory. No State class, no nodes, no edges.
    agent = create_agent(model, tools=TOOLS, checkpointer=InMemorySaver())

    config = {"configurable": {"thread_id": "demo"}}
    question = "What's 23*19, and what's the weather in Tokyo?"
    print("=== Same task as the hand-built graph ===")
    print("Q:", question)
    result = agent.invoke({"messages": [HumanMessage(question)]}, config)
    print("A:", result["messages"][-1].content)

    # Memory comes for free with the checkpointer + same thread_id.
    print("\n=== Follow-up on the same thread (memory) ===")
    follow = "And what's the weather in Paris?"
    print("Q:", follow)
    result = agent.invoke({"messages": [HumanMessage(follow)]}, config)
    print("A:", result["messages"][-1].content)

    print("\nSame behavior as the hand-built graph — in ~3 lines instead of ~30.")


if __name__ == "__main__":
    main()
