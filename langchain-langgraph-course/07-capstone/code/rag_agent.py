"""Capstone reference solution — a stateful RAG agent in LangGraph.

This is the full, runnable answer. It:
  1. Indexes the sample knowledge base (kb.txt) with local embeddings.
  2. Wraps the retriever as a @tool (`search_docs`) — so the AGENT decides when
     to look things up — plus one utility tool (`multiply`).
  3. Builds the tool-calling agent graph: agent <-> ToolNode, routed by
     tools_condition, with a InMemorySaver checkpointer for per-thread memory.
  4. Demonstrates a multi-turn session on ONE thread_id (a doc question, a
     follow-up that only works if it remembers, then a utility-tool question),
     printing the conversation and flagging when search_docs fires.
  5. Shows a FRESH thread_id forgetting the earlier context.

Requires a running local Ollama server (makes real model calls). The embedding model is
local; first run downloads ~90 MB of weights, then it is offline.

Run:
    python 07-capstone/code/rag_agent.py
"""

from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_community.document_loaders import TextLoader
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from sample_kb import ensure_kb


# ── M1: index the knowledge base ──────────────────────────────────────────────
def build_retriever(k: int = 3):
    """Load -> split -> embed -> store -> retriever over kb.txt."""
    kb_path = ensure_kb()
    docs = TextLoader(kb_path).load()
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=80
    ).split_documents(docs)
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )
    store = InMemoryVectorStore.from_documents(chunks, embeddings)
    return store.as_retriever(search_kwargs={"k": k})


# Build the retriever once at import time; the tool below closes over it.
_retriever = build_retriever()


# ── M2: wrap retrieval AS A TOOL ──────────────────────────────────────────────
@tool
def search_docs(query: str) -> str:
    """Search the Lumen Mug product manual for facts about the product.

    Use this whenever the user asks about the Lumen Mug — its battery, charging,
    temperature settings, cleaning, warranty, or any other product detail.
    Returns the most relevant passages from the manual.
    """
    # A visible marker so the demo can SHOW when the agent chose to retrieve.
    print(f"      [search_docs called with query={query!r}]")
    found = _retriever.invoke(query)
    return "\n\n---\n\n".join(d.page_content for d in found)


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the product."""
    print(f"      [multiply called with a={a}, b={b}]")
    return a * b


TOOLS = [search_docs, multiply]


# ── M3 + M4: the agent graph with memory ──────────────────────────────────────
class State(TypedDict):
    messages: Annotated[list, add_messages]


SYSTEM = (
    "You are a helpful support assistant for the Lumen Mug. "
    "When the user asks about the product, call search_docs and answer ONLY "
    "from what it returns. For arithmetic, use the multiply tool. "
    "If the manual does not cover something, say so plainly."
)

model = ChatOllama(model="llama3.1", num_predict=1024)
model_with_tools = model.bind_tools(TOOLS)


def agent(state: State) -> dict:
    """The 'think' node: prepend the persona, then let the model decide."""
    from langchain_core.messages import SystemMessage

    messages = [SystemMessage(SYSTEM), *state["messages"]]
    return {"messages": [model_with_tools.invoke(messages)]}


def build_agent():
    """Wire START -> agent -> (tools_condition) -> tools -> agent, with memory."""
    builder = StateGraph(State)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)  # -> "tools" or END
    builder.add_edge("tools", "agent")  # loop back so the model uses the result
    return builder.compile(checkpointer=InMemorySaver())


# ── M5: the multi-turn demo ───────────────────────────────────────────────────
def _text_of(msg) -> str:
    """Pull plain text out of an AIMessage whose content may be a block list."""
    content = msg.content
    if isinstance(content, str):
        return content
    # Some models return content as a list of blocks; ChatOllama returns a string. Handle both.
    parts = [b.get("text", "") for b in content if isinstance(b, dict)]
    return "".join(parts)


def show_turn(graph, text: str, thread_id: str) -> None:
    """Send one user turn, print the new messages, and flag tool activity."""
    print(f"\n  USER ({thread_id}): {text}")
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"messages": [HumanMessage(text)]}, config)
    # Walk the freshest messages back to (and including) our HumanMessage.
    new = []
    for msg in reversed(result["messages"]):
        new.append(msg)
        if isinstance(msg, HumanMessage) and msg.content == text:
            break
    for msg in reversed(new):
        if isinstance(msg, AIMessage):
            if msg.tool_calls:
                names = ", ".join(c["name"] for c in msg.tool_calls)
                print(f"  AGENT: (decided to call tools: {names})")
            text_part = _text_of(msg)
            if text_part:
                print(f"  AGENT: {text_part}")
        elif isinstance(msg, ToolMessage):
            preview = msg.content.replace("\n", " ")[:90]
            print(f"  TOOL  ({msg.name}) -> {preview}...")


def main() -> None:
    graph = build_agent()

    print("=" * 72)
    print("Agent graph:")
    graph.get_graph().print_ascii()

    print("=" * 72)
    print("SESSION A — one thread, three turns (retrieval, memory, utility tool)")
    print("=" * 72)
    show_turn(graph, "How long does the Lumen Mug hold its temperature?", "session-A")
    # Follow-up with a pronoun: only works if the agent REMEMBERS we mean the mug.
    show_turn(graph, "And how long does it take to charge it fully?", "session-A")
    # A utility-tool question, mid-conversation.
    show_turn(graph, "If I buy 7 mugs at 3 each, what's the total? Use the tool.", "session-A")

    print("\n" + "=" * 72)
    print("SESSION B — a FRESH thread_id has no memory of session A")
    print("=" * 72)
    show_turn(graph, "What did I just ask you about?", "session-B")
    print("\n  (Session B starts blank — it cannot see session A's history.)")


if __name__ == "__main__":
    main()
