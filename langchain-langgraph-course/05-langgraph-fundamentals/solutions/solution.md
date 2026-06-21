# Solution 05 — notes

Run the reference: `python 05-langgraph-fundamentals/solutions/challenge_solution.py`
(prints results and asserts every check; the model task needs your local Ollama server
running).

## Key points

1. **Partial updates.** A node returns *only the keys it changes*. LangGraph merges that
   delta into the state; untouched keys are preserved. You never rebuild the whole dict, and
   you never `return state` — return the slice you wrote.

2. **Overwrite vs reducer.** Without a reducer, a returned key **replaces** the old value
   (last writer wins) — that's why the no-reducer log collapses to `["third"]`.
   `Annotated[list, add]` attaches `operator.add` as the **reducer**, so each node's list is
   *concatenated* onto the running value → `["first", "second", "third"]`. A reducer is just
   "how to combine old + new" for that key.

3. **`add_messages`.** The chat reducer appends new messages and updates in place when a
   message shares an `id` (handy for streaming). State `messages: Annotated[list, add_messages]`
   is the standard agent state — a node returns `{"messages": [reply]}` and history grows.

4. **START / END.** `START` and `END` are sentinels, not nodes you define. `add_edge(START, x)`
   sets the entry point; `add_edge(y, END)` is a terminus. A graph with no path to `END`
   never finishes.

5. **Routers return NODE NAMES.** A conditional-edge function returns a **string naming the
   next node** (or the `END` sentinel) — it does not return state and does no work. The
   string must match a node you registered with `add_node`. The optional `{name: name}` map
   pins the legal targets and makes `print_ascii()` draw every branch.

6. **Loops need a guard.** A loop is a node plus a conditional edge pointing back to it. The
   **counter** is the termination guard: route back while `count < N`, else `END`. Without a
   guard you'd loop forever — LangGraph's `recursion_limit` (default 25) then raises instead
   of hanging, which is your signal that a stop condition is missing.

## Common mistakes

- **Returning the whole state** (`return state`) instead of a partial update. It "works" but
  fights the reducer model and overwrites reducer'd keys with their old value.
- **Forgetting an edge** — most often no `add_edge(START, ...)` (nothing runs) or no edge to
  `END` (the graph can't terminate).
- **A router that returns a *value* instead of a node name**, or a name you never registered
  → LangGraph can't find the next node.
- **Expecting a reducer'd key to append without the `Annotated[..., add]`** — by default it
  overwrites. The annotation is the whole difference.
- **Mutating the incoming state in place** (e.g. `state["log"].append(...)`) instead of
  returning a new partial update. Return the delta; let the reducer merge it.
