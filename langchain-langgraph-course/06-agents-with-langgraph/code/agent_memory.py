"""The same agent graph, now with MEMORY via a checkpointer + thread_id.

Run:
    python 06-agents-with-langgraph/code/agent_memory.py

Needs a running local Ollama server (ollama serve).

A checkpointer saves the graph's state PER thread_id between invokes. So two calls
on the same thread_id share history (the agent remembers); a different thread_id is
a brand-new conversation (it forgets).
"""

from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from tools import TOOLS


class State(TypedDict):
    messages: Annotated[list, add_messages]


model_with_tools = ChatOllama(model="llama3.1", num_predict=1024).bind_tools(TOOLS)


def agent(state: State) -> dict:
    return {"messages": [model_with_tools.invoke(state["messages"])]}


def build_graph_with_memory():
    builder = StateGraph(State)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    # The ONLY change from agent_graph.py: pass a checkpointer at compile time.
    return builder.compile(checkpointer=InMemorySaver())


def ask(graph, text: str, thread_id: str) -> str:
    """Send one human turn on a given thread, return the agent's final reply."""
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"messages": [HumanMessage(text)]}, config)
    return result["messages"][-1].content


def main() -> None:
    graph = build_graph_with_memory()

    print("=== Thread 'sam' — two turns, SAME thread_id ===")
    print("turn 1 >", "My name is Sam.")
    print("        ", ask(graph, "My name is Sam.", thread_id="sam"))
    print("turn 2 >", "What's my name?")
    print("        ", ask(graph, "What's my name?", thread_id="sam"))
    print("  ^ Remembers 'Sam' because both turns share thread_id='sam'.")

    print("\n=== Thread 'fresh' — a DIFFERENT thread_id ===")
    print("turn 1 >", "What's my name?")
    print("        ", ask(graph, "What's my name?", thread_id="fresh"))
    print("  ^ No memory of Sam: this is a separate conversation.")


if __name__ == "__main__":
    main()
