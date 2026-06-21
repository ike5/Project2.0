# Challenge 06 — Agents with LangGraph

Solutions in [`solutions/`](./solutions/). Try first — no peeking until you've attempted
each task. Run everything from the `langchain-langgraph-course` folder with
your local Ollama server running.

## Tasks

1. **Build the agent graph from scratch.** Define **your own two `@tool`s** (e.g. a
   `convert_currency(amount, rate)` and a `lookup_capital(country)` with canned data). Wire a
   `StateGraph` with `messages: Annotated[list, add_messages]`, an `agent` node that calls
   `model.bind_tools(your_tools)`, a `ToolNode`, `START → agent`,
   `add_conditional_edges("agent", tools_condition)`, and `tools → agent`. Compile, then
   `print_ascii()` the graph to confirm the loop.

2. **Run it and ask a tool question.** Invoke with a question that needs one of your tools and
   print the final answer. Then invoke with a question that needs **no** tool and confirm the
   agent answers directly (the loop runs `agent → END`, no tool trip).

3. **Add memory and hold a multi-turn conversation.** Recompile the *same* builder with
   `checkpointer=InMemorySaver()`. On a single `thread_id`, run at least **three** turns where
   later turns depend on earlier ones (e.g. set a fact, use it, then ask a follow-up). Show
   the agent carries context across all turns. Then repeat the last question on a **new**
   `thread_id` and show it has no memory of the conversation.

4. **Force a 2-tool chain and watch the loop iterate twice.** Ask a question whose answer
   requires **both** tools in sequence (the output of one feeds the next, or both are needed
   for the final answer). Stream with `stream_mode="updates"` and show the agent passes
   through `tools` **twice** (two `{'tools': ...}` steps) before ending — proof the loop
   really loops.

5. **Rebuild with `create_agent`.** Recreate the *same* agent (same two tools) with the
   one-liner `create_agent(model, tools=..., checkpointer=InMemorySaver())`. Run the same
   tool question and the same multi-turn memory check, and confirm the behavior matches your
   hand-built graph.

6. **Stretch — explain termination.** In a comment or printout, explain in your own words why
   the loop in task 4 ran `tools` exactly twice and then stopped (tie it to `tools_condition`
   and the absence of `tool_calls` on the final AIMessage).

## Success criteria
- [ ] A hand-wired `StateGraph` agent with **your own** two tools compiles and its
      `print_ascii()` shows `agent`, `tools`, the conditional edge, and the `tools → agent`
      loop-back.
- [ ] A tool question returns a correct answer; a no-tool question goes straight to `END`.
- [ ] On one `thread_id`, a 3+-turn conversation carries context; a new `thread_id` starts
      fresh.
- [ ] A two-tool question makes the graph pass through `tools` **twice** (visible in the
      stream) before ending.
- [ ] The `create_agent` version reproduces the same behavior in a few lines.
- [ ] You can state, in one sentence, why the loop terminates (final AIMessage has no
      `tool_calls`, so `tools_condition` returns `END`).
