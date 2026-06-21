# Lab 06 — Agents with LangGraph

**You'll:** run the hand-built agent and trace its loop, prove memory is per-thread, compare
the one-liner, then extend the agent in the REPL. ⏱️ ~55 min. From the
`langchain-langgraph-course` folder, with your local Ollama server running.

> The scripts import `tools.py` as a sibling module, so run them from the `code/` directory
> (or add it to your path). The commands below `cd` in first.

---

## Part A — Build & trace the loop

```bash
cd 06-agents-with-langgraph/code
python agent_graph.py
```

First you'll see the ASCII graph (`agent`, `tools`, the conditional edge, the loop back),
then the conversation streamed message by message for *"What's 23\*19, and what's the weather
in Tokyo?"*

✅ In the printed messages, **find these three things**:
- the **`AIMessage` with tool_calls** — the model *requesting* `multiply` and `get_weather`
  (it does **not** run them itself);
- the **`ToolMessage`(s)** — the results `437` and `18°C and rainy` that the **`ToolNode`**
  appended;
- the **final `AIMessage`** — natural-language answer, **no** tool_calls. That empty
  `tool_calls` is why `tools_condition` returned `END` and the loop stopped.

✅ State in one sentence why the loop terminated (the last AIMessage had no tool_calls).

## Part B — Memory is per `thread_id`

```bash
python agent_memory.py
```

✅ On thread `"sam"`: turn 1 says *"My name is Sam"*, turn 2 asks *"What's my name?"* and the
agent answers **Sam** — because both turns share `thread_id="sam"` and the checkpointer
reloaded the history.

✅ On thread `"fresh"`: the same *"What's my name?"* gets *"I don't know"* — a different
`thread_id` is a separate, empty conversation.

Confirm the mechanism in the REPL:
```python
>>> from agent_memory import build_graph_with_memory, ask
>>> g = build_graph_with_memory()
>>> ask(g, "Remember the number 42.", thread_id="t1")
>>> ask(g, "What number did I ask you to remember?", thread_id="t1")   # -> 42
>>> ask(g, "What number did I ask you to remember?", thread_id="t2")   # -> doesn't know
```
✅ Same `thread_id` remembers; a new one forgets.

## Part C — The one-liner, for comparison

```bash
python react_prebuilt.py
```

✅ `create_agent(model, tools=TOOLS, checkpointer=InMemorySaver())` does the **same**
task (and a memory follow-up) in ~3 lines. Compare it to `agent_graph.py`: identical
behavior, but you wrote no `State`, no nodes, no edges. Note *when* you'd still hand-build
(custom nodes / branching / human-in-the-loop).

## Part D — Add a third tool and chain two tools

In the REPL (from the `code/` dir), build the agent with an extra tool and ask a question
that needs **two** tools in sequence:

```python
>>> from langchain_core.tools import tool
>>> from langchain_ollama import ChatOllama
>>> from langchain_core.messages import HumanMessage
>>> from langchain.agents import create_agent
>>> from tools import multiply, get_weather

>>> @tool
... def reverse(text: str) -> str:
...     """Reverse a string."""
...     return text[::-1]

>>> agent = create_agent(
...     ChatOllama(model="llama3.1", num_predict=1024),
...     tools=[multiply, get_weather, reverse],
... )
>>> out = agent.invoke({"messages": [HumanMessage(
...     "Reverse the weather description for Tokyo.")]})
>>> print(out["messages"][-1].content)
```
✅ The model calls `get_weather("Tokyo")`, **then** `reverse(...)` on the result — two trips
through the loop. Print `out["messages"]` and count the `ToolMessage`s (there are two).

## Part E — Stretch

- Re-run Part A but print **every** step, not just messages, with
  `for step in graph.stream({...}, stream_mode="updates"): print(step)` — you'll see the
  per-node diffs (`{'agent': ...}`, then `{'tools': ...}`, then `{'agent': ...}`).
- Ask `agent_graph.py`'s graph a question that needs **no** tool (e.g. *"Say hello."*) and
  confirm it goes `agent → END` directly — one node, no tool trip.

---

✅ **Done when:** you can point to the AIMessage-with-tool_calls, the ToolMessage, and the
final answer in the trace; you can show the same thread remembering and a new thread
forgetting; and you can reproduce the agent with `create_agent`.

**Next →** [challenge.md](./challenge.md) then
[Module 07: Capstone — RAG Agent](../07-capstone/)
