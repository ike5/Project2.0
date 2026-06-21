# Module 07 — Capstone: A Stateful RAG Agent

**Goal:** ship a working chatbot that *decides for itself* when to look something
up — answering from a knowledge base through a **retrieval tool**, using a utility
tool when useful, and **remembering the conversation** across turns. Then write a
short **design note** explaining the choices you made. ⏱️ ~3+ h · 🎯 Prereq: 00–06.

This is the synthesis. No new concepts — you assemble Module 04's **RAG**, Module
06's **tool-calling agent**, and **memory** into one app. The hinge that ties them
together is a single idea:

> **Wrap retrieval as a tool.** Instead of *always* retrieving before the model
> runs (the Module-04 chain), you give the agent a `search_docs` tool and let the
> **agent decide** when to call it. "What's the warranty?" → it retrieves. "Hi!"
> or "what's 7×3?" → it doesn't. Retrieval becomes just another tool in the loop.

---

## The architecture

One agent node, one tool node, a checkpointer. The agent thinks; if it asked for
a tool, the `ToolNode` runs it (retrieval *or* the utility) and loops back; when
the agent stops asking for tools, it answers and we hit `END`. The checkpointer
saves the message history **per `thread_id`**, so the next turn remembers this one.

```
                    ┌─────────────────────────────────────────────┐
                    │                                             │
   ┌─────┐   tool calls?  ┌──────────────────────────┐           │
   │START│──▶│ agent │───yes──▶│ ToolNode                 │           │
   └─────┘   │(model │        │  ├─ search_docs(query) ──┼─ retriever│
             │+tools)│◀──results──│  └─ multiply(a, b)        │           │
             └───┬───┘        └──────────────────────────┘           │
                 │ no (no tool calls)                                 │
                 ▼                                                    │
                END                                                   │
                                                                     │
   InMemorySaver (checkpointer) ── saves state per thread_id ──────────┘
```

- **agent** = the model bound to `[search_docs, multiply]`. It returns either a
  final answer *or* one-or-more tool calls.
- **tools** = a prebuilt `ToolNode([search_docs, multiply])` that executes the
  requested tool(s) and appends the results as `ToolMessage`s.
- **`tools_condition`** routes `agent → tools` when there are tool calls, else
  `agent → END`.
- **`search_docs`** wraps your Module-04 retriever: it runs `retriever.invoke(query)`
  and returns the concatenated chunk text.
- **`InMemorySaver`** + a `thread_id` give the agent conversational memory.

---

## Milestones

Build it up one runnable step at a time. The lab ([`lab.md`](./lab.md)) walks each
of these with ✅ checks; the starter ([`code/starter.py`](./code/starter.py)) has
the matching TODOs.

- **M1 — Index your docs.** Load `kb.txt`, split, embed locally, store, get a
  retriever. ✅ `retriever.invoke("warranty")` returns relevant chunks.
- **M2 — Wrap retrieval as a `@tool`.** Define `search_docs(query: str) -> str`
  that runs the retriever and returns the chunk text. ✅ calling
  `search_docs.invoke({"query": "battery"})` returns manual text.
- **M3 — Build the agent graph.** State with `messages: Annotated[list, add_messages]`;
  an `agent` node that calls the tool-bound model; a `ToolNode`; wire
  `START → agent →(tools_condition)→ tools → agent`. ✅ a doc question gets a
  grounded answer and you can see `search_docs` fire.
- **M4 — Add memory.** Compile with `checkpointer=InMemorySaver()`; run with
  `config={"configurable":{"thread_id": ...}}`. ✅ a follow-up like "and how long
  to charge **it**?" resolves the pronoun from history.
- **M5 — Multi-turn demo + design note.** Show a session that (a) retrieves, (b)
  uses memory, (c) uses the utility tool — then write **`DESIGN.md`** (see below).
  ✅ the demo prints all three behaviours; a fresh `thread_id` forgets.

### The design note you write (`DESIGN.md`)

A few short paragraphs — answer these in your own words from your own build:

1. **When does your agent retrieve vs. answer directly?** What in the system
   prompt / tool description drives that choice? Give one example of each.
2. **How does the loop terminate?** Trace one turn that calls a tool and one that
   doesn't, in terms of `tools_condition` and `END`.
3. **How would you swap `InMemoryVectorStore` for a real vector DB** (e.g. Chroma,
   pgvector, Pinecone)? What changes, and what stays the same?
4. **What does a `thread_id` buy you, and how would you persist memory** across
   process restarts (i.e. beyond `InMemorySaver`)?
5. **One limitation** of your agent and how you'd address it.

A filled-in reference is in [`solutions/DESIGN_example.md`](./solutions/DESIGN_example.md)
— **write yours first.**

---

## Deliverables

- [ ] **A runnable agent** — your own `rag_agent.py` (start from
      [`code/starter.py`](./code/starter.py)) that builds the index, defines
      `search_docs` + at least one utility tool, wires the graph with
      `ToolNode` + `tools_condition`, and compiles with a checkpointer.
- [ ] **Retrieval-as-a-tool** — the agent calls `search_docs` *only when needed*,
      not on every turn. You can see when it fires.
- [ ] **Memory works** — a follow-up turn that relies on earlier context succeeds
      on the same `thread_id`; a fresh `thread_id` starts blank.
- [ ] **A multi-turn demo** in `main()` that exercises retrieval, memory, and the
      utility tool, and prints verifiable output.
- [ ] **`DESIGN.md`** — your design note answering the five questions above.

## Stretch goals

- **Return sources.** Have `search_docs` include a chunk id / heading so the agent
  can cite where an answer came from ("per the *Battery and charging* section…").
- **Add a persona / system prompt** that shapes tone and refusal behaviour, and
  show it changes the answers.
- **Stream responses.** Run the graph with `stream_mode="messages"` and print the
  reply token-by-token.
- **Human-in-the-loop.** Add an `interrupt_before=["tools"]` checkpoint so a human
  confirms before the agent runs a tool; resume with the saved state.
- **A second knowledge source / second utility tool**, and watch the agent route
  between them.
- **Swap in a real vector DB** (Chroma is one `pip install` away) behind the same
  `search_docs` tool — the rest of the graph shouldn't change.

---

## Code

[`code/sample_kb.py`](./code/sample_kb.py) (writes the KB · `ensure_kb()`) ·
[`code/starter.py`](./code/starter.py) (your scaffold, with TODOs) ·
[`code/rag_agent.py`](./code/rag_agent.py) (full reference solution).

```bash
python 07-capstone/code/sample_kb.py     # writes the sample knowledge base
python 07-capstone/code/starter.py       # your scaffold (incomplete until you fill TODOs)
python 07-capstone/code/rag_agent.py     # the full reference, end to end
```

## Reference

[`solutions/solution.md`](./solutions/solution.md) — design notes & how the pieces
fit · [`solutions/DESIGN_example.md`](./solutions/DESIGN_example.md) — a worked
example of the write-up. **Build and write yours first**, then compare.

---

🎓 **Finish this and you've shipped a stateful, tool-using RAG agent** — retrieval
the agent controls, a tool loop that terminates cleanly, and memory across turns.
That's the full arc of this course. Congratulations!

← prev: [Module 06 — Agents with LangGraph](../06-agents-with-langgraph/) ·
[← course home](../README.md)
