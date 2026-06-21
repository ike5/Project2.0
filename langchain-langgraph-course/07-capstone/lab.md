# Lab 07 — Build the Stateful RAG Agent

A guided build of the capstone, milestone by milestone. You'll edit
[`code/starter.py`](./code/starter.py) (which runs but is incomplete) and check
your work against the expected behaviour at each step. Stuck? The finished version
is [`code/rag_agent.py`](./code/rag_agent.py) — try first, peek later.

> **Setup.** From the course root, with your venv active and your local Ollama server running
> set. The first run downloads ~90 MB of local embedding weights, then it's
> offline for retrieval. The scaffold imports `ensure_kb` from `sample_kb.py`, so
> work from inside `07-capstone/code/` or keep it on your path.

```bash
python 07-capstone/code/sample_kb.py      # writes the sample knowledge base
```
✅ **Check:** prints `Wrote knowledge base to: …/kb.txt` and a short preview about
the *Lumen Mug*. Skim `kb.txt` — those are the only facts your agent should claim.

---

## M1 — Index your docs

Open `starter.py` and implement `build_retriever()` (follow the docstring). Then
uncomment the `_retriever = build_retriever()` line.

Quick smoke test in a Python shell (from `07-capstone/code/`):

```python
from starter import build_retriever
r = build_retriever()
for d in r.invoke("warranty"):
    print(d.page_content[:60], "…")
```
✅ **Check:** the top chunk mentions the **two-year limited warranty** and
`support@northwind.example`. Retrieval is finding the right passage.

---

## M2 — Wrap retrieval as a `@tool`

Fill in `search_docs` so it runs `_retriever.invoke(query)` and returns the chunks
joined together. Then add `search_docs` to the `TOOLS` list.

```python
from starter import search_docs
print(search_docs.invoke({"query": "How long does the battery last?"}))
```
✅ **Check:** you get back manual text mentioning **six hours** / **3200 mAh**.
`search_docs.name` is `"search_docs"` and `search_docs.description` is its
docstring — that text is what the model reads to decide when to call it.

---

## M3 — Build the agent graph

Implement the `agent` node and `build_agent()` (wire
`START → agent →(tools_condition)→ tools → agent`). Leave the checkpointer out for
*this* check if you like, or include it now.

Inspect the wiring:

```python
from starter import build_agent
build_agent().get_graph().print_ascii()
```
✅ **Check:** the ASCII diagram shows `__start__ → agent`, a conditional edge from
`agent` to both `tools` and `__end__`, and `tools → agent`. Now run:

```bash
python 07-capstone/code/starter.py
```
✅ **Check:** the first question ("How long does the Lumen Mug hold its
temperature?") gets a grounded answer of **about six hours**. If you added a print
inside `search_docs`, you'll see it fire on this turn. Ask "what's 2+2?" and the
agent should answer directly **without** calling `search_docs` — retrieval is
opt-in, driven by the agent.

---

## M4 — Add memory

Make sure `build_agent()` compiles with `checkpointer=InMemorySaver()` and that
`main()` passes `config={"configurable":{"thread_id": "starter-1"}}` on every turn.

✅ **Check:** the second turn, *"And how long does it take to charge **it** fully?"*,
resolves "it" to the mug and answers **~90 minutes** — only possible if the agent
saw the first turn. Change the `thread_id` between the two turns and watch the
follow-up lose the thread (the agent no longer knows what "it" is). That contrast
*is* the memory.

---

## M5 — Multi-turn demo + design note

Flesh out `main()` (or copy the structure from `rag_agent.py`) into a session that
shows all three behaviours on one `thread_id`:

1. a **doc question** → `search_docs` fires, grounded answer;
2. a **memory follow-up** → pronoun resolved from history;
3. a **utility-tool question** → `multiply` fires (e.g. "7 mugs at 3 each").

Then run the full reference to see the target behaviour, including a fresh thread
forgetting:

```bash
python 07-capstone/code/rag_agent.py
```
✅ **Check:** you see `[search_docs called …]` and `[multiply called …]` markers at
the right moments, grounded answers, and **Session B** (a new `thread_id`) unable
to say what was asked in Session A.

Finally, **write `DESIGN.md`** answering the five questions in the
[README](./README.md#the-design-note-you-write-designmd). Then compare with
[`solutions/DESIGN_example.md`](./solutions/DESIGN_example.md) and the design notes
in [`solutions/solution.md`](./solutions/solution.md).

---

## Done?

You've shipped a stateful RAG agent: retrieval the agent decides to use, a tool
loop that terminates on `tools_condition`, and memory across turns. Check the
[Deliverables](./README.md#deliverables) list, then try a
[stretch goal](./README.md#stretch-goals) — returning sources or human-in-the-loop
are the most instructive.

← back to [Module 07 README](./README.md) ·
[Module 06](../06-agents-with-langgraph/) · [course home](../README.md)
