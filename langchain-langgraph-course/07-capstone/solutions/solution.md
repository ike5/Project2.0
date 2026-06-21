# Capstone — Design Notes (reference)

How the reference solution ([`../code/rag_agent.py`](../code/rag_agent.py)) is put
together, and the *why* behind each choice. Read after you've built your own.

---

## 1. Why retrieval-as-a-tool (the agent decides)

The Module-04 RAG chain *always* retrieves: every question, retrieve-then-answer.
That's perfect for a pure Q&A box, but wasteful and wrong for a chatbot — "Hi!",
"thanks", "what's 7×3?", and "summarise what we discussed" don't need a vector
search, and a fixed retrieve step pollutes the prompt with irrelevant chunks.

By exposing retrieval as a **tool** (`search_docs`) bound to the model, the *agent*
chooses per turn. The model reads the tool's **docstring** ("Search the Lumen Mug
product manual… use this whenever the user asks about the product") and the
**system prompt**, and emits a `search_docs` tool call only when the question is
about the product. This is the one idea that unifies the course: RAG (04) becomes
just another tool inside the agent loop (06), and memory rides along for free.

A bonus: because retrieval is a tool, the agent can **reformulate** the query
(turning "and how long to charge it?" into `search_docs(query="Lumen Mug charging
time")`) and can retrieve **more than once** in a single turn if the first results
fall short — both impossible with a fixed pre-retrieval step.

## 2. How the loop terminates

The graph is `START → agent →(tools_condition)→ {tools | END}` with
`tools → agent`. `tools_condition` inspects the last `AIMessage`:

- **It has `tool_calls`** → route to `tools`. The `ToolNode` runs each requested
  tool, appends `ToolMessage`s, and edges back to `agent`. The model now sees the
  tool results and usually produces a final, tool-call-free answer.
- **It has no `tool_calls`** → route to `END`. Done.

So a turn that needs the manual is: `agent` (asks for `search_docs`) → `tools`
(runs it) → `agent` (answers, no tool calls) → `END`. A turn like "hi" is just
`agent` (answers) → `END`. The loop is guaranteed to terminate because the model
eventually stops requesting tools — and you can cap it with a recursion limit if a
buggy prompt loops.

## 3. Memory & threads

`compile(checkpointer=InMemorySaver())` plus `config={"configurable":{"thread_id":
…}}` makes the graph save the full `messages` list **per thread** after every node.
On the next `invoke` with the same `thread_id`, the saved history is loaded first,
so `add_messages` appends the new turn onto the old ones — the model sees the whole
conversation and can resolve "it"/"that"/"the second one". A *different*
`thread_id` is a clean slate (demonstrated by Session B forgetting Session A).

`InMemorySaver` is in-RAM: restart the process and memory is gone. For persistence,
swap it for a DB-backed saver (`langgraph.checkpoint.sqlite.SqliteSaver` or
`langgraph.checkpoint.postgres.PostgresSaver`) — same interface, the rest of the
graph is unchanged.

## 4. Returning sources (stretch)

Have `search_docs` return each chunk with a label, e.g. prefix the section heading
or a `[chunk 3]` id, and tell the agent (in the system prompt) to cite it. Then a
grounded answer becomes "…about six hours (*Battery and charging*)." Add metadata
at split time and surface `doc.metadata` in the joined string. This turns the agent
from "trust me" into "here's where I got it" — a big credibility win and a cheap
way to spot hallucination.

## 5. Productionising

- **Real vector DB.** Replace `InMemoryVectorStore` with Chroma / pgvector /
  Pinecone — same `Embeddings` object, same `.as_retriever()` call, so *only*
  `build_retriever()` changes. The `search_docs` tool and the graph don't move.
  Index once and persist, rather than re-embedding on every process start.
- **Persistent checkpointer.** `SqliteSaver`/`PostgresSaver` so conversations
  survive restarts and scale across workers.
- **Evaluation.** Build a small set of (question → expected fact) pairs and assert
  the agent's answers contain them; track retrieval hit-rate (did the right chunk
  come back?) separately from answer quality. LangSmith makes tracing + eval easy,
  but a plain pytest over canned questions is a fine start.
- **Guardrails.** A system prompt that says "answer ONLY from `search_docs`
  results; if not covered, say so" curbs hallucination; add input/output checks
  and a recursion/timeout cap for safety.

## 6. Model answers for the DESIGN.md questions

See [`DESIGN_example.md`](./DESIGN_example.md) for a fully worked write-up. In
brief:

1. **Retrieve vs. answer directly** — product questions trigger `search_docs`
   (driven by the tool docstring + system prompt); greetings, arithmetic, and
   meta questions ("what did we discuss?") are answered directly or via `multiply`.
2. **Termination** — `tools_condition`: tool calls → `tools → agent`; none → `END`
   (§2 above).
3. **Swap the vector store** — change only `build_retriever()`; the tool and graph
   are untouched (§5).
4. **Threads & persistence** — `thread_id` scopes memory; swap `InMemorySaver` for a
   SQLite/Postgres saver to survive restarts (§3).
5. **A limitation** — single small KB, in-RAM index rebuilt each start, no source
   citations by default; fixes in §4–§5.

---

**Takeaway:** the whole capstone is one move — *make retrieval a tool* — and the
agent loop, memory, and tools from Modules 04–06 click into place around it.
