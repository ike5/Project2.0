# Module 02 — Prompts & LCEL

**Goal:** stop hardcoding strings and start *templating* prompts; turn raw `AIMessage`
replies into the data you actually want with **output parsers**; and learn the one operator
that ties LangChain together — the pipe `|` (**LCEL**, the LangChain Expression Language).
By the end you'll build, stream, batch, and compose multi-step chains. ⏱️ ~2.5 h · 🎯 Prereq: 01.

---

## 0. Why not just f-strings?

In Module 01 you called the model with hand-built messages. The instinct is to reach for an
f-string:

```python
text, language = "good morning", "French"
model.invoke(f"Translate this to {language}: {text}")   # works... until it doesn't
```

This rots fast. The system instructions, the variables, and the call all get tangled in glue
code you can't reuse or test. The fix is to separate the **shape** of the prompt (a reusable
template) from the **values** you fill it with at call time — and then to make that template a
first-class, composable object. That object is a `ChatPromptTemplate`.

## 1. Prompt templates

A `ChatPromptTemplate` is a list of message *roles* with `{placeholders}`. You `.invoke()` it
with a dict; it returns a **PromptValue** (a bundle of real messages) — *no model called yet*.

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You translate English to {language}. Reply with only the translation."),
    ("human", "{text}"),
])

pv = prompt.invoke({"language": "French", "text": "good morning"})
pv.to_messages()
# [SystemMessage("You translate English to French. ..."),
#  HumanMessage("good morning")]
```

The template is reusable: same `prompt`, different dicts. Variables are inferred from the
`{...}` names — `prompt.input_variables` lists them.

### History with `MessagesPlaceholder`

Some of your messages aren't a single string — they're a *running list* (chat history). Drop
in a `MessagesPlaceholder` and fill it with a list of messages:

```python
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])
chat_prompt.invoke({
    "history": [HumanMessage("I'm Ada."), AIMessage("Nice to meet you, Ada!")],
    "input": "What's my name?",
})
```

## 2. Output parsers

`model.invoke(...)` returns an `AIMessage`, but downstream you usually want the *text* (or a
dict, or a Pydantic object). An **output parser** is a small Runnable that transforms the
model's output. The simplest is `StrOutputParser` — `AIMessage → str`:

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
parser.invoke(model.invoke("Say hi"))     # -> "Hi!" (a plain str, not an AIMessage)
```

## 3. The pipe `|` — LCEL

Here's the payoff. Each piece — prompt, model, parser — is a **Runnable**, and the pipe `|`
snaps them into a **chain** where the **output of each step feeds the next**:

```python
chain = prompt | model | StrOutputParser()
chain.invoke({"language": "French", "text": "good morning"})    # -> "bonjour"
```

Read the data flow left to right:

```
{"language","text"}  ──▶  prompt  ──▶  PromptValue  ──▶  model  ──▶  AIMessage  ──▶  parser  ──▶  "bonjour"
       dict in                          messages                    a reply               str out
```

The chain takes a **dict** (what the prompt needs) and returns a **str** (what the parser
produces). Crucially, **the chain is itself a Runnable** — so it has the exact same three
methods every Runnable has.

> Visualize any chain's wiring with `chain.get_graph().print_ascii()`.

## 4. Streaming & batching — for free

Because a chain is a Runnable, it gets `invoke` / `stream` / `batch` automatically — the same
trio you met on the bare model in Module 01. You don't write any extra code:

```python
chain.invoke({"language": "French", "text": "hello"})           # -> one string

for piece in chain.stream({"language": "French", "text": "hello"}):
    print(piece, end="", flush=True)                            # -> string, piece by piece

chain.batch([                                                   # -> list of strings, concurrent
    {"language": "French",  "text": "hello"},
    {"language": "Spanish", "text": "hello"},
    {"language": "German",  "text": "hello"},
])
```

This uniformity is the whole point of LCEL: build a complex thing out of small Runnables, and
the complex thing *is* a Runnable too.

## 5. Composing steps & parallel branches

Real apps chain *multiple* model calls and reshape data between them. Three helpers do the
plumbing:

- **`RunnableLambda(fn)`** — wrap any plain Python function so it fits in the pipe.
- **`RunnablePassthrough()`** — pass the input through unchanged (handy for keeping the
  original alongside a computed value).
- **`RunnableParallel(a=..., b=...)`** — run several Runnables on the *same* input and return
  a **dict** `{"a": ..., "b": ...}`.

**Two-step chain** — the output of step 1 becomes the input of step 2:

```python
from langchain_core.runnables import RunnableLambda

idea_chain  = idea_prompt  | model | StrOutputParser()   # topic -> a story idea (str)
pitch_chain = pitch_prompt | model | StrOutputParser()   # an idea -> a one-line pitch (str)

# pitch_prompt expects {"idea": ...}, so wrap the str into that dict between stages:
story = idea_chain | RunnableLambda(lambda idea: {"idea": idea}) | pitch_chain
story.invoke({"topic": "a lighthouse keeper"})           # -> a one-line pitch
```

**Fan-out** — run branches in parallel, get a dict back:

```python
from langchain_core.runnables import RunnableParallel

both = RunnableParallel(idea=idea_chain, pitch=story)
both.invoke({"topic": "a lighthouse keeper"})
# {"idea": "...", "pitch": "..."}   <- both branches, one call
```

A plain dict literal in a pipe is shorthand for `RunnableParallel` — that's the pattern you'll
see everywhere (including the RAG chain in Module 04):

```python
{"answer": chain, "original": RunnablePassthrough()}     # == RunnableParallel(...)
```

---

## Do the lab
Run the three scripts, then build chains in the REPL — predict what `RunnableParallel`
returns, and watch the output type change when you remove the parser.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/prompt_template.py`](./code/prompt_template.py) — a template → PromptValue → messages
- [`code/first_chain.py`](./code/first_chain.py) — `prompt | model | parser`; invoke/stream/batch + ASCII graph
- [`code/composed_chain.py`](./code/composed_chain.py) — two-step chain + `RunnableParallel`

## Key terms
`ChatPromptTemplate` · placeholder / `input_variables` · `MessagesPlaceholder` · PromptValue ·
output parser / `StrOutputParser` · Runnable · LCEL · the pipe `|` · `invoke`/`stream`/`batch` ·
`RunnableLambda` · `RunnablePassthrough` · `RunnableParallel` (dict-in / dict-out) ·
`get_graph().print_ascii()`

**Next →** [Module 03: Structured Output & Tools](../03-structured-output-and-tools/)
