# DESIGN.md — Stateful RAG Agent (worked example)

> A *worked example* of the design note the capstone asks you to write, so you can
> calibrate yours. Yours should describe **your** build in your own words — what
> matters is that each answer is specific and matches code you actually wrote.
> **Write yours before reading this.**

**Author:** course reference · **Project:** Lumen Mug support agent

---

## 1. When does the agent retrieve vs. answer directly?

The agent calls `search_docs` only for **product questions about the Lumen Mug**.
Two things drive that: the tool's docstring ("Search the Lumen Mug product
manual… use this whenever the user asks about the product — battery, charging,
temperature, cleaning, warranty") and the system prompt ("When the user asks about
the product, call search_docs and answer ONLY from what it returns").

- **Retrieves:** *"How long does the mug hold its temperature?"* → the model emits
  `search_docs(query="Lumen Mug temperature hold time")`, gets the *Battery and
  charging* passage, and answers "about six hours."
- **Answers directly:** *"What's 7 × 3?"* → no manual needed; it calls `multiply`
  (a utility tool), not `search_docs`. *"Hi!"* → it just replies, no tools at all.

So retrieval is **opt-in per turn**, decided by the model from the question — not a
fixed step on every message.

## 2. How does the loop terminate?

The graph is `START → agent →(tools_condition)→ {tools | END}`, with
`tools → agent`. `tools_condition` looks at the last `AIMessage`:

- **A turn that calls a tool** — *"What's the warranty?"*: `agent` returns an
  `AIMessage` *with* a `search_docs` tool call → `tools_condition` routes to
  `tools` → `ToolNode` runs it and appends a `ToolMessage` → back to `agent` →
  this time the model returns a plain answer (no tool calls) → `tools_condition`
  routes to **`END`**.
- **A turn that doesn't** — *"Thanks!"*: `agent` returns an answer with **no**
  tool calls → `tools_condition` goes straight to **`END`**.

It terminates because the model eventually stops requesting tools; a recursion
limit would backstop a pathological loop.

## 3. Swapping `InMemoryVectorStore` for a real vector DB

Only `build_retriever()` changes. To move to **Chroma**, for example, I'd replace
`InMemoryVectorStore.from_documents(chunks, embeddings)` with a persisted Chroma
collection (`Chroma.from_documents(chunks, embeddings, persist_directory=…)`),
index **once** instead of re-embedding on every start, and keep the same
`.as_retriever(search_kwargs={"k": 3})` call. Crucially, **`search_docs` and the
whole graph are untouched** — they only ever see a retriever with `.invoke()`. The
same embedding model carries over (or I'd switch to a hosted embeddings endpoint
for scale).

## 4. What a `thread_id` buys me, and persisting memory

The `thread_id` scopes the saved conversation: every call with the same id loads
that thread's prior `messages` first, so the agent can resolve "it"/"the second
one" and recall earlier answers; a different id is a fresh conversation (my demo's
Session B proves it forgets Session A). Right now I use `InMemorySaver`, which lives
in RAM and is lost on restart. To persist across restarts and multiple workers I'd
compile with a `SqliteSaver` (single box) or `PostgresSaver` (shared) — same
checkpointer interface, no other code changes.

## 5. One limitation and how I'd fix it

The agent answers from a single small manual and doesn't **cite** where a fact came
from, so a user can't verify it and I can't easily catch a hallucination. Fix:
return source labels from `search_docs` (prefix each chunk with its section
heading / id) and instruct the agent to cite them — turning "about six hours" into
"about six hours (*Battery and charging*)." A close second limitation is that the
in-RAM index is rebuilt on every process start; the §3 vector-DB swap addresses
that.
