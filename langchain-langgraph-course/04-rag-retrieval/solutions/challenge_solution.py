"""Reference solution for Challenge 04 — a RAG chain that also returns its sources.

Run:
    python 04-rag-retrieval/solutions/challenge_solution.py

Needs a running Ollama server (only the final answer step calls the chat model). Builds a RAG
chain over a small text, returns BOTH the grounded answer AND the chunks it used,
shows refusal on an out-of-context question, and prints the effect of chunk size.
"""

import sys
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_ollama import ChatOllama

# Reuse the sample knowledge file from the module's code/ folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from sample_docs import ensure_docs  # noqa: E402


def format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)


def build_rag_with_sources(chunk_size: int = 300, chunk_overlap: int = 50):
    """A chain returning {'answer': str, 'context': list[Document]}."""
    text = ensure_docs().read_text(encoding="utf-8")
    docs = [Document(page_content=text)]
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    ).split_documents(docs)

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )
    store = InMemoryVectorStore.from_documents(chunks, embeddings)
    retriever = store.as_retriever(search_kwargs={"k": 3})

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer using ONLY the context below. If the answer is not in the "
                "context, say you don't know.\n\nContext:\n{context}",
            ),
            ("human", "{question}"),
        ]
    )
    model = ChatOllama(model="llama3.1", num_predict=1024)

    # First fetch the docs ONCE, then fan out: format them for the answer prompt,
    # and also pass the raw Documents straight through so we can show the sources.
    answer = (
        RunnablePassthrough.assign(context=lambda x: format_docs(x["context"]))
        | prompt
        | model
        | StrOutputParser()
    )
    chain = RunnableParallel(
        context=(lambda q: q) | retriever,
        question=RunnablePassthrough(),
    ).assign(answer=answer)
    return chain, len(chunks)


def ask(chain, question: str) -> None:
    out = chain.invoke(question)
    print(f"\nQ: {question}")
    print(f"A: {out['answer']}")
    print("Sources used:")
    for i, doc in enumerate(out["context"], start=1):
        snippet = doc.page_content.replace("\n", " ")
        print(f"  [{i}] {snippet[:80]}{'...' if len(snippet) > 80 else ''}")


def main() -> None:
    chain, n_chunks = build_rag_with_sources()
    print(f"Indexed {n_chunks} chunks.")

    print("\n" + "=" * 60)
    print("Grounded answers, WITH the sources behind them:")
    print("=" * 60)
    ask(chain, "How do I reset the lamp if it won't turn on?")
    ask(chain, "What is the lamp made of and how much does it weigh?")

    print("\n" + "=" * 60)
    print("A question outside the docs — confirm refusal:")
    print("=" * 60)
    ask(chain, "What is the WiFi password for the Lumina lamp?")

    print("\n" + "=" * 60)
    print("Effect of chunk_size: tiny chunks fragment a single fact.")
    print("=" * 60)
    small, n_small = build_rag_with_sources(chunk_size=80, chunk_overlap=10)
    print(f"chunk_size=80 -> {n_small} chunks (vs {n_chunks} at 300).")
    ask(small, "How long does the battery last?")
    print("\nSmaller chunks = more, more-focused pieces, but a fact split across")
    print("two chunks can lose context. Bigger chunks keep facts whole but dilute")
    print("the match with unrelated sentences. 300/50 is a sane starting point.")


if __name__ == "__main__":
    main()
