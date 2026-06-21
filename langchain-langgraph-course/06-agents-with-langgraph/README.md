# Module 06 — Agents with LangGraph

**Goal:** build a real **agent** — a model that loops *think → act → observe* until it
has an answer — as an explicit LangGraph state machine. You'll wire an **agent node**, a
**`ToolNode`**, and **`tools_condition`** into a loop, understand *why the loop ends*, add
**memory** with a checkpointer, and meet the **`create_agent`** one-liner.
⏱️ ~3.5 h · 🎯 Prereq: 05 (graphs) + 03 (tools).

---

## 1. An agent is a loop

In Module 03 you let the model **call your Python functions**. But you ran the loop by
hand: ask → model requests a tool → *you* run it → feed the result back → model answers.
An **agent** is exactly that loop, but the system drives it automatically and repeats as
needed:

```
         ┌──────────────────────────────────────┐
         │                                       │
   START ──▶ ┌───────┐  tool_calls?  ┌────────┐  │
             │ agent │ ──── yes ────▶│ tools  │──┘
             │(model)│               │(ToolNode)
             └───────┘ ◀─────────────┘
                 │ no tool_calls
                 ▼
                END
```

**Think** (the model decides what to do), **act** (run a tool), **observe** (read the
result), then think again — looping until the model answers with no further tool request.
That loop is a perfect fit for a **graph**: typed state, a node per step, and a conditional
edge that decides whether to loop or stop. Each box above becomes a node; each arrow an
edge.

## 2. Message state with `add_messages`

The agent's "memory of this turn" is a growing list of messages. The state is a `TypedDict`
whose `messages` key uses the **`add_messages`** reducer so every node **appends** to the
list instead of overwriting it:

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]   # returned messages are APPENDED
```

Without that reducer, the agent node's reply would *replace* the conversation and the model
would forget the question. `add_messages` is what makes the list accumulate
`Human → AI → Tool → AI → …` as the loop runs.

## 3. The agent node

The agent node is one line: call the tool-bound model on the whole conversation so far and
return its reply to be appended.

```python
from langchain_ollama import ChatOllama

model_with_tools = ChatOllama(model="llama3.1", num_predict=1024).bind_tools(tools)

def agent(state: State) -> dict:
    return {"messages": [model_with_tools.invoke(state["messages"])]}
```

The returned `AIMessage` either **answers** the user or **requests tools** (it has
`.tool_calls`). The next edge looks at which.

## 4. `ToolNode` + `tools_condition` — the loop, automated

LangGraph ships the two pieces that turn a single model call into a loop:

```python
from langgraph.prebuilt import ToolNode, tools_condition

ToolNode(tools)   # a NODE: runs whatever tools the last AIMessage requested,
                  #         appends a ToolMessage with each result to state["messages"]
tools_condition   # a conditional-edge FN: returns "tools" if the last AIMessage had
                  #         tool_calls, else END
```

> **This is the payoff from Module 03.** The hand-rolled `tool_loop.py` you wrote there —
> "model requests a tool → *you* look it up by name → run it → wrap the result in a
> `ToolMessage` → feed it back" — is **exactly** what `ToolNode` does, and `tools_condition`
> is the `if ai.tool_calls:` check you wrote by hand. Module 06 doesn't add new tool
> mechanics; it **automates** the loop so it can repeat as many times as the task needs.

## 5. Wiring the loop (and why it ends)

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)  # agent -> "tools" or END
builder.add_edge("tools", "agent")                        # after tools, back to the model
graph = builder.compile()
```

Read the edges as the loop: start at `agent`; if the model asked for tools, go to `tools`,
run them, and return to `agent`; the model now *sees the tool results* and tries again.

**Why it terminates:** every trip through `tools` adds `ToolMessage` results to the
conversation, so on the next `agent` call the model has more information. Once it has enough
to answer, it returns an `AIMessage` with **no** `tool_calls` — `tools_condition` then
returns `END` and the graph stops. The loop is driven entirely by whether the latest
message requests tools.

> ⚠️ A misbehaving prompt or tool can loop indefinitely. Production agents cap iterations
> (LangGraph's `recursion_limit`) as a safety net — but a well-defined task stops on its own.

## 6. Memory via `InMemorySaver` + `thread_id`

The graph above forgets everything between `invoke` calls. Add a **checkpointer** and the
graph saves its state **per `thread_id`**:

```python
from langgraph.checkpoint.memory import InMemorySaver

graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "sam"}}
graph.invoke({"messages": [HumanMessage("My name is Sam.")]}, config)
graph.invoke({"messages": [HumanMessage("What's my name?")]}, config)  # -> "Sam"

graph.invoke({"messages": [HumanMessage("What's my name?")]},
             {"configurable": {"thread_id": "other"}})                 # -> doesn't know
```

- **Same `thread_id`** → the saved messages are reloaded first, so the agent **remembers**.
- **New `thread_id`** → a fresh, empty conversation.
- `InMemorySaver` lives in RAM (gone when the process exits). Swap in a DB-backed saver to
  persist across restarts — same API.

## 7. The `create_agent` one-liner

When you don't need custom nodes or branching, skip the hand-wiring entirely:

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(model, tools=tools, checkpointer=InMemorySaver())
agent.invoke({"messages": [HumanMessage("What's 23*19, and the weather in Tokyo?")]},
             {"configurable": {"thread_id": "1"}})
```

That single call builds **the same** agent node + `ToolNode` + conditional loop + memory you
assembled in sections 2–6. Build the graph by hand when you need custom nodes, extra
branches, or a human-in-the-loop pause; reach for `create_agent` for the common case.

---

## Do the lab
Run the hand-built agent and trace the loop message by message, prove memory works per
thread, then contrast with the one-liner — and chain two tools in the REPL.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/tools.py`](./code/tools.py) — shared `@tool`s (`multiply`, `get_weather`, `word_count`)
- [`code/agent_graph.py`](./code/agent_graph.py) — the agent loop built by hand; streams the messages so you see model→tool→model
- [`code/agent_memory.py`](./code/agent_memory.py) — same graph + `InMemorySaver`; same thread remembers, new thread forgets
- [`code/react_prebuilt.py`](./code/react_prebuilt.py) — the `create_agent` shortcut, same task in a few lines

## Key terms
agent · think→act→observe loop · message state · `add_messages` reducer · agent node ·
`ToolNode` · `tools_condition` · conditional edge · loop termination · `recursion_limit` ·
checkpointer · `InMemorySaver` · `thread_id` · `create_agent`

**Next →** [Module 07: Capstone — RAG Agent](../07-capstone/)
