# Lab 00 — Setup & First Call

**You'll:** confirm the install, make a live call to your local model, watch streaming, and
read token usage. ⏱️ ~20 min. Run from the `langchain-langgraph-course` folder with your venv
active and your local Ollama server running.

---

## Part A — Versions, Ollama & a live call

```bash
python 00-setup/code/verify_install.py
```
✅ You see version lines for `langchain`, `langgraph`, and `langchain-ollama`, then
`Ollama server : reachable at localhost:11434 ✅`, a reply like
`model says : hello from ollama`, and finally `live call OK ✅`.
If a package shows **NOT INSTALLED**, re-run `pip install -r requirements.txt`. If the Ollama
line fails, start the server (`ollama serve`) and pull the model (`ollama pull llama3.1`) —
see the [README](./README.md) — and re-run.

## Part B — Invoke vs stream

```bash
python 00-setup/code/hello_ollama.py
```
✅ Under **invoke (batched)** you see the whole answer appear at once, then a
`tokens -> input: .. output: ..` line. Under **stream (token by token)** you see the *same*
answer trickle in piece by piece. Same model, same prompt — two delivery modes.

## Part C — Poke at a call in the REPL

```bash
python
```
```python
>>> from langchain_ollama import ChatOllama
>>> model = ChatOllama(model="llama3.1", num_predict=128)
>>> resp = model.invoke("Name three primary colors.")
>>> resp.content            # the reply text
>>> resp.usage_metadata     # {'input_tokens': .., 'output_tokens': .., ...}
>>> type(resp)              # langchain_core.messages.ai.AIMessage
>>> exit()
```
✅ `resp` is an **`AIMessage`**: `.content` holds the text and `.usage_metadata` holds the
token counts. Every model call in this course returns this shape.

## Part D — Stretch: control the reply with a system message

In the REPL, steer the model with a `SystemMessage`:

```python
>>> from langchain_core.messages import SystemMessage, HumanMessage
>>> msgs = [SystemMessage("Answer with exactly one word."),
...         HumanMessage("What is the capital of France?")]
>>> model.invoke(msgs).content      # -> "Paris"
```
✅ The system message changed the *behavior*, not the question. Compare the
`output_tokens` to a chatty answer — fewer words, fewer tokens, faster replies.

---

✅ **Done when:** you've made a live call, seen streaming, and read token usage.

**Next →** [Module 01](../01-chat-models-messages/)
