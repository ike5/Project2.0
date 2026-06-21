# Glossary

Plain-English definitions of the LangChain, LangGraph, and LLM terms in this course.

## Core LLM ideas

- **LLM / chat model** — a model that takes a list of **messages** and returns a new
  message. In this course that's a **local open-weight model** (Llama 3.1) served by
  **Ollama** via `ChatOllama`.
- **Ollama** — a tool that runs open-weight models on your own machine and exposes them at
  `http://localhost:11434`. You `ollama pull <model>` once; no API key, no cloud.
- **Token** — the unit a model reads and writes (roughly ¾ of a word). `num_predict` (Ollama's
  name for "max tokens") caps how many the model may *generate*. Running locally, tokens are
  free — they cost time, not money.
- **Message** — one turn in a conversation, with a **role**. LangChain types:
  `SystemMessage` (instructions), `HumanMessage` (user input), `AIMessage` (model output),
  `ToolMessage` (a tool's result fed back to the model).
- **System prompt** — standing instructions that shape every reply (persona, rules, format).
  Sent as a `SystemMessage`.
- **Temperature** — a knob for randomness. Lower = more focused/repeatable. (Some newer
  models ignore it; default behavior is fine for this course.)
- **Streaming** — receiving the reply token-by-token as it's generated, instead of waiting
  for the whole thing. Better UX for long answers.
- **Context window** — the maximum tokens a model can consider at once (prompt + reply).

## LangChain building blocks

- **`ChatOllama`** — LangChain's wrapper around an Ollama-served chat model.
  `model="llama3.1"`. Exposes `.invoke()`, `.stream()`, `.batch()`.
- **`invoke` / `stream` / `batch`** — the three ways to run *anything* runnable: once
  (`invoke`), token-by-token (`stream`), or many inputs at once (`batch`).
- **Runnable** — LangChain's universal interface. Models, prompts, parsers, and whole chains
  are all Runnables, so they share the same `invoke`/`stream`/`batch` methods.
- **LCEL (LangChain Expression Language)** — composing Runnables with the `|` (pipe)
  operator: `prompt | model | parser`. Output of the left feeds the right.
- **Prompt template** — a reusable, parameterized prompt. `ChatPromptTemplate.from_messages([...])`
  with `{placeholders}` you fill at call time.
- **Output parser** — turns the model's `AIMessage` into something usable:
  `StrOutputParser` (→ plain string), structured parsers (→ objects).
- **Structured output** — making the model return data matching a schema (a Pydantic model)
  instead of free text, via `model.with_structured_output(Schema)`.
- **Tool** — a Python function the model can *call*. Define with the `@tool` decorator;
  attach with `model.bind_tools([...])`. The model emits a **tool call**; your code runs the
  function and feeds the result back.
- **Tool call** — the model's request to run a tool: a name + arguments. Found on
  `AIMessage.tool_calls`.

## Retrieval-augmented generation (RAG)

- **RAG** — giving the model relevant text *retrieved from your own documents* so it answers
  from facts instead of memory. Retrieve → stuff into the prompt → generate.
- **Document loader** — reads a source (text file, web page, PDF) into LangChain `Document`
  objects (text + metadata).
- **Text splitter** — chops long documents into **chunks** small enough to embed and
  retrieve. `RecursiveCharacterTextSplitter` is the default.
- **Embedding** — a vector (list of numbers) representing a chunk's *meaning*. Similar
  meanings → nearby vectors. This course embeds **locally through Ollama** with
  `OllamaEmbeddings(model="nomic-embed-text")`.
- **Vector store** — a database of embeddings you can search by similarity.
  `InMemoryVectorStore` keeps them in RAM (no external DB needed).
- **Retriever** — the thing you `.invoke(query)` to get back the most relevant chunks.
- **Grounding** — answering *only* from retrieved context, reducing made-up facts.

## LangGraph

- **Graph / `StateGraph`** — a workflow defined as **nodes** connected by **edges**, sharing
  a single **state** object. The replacement for a straight-line chain when you need loops or
  branches.
- **State** — the data passed between nodes, defined as a `TypedDict`. Each node receives the
  state and returns updates to it.
- **Reducer** — a rule for how a state update *merges* with the existing value.
  `add_messages` (from `langgraph.graph.message`) appends new messages instead of replacing
  the list — the key reducer for chat state.
- **Node** — a Python function (or a Runnable) that takes the state and returns a partial
  state update. The unit of work in a graph.
- **Edge** — a connection from one node to the next. A **normal edge** always goes A→B; a
  **conditional edge** picks the next node by running a function on the state.
- **`START` / `END`** — sentinel nodes marking where the graph begins and finishes.
- **`compile()`** — turns a `StateGraph` builder into a runnable graph (itself a Runnable, so
  it has `invoke`/`stream`).
- **`ToolNode`** — a prebuilt node that executes whatever tools the last `AIMessage` asked
  for and appends the `ToolMessage` results.
- **`tools_condition`** — a prebuilt conditional-edge function: route to the tool node if the
  model made a tool call, else to `END`.
- **The agent loop** — agent node calls the model → if it requested tools, go to the tool
  node → feed results back → agent node again → repeat until no tool call → `END`.
- **Checkpointer** — what gives a graph **memory**. `InMemorySaver` (in RAM) or a database
  saves state per **thread**, so a conversation persists across `invoke` calls. (`MemorySaver`
  is the older alias for `InMemorySaver`.)
- **Thread / `thread_id`** — the conversation key. Pass it in `config={"configurable":
  {"thread_id": "..."}}` so the checkpointer knows which history to load.
- **`create_agent`** — LangChain 1.x's prebuilt agent harness (model + tools + loop + memory)
  you get in one line — `from langchain.agents import create_agent` — for when you don't need
  to wire the graph by hand. (It supersedes the older `langgraph.prebuilt.create_react_agent`.)

## Tooling & ops

- **Ollama server** — the local process (`ollama serve`, on `http://localhost:11434`) that
  hosts your models. `ChatOllama`/`OllamaEmbeddings` talk to it; no API key is involved. Pull
  models with `ollama pull <name>`.
- **LangSmith** — LangChain's tracing/observability UI. Optional; set `LANGSMITH_TRACING=true`
  to see every step of a chain or graph.
