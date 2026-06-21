# Module 04 — RAG: Retrieval

**Goal:** give the model knowledge it doesn't have. A chat model only knows what it
saw in training — it has a **knowledge cutoff**, has never read your private docs, and
will sometimes confidently make things up. **Retrieval-Augmented Generation (RAG)** fixes
this: before answering, you *fetch the relevant text* from your own documents and hand it
to the model as context. You'll build the five-stage pipeline — **load → split → embed →
store → retrieve** — then wire a **grounded Q&A chain** that answers *only* from what it
retrieved, and watch it correctly say "I don't know" when the answer isn't there.
⏱️ ~3 h · 🎯 Prereq: 03.

```python
# The whole idea in one line: fetch relevant text, then answer from it.
retriever.invoke("How long does the battery last?")   # -> the chunks that mention battery
rag.invoke("How long does the battery last?")          # -> grounded answer from those chunks
```

---

## 1. The problem RAG solves

A chat model is a snapshot. Three gaps follow from that:

- **Knowledge cutoff.** It was trained up to some date and knows nothing after it.
- **Private / local docs.** It never saw your handbook, your wiki, your product notes.
- **Hallucination.** Asked something it doesn't know, it often *guesses fluently* — a
  wrong answer that reads like a right one.

You can't retrain the model for every question. RAG sidesteps all three: keep the model
as-is, and at question time **retrieve the relevant passages from your documents and put
them in the prompt.** The model then answers from text in front of it instead of from
memory. Fresh facts, your private data, and far less making-things-up — because the
answer is *grounded* in retrieved evidence.

> RAG is "open-book exam" for an LLM. The model is smart but forgetful; you hand it the
> right page before it answers.

## 2. The pipeline: load → split → embed → store → retrieve

RAG has two halves. The **indexing** half runs once to prepare your documents; the
**retrieval + generation** half runs per question.

```
  INDEX ONCE                                        ANSWER PER QUESTION
  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    ┌──────────┐  ┌────────┐
  │  LOAD  │─▶│ SPLIT  │─▶│ EMBED  │─▶│ STORE  │    │ RETRIEVE │─▶│  LLM   │
  │ a file │  │ chunks │  │vectors │  │ vector │    │ k closest│  │grounded│
  │        │  │        │  │(local) │  │ store  │◀───│  chunks  │  │ answer │
  └────────┘  └────────┘  └────────┘  └────────┘    └──────────┘  └────────┘
                                          ▲              │
                                          └── query embedded, compared ──┘
```

1. **Load** — read your source into LangChain `Document`s. A `TextLoader` gives you a
   `list[Document]`, each with `.page_content` (the text) and `.metadata`.
   ```python
   from langchain_community.document_loaders import TextLoader
   docs = TextLoader("notes.txt").load()       # -> list[Document]
   ```
2. **Split** — a whole document is too big to retrieve usefully, so cut it into **chunks**.
   `RecursiveCharacterTextSplitter` breaks on paragraphs/sentences and keeps a small
   **overlap** so a fact isn't sliced in half at a boundary.
   ```python
   from langchain_text_splitters import RecursiveCharacterTextSplitter
   chunks = RecursiveCharacterTextSplitter(
       chunk_size=300, chunk_overlap=50
   ).split_documents(docs)
   ```
   - **`chunk_size`** — target characters per chunk. Smaller = more, tighter pieces.
   - **`chunk_overlap`** — characters repeated between neighbors, so context that spans a
     boundary isn't lost.
3. **Embed → 4. Store → 5. Retrieve** — covered next.

## 3. Embeddings & vector stores, in plain English

An **embedding** turns a piece of text into a **vector** — a list of numbers that captures
its *meaning*. The model that does this is trained so that **texts with similar meaning land
near each other** in that number-space, and unrelated texts land far apart. "How long does
the battery last?" and "The battery lasts about 18 hours" end up close — even though they
share almost no words — because they *mean* similar things. That's **semantic search**:
matching on meaning, not keywords.

We use a small **local** embedding model so this runs offline with **no second API key**.
The first run downloads ~100MB once; after that it's on your machine.

```python
from langchain_ollama import OllamaEmbeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")
```

A **vector store** holds every chunk's vector and can answer "which stored vectors are
*nearest* to this new one?" fast. `InMemoryVectorStore` keeps them in RAM — perfect for
learning; production swaps in Chroma, FAISS, pgvector, etc., with the same interface.

```python
from langchain_core.vectorstores import InMemoryVectorStore
store = InMemoryVectorStore.from_documents(chunks, embeddings)   # embeds + stores all chunks
```

> **Only embeddings are local; only the final answer step calls the API.** Loading,
> splitting, embedding, storing, and retrieving all run on your machine for free. The
> The model call happens *once*, at the very end, to write the answer.

## 4. The retriever — fetch the k closest chunks

Wrap the store as a **retriever**: give it a query, get back the most relevant chunks. It
embeds your query with the *same* model, finds the nearest stored vectors, and returns
those chunks as `Document`s.

```python
retriever = store.as_retriever(search_kwargs={"k": 3})
retriever.invoke("How long does the battery last?")    # -> the 3 closest chunks (list[Document])
```

**`k`** is how many chunks to return. Too small and you might miss the answer; too large
and you flood the prompt with noise (and tokens). `k=3` is a sane default for small docs.
Run [`code/build_index.py`](./code/build_index.py) to *see* this — it prints the retrieved
chunks for a few queries **before any LLM is involved**, so you can confirm retrieval works
on its own.

## 5. The grounded chain — stuff context into the prompt

Now connect retrieval to generation with LCEL. The prompt has two slots: **`{context}`**
(the retrieved chunks) and **`{question}`** (what the user asked). A tiny helper flattens
the retrieved `Document`s into one string:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using ONLY the context below. If the answer is not in the "
               "context, say you don't know.\n\nContext:\n{context}"),
    ("human", "{question}"),
])
def format_docs(docs): return "\n\n".join(d.page_content for d in docs)

model = ChatOllama(model="llama3.1", num_predict=1024)

rag = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | model | StrOutputParser()
)
rag.invoke("What does the warranty cover?")     # -> a grounded answer string
```

Read the dict at the front carefully — it builds the prompt's inputs **in parallel** from
the *same* incoming question:

- **`"context": retriever | format_docs`** — the question goes to the retriever, whose
  chunks are flattened into the `{context}` string.
- **`"question": RunnablePassthrough()`** — the same question is passed straight through to
  fill `{question}`.

Then `prompt | model | StrOutputParser()` formats, calls the local model, and returns plain text —
the same LCEL pipe you've used since Module 02.

## 6. Why "answer ONLY from context" matters

That instruction in the system prompt is what makes the answer **grounded**. It tells the
model: *use the retrieved text, and if the answer isn't there, say so* — instead of falling
back on its training-memory or inventing something. The payoff is visible in
[`code/rag_chain.py`](./code/rag_chain.py): it asks two questions the notes **can** answer
(grounded, correct) and one they **cannot** (the price), and the model **declines** rather
than guessing a number.

This is the difference between a demo and something you can trust. Without grounding, a
RAG app will happily hallucinate when retrieval misses. With it, "I don't know" is a
*feature* — an honest miss you can detect, instead of a confident lie. Pair it with the
returned **source chunks** (the challenge) and you get answers a user can actually verify.

---

## Do the lab
Run the scripts and **watch retrieval work before any LLM call**, then see grounded answers
vs an honest refusal. In the REPL you'll change `k` and `chunk_size` and feel the tradeoffs.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/sample_docs.py`](./code/sample_docs.py) — writes the sample `notes.txt`; `ensure_docs()` helper
- [`code/build_index.py`](./code/build_index.py) — load → split → embed → store, then **print retrieved chunks** (no LLM)
- [`code/rag_chain.py`](./code/rag_chain.py) — the full grounded Q&A chain: grounded answers + an honest "I don't know"

## Key terms
RAG · knowledge cutoff · grounding · hallucination · load / split / embed / store / retrieve ·
`TextLoader` · `Document` (`.page_content` / `.metadata`) · `RecursiveCharacterTextSplitter` ·
`chunk_size` / `chunk_overlap` · embedding (vector of meaning) · semantic search ·
`OllamaEmbeddings` (local) · vector store · `InMemoryVectorStore` · retriever · `k` ·
`format_docs` · `{context}` / `{question}` · "answer only from context"

**Next →** [Module 05: LangGraph Fundamentals](../05-langgraph-fundamentals/)
