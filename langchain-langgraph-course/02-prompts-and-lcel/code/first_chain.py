"""Your first LCEL chain: prompt | model | StrOutputParser(), then invoke/stream/batch.

Run (needs a running local Ollama server):
    python 02-prompts-and-lcel/code/first_chain.py

The chain takes a dict (what the prompt needs) and returns a str (what the parser
produces). Because the chain is itself a Runnable, it gets invoke/stream/batch for
free — the same three methods you used on the bare model in Module 01.
"""

from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


def section(title: str) -> None:
    print("\n" + "-" * 56)
    print(title)
    print("-" * 56)


def main() -> None:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You translate English to {language}. Reply with only the translation."),
        ("human", "{text}"),
    ])
    model = ChatOllama(model="llama3.1", num_predict=1024)

    # The pipe snaps three Runnables into one. Output of each step feeds the next:
    #   dict -> prompt -> PromptValue -> model -> AIMessage -> parser -> str
    chain = prompt | model | StrOutputParser()

    section("0. The chain's structure")
    chain.get_graph().print_ascii()

    section("1. invoke -> one string")
    out = chain.invoke({"language": "French", "text": "good morning"})
    print(repr(out), " (type:", type(out).__name__ + ")")

    section("2. stream -> the same string, piece by piece")
    for piece in chain.stream({"language": "French", "text": "Where is the library?"}):
        print(piece, end="", flush=True)
    print()

    section("3. batch -> a list of strings, run concurrently")
    results = chain.batch([
        {"language": "French",  "text": "hello"},
        {"language": "Spanish", "text": "hello"},
        {"language": "German",  "text": "hello"},
    ])
    for r in results:
        print(" ", repr(r))

    print("\nDone. Same chain, three execution modes — none of which you had to implement.")


if __name__ == "__main__":
    main()
