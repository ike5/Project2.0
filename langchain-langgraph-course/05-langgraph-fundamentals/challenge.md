# Challenge 05 — LangGraph Fundamentals

Build the graphs from scratch. Solutions in [`solutions/`](./solutions/) — try first, no
peeking until you've attempted each task. One runnable reference covers them all:
`python 05-langgraph-fundamentals/solutions/challenge_solution.py`.

## Tasks

1. **Reducer-accumulated log.** Define a `State` with a key `log: Annotated[list, add]`.
   Build a graph `START → first → second → third → END` where each node appends one string
   (e.g. `{"log": ["first"]}`). Invoke from `{"log": []}` and confirm the final log is
   `["first", "second", "third"]` — all three, in order. Then remove the reducer and show it
   collapses to `["third"]`.

2. **Loop a fixed number of times, accumulating.** Build a graph that loops exactly `N`
   times (use `N = 5`). A `work` node increments a `count` and appends `count` to a
   reducer'd `results` list; a router edges back to `work` while `count < N`, else to `END`.
   Invoke from `{"count": 0, "results": []}` and confirm `count == 5` and
   `results == [1, 2, 3, 4, 5]`. Stream it and observe each per-node update.

3. **Conditional edge to one of two terminal nodes.** Build a graph that, from `START`,
   routes on a `category` field: `"q"` → a `handle_question` node, `"c"` → a
   `handle_command` node. Each terminal node writes a distinct `answer` into state, then
   edges to `END`. Test both categories and confirm the right node ran (assert on `answer`).

4. **Stretch — a node that calls the model.** Add a `State` with
   `messages: Annotated[list, add_messages]` and a single node that calls
   `ChatOllama(model="llama3.1", num_predict=512)` on `state["messages"]` and
   returns `{"messages": [reply]}`. Invoke with one `HumanMessage` and print the conversation
   — confirm both the human message and the model's `AIMessage` are present (the reducer
   appended the reply). Requires a running local Ollama server.

## Success criteria
- [ ] Task 1: the reducer'd log is `["first", "second", "third"]`; without the reducer it's
      `["third"]`, and you can explain the difference in one sentence.
- [ ] Task 2: the loop terminates at `count == 5` with `results == [1, 2, 3, 4, 5]`; the
      counter is what guarantees it stops.
- [ ] Task 3: each category routes to its own terminal node and writes the expected `answer`
      (verified by assertion).
- [ ] Every graph compiles and `invoke`/`stream` runs without error; routers return node
      **names** (or `END`), and nodes return **partial** updates.
- [ ] Stretch (if attempted): both the human and AI messages appear in the final state.
