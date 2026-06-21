"""Reference solution for Challenge 06. Run:
    python 06-agents-with-langgraph/solutions/challenge_solution.py

Needs a running local Ollama server (ollama serve). Builds a hand-wired agent with two custom tools, runs a
no-tool vs tool question, a multi-turn memory check (and a fresh-thread check), a
two-tool chain streamed so you see the loop iterate twice, then rebuilds the same
agent with create_agent and confirms matching behavior.
"""

from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.agents import create_agent


# --- Task 1: two custom tools ------------------------------------------------
@tool
def lookup_capital(country: str) -> str:
    """Return the capital city of a country."""
    capitals = {
        "france": "Paris",
        "japan": "Tokyo",
        "kenya": "Nairobi",
        "brazil": "Brasília",
    }
    return capitals.get(country.strip().lower(), f"Unknown capital for {country}")


@tool
def char_count(text: str) -> int:
    """Count the number of characters in a piece of text."""
    return len(text)


TOOLS = [lookup_capital, char_count]


# --- Task 1: state + agent node ----------------------------------------------
class State(TypedDict):
    messages: Annotated[list, add_messages]


model_with_tools = ChatOllama(model="llama3.1", num_predict=1024).bind_tools(TOOLS)


def agent(state: State) -> dict:
    return {"messages": [model_with_tools.invoke(state["messages"])]}


def make_builder() -> StateGraph:
    """The shared wiring; compile with or without a checkpointer."""
    builder = StateGraph(State)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder


def task1_build_and_show() -> None:
    print("\n[1] Hand-wired agent graph")
    graph = make_builder().compile()
    graph.get_graph().print_ascii()


def task2_tool_vs_no_tool() -> None:
    print("\n[2] Tool question vs no-tool question")
    graph = make_builder().compile()

    out = graph.invoke({"messages": [HumanMessage("What's the capital of Japan?")]})
    print("  tool question ->", out["messages"][-1].content.strip())
    # The model used lookup_capital, so a ToolMessage must be in the history.
    assert any(m.__class__.__name__ == "ToolMessage" for m in out["messages"])

    out = graph.invoke({"messages": [HumanMessage("Say the word 'hello'.")]})
    print("  no-tool question ->", out["messages"][-1].content.strip())
    assert not any(m.__class__.__name__ == "ToolMessage" for m in out["messages"])


def task3_memory() -> None:
    print("\n[3] Multi-turn memory on one thread; fresh thread forgets")
    graph = make_builder().compile(checkpointer=InMemorySaver())

    def ask(text: str, thread_id: str) -> str:
        cfg = {"configurable": {"thread_id": thread_id}}
        return graph.invoke({"messages": [HumanMessage(text)]}, cfg)["messages"][-1].content

    print("  t1 >", ask("My favorite country is Kenya.", "t1").strip()[:80])
    print("  t1 >", ask("What is the capital of my favorite country?", "t1").strip()[:80])
    answer = ask("Remind me which country I said was my favorite.", "t1")
    print("  t1 >", answer.strip()[:80])
    assert "kenya" in answer.lower()

    fresh = ask("Which country did I say was my favorite?", "fresh")
    print("  fresh >", fresh.strip()[:80])
    assert "kenya" not in fresh.lower()


def task4_two_tool_chain() -> None:
    print("\n[4] Two-tool chain — watch the loop iterate twice")
    graph = make_builder().compile()
    question = ("Find the capital of Brazil, then tell me how many characters "
                "are in that city's name.")
    tool_passes = 0
    for step in graph.stream({"messages": [HumanMessage(question)]}, stream_mode="updates"):
        for node in step:
            print(f"  step -> node '{node}'")
            if node == "tools":
                tool_passes += 1
    final = graph.invoke({"messages": [HumanMessage(question)]})["messages"][-1].content
    print("  final answer ->", final.strip()[:120])
    print(f"  passed through 'tools' {tool_passes} time(s)")
    assert tool_passes >= 2, "expected the loop to use tools at least twice"


def task5_prebuilt_equivalent() -> None:
    print("\n[5] Same agent via create_agent")
    model = ChatOllama(model="llama3.1", num_predict=1024)
    agent_app = create_agent(model, tools=TOOLS, checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "react"}}

    out = agent_app.invoke({"messages": [HumanMessage("Capital of France?")]}, cfg)
    print("  tool question ->", out["messages"][-1].content.strip()[:80])

    out = agent_app.invoke({"messages": [HumanMessage("What city did you just name?")]}, cfg)
    print("  memory follow-up ->", out["messages"][-1].content.strip()[:80])
    assert "paris" in out["messages"][-1].content.lower()


def main() -> None:
    task1_build_and_show()
    task2_tool_vs_no_tool()
    task3_memory()
    task4_two_tool_chain()
    task5_prebuilt_equivalent()
    # [6] Why it terminates: tools_condition routes to "tools" only while the last
    # AIMessage has tool_calls; once the model answers without requesting a tool, it
    # returns END. In task 4 the model needed lookup_capital, then char_count on the
    # result, then had everything to answer — so it looped tools exactly twice and stopped.
    print("\nAll checks passed ✅")


if __name__ == "__main__":
    main()
