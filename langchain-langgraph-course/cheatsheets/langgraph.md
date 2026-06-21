# LangGraph cheatsheet (local, with Ollama)

Everything you reach for in this course's LangGraph modules (05–07), in one place.
Up to date for 2026: current LangGraph + LangChain 1.x `create_agent`.

## The minimal graph

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    value: int

def increment(state: State) -> dict:
    return {"value": state["value"] + 1}     # return ONLY the keys you change

builder = StateGraph(State)
builder.add_node("inc", increment)
builder.add_edge(START, "inc")
builder.add_edge("inc", END)
graph = builder.compile()

graph.invoke({"value": 0})                   # -> {"value": 1}
```

Rules of thumb:
- **State** is a `TypedDict`. Nodes receive the whole state, return a *partial* update.
- By default a returned key **overwrites** the old value. Use a **reducer** to merge instead.

## Reducers — merge instead of overwrite

```python
from typing import Annotated, TypedDict
from operator import add

class State(TypedDict):
    log: Annotated[list, add]     # returned lists are APPENDED, not replaced
```

For chat, use the built-in message reducer:

```python
from typing import Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]   # appends; updates by message id
```

## Edges — straight, branching, and conditional

```python
builder.add_edge("a", "b")                    # always a -> b
builder.add_edge(START, "a")                  # entry point
builder.add_edge("b", END)                    # finish

# Conditional: a function returns the NAME of the next node
def route(state) -> str:
    return "tools" if state["messages"][-1].tool_calls else END

builder.add_conditional_edges("agent", route)         # route() decides agent -> ?
builder.add_conditional_edges("agent", route, {"tools": "tools", END: END})  # explicit map
```

## A tool-calling agent (by hand)

```python
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing import Annotated, TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]

model = ChatOllama(model="llama3.1").bind_tools(my_tools)

def agent(state: State) -> dict:
    return {"messages": [model.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(my_tools))      # see below
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)   # -> "tools" or END
builder.add_edge("tools", "agent")                 # loop back after running tools
graph = builder.compile()
```

## Prebuilt tool helpers

```python
from langgraph.prebuilt import ToolNode, tools_condition

ToolNode(my_tools)       # a node: runs the tools the last AIMessage requested,
                         #   appends ToolMessage results to state["messages"]
tools_condition          # a conditional-edge fn: "tools" if there were tool calls, else END
```

## Memory — checkpointers & threads

```python
from langgraph.checkpoint.memory import InMemorySaver   # (older name: MemorySaver)

graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "user-42"}}
graph.invoke({"messages": [HumanMessage("My name is Sam.")]}, config)
graph.invoke({"messages": [HumanMessage("What's my name?")]}, config)  # remembers "Sam"
```

- The checkpointer saves state **per `thread_id`** between calls.
- A new `thread_id` = a fresh conversation. `InMemorySaver` is in-RAM; swap for a DB-backed
  saver (e.g. `langgraph-checkpoint-sqlite`) to persist across process restarts.

## Running & inspecting

```python
graph.invoke(state, config)               # run to completion
for step in graph.stream(state, config):  # yields the state update after each node
    print(step)
graph.get_graph().print_ascii()           # ASCII diagram of nodes + edges
snapshot = graph.get_state(config)        # current saved state for a thread
```

`stream_mode` options: `"updates"` (per-node diffs), `"values"` (full state each step),
`"messages"` (token-by-token LLM output inside the graph).

## The one-liner agent (LangChain 1.x `create_agent`)

```python
from langchain.agents import create_agent           # the modern agent harness (built on LangGraph)
from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama

model = ChatOllama(model="llama3.1")
agent = create_agent(model, tools=my_tools, checkpointer=InMemorySaver())
agent.invoke(
    {"messages": [HumanMessage("What's the weather in Paris, then add 2+2?")]},
    config={"configurable": {"thread_id": "1"}},
)
```

`create_agent` gives you the model + tool loop + memory wired up (it replaces the older
`langgraph.prebuilt.create_react_agent`). Build the graph by hand (above) when you need
custom nodes, branching, or human-in-the-loop.
