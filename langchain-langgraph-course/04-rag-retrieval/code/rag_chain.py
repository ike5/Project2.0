"""The full grounded Q&A chain: retrieve -> stuff context into a prompt -> answer.

Run:
    python 04-rag-retrieval/code/rag_chain.py

Needs a running Ollama server (only the FINAL generation step calls the chat model; embeddings
and retrieval run locally). Asks two questions the notes can answer, and one they
CANNOT — to show the model says it doesn't know rather than making something up.
"""

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

from sample_docs import ensure_docs


def format_docs(docs) -> str:
    """Join retrieved chunks into one context string for the prompt."""
    return "\n\n".join(d.page_content for d in docs)


def build_rag():
    path = ensure_docs()

    # Retrieval side — all local, no API key.
    docs = TextLoader(str(path)).load()
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=300, chunk_overlap=50
    ).split_documents(docs)
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )
    store = InMemoryVectorStore.from_documents(chunks, embeddings)
    retriever = store.as_retriever(search_kwargs={"k": 3})

    # Generation side — the only step that hits the API.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. Answer the question using ONLY the "
                "context below. If the answer is not in the context, say you don't "
                "know — do not make anything up.\n\nContext:\n{context}",
            ),
            ("human", "{question}"),
        ]
    )
    model = ChatOllama(model="llama3.1", num_predict=1024)

    # LCEL: the retriever fills {context}, the raw question fills {question}.
    rag = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )
    return rag


def main() -> None:
    rag = build_rag()

    print("=" * 64)
    print("Questions the notes CAN answer (grounded):")
    print("=" * 64)
    for q in [
        "How long does the Lumina battery last and how long to charge it?",
        "What does the warranty cover and what does it exclude?",
    ]:
        print(f"\nQ: {q}")
        print(f"A: {rag.invoke(q)}")

    print("\n" + "=" * 64)
    print("A question the notes CANNOT answer (should decline):")
    print("=" * 64)
    q = "How much does the Lumina lamp cost in US dollars?"
    print(f"\nQ: {q}")
    print(f"A: {rag.invoke(q)}")
    print("\nThe price is nowhere in the notes, so a grounded model says it")
    print("doesn't know instead of inventing a number. That's the whole point.")


if __name__ == "__main__":
    main()
