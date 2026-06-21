# LangChain cheatsheet (local, with Ollama)

Everything you reach for in this course's LangChain modules (00–04), in one place.
Up to date for 2026: LangChain 1.x + langchain-ollama 1.1+.

## The chat model (local Ollama)

```python
from langchain_ollama import ChatOllama

model = ChatOllama(model="llama3.1", num_predict=512)   # talks to localhost:11434
# num_predict = max tokens to generate (Ollama's name for it; default 128, -1 = unlimited)
# temperature=0 for repeatable output;  base_url="http://host:11434" for a remote Ollama
```

> No API key. The model must be pulled first: `ollama pull llama3.1`.

## Messages

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

msgs = [
    SystemMessage("You are a terse assistant."),
    HumanMessage("Capital of France?"),
]
resp = model.invoke(msgs)        # -> AIMessage
resp.content                     # the text
resp.tool_calls                  # list of tool calls (empty if none)
resp.usage_metadata              # {'input_tokens': .., 'output_tokens': ..}
```

A bare string is shorthand for one `HumanMessage`:

```python
model.invoke("Hello")            # same as [HumanMessage("Hello")]
```

## Run anything: invoke / stream / batch

```python
model.invoke("one input")                       # -> single result
for chunk in model.stream("write a haiku"):     # -> token-by-token
    print(chunk.content, end="", flush=True)
model.batch(["q1", "q2", "q3"])                 # -> list of results
```

These three methods exist on **every** Runnable — models, prompts, parsers, and chains.

## Prompt templates

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You translate English to {language}."),
    ("human", "{text}"),
])
prompt.invoke({"language": "French", "text": "good morning"})   # -> a PromptValue (messages)
```

Inject a running list of messages (for chat history) with a placeholder:

```python
from langchain_core.prompts import MessagesPlaceholder
ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])
```

## Output parsers

```python
from langchain_core.output_parsers import StrOutputParser
StrOutputParser()                # AIMessage -> str
```

## LCEL — compose with the pipe `|`

```python
chain = prompt | model | StrOutputParser()
chain.invoke({"language": "French", "text": "good morning"})    # -> "bonjour"
chain.stream({...})              # streams the final string
chain.batch([{...}, {...}])      # many at once
```

Output of each step feeds the next. The whole chain is itself a Runnable.

Pass data through / run in parallel:

```python
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
RunnableParallel(answer=chain, original=RunnablePassthrough())
```

## Structured output (→ Pydantic objects)

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="full name")
    age: int

structured = model.with_structured_output(Person)
structured.invoke("Ada Lovelace was 36.")        # -> Person(name='Ada Lovelace', age=36)
```

> Tip: structured output and tool calling lean on the model's tool-calling ability —
> `llama3.1` handles these well; very small models can be flaky.

## Tools — let the model call your functions

```python
from langchain_core.tools import tool

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""          # the docstring is the tool description
    return a + b

model_with_tools = model.bind_tools([add])
resp = model_with_tools.invoke("What is 2 + 3?")
resp.tool_calls          # [{'name': 'add', 'args': {'a': 2, 'b': 3}, 'id': '...'}]
```

Run the tool and feed the result back:

```python
from langchain_core.messages import HumanMessage, ToolMessage
messages = [HumanMessage("What is 2 + 3?")]
ai = model_with_tools.invoke(messages); messages.append(ai)
for call in ai.tool_calls:
    result = add.invoke(call["args"])
    messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
final = model_with_tools.invoke(messages)        # model uses the result -> "5"
```

(Module 06 replaces this hand-rolled loop with a LangGraph `ToolNode`.)

## RAG — load → split → embed → store → retrieve (all local)

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

docs   = TextLoader("notes.txt").load()
chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)

embeddings = OllamaEmbeddings(model="nomic-embed-text")   # local; ollama pull nomic-embed-text
store      = InMemoryVectorStore.from_documents(chunks, embeddings)
retriever  = store.as_retriever(search_kwargs={"k": 3})

retriever.invoke("some question")     # -> list[Document], the 3 closest chunks
```

Grounded answer chain:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer ONLY from this context:\n\n{context}"),
    ("human", "{question}"),
])
def format_docs(docs): return "\n\n".join(d.page_content for d in docs)

rag = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | model | StrOutputParser()
)
rag.invoke("some question")
```

## Handy

```python
resp.pretty_print()                       # readable message dump
chain.get_graph().print_ascii()           # visualize a chain's structure
```
