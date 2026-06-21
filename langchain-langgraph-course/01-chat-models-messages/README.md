# Module 01 — Chat Models & Messages

**Goal:** get fluent with the two things every LangChain app is built on — **messages**
(the typed turns of a conversation) and the **chat model** that consumes them. You'll learn
the four message roles, the three universal run methods (`invoke` / `stream` / `batch`),
that **a conversation is just a list you manage yourself**, how to set a persona with a
system prompt, and how to read token usage. ⏱️ ~2 h · 🎯 Prereq: 00.

```python
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

model = ChatOllama(model="llama3.1", num_predict=1024)
reply = model.invoke([
    SystemMessage("You are a terse assistant."),
    HumanMessage("Name three primary colors."),
])
print(reply.content)
```

---

## 1. Messages & roles

A chat model doesn't take a string — it takes a **list of messages**, each tagged with a
**role**. LangChain gives you one class per role:

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

SystemMessage("You are a helpful pirate.")   # system: sets behavior, not a turn the user sees
HumanMessage("What's the weather like?")      # human: what the user said
AIMessage("Arr, I cannot check the weather!") # ai: what the model said (you append these)
```

- **System** — instructions that shape *how* the model behaves (persona, rules, format).
  Usually the first message; there's typically one.
- **Human** — a user turn.
- **AI** — a model turn. `model.invoke(...)` *returns* an `AIMessage`; you also *append*
  past ones back into the list to give the model memory (section 3).
- **Tool** — the result of a tool/function call fed back to the model. We only mention it
  here; it's covered in **Module 03**.

> **Shortcut:** passing a bare string is sugar for a single `HumanMessage`.
> `model.invoke("hi")` ≡ `model.invoke([HumanMessage("hi")])`.

## 2. invoke / stream / batch — the three universal run methods

Every chat model exposes the **same three methods**. (So does every prompt, parser, and
chain you'll build later — they're all *Runnables*. This is the interface LCEL is built on,
foreshadowed in Module 02.)

```python
# invoke: one input -> one AIMessage (blocks until the whole reply is ready)
msg = model.invoke("Explain RAM in one sentence.")
print(msg.content)

# stream: one input -> an iterator of chunks, as the model produces them
for chunk in model.stream("Count from 1 to 5."):
    print(chunk.content, end="", flush=True)   # tokens appear live

# batch: many inputs -> a list of AIMessages, run concurrently (faster than a loop)
replies = model.batch(["Capital of France?", "Capital of Japan?", "Capital of Peru?"])
print([r.content for r in replies])
```

Use **invoke** for a single call, **stream** for a responsive UI, **batch** when you have
many independent inputs and want them answered in parallel.

## 3. Multi-turn = managing a list yourself

The API is **stateless**: the model remembers *nothing* between calls. A "conversation" is
just a Python list that you grow and **re-send in full** every time. After each call you
append the model's `AIMessage`, then the next `HumanMessage`, then invoke again:

```python
messages = [SystemMessage("You are a concise math tutor.")]

messages.append(HumanMessage("I'm thinking of the number 7. Remember it."))
ai = model.invoke(messages)          # -> AIMessage
messages.append(ai)                  # <-- keep the reply in the history!

messages.append(HumanMessage("What number did I pick?"))
ai = model.invoke(messages)          # the model sees the WHOLE list, so it "remembers"
print(ai.content)                    # -> 7
```

If you *don't* append the history, the second call has no idea about the 7 — it isn't
memory loss, it's that you never told it. (You'll prove this to yourself in the lab.)

## 4. System prompts shape behavior

The `SystemMessage` is your steering wheel: persona, tone, rules, and output format all go
here. Same human question, different system prompt, very different answer:

```python
def ask(persona: str, question: str) -> str:
    return model.invoke([SystemMessage(persona), HumanMessage(question)]).content

ask("You are a medieval bard. Answer in rhyme.", "What is the sun?")
ask("You are a NASA engineer. Be precise and technical.", "What is the sun?")
```

## 5. Inspecting usage (tokens & metadata)

Every `AIMessage` carries metadata so you can track cost and debug. Read it constantly:

```python
msg = model.invoke("Write a haiku about tensors.")
print(msg.usage_metadata)
# {'input_tokens': 14, 'output_tokens': 21, 'total_tokens': 35}
print(msg.response_metadata["model"])   # which model actually answered
print(msg.response_metadata["done_reason"])  # e.g. 'stop' or 'length'
```

> Two model params worth knowing now: **`num_predict`** caps the reply length (and your
> cost); **`temperature`** (0 = deterministic-ish, higher = more random/creative) controls
> sampling. Both are set on the `ChatOllama(...)` constructor or per-call.

---

## Do the lab
Run the three scripts, then reproduce the results yourself — including *predicting* whether
the model will remember a fact when you drop the history.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/messages_basics.py`](./code/messages_basics.py) — System+Human messages, content + usage, bare-string call
- [`code/invoke_stream_batch.py`](./code/invoke_stream_batch.py) — the same prompt three ways
- [`code/conversation.py`](./code/conversation.py) — a 3-turn conversation held in a list

## Key terms
message · role · `SystemMessage`/`HumanMessage`/`AIMessage`/Tool · `ChatOllama` ·
`invoke`/`stream`/`batch` · Runnable · stateless · conversation history · system prompt /
persona · `usage_metadata` · `response_metadata` · `num_predict` · `temperature`

**Next →** [Module 02: Prompts & LCEL](../02-prompts-and-lcel/)
