"""Compose multi-step chains and fan out with RunnableParallel.

Run (needs a running local Ollama server):
    python 02-prompts-and-lcel/code/composed_chain.py

Step 1 turns a topic into a short story idea. Step 2 turns that idea into a
one-line pitch. A RunnableLambda reshapes the str from step 1 into the dict step 2
expects. Then RunnableParallel runs both views on the same input and returns a dict.
"""

from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel


def section(title: str) -> None:
    print("\n" + "-" * 56)
    print(title)
    print("-" * 56)


def main() -> None:
    model = ChatOllama(model="llama3.1", num_predict=1024)

    # Step 1: a topic -> a one-sentence story idea.
    idea_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a fiction brainstormer. Give ONE vivid story idea in a single sentence."),
        ("human", "Topic: {topic}"),
    ])
    idea_chain = idea_prompt | model | StrOutputParser()

    # Step 2: a story idea -> a punchy one-line marketing pitch.
    pitch_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a marketing copywriter. Turn the idea into ONE catchy one-line pitch."),
        ("human", "Idea: {idea}"),
    ])
    pitch_chain = pitch_prompt | model | StrOutputParser()

    # pitch_chain expects {"idea": ...}, but idea_chain emits a bare str.
    # RunnableLambda wraps a plain function to reshape between stages.
    topic_to_pitch = idea_chain | RunnableLambda(lambda idea: {"idea": idea}) | pitch_chain

    topic = {"topic": "a lighthouse keeper who collects lost radio signals"}

    section("1. Two-step chain: topic -> idea -> pitch")
    pitch = topic_to_pitch.invoke(topic)
    print("pitch:", pitch)

    section("2. RunnableParallel -> a dict with both views, in one call")
    both = RunnableParallel(idea=idea_chain, pitch=topic_to_pitch)
    result = both.invoke(topic)
    print("keys:", list(result.keys()))          # ['idea', 'pitch']
    print("idea :", result["idea"])
    print("pitch:", result["pitch"])

    print("\nDone. dict-in, dict-out: RunnableParallel keys become the result keys.")


if __name__ == "__main__":
    main()
