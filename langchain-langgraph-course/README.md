# Building LLM Apps with LangChain & LangGraph (Local, with Ollama) 🦜🕸️🦙

A hands-on course that takes you from your **first model call** to a **stateful, tool-using
agent** — running **100% locally on your own machine with [Ollama](https://ollama.com)**, no
API keys, no cloud, no per-token bill. You build up through prompts, chains (LCEL),
structured output, tool calling, retrieval-augmented generation (RAG), and finally
**LangGraph**, where you wire an agent as an explicit graph of state, nodes, and edges and
*watch it loop*.

> **Who this is for:** You can write basic Python (functions, dicts, type hints) and you've
> used a terminal. No prior LangChain, no ML background, no GPU required. We build the mental
> model for *messages → chains → graphs* from scratch, one runnable script at a time.

> **Up to date for 2026:** built on **LangChain 1.x**, **langchain-ollama 1.1+**, and the
> current **LangGraph**. Agents use the modern `langchain.agents.create_agent` harness, and
> everything talks to a local Ollama server.

---

## Why LangChain (and why LangGraph) — and why local

A modern LLM app is mostly the same handful of moves repeated: **format a prompt, call a
model, parse what comes back, maybe call a tool, maybe loop.** The hard part for beginners
is that these moves get tangled together in glue code that's impossible to test or reuse.

- **LangChain** gives you small, composable pieces — **chat models**, **prompt templates**,
  **output parsers**, **tools**, **retrievers** — and one operator (`|`, the *pipe*) to snap
  them together into a **chain** you can `invoke`, `stream`, and `batch` uniformly.
- **LangGraph** is for when a straight line isn't enough. Agents *loop*: think → act →
  observe → think again. LangGraph makes that loop an explicit **graph** with typed
  **state**, so you can add memory, branch on conditions, pause for a human, and resume.
- **Ollama** runs open-weight models (Llama 3.1/3.2, and more) **on your laptop**. You
  `ollama pull` a model once and every example in this course runs offline, free, and
  private. Swap the one `ChatOllama(model="…")` line for any model you've pulled.

```
   LangChain (a chain = a straight line)        LangGraph (a graph = loops & branches)
 ┌───────────────────────────────────┐        ┌──────────────────────────────────────┐
 │ prompt | model | parser           │        │   ┌─────┐  tool calls?  ┌────────┐    │
 │   →  one pass, input to output    │        │   │agent│ ───yes──────▶ │ tools  │    │
 └───────────────────────────────────┘        │   └─────┘ ◀──results──── └────────┘    │
                                              │      │ no                              │
        all running on  🦙 localhost:11434     │      ▼  END                            │
                                              └──────────────────────────────────────┘
```

Every concept — messages, LCEL, tools, graphs — is provider-agnostic. We use Ollama so it's
free and local; the same code runs against any chat model by changing one line.

---

## What makes it effective

- **Learn by doing.** Every module = concepts + a guided lab you run + an unguided
  challenge + reference solutions.
- **Every script runs — locally.** No notebooks required, no keys to manage. Each example is
  a plain `python script.py` that hits your local Ollama and prints something you can read.
- **Build up real skill.** You go from one model call → a templated chain → structured JSON
  out of the model → a model that calls your Python functions → a RAG pipeline over your own
  docs → a LangGraph state machine → a looping agent → a capstone that ties it together.
- **A capstone.** Ship a stateful RAG **agent** with persistent memory built in LangGraph,
  plus a short design write-up you do yourself.

---

## Prerequisites

- **Python 3.10+** and `pip` (LangGraph needs 3.10+). A laptop is plenty — a Mac (Apple
  Silicon), Linux, or Windows all work.
- **[Ollama](https://ollama.com) installed and running.** Download it, then pull the two
  models this course uses:
  ```bash
  ollama pull llama3.1            # the chat model (good tool-calling; ~4.7 GB)
  ollama pull nomic-embed-text    # the embedding model for RAG (Module 04)
  ```
  Ollama serves on `http://localhost:11434` by default — no key, no signup. (On a tighter
  machine you can swap `llama3.1` for the smaller `llama3.2`; quality on the tool/agent
  modules is a bit lower.)
- Comfort running commands in a terminal and reading printed output.
- ~6 GB free disk for the two models above.

Versions: **LangChain 1.x**, **LangGraph (current)**, **langchain-ollama 1.1+**. Embeddings
in the RAG module run **locally through Ollama** (`nomic-embed-text`) — still no second
service.

---

## The learning path

| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 00 | [Setup & First Call](./00-setup/) | Install the stack; start Ollama; call a local model and stream a reply | 0.5 h |
| 01 | [Chat Models & Messages](./01-chat-models-messages/) | `HumanMessage`/`SystemMessage`/`AIMessage`; `invoke`/`stream`/`batch` | 2 h |
| 02 | [Prompts & LCEL](./02-prompts-and-lcel/) | `ChatPromptTemplate`; the `|` pipe; output parsers; build a chain | 2.5 h |
| 03 | [Structured Output & Tools](./03-structured-output-and-tools/) | `with_structured_output`; the `@tool` decorator; `bind_tools` | 3 h |
| 04 | [RAG: Retrieval](./04-rag-retrieval/) | Load → split → embed → store → retrieve; a grounded Q&A chain | 3 h |
| 05 | [LangGraph Fundamentals](./05-langgraph-fundamentals/) | `StateGraph`, state, nodes, edges, `compile`; run your first graph | 3 h |
| 06 | [Agents with LangGraph](./06-agents-with-langgraph/) | The tool-calling loop; `ToolNode`; memory; `create_agent` | 3.5 h |
| 07 | [Capstone: RAG Agent](./07-capstone/) | Ship a stateful RAG agent with persistence + a design write-up | 3+ h |

**Total: a realistic ~20 hours.**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts. Read first.
├── lab.md         ← Step-by-step guided lab with expected output. Do second.
├── code/          ← Runnable .py scripts the lab uses.
├── challenge.md   ← An unguided task. Do third.
└── solutions/     ← Reference answers — peek only after trying.
```

Every code script is a plain `python script.py` — no notebooks required (though they work
fine in one if you prefer).

---

## Reference material

- **[cheatsheets/langchain.md](./cheatsheets/langchain.md)** — messages, prompts, LCEL, tools, RAG
- **[cheatsheets/langgraph.md](./cheatsheets/langgraph.md)** — `StateGraph`, edges, `ToolNode`, checkpoints, `create_agent`
- **[GLOSSARY.md](./GLOSSARY.md)** — every term in plain English
- **[VERIFY.md](./VERIFY.md)** — confirm your install + Ollama work before Module 01
- **[requirements.txt](./requirements.txt)** — exact packages to `pip install`

## Quick start

```bash
cd langchain-langgraph-course
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# In another terminal (or as a background service), make sure Ollama is running:
ollama serve            # usually already running after install
ollama pull llama3.1
ollama pull nomic-embed-text

python 00-setup/code/verify_install.py              # prints versions + a live local reply
```

Ready? **→ [Start with Module 00: Setup & First Call](./00-setup/)**
