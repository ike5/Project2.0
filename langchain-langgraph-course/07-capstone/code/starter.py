"""STARTER scaffold — build a stateful RAG agent. Fill in the TODOs.

This file runs as-is, but it is INCOMPLETE: the retrieval tool is a stub and the
graph isn't wired, so the agent can't actually answer from the docs yet. Work
through the TODOs (they map to milestones M1–M4 in the README/lab), running the
script after each one to watch it come to life. The full answer is in
`rag_agent.py` — try first, peek later.

Run:
    python 07-capstone/code/starter.py
"""

from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_community.document_loaders import TextLoader
from langchain_core.messages import HumanMessage, SystemMessage
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
    """TODO (M1): load kb.txt, split, embed locally, store, return a retriever.

    Steps (see cheatsheets/langchain.md, the RAG section):
      - kb_path = ensure_kb()
      - docs   = TextLoader(kb_path).load()
      - chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
                    .split_documents(docs)
      - embeddings = OllamaEmbeddings(
            model="nomic-embed-text")
      - store = InMemoryVectorStore.from_documents(chunks, embeddings)
      - return store.as_retriever(search_kwargs={"k": k})
    """
    raise NotImplementedError("TODO M1: build and return the retriever")


# Build it once so the tool below can close over it.
# TODO (M1): uncomment after build_retriever works.
# _retriever = build_retriever()


# ── M2: wrap retrieval AS A TOOL ──────────────────────────────────────────────
@tool
def search_docs(query: str) -> str:
    """Search the Lumen Mug product manual for facts about the product.

    Use this whenever the user asks about the Lumen Mug — battery, charging,
    temperature, cleaning, warranty, or any product detail.
    """
    # TODO (M2): run the retriever and return the chunk text joined together.
    #   found = _retriever.invoke(query)
    #   return "\n\n---\n\n".join(d.page_content for d in found)
    return "TODO: retrieval not wired yet"


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the product."""
    return a * b


# TODO (M2): add search_docs to this list once it works.
TOOLS = [multiply]


# ── M3 + M4: the agent graph ──────────────────────────────────────────────────
class State(TypedDict):
    messages: Annotated[list, add_messages]


SYSTEM = (
    "You are a helpful support assistant for the Lumen Mug. "
    "When the user asks about the product, call search_docs and answer ONLY "
    "from what it returns. For arithmetic, use the multiply tool."
)

model = ChatOllama(model="llama3.1", num_predict=1024)
model_with_tools = model.bind_tools(TOOLS)


def agent(state: State) -> dict:
    """TODO (M3): prepend the SYSTEM persona, call the model, return its reply.

    Return ONLY the changed key:
        messages = [SystemMessage(SYSTEM), *state["messages"]]
        return {"messages": [model_with_tools.invoke(messages)]}
    """
    raise NotImplementedError("TODO M3: implement the agent node")


def build_agent():
    """TODO (M3 + M4): wire the graph and add memory.

    builder = StateGraph(State)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)   # -> "tools" or END
    builder.add_edge("tools", "agent")                        # loop back
    return builder.compile(checkpointer=InMemorySaver())        # M4: memory
    """
    raise NotImplementedError("TODO M3/M4: build, wire, and compile the graph")


# ── M5: a tiny multi-turn demo ────────────────────────────────────────────────
def main() -> None:
    graph = build_agent()
    config = {"configurable": {"thread_id": "starter-1"}}

    for turn in [
        "How long does the Lumen Mug hold its temperature?",
        "And how long does it take to charge it fully?",  # needs memory of "it"
    ]:
        print(f"\nUSER: {turn}")
        result = graph.invoke({"messages": [HumanMessage(turn)]}, config)
        print(f"AGENT: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
