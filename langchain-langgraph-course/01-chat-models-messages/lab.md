# Lab 01 — Chat Models & Messages

**You'll:** run the three scripts, then reproduce the key results yourself in a Python REPL
(or a scratch script). ⏱️ ~50 min. From the `langchain-langgraph-course` folder, with
your local Ollama server running.

> Start a REPL with `python`. First two lines for every snippet below:
> ```python
> >>> from langchain_ollama import ChatOllama
> >>> from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
> >>> model = ChatOllama(model="llama3.1", num_predict=1024)
> ```

---

## Part A — Messages & usage

```bash
python 01-chat-models-messages/code/messages_basics.py
```
✅ Read the printed `usage_metadata`. Confirm `input_tokens + output_tokens == total_tokens`
(the script asserts it).

Now reproduce a call yourself and inspect the return type:
```python
>>> reply = model.invoke([
...     SystemMessage("You are a terse assistant."),
...     HumanMessage("Name three primary colors."),
... ])
>>> type(reply).__name__      # 'AIMessage'
>>> reply.content
>>> reply.usage_metadata      # a dict of input/output/total tokens
```
✅ You can say what each of `SystemMessage` / `HumanMessage` / `AIMessage` is for, and that
`invoke` *returns* an `AIMessage`.

Try the bare-string shortcut:
```python
>>> model.invoke("Say only the word 'ping'.").content
```
✅ You can explain that `model.invoke("hi")` is sugar for `model.invoke([HumanMessage("hi")])`.

## Part B — invoke vs stream vs batch

```bash
python 01-chat-models-messages/code/invoke_stream_batch.py
```
✅ In the **stream** section the text appears piece-by-piece (not all at once). In **batch**
you get one answer per question, in order.

Reproduce streaming yourself and *watch the tokens land*:
```python
>>> for chunk in model.stream("Count slowly from 1 to 10."):
...     print(chunk.content, end="", flush=True)
```
✅ You can state when you'd pick each method: **invoke** (single call), **stream**
(responsive UI), **batch** (many independent inputs at once).

Now batch three questions:
```python
>>> rs = model.batch(["2+2?", "3+3?", "4+4?"])
>>> [r.content for r in rs]      # a list, same order as the questions
>>> len(rs)                       # 3
```
✅ `batch` returns a **list** of `AIMessage`s, one per input, run concurrently.

## Part C — Memory is a list you manage

```bash
python 01-chat-models-messages/code/conversation.py
```
✅ The final turn recalls the favorite number **7** — and you can explain it's because the
whole history list was re-sent each `invoke`, not because the server remembered anything.

Build a 2-turn conversation by hand, appending the reply:
```python
>>> msgs = [SystemMessage("You are concise.")]
>>> msgs.append(HumanMessage("Remember the codeword BANANA."))
>>> msgs.append(model.invoke(msgs))          # append the AIMessage
>>> msgs.append(HumanMessage("What was the codeword?"))
>>> model.invoke(msgs).content                # -> mentions BANANA
```
✅ It recalls `BANANA`.

## Part D — Predict: drop the history → break memory

**Predict before running:** if you ask the recall question *without* re-sending the earlier
turns, will the model know the codeword? Write down your guess, then run:
```python
>>> model.invoke([HumanMessage("What was the codeword?")]).content
```
✅ It does **not** know — there's no codeword anywhere in *this* list. The lesson: the model
has no hidden memory; if a fact isn't in the messages you send, it can't use it.

## Part E — Stretch

- **Persona swap.** Ask the same question with two different `SystemMessage`s
  (e.g. `"Answer in rhyme."` vs `"Answer in one technical sentence."`) and compare:
  ```python
  >>> def ask(persona, q):
  ...     return model.invoke([SystemMessage(persona), HumanMessage(q)]).content
  >>> ask("You are a pirate. Answer in pirate slang.", "What is the ocean?")
  >>> ask("You are a marine biologist. Be precise.", "What is the ocean?")
  ```
- **Token accounting.** Sum `total_tokens` across a 3-turn conversation and notice it grows
  each turn — because you re-send the whole (growing) history every call.
- **Read `response_metadata`.** Print `reply.response_metadata` and find `model` and
  `done_reason`. Lower `num_predict=20` on the constructor and watch `done_reason` become
  `'length'`.

---

✅ **Done when:** you can run all three scripts, build a multi-turn conversation by hand by
appending `AIMessage`s, and explain in one sentence why dropping the history makes the model
"forget."

**Next →** [challenge.md](./challenge.md) then
[Module 02: Prompts & LCEL](../02-prompts-and-lcel/)
