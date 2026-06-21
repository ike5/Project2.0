"""The three universal run methods: invoke, stream, batch.

Run:
    python 01-chat-models-messages/code/invoke_stream_batch.py

Needs a running local Ollama server (ollama serve). Every Runnable (models now, chains later) exposes these
three. invoke = one call; stream = tokens as they arrive; batch = many inputs
answered concurrently.
"""

from langchain_ollama import ChatOllama


def section(title: str) -> None:
    print("\n" + "=" * 56)
    print(title)
    print("=" * 56)


def main() -> None:
    model = ChatOllama(model="llama3.1", num_predict=1024)

    section("invoke — one input, one AIMessage (blocks for the full reply)")
    prompt = "Explain what an API is in exactly one sentence."
    msg = model.invoke(prompt)
    print(msg.content)
    print(f"[tokens: {msg.usage_metadata['total_tokens']}]")

    section("stream — same prompt, tokens printed live as they arrive")
    pieces = []
    for chunk in model.stream(prompt):
        print(chunk.content, end="", flush=True)   # appears incrementally
        pieces.append(chunk.content)
    print()  # newline after the stream
    print(f"[received {len(pieces)} chunks; joined length = {len(''.join(pieces))} chars]")

    section("batch — 3 different questions answered concurrently")
    questions = [
        "What is the capital of France?",
        "What is the capital of Japan?",
        "What is the capital of Peru?",
    ]
    replies = model.batch(questions)              # list[AIMessage], run in parallel
    assert len(replies) == len(questions)
    for q, r in zip(questions, replies):
        print(f"  Q: {q}\n  A: {r.content}\n")

    print("Done. Same model, three call shapes — pick by your use case.")


if __name__ == "__main__":
    main()
