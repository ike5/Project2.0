# Module 03 — Structured Output & Tools

**Goal:** stop treating the model as a text box. Two upgrades that turn a chat model into a
component you can build on: **structured output** (get a validated Python object back instead
of a paragraph you have to parse) and **tools** (let the model decide to call *your* Python
functions). You'll learn `with_structured_output` with Pydantic, the `@tool` decorator and
`bind_tools`, how to read `.tool_calls` — and the key fact that **the model only *requests* a
tool; you run it** — then wire the full request → run → feed-back → final-answer loop by hand.
⏱️ ~3 h · 🎯 Prereq: 02.

```python
from langchain_ollama import ChatOllama
from pydantic import BaseModel

model = ChatOllama(model="llama3.1", num_predict=1024)

class Person(BaseModel):
    name: str
    age: int

structured = model.with_structured_output(Person)
structured.invoke("Ada Lovelace was 36.")   # -> Person(name='Ada Lovelace', age=36)
```

---

## 1. Structured output — typed objects, not prose

Ask a plain model "who is this and how old?" and you get a sentence. To *use* the answer in
code you'd have to write a brittle parser. Instead, hand the model a **schema** and it fills
it in. Define the shape with a [Pydantic](https://docs.pydantic.dev) `BaseModel`, then wrap
the model with `with_structured_output`:

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="the person's full name")
    age: int = Field(description="age in years")

structured = model.with_structured_output(Person)
result = structured.invoke("Grace Hopper was a 79-year-old computer scientist.")
result            # -> Person(name='Grace Hopper', age=79)
result.name       # 'Grace Hopper'   <- a real attribute, typed
result.age + 1    # 80               <- it's an int, do math on it
```

`structured.invoke(...)` returns an **instance of your class** — not text, not a dict you
have to `json.loads`. `Field(description=...)` is how you *guide* the model on what each
field means; spend your effort there.

### Optional, lists, and nested models

Real data is messier than two scalars. Pydantic gives you the vocabulary:

```python
from typing import Optional

class Person(BaseModel):
    name: str
    age: int
    email: Optional[str] = Field(default=None, description="email if mentioned, else null")
    skills: list[str] = Field(default_factory=list, description="skills mentioned")
```

- **`Optional[str]`** — the field may be absent. The model returns `None` when the text
  doesn't mention it, instead of hallucinating one.
- **`list[str]`** — zero or more items.
- **Nested models** — a field can be another `BaseModel`, and a `list[...]` of one:

```python
class LineItem(BaseModel):
    description: str
    amount: float

class Invoice(BaseModel):
    vendor: str
    items: list[LineItem]                       # a list of nested objects
    total: float = Field(description="sum of all item amounts")

inv = model.with_structured_output(Invoice).invoke(
    "Invoice from Acme: 2 widgets $10, 1 gadget $25."
)
inv.items[0].description     # 'widgets'
inv.total                    # 45.0
```

The model now returns a fully-built object tree, each field type-checked by Pydantic.

## 2. Why this matters

- **Parse-free.** No regex, no `split(",")`, no "the model put the colon in a weird place."
  You go straight from text to `result.age`.
- **Validated.** If the model returns `age: "old"` instead of an int, Pydantic raises rather
  than letting bad data flow downstream. The types in your schema are a contract.
- **Self-documenting & composable.** The schema *is* the spec, and the wrapped model is still
  a Runnable — it `invoke`s, `stream`s (final object), and `batch`es like anything else, and
  drops into an LCEL chain.

Reach for structured output whenever you need the model's answer *as data*: extraction,
classification, filling a form, returning options to your UI.

## 3. Tools — let the model call your functions

A model can't check today's weather, hit your database, or do exact arithmetic. **Tools**
fix that: you expose Python functions, and the model can choose to call them. Define one with
the `@tool` decorator on a typed function — **the docstring becomes the tool's description**,
which is what the model reads to decide whether and how to use it:

```python
from langchain_core.tools import tool

@tool
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"It's 72°F and sunny in {city}."
```

Type hints define the arguments; the docstring sells the tool. Write both for the model, not
just for yourself. Then **bind** the tools to the model so it knows they exist:

```python
model_with_tools = model.bind_tools([add, get_weather])
```

`bind_tools` returns a *new* model that advertises those tools on every call. It does **not**
run anything — it just tells the model "these are available."

## 4. Reading `.tool_calls` — the model requests, it does not run

Invoke the bound model and look at the response:

```python
resp = model_with_tools.invoke("What is 2 + 3?")
resp.tool_calls
# [{'name': 'add', 'args': {'a': 2, 'b': 3}, 'id': 'toolu_01...'}]
resp.content      # often '' — the model is asking, not answering yet
```

`resp` is an `AIMessage`. Its `.tool_calls` is a **list of dicts**, each:

```python
{"name": "add", "args": {"a": 2, "b": 3}, "id": "toolu_01..."}
```

This is the whole mental model: **the model returned a *request* to run `add(a=2, b=3)` — it
did not run it.** Nothing executed. *You* decide whether to honor the request. And when the
question needs no tool, `.tool_calls` is simply **empty**:

```python
model_with_tools.invoke("Say hello.").tool_calls    # []  -> just answers in .content
```

Always branch on `if resp.tool_calls:` — never assume a tool was called.

## 5. The manual tool-calling loop

Putting it together: ask a question, let the model request a tool, **run it yourself**, send
the result back as a `ToolMessage`, and let the model write the final answer. You also call
a `@tool` directly with `.invoke(args_dict)`:

```python
from langchain_core.messages import HumanMessage, ToolMessage

messages = [HumanMessage("What is 2 + 3?")]
ai = model_with_tools.invoke(messages)
messages.append(ai)                       # keep the model's request in the history

for call in ai.tool_calls:                # may be more than one!
    result = add.invoke(call["args"])     # run the tool: add.invoke({'a': 2, 'b': 3}) -> 5
    messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

final = model_with_tools.invoke(messages) # model reads the ToolMessage -> "2 + 3 is 5."
print(final.content)
```

Two things make this work:

- **`tool_call_id` pairing.** Each `ToolMessage` carries the `id` of the call it answers. The
  model matches result to request by that id — get it wrong and the call is malformed.
- **It's a loop, not a step.** Iterate `ai.tool_calls` because the model can request several
  tools at once. And the model *could* ask for more tools after seeing a result, so a real
  agent keeps looping until `.tool_calls` comes back empty — that's the "agent loop."

> **You are watching what an agent automates.** This hand-rolled loop — append the AI message,
> run each tool, append a `ToolMessage`, re-invoke — is exactly what **Module 06** replaces
> with a LangGraph **`ToolNode`** and a conditional edge. We do it by hand here so that when
> the graph does it for you, you know precisely what each node is doing.

---

## Do the lab
Run the three scripts, then in the REPL confirm the load-bearing facts yourself: that
`.tool_calls` is empty for chit-chat, and that the model *cannot* compute the answer until
you feed the tool result back.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/structured_output.py`](./code/structured_output.py) — `Person` + a nested/list/Optional schema
- [`code/define_tools.py`](./code/define_tools.py) — `@tool` + `bind_tools`, read `.tool_calls` (incl. the empty case)
- [`code/tool_loop.py`](./code/tool_loop.py) — the full manual request → run → feed-back → answer loop

## Key terms
structured output · `with_structured_output` · Pydantic `BaseModel` / `Field` ·
`Optional` / `list` / nested model · validation · `@tool` decorator · docstring-as-description ·
`bind_tools` · `.tool_calls` (request, not run) · `tool_call_id` · `ToolMessage` ·
the manual tool loop · (Module 06: `ToolNode`)

**Next →** [Module 04: RAG — Retrieval](../04-rag-retrieval/)
