# Lab 04 — RAG: Retrieval

**You'll:** build a tiny index and **watch retrieval work before any LLM call**, then see a
grounded answer vs an honest "I don't know," then feel the `k` and `chunk_size` tradeoffs in
the REPL. ⏱️ ~70 min. From the `langchain-langgraph-course` folder. (Parts A–B need no API
all local for embeddings; Part C needs your Ollama server running.)

> First run downloads the ~100MB local embedding model once. After that it's offline.

---

## Part A — Make the docs, then SEE retrieval

```bash
python 04-rag-retrieval/code/sample_docs.py
python 04-rag-retrieval/code/build_index.py
```
The first command writes `code/notes.txt` (eight facts about a fictional lamp). The second
splits it, embeds it **locally**, and prints the top-3 chunks for three queries — *no model
call yet*.

✅ **Predict, then check.** Before reading the output for `"What does the warranty cover?"`,
say which fact should come back. The chunk mentioning the **two-year warranty** should be
`[1]` — even though your query never used the word "two-year." That's semantic search:
matching on meaning, not keywords.

## Part B — Change `k` in the REPL

Retrieval is just `retriever.invoke(query)`. Watch `k` change *how many* chunks come back:
```python
>>> import sys; sys.path.insert(0, "04-rag-retrieval/code")
>>> from build_index import build_retriever
>>> r1, _ = build_retriever(k=1)
>>> r3, _ = build_retriever(k=3)
>>> len(r1.invoke("how do I reset the lamp?"))     # 1
>>> len(r3.invoke("how do I reset the lamp?"))     # 3
>>> for d in r1.invoke("how do I reset the lamp?"):
...     print(d.page_content[:70])
```
✅ `k` controls how many chunks you retrieve. With `k=1` you get only the single closest
chunk; with `k=3` you also pull two neighbors. Too small risks **missing** the answer; too
large floods the prompt with **noise** (and tokens).

## Part C — Grounded answer vs honest refusal

```bash
python 04-rag-retrieval/code/rag_chain.py
```
✅ The two **answerable** questions (battery life, warranty) come back **grounded** — the
facts match `notes.txt`. The **unanswerable** one (the price) makes the model say it
**doesn't know** instead of inventing a number. The price simply isn't in the notes.

Now prove grounding is doing the work. Ask the *same* unanswerable question with and without
the "only from context" instruction:
```python
>>> import sys; sys.path.insert(0, "04-rag-retrieval/code")
>>> from rag_chain import build_rag
>>> rag = build_rag()
>>> print(rag.invoke("How much does the Lumina lamp cost?"))   # declines — not in context
>>> from langchain_ollama import ChatOllama
>>> plain = ChatOllama(model="llama3.1", num_predict=1024)
>>> print(plain.invoke("How much does the Lumina lamp cost?").content)  # may GUESS a price
```
✅ The grounded chain declines; the bare model (no context, no instruction) is liable to
**make a price up**. The system prompt's "answer ONLY from this context" is what buys you the
honest miss.

## Part D — Change `chunk_size` and watch chunk count

```python
>>> from build_index import build_retriever
>>> _, big   = build_retriever(chunk_size=500)
>>> _, small = build_retriever(chunk_size=80)
>>> len(big), len(small)        # few big chunks vs many small ones
>>> small_r, _ = build_retriever(chunk_size=80, k=3)
>>> for d in small_r.invoke("how long to charge the battery?"):
...     print(repr(d.page_content[:60]))
```
✅ Smaller `chunk_size` → **more, tighter** chunks; larger → **fewer, broader** ones. Tiny
chunks can split one fact across two pieces (you may see the "2.5 hours" and the sentence it
belongs to land in different chunks); big chunks keep facts whole but dilute the match with
unrelated sentences.

## Part E — Stretch: add a second source doc

Index a second fact file alongside the first and confirm retrieval reaches into both:
```python
>>> from pathlib import Path
>>> from langchain_community.document_loaders import TextLoader
>>> from langchain_text_splitters import RecursiveCharacterTextSplitter
>>> from langchain_ollama import OllamaEmbeddings
>>> from langchain_core.vectorstores import InMemoryVectorStore
>>> Path("04-rag-retrieval/code/extra.txt").write_text(
...     "The Lumina Pro adds a wireless charging pad in the base and costs $149.")
>>> docs = (TextLoader("04-rag-retrieval/code/notes.txt").load()
...         + TextLoader("04-rag-retrieval/code/extra.txt").load())
>>> chunks = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50).split_documents(docs)
>>> emb = OllamaEmbeddings(model="nomic-embed-text")
>>> store = InMemoryVectorStore.from_documents(chunks, emb)
>>> r = store.as_retriever(search_kwargs={"k": 2})
>>> [d.page_content[:50] for d in r.invoke("Is there wireless charging?")]  # finds the new doc
```
✅ A query about wireless charging now retrieves the **second** file's chunk. Loading more
sources is just more `Document`s into the same splitter and store.

---

✅ **Done when:** you can predict which chunk a query retrieves and confirm it *before* any
LLM call, you've seen a grounded answer next to an honest "I don't know," and you can explain
in one sentence what `k` and `chunk_size` each trade off.

**Next →** [challenge.md](./challenge.md) then
[Module 05: LangGraph Fundamentals](../05-langgraph-fundamentals/)
