# Lab 05 — LangGraph Fundamentals

**You'll:** run the three scripts (predicting outputs *before* you look), then build a small
graph yourself in the REPL. ⏱️ ~55 min. From the `langchain-langgraph-course` folder.

The branch/loop parts need no API key. Only Part D's stretch optionally calls the model.

---

## Part A — Your first graph

```bash
python 05-langgraph-fundamentals/code/first_graph.py
```
✅ Read the `print_ascii()` diagram: you should see `__start__ → inc → __end__`. Before you
look at the output, **predict** `invoke({"value": 41})`. (The node returns `{"value": value+1}`,
so → `{"value": 42}`.)

In the REPL, confirm a node returns a *partial* update, not the whole state:
```python
>>> from typing import TypedDict
>>> from langgraph.graph import StateGraph, START, END
>>> class S(TypedDict):
...     value: int
...     tag: str
>>> def only_value(s): return {"value": s["value"] + 1}   # never touches "tag"
>>> b = StateGraph(S); b.add_node("n", only_value)
>>> b.add_edge(START, "n"); b.add_edge("n", END)
>>> g = b.compile()
>>> g.invoke({"value": 0, "tag": "hi"})    # {'value': 1, 'tag': 'hi'}  -> tag survived
```
✅ You can state the rule: **a node returns only the keys it changes; the rest are kept.**

## Part B — Overwrite vs append (reducers)

```bash
python 05-langgraph-fundamentals/code/reducers.py
```
Before reading the output, **predict** each final `log`:
- Section A (no reducer): `step_a` then `step_b` each return a one-item list. Final? → `['b ran']`.
- Section B (`Annotated[list, add]`): same nodes. Final? → `['a ran', 'b ran']`.

✅ The only difference between the two graphs is the `Annotated[list, add]` on the `log` key —
yet one **overwrites** and one **appends**. Say out loud *why*.

✅ Section C: the `HumanMessage` you passed in is still there and the `AIMessage` was
**appended** by `add_messages`. That's the chat state your agent uses next module.

## Part C — Branch and loop

```bash
python 05-langgraph-fundamentals/code/branch_and_loop.py
```
✅ Part A of the script: `value=4` routes to `even_node`, `value=7` to `odd_node`. The
**router returned the node's name** — it didn't compute the label itself.

✅ Part B: trace the loop in your head first. `tick` starts at `count=0`, the router
`keep_going` sends it back while `count < 3`. Predict the streamed updates:
```
{'tick': {'count': 1, 'history': [1]}}
{'tick': {'count': 2, 'history': [2]}}
{'tick': {'count': 3, 'history': [3]}}
```
Then check. ✅ Note: each streamed *update* shows just that tick's `history` (`[2]`), but the
**final state** accumulates `[1, 2, 3]` because of the `add` reducer. With
`stream_mode="values"` you instead see the **full** growing state each step.

## Part D — Build a 2-node sequential graph yourself

In the REPL, wire `START → double → shout → END` over a string-and-int state:
```python
>>> from typing import TypedDict
>>> from langgraph.graph import StateGraph, START, END
>>> class S(TypedDict):
...     n: int
...     text: str
>>> def double(s): return {"n": s["n"] * 2}
>>> def shout(s):  return {"text": f"n is {s['n']}!"}     # reads the doubled n
>>> b = StateGraph(S)
>>> b.add_node("double", double); b.add_node("shout", shout)
>>> b.add_edge(START, "double"); b.add_edge("double", "shout"); b.add_edge("shout", END)
>>> g = b.compile()
>>> g.invoke({"n": 5, "text": ""})        # {'n': 10, 'text': 'n is 10!'}
>>> g.get_graph().print_ascii()
```
✅ `shout` sees the value `double` wrote — nodes run in edge order and share one state.

## Part E — Stretch

- **Add a branch.** Insert a router after `double`: if `n` is now `> 10` go to `shout`,
  else go to a new `quiet` node that sets `text="small"`. Use
  `add_conditional_edges("double", route, {"shout": "shout", "quiet": "quiet"})` and edge
  both terminal nodes to `END`. Try `n=2` and `n=8`.
- **One model node (optional, needs a running Ollama server).** Add a node whose body is
  `from langchain_ollama import ChatOllama` →
  `reply = ChatOllama(model="llama3.1", num_predict=512).invoke(state["text"])`
  and return `{"text": reply.content}`. Notice a node can do *anything* — the graph doesn't
  care whether it's pure Python or an API call.

---

✅ **Done when:** you can (1) explain why a node returns a partial update, (2) say what
`Annotated[list, add]` changes vs the default, and (3) trace a counter loop to its `END`.

**Next →** [challenge.md](./challenge.md) then
[Module 06: Agents with LangGraph](../06-agents-with-langgraph/)
