# Challenge 01 — Chat Models & Messages

Solutions in [`solutions/`](./solutions/). Try first — no peeking until you've attempted
each task. Everything here uses only what's in this module: messages, `invoke`/`stream`/
`batch`, a self-managed history list, and `usage_metadata`. Make sure your local Ollama server is running first.

## Tasks

1. **Persona bot.** Write a function `make_bot(persona: str)` that returns a callable
   `bot(question) -> str`. The persona is fixed in a `SystemMessage`; each call sends that
   system message plus the user's question. Show the *same* question answered by two
   different personas (e.g. a pirate vs. a formal butler) and print both replies.

2. **`chat(history, user_msg)`.** Write a function with signature
   `chat(history: list, user_msg: str) -> tuple[str, list]` that:
   appends a `HumanMessage(user_msg)` to `history`, invokes the model, appends the returned
   `AIMessage`, and returns `(reply_text, new_history)`. Use it to hold a 3-turn
   conversation where turn 3 depends on a fact from turn 1 — and assert the fact is recalled.

3. **Drop the history → break memory.** Reusing task 2, show the contrast: run the recall
   question *with* the full history (it remembers) and again with a **fresh** history (it
   does not). Assert the difference. Explain in a comment why.

4. **Batch vs sequential — tokens & wall-clock.** Pick 5 distinct questions. Answer them
   (a) by calling `invoke` in a Python loop and (b) with a single `model.batch(...)`. Sum
   `total_tokens` for each approach and time both with `time.perf_counter()`. Print the two
   token totals (they should be ~the same — same prompts) and the two durations (batch
   should be faster, since it runs concurrently).

5. **Usage report.** For one prompt, print a small report: `input_tokens`, `output_tokens`,
   `total_tokens`, plus `model` and `done_reason` from `response_metadata`. Then set
   `num_predict=16` on a fresh model, re-run, and show `done_reason` becomes `'length'`.

6. **Stretch — stream into a string.** Consume `model.stream(prompt)`, print each chunk
   live, *and* accumulate the chunks into one string. Assert the joined string is non-empty
   and equals what you printed.

## Success criteria
- [ ] `make_bot` produces two personas that answer the same question differently.
- [ ] `chat(history, user_msg)` returns `(reply, new_history)` and a 3-turn conversation
      recalls a fact from turn 1.
- [ ] You demonstrate (with an assert) that a fresh, history-less call cannot recall the fact.
- [ ] Batch and sequential give ~equal total tokens; batch is measurably faster.
- [ ] You can print a usage report and force `done_reason == 'length'`.
- [ ] You can explain in one sentence why the model "forgets" when you drop the history.
