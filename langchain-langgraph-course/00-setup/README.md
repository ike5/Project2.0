# Module 00 — Setup & First Call

**Goal:** install the LangChain + LangGraph stack, start your local Ollama server, and make
your first live call to a local model — both batched (`invoke`) and streamed (`stream`).
⏱️ ~30 min.

---

## What is LangChain?

**LangChain** is a toolkit for building apps on top of language models. Instead of
hand-rolling HTTP calls, it gives you small, composable pieces — **chat models**, **prompt
templates**, **output parsers**, **tools**, **retrievers** — that snap together with one
operator (`|`, the pipe) into a **chain** you can `invoke`, `stream`, and `batch` uniformly.
**LangGraph** (later modules) extends this to looping, stateful **agents**. We run a **local
open-weight model (Llama 3.1) with [Ollama](https://ollama.com)** via `langchain-ollama` — no
API key, no cloud — but every concept here is provider-agnostic.

## 1. Install

From the course folder, in a fresh virtual environment (see [VERIFY.md](../VERIFY.md)):

```bash
pip install -r ../requirements.txt    # langchain, langchain-ollama, langgraph, ...
```

Python **3.10+** is required (LangGraph needs it). A laptop CPU is plenty.

## 2. Start Ollama and pull the model

[Install Ollama](https://ollama.com), make sure the server is running, and pull the chat
model this course uses. There is **no API key** — `ChatOllama` talks to the local server at
`http://localhost:11434`.

```bash
ollama serve                 # start the local server (often already running after install)
ollama pull llama3.1         # the chat model (~4.7 GB, one-time download)
ollama list                  # confirm llama3.1 shows up
```

> Short on RAM/disk? Swap `llama3.1` for the smaller `llama3.2` everywhere (just change the
> `model=` argument) — tool-calling in later modules is a bit more reliable on `llama3.1`.

## 3. Your first call

The absolute minimum is three lines — import, construct, invoke:

```python
from langchain_ollama import ChatOllama

model = ChatOllama(model="llama3.1", num_predict=1024)
print(model.invoke("Say hello in one short sentence.").content)
```

`invoke(...)` sends your prompt and returns an **`AIMessage`**; `.content` is the reply text.
A bare string is shorthand for a single user message (you'll use explicit `SystemMessage` /
`HumanMessage` objects in Module 01).

## 4. Two ways to run a model: `invoke` vs `stream`

Every model (and later, every chain and graph) supports the same two calls:

- **`invoke(prompt)`** — run once, wait, get the whole reply back as an `AIMessage`. Simplest.
- **`stream(prompt)`** — get the reply **token by token** as it's generated, so the user sees
  text appear immediately:

```python
for chunk in model.stream("Count to five."):
    print(chunk.content, end="", flush=True)
```

Same model, same prompt — `invoke` is one block at the end, `stream` is a live trickle.

---

## Do the lab 👉 [lab.md](./lab.md)

## Code
- [`code/verify_install.py`](./code/verify_install.py) — versions, Ollama check, one live call
- [`code/hello_ollama.py`](./code/hello_ollama.py) — invoke (with token usage) + streaming

## Key terms
LangChain · LangGraph · Ollama · `ChatOllama` · `invoke` · `stream` ·
`AIMessage` · `.content` · `.usage_metadata` · tokens

**Next →** [Module 01: Chat Models & Messages](../01-chat-models-messages/)
