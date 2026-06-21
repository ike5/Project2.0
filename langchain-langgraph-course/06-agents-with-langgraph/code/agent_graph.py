"""Build a tool-calling AGENT as a LangGraph state machine — by hand.

Run:
    python 06-agents-with-langgraph/code/agent_graph.py

Needs a running local Ollama server (ollama serve).

The agent is just a loop:  agent (model) -> tools? -> tools -> agent -> ... -> END.
We wire it with one custom node (the model call), a prebuilt ToolNode (runs the
tools the model asked for), and tools_condition (the conditional edge that decides
"loop to tools" vs "we're done"). No memory yet — that's agent_memory.py.
"""

from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Import the shared tools (run this file from the repo root; the code/ dir is on
# sys.path when you run the script directly).
from tools import TOOLS


# 1) State: a growing list of messages. add_messages is the reducer that APPENDS
#    each node's returned messages instead of overwriting the list.
class State(TypedDict):
    messages: Annotated[list, add_messages]


# Bind the tools so the model knows their names/schemas and can REQUEST them.
model_with_tools = ChatOllama(model="llama3.1", num_predict=1024).bind_tools(TOOLS)


# 2) The agent node: call the model on the whole conversation so far. Its reply
#    (an AIMessage) gets appended to state["messages"].
def agent(state: State) -> dict:
    return {"messages": [model_with_tools.invoke(state["messages"])]}


def build_graph():
    builder = StateGraph(State)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(TOOLS))  # runs requested tools, appends ToolMessages

    builder.add_edge(START, "agent")
    # tools_condition routes "agent" -> "tools" if the last AIMessage had tool_calls,
    # otherwise -> END. THIS is what automates Module 03's manual request->run->feedback loop.
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")  # after running tools, go back to the model
    return builder.compile()


def main() -> None:
    graph = build_graph()

    print("=== Graph structure ===")
    graph.get_graph().print_ascii()

    question = "What's 23*19, and what's the weather in Tokyo?"
    print(f"\n=== Question ===\n{question}\n")

    # stream_mode="values" yields the FULL state after each node, so we can watch
    # the message list grow: Human -> AI(tool_calls) -> Tool(s) -> AI(final answer).
    print("=== The loop, message by message ===")
    seen = 0
    for state in graph.stream({"messages": [HumanMessage(question)]}, stream_mode="values"):
        msgs = state["messages"]
        for m in msgs[seen:]:  # only print messages we haven't shown yet
            kind = m.__class__.__name__
            if getattr(m, "tool_calls", None):
                calls = [f"{c['name']}({c['args']})" for c in m.tool_calls]
                print(f"  {kind:12} -> requests tools: {calls}")
            elif kind == "ToolMessage":
                print(f"  {kind:12} -> tool result: {m.content}")
            else:
                text = m.content if isinstance(m.content, str) else str(m.content)
                print(f"  {kind:12} -> {text.strip()[:200]}")
        seen = len(msgs)

    print("\nNotice: the model first REQUESTED both tools, the ToolNode RAN them, then the")
    print("model used the results to write the final answer. The loop ended because that")
    print("last AIMessage had no tool_calls, so tools_condition returned END.")


if __name__ == "__main__":
    main()
