"""Reference solution for Challenge 01. Run:
    python 01-chat-models-messages/solutions/challenge_solution.py

Needs a running local Ollama server (ollama serve). Asserts the checks that don't depend on the model's exact
wording (token sums, recall via substring, done_reason, etc.).
"""

import time
from typing import Callable

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def model(num_predict: int = 1024) -> ChatOllama:
    return ChatOllama(model="llama3.1", num_predict=num_predict)


# --- Task 1: persona bot via a closure -----------------------------------
def make_bot(persona: str) -> Callable[[str], str]:
    """Return a bot that always answers with `persona` fixed in a SystemMessage."""
    m = model()

    def bot(question: str) -> str:
        # Build the message list FRESH each call so personas don't leak.
        return m.invoke([SystemMessage(persona), HumanMessage(question)]).content

    return bot


def task1_persona_bot() -> None:
    section("[1] Persona bot — same question, two personas")
    pirate = make_bot("You are a salty pirate. Answer in one short sentence of pirate slang.")
    butler = make_bot("You are a formal English butler. Answer in one polished sentence.")
    q = "Is it going to rain today?"
    print("  pirate:", pirate(q))
    print("  butler:", butler(q))


# --- Task 2: chat(history, user_msg) -> (reply, new_history) --------------
def chat(history: list, user_msg: str) -> tuple[str, list]:
    """Append the user turn, invoke the whole history, append the reply, return both."""
    m = model()
    history.append(HumanMessage(user_msg))
    ai = m.invoke(history)
    history.append(ai)            # keep the model's reply in history
    return ai.content, history


def task2_chat() -> list:
    section("[2] chat(history, user_msg) — a 3-turn conversation")
    history = [SystemMessage("You are a concise assistant. One sentence per reply.")]
    _, history = chat(history, "My lucky number is 42. Please remember it.")
    _, history = chat(history, "Name a planet in our solar system.")
    reply, history = chat(history, "What is my lucky number?")
    print("  turn-3 reply:", reply)
    assert "42" in reply, "Should recall 42 from turn 1 (full history was re-sent)."
    print(f"  history length: {len(history)} messages")
    assert isinstance(history[-1], AIMessage)
    return history


# --- Task 3: drop the history -> break memory ----------------------------
def task3_drop_history() -> None:
    section("[3] Dropping the history breaks recall")
    m = model()
    # With history: build one carrying the fact, then ask.
    hist = [SystemMessage("You are concise.")]
    _, hist = chat(hist, "The secret codeword is AVOCADO.")
    with_hist = m.invoke(hist + [HumanMessage("What is the codeword?")]).content
    # Without history: the recall question stands completely alone.
    without_hist = m.invoke([HumanMessage("What is the codeword?")]).content
    print("  with history   :", with_hist)
    print("  without history:", without_hist)
    assert "AVOCADO" in with_hist.upper(), "Should recall when history is present."
    assert "AVOCADO" not in without_hist.upper(), "Cannot recall what was never sent."
    # WHY: the model is stateless; 'memory' is only the messages you choose to re-send.


# --- Task 4: batch vs sequential — tokens & wall-clock -------------------
def task4_batch_vs_sequential() -> None:
    section("[4] Batch vs sequential — tokens (~equal) & time (batch faster)")
    questions = [
        "What is the capital of France?",
        "What is the capital of Japan?",
        "What is the capital of Peru?",
        "What is the capital of Egypt?",
        "What is the capital of Canada?",
    ]
    m = model()

    t0 = time.perf_counter()
    seq_msgs = [m.invoke(q) for q in questions]
    seq_time = time.perf_counter() - t0
    seq_tokens = sum(x.usage_metadata["total_tokens"] for x in seq_msgs)

    t0 = time.perf_counter()
    batch_msgs = m.batch(questions)
    batch_time = time.perf_counter() - t0
    batch_tokens = sum(x.usage_metadata["total_tokens"] for x in batch_msgs)

    print(f"  sequential: total_tokens={seq_tokens:4d}  time={seq_time:.2f}s")
    print(f"  batch     : total_tokens={batch_tokens:4d}  time={batch_time:.2f}s")
    print("  -> tokens ~equal (same prompts); batch saves wall-clock via concurrency.")
    assert len(batch_msgs) == len(questions)
    # Tokens depend on per-prompt cost, not on how we ran them: within a small margin.
    assert abs(seq_tokens - batch_tokens) <= max(20, int(0.2 * seq_tokens))


# --- Task 5: usage report + forced num_predict stop -----------------------
def task5_usage_report() -> None:
    section("[5] Usage report + forcing done_reason == 'length'")
    full = model().invoke("Write a two-sentence summary of what an LLM is.")
    u = full.usage_metadata
    print(f"  input_tokens : {u['input_tokens']}")
    print(f"  output_tokens: {u['output_tokens']}")
    print(f"  total_tokens : {u['total_tokens']}")
    print(f"  model   : {full.response_metadata.get('model')}")
    print(f"  done_reason  : {full.response_metadata.get('done_reason')}")
    assert u["input_tokens"] + u["output_tokens"] == u["total_tokens"]

    capped = model(num_predict=16).invoke(
        "Write a long, detailed essay about the history of computing."
    )
    print(f"  capped done_reason: {capped.response_metadata.get('done_reason')}")
    assert capped.response_metadata.get("done_reason") == "length"


# --- Task 6 (stretch): stream into a string ------------------------------
def task6_stream_into_string() -> None:
    section("[6] Stretch — stream live AND accumulate into one string")
    pieces = []
    print("  live: ", end="")
    for chunk in model().stream("Count from 1 to 5, comma separated."):
        print(chunk.content, end="", flush=True)
        pieces.append(chunk.content)
    print()
    joined = "".join(pieces)
    print(f"  joined ({len(joined)} chars): {joined!r}")
    assert joined.strip(), "Streamed text should be non-empty."


def main() -> None:
    task1_persona_bot()
    task2_chat()
    task3_drop_history()
    task4_batch_vs_sequential()
    task5_usage_report()
    task6_stream_into_string()
    print("\nAll checks passed ✅")


if __name__ == "__main__":
    main()
