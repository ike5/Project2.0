"""Reference solution for Challenge 02 — Prompts & LCEL.

Run (needs a running local Ollama server):
    python 02-prompts-and-lcel/solutions/challenge_solution.py

Each task prints results you can read. The big idea throughout: prompt, model,
parser, lambda, and the whole chain are all Runnables sharing invoke/stream/batch,
which is what makes the pipe `|`, parallel branches, and free batching work.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnableParallel

MODEL = ChatOllama(model="llama3.1", num_predict=1024)

PASSAGE = (
    "The lighthouse had stood for ninety years, its lamp swept the bay each night, "
    "and the keeper logged every passing ship by hand. When the harbor automated, "
    "the logbooks were boxed away — but sailors still spoke of the steady light "
    "that had guided them home through a hundred storms."
)


def section(title: str) -> None:
    print("\n" + "-" * 56)
    print(title)
    print("-" * 56)


def task1_explain_like_age() -> None:
    section("[1] explain like I'm {age}, batched")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Explain things for a {age}-year-old. Match their vocabulary. 2 sentences max."),
        ("human", "Explain: {concept}"),
    ])
    chain = prompt | MODEL | StrOutputParser()
    results = chain.batch([
        {"age": 5, "concept": "how vaccines work"},
        {"age": 25, "concept": "how vaccines work"},
        {"age": 80, "concept": "how vaccines work"},
    ])
    for age, text in zip([5, 25, 80], results):
        print(f"  age {age:>2}: {text}")


def task2_history() -> None:
    section("[2] MessagesPlaceholder injects chat history")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Use the conversation so far."),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])
    chain = prompt | MODEL | StrOutputParser()
    answer = chain.invoke({
        "history": [
            HumanMessage("My favorite color is teal."),
            AIMessage("Got it — teal is a lovely choice!"),
        ],
        "input": "What did I say my favorite color was?",
    })
    print("  answer:", answer, "  (should mention 'teal')")


def task3_summarize_then_translate() -> None:
    section("[3] two-stage chain: summarize -> translate the summary")
    summarize = (
        ChatPromptTemplate.from_messages([
            ("system", "Summarize the passage in ONE sentence."),
            ("human", "{passage}"),
        ])
        | MODEL | StrOutputParser()
    )
    translate = (
        ChatPromptTemplate.from_messages([
            ("system", "Translate the text into {language}. Reply with only the translation."),
            ("human", "{summary}"),
        ])
        | MODEL | StrOutputParser()
    )
    # Reshape stage 1's str into the dict stage 2 expects (and thread in the language).
    two_stage = (
        summarize
        | RunnableLambda(lambda s: {"summary": s, "language": "French"})
        | translate
    )
    print("  translated summary:", two_stage.invoke({"passage": PASSAGE}))


def task4_parallel_summary_sentiment() -> None:
    section("[4] RunnableParallel -> {summary, sentiment} in one call")
    summarize = (
        ChatPromptTemplate.from_messages([
            ("system", "Summarize in ONE sentence."),
            ("human", "{text}"),
        ])
        | MODEL | StrOutputParser()
    )
    sentiment = (
        ChatPromptTemplate.from_messages([
            ("system", "Classify sentiment as exactly one word: positive, negative, or neutral."),
            ("human", "{text}"),
        ])
        | MODEL | StrOutputParser()
    )
    combined = RunnableParallel(summary=summarize, sentiment=sentiment)
    result = combined.invoke({"text": PASSAGE})
    print("  keys:", sorted(result.keys()))      # ['sentiment', 'summary']
    print("  summary  :", result["summary"])
    print("  sentiment:", result["sentiment"])
    assert set(result.keys()) == {"summary", "sentiment"}


def task5_batch() -> None:
    section("[5] batch returns one result per input")
    chain = (
        ChatPromptTemplate.from_messages([("human", "Give a one-word vibe for: {thing}")])
        | MODEL | StrOutputParser()
    )
    inputs = [{"thing": "a thunderstorm"}, {"thing": "a sunrise"}, {"thing": "an empty office"}]
    results = chain.batch(inputs)
    for inp, out in zip(inputs, results):
        print(f"  {inp['thing']:>16} -> {out}")
    assert len(results) == len(inputs)


def task6_visualize_and_parser_swap() -> None:
    section("[6] visualize a chain; parser vs no parser")
    prompt = ChatPromptTemplate.from_messages([("human", "Say hello in {language}.")])
    with_parser = prompt | MODEL | StrOutputParser()
    no_parser = prompt | MODEL

    with_parser.get_graph().print_ascii()

    s = with_parser.invoke({"language": "Italian"})
    m = no_parser.invoke({"language": "Italian"})
    print(f"  with StrOutputParser -> {type(s).__name__}: {s!r}")
    print(f"  without parser       -> {type(m).__name__}; .content = {m.content!r}")
    assert isinstance(s, str)
    assert isinstance(m, AIMessage)


def main() -> None:
    task1_explain_like_age()
    task2_history()
    task3_summarize_then_translate()
    task4_parallel_summary_sentiment()
    task5_batch()
    task6_visualize_and_parser_swap()
    print("\nAll tasks ran ✅")


if __name__ == "__main__":
    main()
