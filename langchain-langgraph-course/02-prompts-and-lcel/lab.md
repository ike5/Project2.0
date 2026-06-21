# Lab 02 — Prompts & LCEL

**You'll:** run the three scripts, then build templates and chains yourself in the REPL —
predicting outputs before you check them. ⏱️ ~60 min. From the `langchain-langgraph-course`
folder, with your local Ollama server running.

---

## Part A — Templates produce messages, not text

```bash
python 02-prompts-and-lcel/code/prompt_template.py
```
✅ Notice the script makes **no API call** — a template only *formats* messages. Read each
printed `SystemMessage` / `HumanMessage` and confirm the `{placeholders}` got filled.

Now in the REPL, build one yourself and inspect it:
```python
>>> from langchain_core.prompts import ChatPromptTemplate
>>> p = ChatPromptTemplate.from_messages([
...     ("system", "You are a {style} assistant."),
...     ("human", "{question}"),
... ])
>>> p.input_variables                 # ['style', 'question']  (order may vary)
>>> pv = p.invoke({"style": "terse", "question": "Capital of Japan?"})
>>> pv.to_messages()                  # two messages, placeholders filled
```
✅ You can predict `input_variables` from the `{...}` names before printing them, and you can
explain that `pv` is a **PromptValue** (messages), not a string.

## Part B — The pipe builds a chain

```bash
python 02-prompts-and-lcel/code/first_chain.py
```
✅ Study the `print_ascii()` diagram: input → `PromptTemplate` → `ChatOllama` → parser →
output. Confirm `invoke` returns one string, `stream` prints it in pieces, and `batch`
returns a **list**.

Build the chain yourself and watch the **output type change** when you drop the parser:
```python
>>> from langchain_ollama import ChatOllama
>>> from langchain_core.output_parsers import StrOutputParser
>>> model = ChatOllama(model="llama3.1", num_predict=1024)
>>> chain  = p | model | StrOutputParser()
>>> chain.invoke({"style": "terse", "question": "Capital of Japan?"})   # -> a str
>>> nopars = p | model                         # same chain, NO parser
>>> nopars.invoke({"style": "terse", "question": "Capital of Japan?"})  # -> an AIMessage!
```
✅ You can state the difference: **with** `StrOutputParser` you get a `str`; **without** it you
get an `AIMessage` (and would reach `.content` for the text). The parser is just the last
Runnable in the pipe.

## Part C — Streaming & batching come free

```python
>>> for piece in chain.stream({"style": "chatty", "question": "Describe the ocean."}):
...     print(piece, end="", flush=True)
>>> print()
>>> chain.batch([
...     {"style": "terse", "question": "2+2?"},
...     {"style": "terse", "question": "3+3?"},
... ])
```
✅ You can explain *why* you didn't have to write any streaming/batching code: the chain **is**
a Runnable, so it inherits `invoke`/`stream`/`batch` — the same trio the bare model had in
Module 01.

## Part D — Composing & parallel branches

```bash
python 02-prompts-and-lcel/code/composed_chain.py
```
✅ Trace the two-step flow: topic → **idea** (str) → `RunnableLambda` rewraps it as
`{"idea": ...}` → **pitch** (str). Without that lambda, step 2 would get a bare string and
fail (it expects a dict with key `idea`).

Predict, *then* check, what `RunnableParallel` returns:
```python
>>> from langchain_core.runnables import RunnableParallel, RunnablePassthrough
>>> joke  = (ChatPromptTemplate.from_messages([("human", "Tell a one-line joke about {x}.")])
...          | model | StrOutputParser())
>>> fan = RunnableParallel(joke=joke, topic=RunnablePassthrough())
>>> out = fan.invoke({"x": "databases"})
>>> sorted(out.keys())        # predict first!  -> ['joke', 'topic']
>>> out["topic"]              # the ORIGINAL input, passed through unchanged
```
✅ You can predict the dict keys (`RunnableParallel`'s keyword names) and explain
`RunnablePassthrough` carries the input forward untouched — the **dict-in / dict-out** pattern
you'll reuse in RAG (Module 04).

## Part E — Stretch

- Build an **"explain like I'm {age}"** chain: a system message parameterized by `age`, then
  `batch` it over `[{"age": 5, ...}, {"age": 25, ...}, {"age": 80, ...}]` on the same topic and
  read how the tone shifts.
- Add a `MessagesPlaceholder("history")` to a prompt, prime it with one `HumanMessage` /
  `AIMessage` pair, then ask a follow-up that only makes sense given that history (e.g. "and
  what's my name?"). Confirm the model uses it.
- Insert a `RunnableLambda(str.upper)` as the final step of a chain and confirm the output
  comes back shouting — proof that *any* function drops into the pipe.

---

✅ **Done when:** you can build a `prompt | model | parser` chain, explain why removing the
parser yields an `AIMessage` instead of a `str`, predict the keys a `RunnableParallel` returns,
and reshape data between two model calls with a `RunnableLambda`.

**Next →** [challenge.md](./challenge.md) then
[Module 03](../03-structured-output-and-tools/)
