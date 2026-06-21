# Lab 03 — Structured Output & Tools

**You'll:** run the three scripts, then in the REPL confirm the two facts the whole module
hinges on — that `.tool_calls` is **empty** for chit-chat, and that the model **can't** give
the answer until you feed the tool result back. ⏱️ ~60 min. From the
`langchain-langgraph-course` folder. (Needs your local Ollama server running.)

---

## Part A — Structured output

```bash
python 03-structured-output-and-tools/code/structured_output.py
```
✅ The simple `Person` comes back as a **typed object** — `p1.age + 1` is real arithmetic,
and `email` is `None` when the text doesn't mention one. The nested `Profile` holds a
**list of `Skill` objects** you can index into.

Now in the REPL, build a schema from scratch:
```python
>>> from langchain_ollama import ChatOllama
>>> from pydantic import BaseModel, Field
>>> from typing import Optional
>>> class Book(BaseModel):
...     title: str
...     author: str
...     year: Optional[int] = Field(default=None, description="publication year if stated")
>>> m = ChatOllama(model="llama3.1", num_predict=1024)
>>> b = m.with_structured_output(Book).invoke("Dune was written by Frank Herbert in 1965.")
>>> b.title, b.author, b.year      # ('Dune', 'Frank Herbert', 1965)
>>> type(b).__name__               # 'Book'  <- a real object, not a dict or string
```
✅ You get a `Book` instance, and `year` is an `int` you could do math on — no parsing.

## Part B — Defining tools & reading `.tool_calls`

```bash
python 03-structured-output-and-tools/code/define_tools.py
```
✅ The math question produces a **request** (`{'name': 'add', 'args': {...}, 'id': ...}`)
and nothing runs. The chit-chat question produces an **empty** `.tool_calls`.

Confirm the empty case yourself — this is the rule "the model decides if a tool is needed":
```python
>>> from langchain_ollama import ChatOllama
>>> from langchain_core.tools import tool
>>> @tool
... def add(a: int, b: int) -> int:
...     """Add two integers."""
...     return a + b
>>> m = ChatOllama(model="llama3.1", num_predict=1024).bind_tools([add])
>>> m.invoke("hello").tool_calls        # []   <- no tool needed
>>> m.invoke("what is 8 + 9?").tool_calls   # [{'name': 'add', 'args': {'a': 8, 'b': 9}, ...}]
```
✅ You can state it: **`.tool_calls` is empty unless the model decides a tool is needed, and
even then the tool has not run — it's a request.**

## Part C — The model can't compute without the result

```bash
python 03-structured-output-and-tools/code/tool_loop.py
```
✅ You see three stages: the request, *your* run of `multiply` (→ 84), and the final
natural-language answer.

Now prove the middle stage is load-bearing. Stop the loop **before** feeding the result back
and ask the model to answer anyway:
```python
>>> from langchain_ollama import ChatOllama
>>> from langchain_core.messages import HumanMessage
>>> from langchain_core.tools import tool
>>> @tool
... def multiply(a: int, b: int) -> int:
...     """Multiply two integers."""
...     return a * b
>>> mt = ChatOllama(model="llama3.1", num_predict=1024).bind_tools([multiply])
>>> ai = mt.invoke([HumanMessage("What is 12 * 7?")])
>>> ai.tool_calls          # it WANTS to multiply...
>>> ai.content             # ...and has NOT given you 84 — it's waiting on the result
```
✅ The model returns a tool request, not the number. It physically cannot finish until you
run the tool and append a `ToolMessage` (the next part).

## Part D — Close the loop by hand

Continue from Part C — run the tool and feed it back, then watch the answer appear:
```python
>>> from langchain_core.messages import ToolMessage
>>> messages = [HumanMessage("What is 12 * 7?")]
>>> ai = mt.invoke(messages); messages.append(ai)
>>> for call in ai.tool_calls:
...     result = multiply.invoke(call["args"])          # multiply.invoke({'a':12,'b':7}) -> 84
...     messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
>>> mt.invoke(messages).content        # now it says "12 * 7 is 84." (or similar)
```
✅ The answer appears *only* after the `ToolMessage` (paired by `tool_call_id`) goes back in.
That append-run-append-reinvoke is the loop **Module 06 automates with a `ToolNode`.**

## Part E — Stretch

- **An enum/`Literal` tool argument.** Constrain what the model may pass:
  ```python
  >>> from typing import Literal
  >>> @tool
  ... def set_status(state: Literal["open", "closed", "pending"]) -> str:
  ...     """Set the ticket status to one of: open, closed, pending."""
  ...     return f"status set to {state}"
  >>> ms = ChatOllama(model="llama3.1", num_predict=1024).bind_tools([set_status])
  >>> ms.invoke("close the ticket").tool_calls   # args 'state' will be one of the allowed values
  ```
  ✅ The `state` in `.tool_calls` is always one of the three literals — the type schema is
  passed to the model.
- **Two tools, one question.** Bind both `add` and `multiply`, ask "add 2 and 3"; confirm the
  model picks `add`. Ask something needing neither; confirm `.tool_calls == []`.

---

✅ **Done when:** you can get a typed Pydantic object out of a sentence, you can explain why
`.tool_calls` being a *request* (not a result) matters, and you've watched the model produce a
final answer only after you ran the tool and returned a `ToolMessage`.

**Next →** [challenge.md](./challenge.md) then
[Module 04: RAG — Retrieval](../04-rag-retrieval/)
