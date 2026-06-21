"""Reference solution for Challenge 03 — structured output & tools.

Run:
    python 03-structured-output-and-tools/solutions/challenge_solution.py

Needs a running local Ollama server (ollama serve). Each task prints its result and asserts the key checks.

Covers:
  1. Extract a nested Invoice (list of LineItem) with structured output.
  2. A calculator tool set + a manual loop that solves a word problem (= 19),
     looping until .tool_calls is empty and handling multiple/sequential calls.
  3. A chit-chat question the model should NOT call a tool for (.tool_calls == []).
  4. Structured output to classify intent, then route math -> the calculator loop.
  5. Stretch: a tool that raises (divide-by-zero) is caught and fed back as a
     ToolMessage so the model can recover.
"""

from typing import Literal

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field


def section(title: str) -> None:
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


# ---------------------------------------------------------------------------
# Task 1 — nested Invoice extraction
# ---------------------------------------------------------------------------
class LineItem(BaseModel):
    description: str = Field(description="what the item is")
    quantity: int = Field(description="how many")
    unit_price: float = Field(description="price per single unit, in dollars")


class Invoice(BaseModel):
    vendor: str = Field(description="who issued the invoice")
    items: list[LineItem] = Field(description="the line items")
    total: float = Field(description="sum of quantity * unit_price across all items")


def task1_invoice(model: ChatOllama) -> None:
    section("Task 1 — extract a nested Invoice")
    text = "Invoice from Acme Corp: 3 widgets at $4.50 each, and 2 gadgets at $12.00 each."
    inv = model.with_structured_output(Invoice).invoke(text)

    print("vendor:", inv.vendor)
    for it in inv.items:
        print(f"  {it.quantity} x {it.description} @ ${it.unit_price:.2f}")
    print("total:", inv.total)

    computed = sum(it.quantity * it.unit_price for it in inv.items)
    print("computed from line items:", computed)
    assert len(inv.items) == 2, "expected two line items"
    assert abs(inv.total - computed) < 0.01, "total should match summed line items"
    assert abs(computed - 37.50) < 0.01, "3*4.50 + 2*12.00 = 37.50"
    print("OK: total matches the summed line items.")


# ---------------------------------------------------------------------------
# Tasks 2/4/5 — calculator tools + the manual loop
# ---------------------------------------------------------------------------
@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """Divide a by b. Raises if b is zero."""
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b


CALC_TOOLS = [add, subtract, multiply, divide]
CALC_BY_NAME = {t.name: t for t in CALC_TOOLS}


def run_calc_loop(model_with_tools, question: str, verbose: bool = True) -> str:
    """Manual tool loop: invoke -> run tools -> feed back -> repeat until done.

    Catches tool errors and feeds them back so the model can recover (task 5).
    Returns the model's final natural-language answer.
    """
    messages = [HumanMessage(question)]
    while True:
        ai = model_with_tools.invoke(messages)
        messages.append(ai)
        if not ai.tool_calls:
            return ai.content  # the model is done

        for call in ai.tool_calls:  # possibly several at once
            tool_fn = CALC_BY_NAME[call["name"]]
            try:
                result = tool_fn.invoke(call["args"])
            except Exception as exc:  # task 5: report the error back, don't crash
                result = f"ERROR: {exc}"
            if verbose:
                print(f"  ran {call['name']}({call['args']}) -> {result}")
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))


def task2_word_problem(model: ChatOllama) -> None:
    section("Task 2 — calculator loop on a word problem (expect 19)")
    mt = model.bind_tools(CALC_TOOLS)
    q = "I bought 3 packs of 8 pencils and then gave away 5. How many do I have left?"
    answer = run_calc_loop(mt, q)
    print("final answer:", answer)
    assert "19" in answer, "3*8 - 5 = 19 should appear in the answer"
    print("OK: '19' is in the final answer.")


# ---------------------------------------------------------------------------
# Task 3 — a question the model should NOT use a tool for
# ---------------------------------------------------------------------------
def task3_no_tool(model: ChatOllama) -> None:
    section("Task 3 — chit-chat: the model should NOT call a tool")
    mt = model.bind_tools(CALC_TOOLS)
    resp = mt.invoke("What's your favorite color?")
    print(".tool_calls:", resp.tool_calls)
    print(".content   :", resp.content)
    assert resp.tool_calls == [], "no calculator tool applies to a chit-chat question"
    print("OK: tool_calls is empty — no calculator applies to 'favorite color'.")


# ---------------------------------------------------------------------------
# Task 4 — structured output to classify intent, then route
# ---------------------------------------------------------------------------
class Intent(BaseModel):
    category: Literal["math", "weather", "chitchat"] = Field(
        description="the kind of request the user is making"
    )
    confidence: float = Field(description="confidence from 0.0 to 1.0")


def task4_classify_and_route(model: ChatOllama) -> None:
    section("Task 4 — classify intent (structured output), then route")
    classifier = model.with_structured_output(Intent)
    mt = model.bind_tools(CALC_TOOLS)

    messages = [
        "What is 6 times 9 minus 4?",
        "How are you doing today?",
    ]
    for msg in messages:
        intent = classifier.invoke(msg)
        print(f"\n{msg!r} -> {intent.category} (conf {intent.confidence:.2f})")
        assert intent.category in ("math", "weather", "chitchat")
        if intent.category == "math":
            answer = run_calc_loop(mt, msg, verbose=False)
            print("  routed to calculator loop ->", answer)
            assert "50" in answer, "6*9 - 4 = 50"
        else:
            print("  routed to a plain answer ->", model.invoke(msg).content[:80], "...")
    print("\nOK: classified each message and routed math into the tool loop.")


# ---------------------------------------------------------------------------
# Task 5 — error recovery in the loop
# ---------------------------------------------------------------------------
def task5_error_recovery(model: ChatOllama) -> None:
    section("Task 5 — divide-by-zero is caught and fed back; model recovers")
    mt = model.bind_tools(CALC_TOOLS)
    answer = run_calc_loop(mt, "What is 10 divided by 0?")
    print("final answer:", answer)
    # The model should explain the problem rather than the program crashing.
    assert answer, "expected a final natural-language answer, not a crash"
    print("OK: the loop survived the tool error and the model explained it.")


def main() -> None:
    model = ChatOllama(model="llama3.1", num_predict=1024)
    task1_invoice(model)
    task2_word_problem(model)
    task3_no_tool(model)
    task4_classify_and_route(model)
    task5_error_recovery(model)
    print("\nAll challenge checks passed.")


if __name__ == "__main__":
    main()
