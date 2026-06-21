# Challenge 03 — Structured Output & Tools

Solutions in [`solutions/`](./solutions/). Try first — no peeking until you've attempted each
task. (Needs a running Ollama server.) A runnable reference is
[`solutions/challenge_solution.py`](./solutions/challenge_solution.py).

## Tasks

1. **Extract a structured Invoice (nested line items).** Define two Pydantic models —
   `LineItem(description: str, quantity: int, unit_price: float)` and
   `Invoice(vendor: str, items: list[LineItem], total: float)` — and extract them from a
   sentence like:
   *"Invoice from Acme Corp: 3 widgets at $4.50 each, and 2 gadgets at $12.00 each."*
   Print the vendor, each line item, and assert the `total` is the sum of `quantity ×
   unit_price` across items (to a small tolerance — the model computes it).

2. **A calculator tool set + a loop that answers a word problem.** Define `@tool`s for
   `add`, `subtract`, `multiply`, and `divide`. Bind them, and run the full manual loop on a
   word problem such as *"I bought 3 packs of 8 pencils and gave away 5. How many are left?"*
   Handle **multiple and possibly sequential** tool calls: keep looping
   (`invoke → run tools → append ToolMessage`) until `.tool_calls` comes back empty, then
   print the final answer. Confirm it equals 19.

3. **A tool the model should NOT call.** Bind your calculator tools, then ask a pure
   chit-chat question (*"What's your favorite color?"*). Verify `.tool_calls == []` and that
   the model answers in `.content`. Write one sentence on *why* — what in the request (or the
   tool docstrings) told the model no tool applied.

4. **Combine: structured output to classify intent.** Define
   `Intent(category: Literal["math", "weather", "chitchat"], confidence: float)` and use
   `with_structured_output` to classify several user messages. Then branch on the result: for
   `"math"` route into the calculator loop from task 2; otherwise just answer. (This is the
   pattern a real router/agent uses — classify, then dispatch.)

5. **Stretch — robustness.** Make one tool raise on bad input (e.g. `divide` by zero). In
   your loop, catch the error and feed a useful message back as the `ToolMessage` content;
   confirm the model recovers and explains the problem instead of crashing.

## Success criteria
- [ ] `Invoice` extracts with a populated `list[LineItem]`; `total` matches the summed line
      items within tolerance.
- [ ] The calculator loop solves the word problem (= 19), correctly handling more than one
      tool call and re-invoking until `.tool_calls` is empty.
- [ ] The chit-chat question yields `.tool_calls == []` and a normal `.content` answer; you
      can explain in one sentence why no tool fired.
- [ ] `Intent` classification returns one of the allowed `Literal` categories with a
      confidence, and you route on it (math → loop, else → answer).
- [ ] You can state the distinction: **structured output = "give me data in this shape";
      tools = "the model may request that I run a function" — and the model never runs it
      itself.**
