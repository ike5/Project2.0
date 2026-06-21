# Challenge 02 — Prompts & LCEL

Solutions in [`solutions/`](./solutions/). Try first — no peeking until you've attempted each
task. Put your work in one runnable script; it should `print` results you can read.
Needs a running Ollama server.

## Tasks

1. **Parameterized "explain like I'm {age}".** Build a `ChatPromptTemplate` whose system
   message takes an `age` and whose human message takes a `concept`. Compose
   `prompt | model | StrOutputParser()` and `batch` it over the **same** concept (say,
   `"how vaccines work"`) at ages `5`, `25`, and `80`. Print all three and note how the tone
   shifts.

2. **Add chat history with `MessagesPlaceholder`.** Build a prompt with a
   `MessagesPlaceholder("history")` between the system and human messages. Invoke its chain
   once with a primed history (one `HumanMessage` stating a fact about the user, one
   `AIMessage` acknowledging it) and a follow-up `input` that *depends* on that fact (e.g. the
   user said their favorite color is teal; ask "what did I say my favorite color was?").
   Confirm the answer uses the history.

3. **Two-stage chain: summarize → translate the summary.** Stage 1 summarizes a passage in
   one sentence. Stage 2 translates that summary into a target `language`. Wire them with a
   `RunnableLambda` that reshapes stage 1's string output into the dict stage 2 expects.
   Invoke on a short paragraph and print the translated summary.

4. **Fan-out with `RunnableParallel`: summary + sentiment in one call.** Build two chains over
   the same input text — one that summarizes it, one that classifies its sentiment
   (`positive`/`negative`/`neutral`). Combine them with
   `RunnableParallel(summary=..., sentiment=...)` and print the returned dict. Confirm the keys
   are exactly `summary` and `sentiment`.

5. **Batch it.** Take any one of your chains and `batch` it over a list of at least three input
   dicts. Print the list of results and confirm `len(results) == len(inputs)`.

6. **Stretch — visualize & verify parser swap.** Call `get_graph().print_ascii()` on your
   two-stage chain. Then show, with a printed example, that the *same* chain **without**
   `StrOutputParser` returns an `AIMessage` (reach `.content` for the text) while **with** it
   you get a plain `str`.

## Success criteria
- [ ] The "explain like I'm {age}" chain runs via `batch` and visibly changes tone with `age`.
- [ ] The history chain answers a question that is only answerable from the injected history.
- [ ] The two-stage chain reshapes string → dict between stages with a `RunnableLambda` and
      prints a translated summary.
- [ ] `RunnableParallel` returns a dict with exactly the keys `summary` and `sentiment`.
- [ ] A `batch` call returns a list whose length equals the number of inputs.
- [ ] You can explain why dropping `StrOutputParser` yields an `AIMessage` instead of a `str`,
      and why a chain inherits `invoke`/`stream`/`batch` for free.
