# Module 05 — LangGraph Fundamentals

**Goal:** build the mental model for **graphs**. A chain is a straight line:
`prompt | model | parser`, one pass, input to output. But agents *loop* — think, act,
observe, think again — and real apps *branch*. LangGraph lets you wire that as an explicit
**graph** of typed **state**, **nodes**, and **edges** you can inspect and step through.
This module is pure mechanics (mostly plain-Python nodes, deterministic output) so the
concepts stay crisp. Agents and tools come in Module 06. ⏱️ ~3 h · 🎯 Prereq: 04.

---

## 1. Chains vs graphs (loops & branches)

LCEL chains (Modules 02–04) are **directed and acyclic**: data flows one way, start to
finish. That's perfect for "format → call → parse." It falls apart the moment you need to:

- **Loop:** keep calling the model until it stops asking for tools (an agent).
- **Branch:** route to *this* node if the input is a question, *that* node if it's a command.
- **Carry state:** accumulate a running list (a conversation, a scratchpad) across steps.

```
   Chain (a straight line)                     Graph (loops & branches)
 ┌──────────────────────────┐         ┌────────────────────────────────────┐
 │ A ──▶ B ──▶ C ──▶ END     │         │  START ──▶ work ──▶ route? ──done──▶ END │
 │   one pass, no looking    │         │              ▲          │               │
 │   back                    │         │              └──not yet──┘  (a loop)    │
 └──────────────────────────┘         └────────────────────────────────────┘
```

A **graph** is: a shared **State** (a `TypedDict`), **nodes** (functions that read state and
return an update), and **edges** (what runs next — fixed, or chosen by a router). You
`compile()` it once, then `invoke()` / `stream()` it like any runnable.

## 2. State (a TypedDict) + your first single-node graph

**State** is the data every node shares. Declare it as a `TypedDict`. A **node** is a plain
function `def node(state) -> dict:` that returns **only the keys it changes** — a *partial
update*. LangGraph merges that update into the state for you.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    value: int

def increment(state: State) -> dict:
    return {"value": state["value"] + 1}     # return ONLY what changed

builder = StateGraph(State)
builder.add_node("inc", increment)
builder.add_edge(START, "inc")               # entry point
builder.add_edge("inc", END)                 # finish
graph = builder.compile()

graph.invoke({"value": 0})                    # -> {"value": 1}
```

`START` and `END` are sentinel nodes: `START → "inc"` says "begin here," `"inc" → END` says
"then stop." Inspect the wiring any time with `graph.get_graph().print_ascii()`.

> **Why a TypedDict?** It documents the shape of your state and lets nodes return just a
> slice of it. You never reconstruct the whole dict — you return the delta.

## 3. Nodes return partial updates (overwrite semantics)

A node returns a dict of changed keys. By default, a returned key **overwrites** the old
value — last writer wins. Keys the node *doesn't* return are left untouched.

```python
class State(TypedDict):
    value: int
    note: str

def bump(state):  return {"value": state["value"] + 10}   # only touches "value"
def label(state): return {"note": "done"}                  # only touches "note"
```

After both run, `value` is bumped and `note` is set — each node contributed its slice. If
two nodes both returned `value`, the later one's number would simply replace the earlier
one. Overwrite is the default. When you want to *accumulate* instead, you need a reducer.

## 4. Reducers — merge instead of overwrite

A **reducer** is a function attached to a state key that says *how to combine* the old value
with a node's returned value. Annotate the key with `Annotated[type, reducer]`. The classic
one is `operator.add`, which on lists means **append**:

```python
from typing import Annotated, TypedDict
from operator import add

class State(TypedDict):
    log: Annotated[list, add]      # returned lists are APPENDED, not replaced

def step_a(state): return {"log": ["a ran"]}
def step_b(state): return {"log": ["b ran"]}
# after a then b:  log == ["a ran", "b ran"]   (NOT just ["b ran"])
```

Without the `Annotated[..., add]`, `log` would end up `["b ran"]` — `step_b` overwrote
`step_a`. *With* the reducer, each node's list is concatenated onto the running log. This is
the single most important idea for stateful graphs.

For **chat history**, LangGraph ships a purpose-built reducer, `add_messages`. It appends new
messages, and — cleverly — *updates in place* when a message has the same `id` (so streamed
partial messages don't duplicate):

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    messages: Annotated[list, add_messages]   # appends; dedupes/updates by message id
```

This is exactly the state your agent will use in Module 06 — every node that talks to the
model just returns `{"messages": [reply]}` and the reducer grows the conversation.

## 5. Conditional edges (branching)

A fixed edge always goes to the same place. A **conditional edge** runs a **router** — a
function that reads the state and returns the **name of the next node** (or `END`):

```python
def route(state) -> str:
    return "even_node" if state["value"] % 2 == 0 else "odd_node"

builder.add_conditional_edges("check", route)
# or pin the possibilities with an explicit map:
builder.add_conditional_edges("check", route, {"even_node": "even_node",
                                                "odd_node": "odd_node"})
```

The router doesn't *do* work — it **decides**. It returns a string that must match a node
name you registered (or the `END` sentinel). The explicit map is optional but documents
every branch and lets `print_ascii()` draw them.

## 6. Loops — a counter node + a router that loops back

Cycles are what graphs give you that chains can't. The recipe: a node that makes progress
(and bumps a counter), plus a conditional edge that points **back to that node** until a stop
condition holds, then to `END`.

```python
class State(TypedDict):
    count: int

def tick(state):  return {"count": state["count"] + 1}

def keep_going(state) -> str:
    return "tick" if state["count"] < 3 else END   # loop back, or stop

builder.add_node("tick", tick)
builder.add_edge(START, "tick")
builder.add_conditional_edges("tick", keep_going, {"tick": "tick", END: END})
graph = builder.compile()
graph.invoke({"count": 0})        # tick runs until count == 3 -> {"count": 3}
```

The counter is your loop guard — it guarantees termination. (LangGraph also has a
`recursion_limit` that hard-stops runaway loops, so a missing guard fails loudly instead of
hanging.) **Watch it run** by streaming the per-node updates:

```python
for step in graph.stream({"count": 0}):
    print(step)                   # {'tick': {'count': 1}}, {'tick': {'count': 2}}, ...
```

`stream` yields the **update after each node** by default. Pass `stream_mode="values"` to
get the **full state** at each step instead of just the diff.

---

## Do the lab
Run all three scripts; predict each final state, predict append-vs-overwrite, and trace the
loop step by step. Then build a 2-node sequential graph yourself in the REPL.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/first_graph.py`](./code/first_graph.py) — a minimal one-node graph; invoke + `print_ascii()`
- [`code/reducers.py`](./code/reducers.py) — overwrite vs `Annotated[list, add]` vs `add_messages`
- [`code/branch_and_loop.py`](./code/branch_and_loop.py) — a conditional branch + a counting loop, streamed

## Key terms
graph vs chain · `StateGraph` · State (`TypedDict`) · node (partial update) · `START`/`END` ·
edge · `add_edge` · `compile` · `invoke` · partial update / overwrite · reducer ·
`Annotated[list, add]` · `add_messages` · conditional edge · router (returns a node **name**) ·
loop / counter guard · `stream` · `stream_mode` (`"updates"` vs `"values"`) · `print_ascii`

**Next →** [Module 06: Agents with LangGraph](../06-agents-with-langgraph/)
