# Solution 03 — notes

Run the reference: `python 03-structured-output-and-tools/solutions/challenge_solution.py`
(prints every result and asserts the checks). Needs a running Ollama server.

## Key points

1. **Invoice extraction.** Nesting is just a field whose type is another `BaseModel` (or a
   `list[...]` of one). Put `Field(description=...)` on the ambiguous fields — especially
   `total` ("sum of quantity × unit_price across items") — so the model knows to *compute* it
   rather than copy a number. Don't assert exact float equality; the model does the
   arithmetic, so compare with a tolerance (`abs(a - b) < 0.01`).

2. **The calculator loop is a `while`, not a single pass.** A word problem needs several
   steps (multiply, then subtract), and the model may request them across multiple turns. The
   robust shape is:
   ```python
   messages = [HumanMessage(question)]
   while True:
       ai = model_with_tools.invoke(messages)
       messages.append(ai)
       if not ai.tool_calls:          # model is done -> ai.content is the answer
           break
       for call in ai.tool_calls:     # could be several at once
           tool = tools_by_name[call["name"]]
           messages.append(ToolMessage(content=str(tool.invoke(call["args"])),
                                        tool_call_id=call["id"]))
   ```
   Look tools up by `call["name"]` so you can dispatch whichever one was requested.

3. **`.tool_calls` vs running the tool — the core distinction.** `model_with_tools.invoke(...)`
   returns an `AIMessage` whose `.tool_calls` is a *request* — a list of
   `{"name", "args", "id"}` dicts. **Nothing executed.** You run the tool yourself
   (`tool.invoke(call["args"])`) and report the result back. The model never touches your
   Python; it only ever asks. This is the single most-missed idea in the module.

4. **`tool_call_id` pairing.** Every `ToolMessage` must carry the `id` of the call it answers
   (`tool_call_id=call["id"]`). The model matches result → request by that id. Mismatched or
   missing ids make the conversation malformed and the provider will reject it.

5. **When no tool fires.** For chit-chat, `.tool_calls == []` and the answer is in `.content`.
   The model decided none of the bound tools applied — driven by the question *and* the tool
   docstrings (a calculator's "Add two integers" doesn't match "favorite color"). Always
   branch on `if ai.tool_calls:`; never assume one ran.

6. **Structured output vs tools — when to use which.**
   - **Structured output** = "*give me your answer as data in this shape.*" One call, one
     typed object back. Use for extraction, classification, filling a form. The model still
     does the thinking; you just constrain the *format*.
   - **Tools** = "*you may request that I run one of these functions.*" Use when the model
     needs a capability it doesn't have — live data, a database, exact computation, side
     effects. The work happens in *your* code; the model orchestrates.
   - They compose: task 4 uses structured output to **classify intent**, then routes the
     `"math"` ones into the **tool loop**. Classify, then dispatch — that's the skeleton of
     the LangGraph agent you'll build in Module 06, where the loop becomes a `ToolNode` and a
     conditional edge.

7. **Stretch — error handling.** Wrap `tool.invoke(...)` in `try/except` and, on failure,
   make the `ToolMessage` content a human-readable error string. The model reads it like any
   other result and can explain or retry — far better than letting the exception kill the
   loop.
