# Solution 06 — notes

Run the reference: `python 06-agents-with-langgraph/solutions/challenge_solution.py`
(builds a hand-wired agent with two custom tools, runs the memory + two-tool-chain checks,
then rebuilds the same agent with `create_agent`). Needs a running Ollama server.

## Key points

1. **Why the loop terminates.** The conditional edge `tools_condition` looks at the **last**
   message. If it's an `AIMessage` *with* `tool_calls`, it routes to `"tools"`; otherwise it
   returns `END`. Every pass through `ToolNode` appends `ToolMessage` results, so the model
   gets strictly more information each iteration. Once it can answer, it emits an `AIMessage`
   with **no** `tool_calls` → `tools_condition` returns `END` → the graph stops. There's no
   counter or special "done" signal; termination is *purely* "the model stopped asking for
   tools." (A bad prompt/tool can loop forever, which is why `recursion_limit` exists as a
   guardrail.)

2. **`add_messages` is what makes appending work.** The state key is
   `messages: Annotated[list, add_messages]`. Without that reducer, each node's returned
   `{"messages": [...]}` would **overwrite** the list and the conversation would reset to a
   single message every step — the model would never see the tool results, so the loop could
   never converge. The reducer appends (and de-duplicates by message `id`), which is what lets
   `Human → AI(tool_calls) → Tool → AI(answer)` accumulate.

3. **The agent node is deliberately tiny.** `return {"messages": [model.invoke(state["messages"])]}`
   — it just calls the tool-bound model on the whole history and hands back one message.
   *Requesting* a tool and *running* a tool are separate steps: the agent node only requests
   (the `AIMessage.tool_calls`); the `ToolNode` runs. That separation is exactly the manual
   split from Module 03's `tool_loop.py`, now expressed as two graph nodes.

4. **`thread_id` semantics.** The checkpointer stores a saved state **keyed by `thread_id`**.
   Passing `config={"configurable": {"thread_id": "x"}}` makes an invoke (a) reload everything
   saved under `"x"`, (b) run, (c) save the updated state back under `"x"`. Same id → continues
   the conversation; new id → fresh state. `InMemorySaver` keeps this in RAM only; a DB-backed
   checkpointer (e.g. SQLite/Postgres) uses the identical API but survives restarts.

5. **Two-tool chain → two loop iterations.** When a question needs tool B's input to come from
   tool A's output (or simply needs both before answering), the model often requests them
   across **two** turns: `agent → tools (A) → agent → tools (B) → agent → END`. Streaming with
   `stream_mode="updates"` shows two `{'tools': ...}` steps. The loop "just works" because
   after each tool result the agent re-evaluates with more context.

6. **Hand-built vs `create_agent` — tradeoffs.**
   - *Use the prebuilt* (`create_agent`) for the common ReAct case: model + tools + loop
     (+ optional memory) with no custom logic. Less code, fewer bugs.
   - *Build by hand* (`StateGraph`) when you need things the prebuilt loop doesn't give you:
     extra nodes (validation, retrieval, formatting), additional conditional branches, a
     human-in-the-loop pause/resume, custom state beyond `messages`, or precise control over
     ordering. The capstone (Module 07) hand-builds so it can slot a RAG retrieval step into
     the loop. Both produce a compiled graph you `invoke`/`stream` the same way — so you can
     prototype with the one-liner and graduate to a custom graph without changing callers.
