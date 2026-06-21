# Solution 01 — notes

Run the reference: `python 01-chat-models-messages/solutions/challenge_solution.py`
(prints results and asserts the checks that don't depend on the model's exact wording).
Needs a running Ollama server.

## Key points

1. **Persona bot.** The persona is a `SystemMessage`; the user's text is a `HumanMessage`.
   A closure is the clean way to "bake in" the persona: `make_bot` captures `persona` and
   returns `bot(question)` that builds `[SystemMessage(persona), HumanMessage(question)]`
   fresh each call. Same human question + different system message ⇒ different answer, which
   is the whole point of system prompts.

2. **`chat(history, user_msg)`.** The function must do three things in order: append the
   `HumanMessage`, `invoke` the *whole* history, append the returned `AIMessage`. Returning
   `(reply, new_history)` keeps the caller in control of state — that's the LangChain mental
   model: **you** own the conversation list, the model is stateless. We mutate-and-return the
   same list here; returning a copy is also fine if you want immutability.

3. **Drop the history → break memory.** With the full history re-sent, the fact (a codeword)
   is literally present in the messages, so the model repeats it. With a fresh `history`, the
   recall question stands alone — nothing to recall. This isn't forgetting; the model never
   had server-side state. The only "memory" is the list you choose to re-send.

4. **Batch vs sequential.** `model.batch(qs)` fires the requests concurrently, so wall-clock
   time is roughly the *slowest* single call rather than the *sum* — a clear speedup for
   independent inputs. Total **tokens** are about the same either way, because token cost is
   per-prompt and the prompts are identical; concurrency saves time, not tokens. (Exact token
   counts can wobble by a few if the model's replies differ slightly in length.)

5. **Usage report.** `usage_metadata` is the portable token dict
   (`input_tokens`/`output_tokens`/`total_tokens`). `response_metadata` holds provider
   details like `model` and `done_reason`. A normal completion ends with
   `done_reason == 'stop'`; capping `num_predict` very low truncates the reply and you get
   `done_reason == 'length'` — the signal that the model was cut off, not finished.

6. **Stream into a string.** Each streamed chunk is a message chunk with `.content`; you can
   both print it live (`end="", flush=True`) and append it to a list, then `"".join(...)` to
   recover the full text. Streaming changes *how* you receive the reply, not *what* it is.

## Common pitfalls
- **Forgetting to append the `AIMessage`.** The next turn then loses the model's own prior
  statements — a subtle memory bug. Always append both sides.
- **Re-using a list across `make_bot` calls.** Build the message list fresh inside `bot` so
  personas don't leak into each other.
- **Expecting batch to cut tokens.** It cuts latency, not token cost.
- **Hardcoding an exact reply string in an assert.** Models vary wording; assert on a
  substring (e.g. the codeword) or a structural fact, not the whole sentence.
