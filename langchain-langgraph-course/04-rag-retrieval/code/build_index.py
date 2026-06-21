"""The retrieval half of RAG: load -> split -> embed -> store -> retrieve.

Run:
    python 04-rag-retrieval/code/build_index.py

No API key needed — embeddings run on a small LOCAL model. (First run downloads
~100MB of model weights once; after that it's offline.) This script makes you SEE
retrieval working — the chunks it pulls back for a query — before any LLM is involved.
"""

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

from sample_docs import ensure_docs


def build_retriever(k: int = 3, chunk_size: int = 300, chunk_overlap: int = 50):
    """Load the notes, split, embed locally, store, and return a retriever + chunks."""
    path = ensure_docs()

    # 1. LOAD — a TextLoader reads the file into a list[Document].
    docs = TextLoader(str(path)).load()

    # 2. SPLIT — break the document into chunks small enough to embed and retrieve.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(docs)

    # 3. EMBED — a local Ollama model (nomic-embed-text) turns text into vectors.
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    # 4. STORE — keep the chunk vectors in an in-memory vector store.
    store = InMemoryVectorStore.from_documents(chunks, embeddings)

    # 5. RETRIEVE — wrap the store so we can fetch the k closest chunks to a query.
    retriever = store.as_retriever(search_kwargs={"k": k})
    return retriever, chunks


def show(query: str, retriever) -> None:
    print(f'\nQuery: "{query}"')
    for i, doc in enumerate(retriever.invoke(query), start=1):
        text = doc.page_content.replace("\n", " ")
        print(f"  [{i}] {text[:90]}{'...' if len(text) > 90 else ''}")


def main() -> None:
    retriever, chunks = build_retriever(k=3)
    print(f"Built a vector store from {len(chunks)} chunks.")
    print("Retrieving the 3 closest chunks per query (no LLM yet):")

    # Ask things the notes DO cover — watch the right chunk surface to the top.
    show("How long does the battery last?", retriever)
    show("What does the warranty cover?", retriever)
    show("Where was the company founded?", retriever)

    print("\nNotice: each query pulls back the chunk that actually contains the")
    print("answer, even though the wording differs. That's semantic search.")


if __name__ == "__main__":
    main()
