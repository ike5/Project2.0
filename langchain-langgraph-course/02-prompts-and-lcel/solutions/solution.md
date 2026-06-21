# Solution 02 — notes

Run the reference: `python 02-prompts-and-lcel/solutions/challenge_solution.py`
(prints results for every task; needs a running Ollama server).

## Key points

1. **"Explain like I'm {age}".** Put `{age}` in the *system* message — it steers the whole
   reply — and the `{concept}` in the human message. The magic is `batch`: one call, a list of
   dicts in, a list of strings out, run **concurrently**. You wrote no loop and no threading;
   `batch` is inherited because the chain is a Runnable.

2. **`MessagesPlaceholder`.** The placeholder name (`"history"`) becomes a required input
   variable that you fill with a **list of messages**, not a string. At call time the prompt
   splices those messages in between the system and human turns, so the model sees a real
   conversation and can answer "what did I say my favorite color was?" from it. (This is the
   manual version of memory; Module 06 makes it stateful in LangGraph.)

3. **Two-stage chain (string → dict reshaping).** Stage 1 emits a **str** (thanks to
   `StrOutputParser`), but stage 2's prompt expects a **dict** like `{"summary": ..., "language":
   ...}`. A `RunnableLambda` bridges the gap. Note the `language` value has to be threaded in —
   a clean trick is `RunnableLambda(lambda s: {"summary": s, "language": "French"})`, or use a
   parallel dict that keeps the original input around. Without the lambda, stage 2 receives a
   bare string and raises a "missing variable / expected dict" error.

4. **`RunnableParallel` (dict-in / dict-out).** Both branches receive the **same** input and
   run concurrently; the keyword names you pass (`summary=`, `sentiment=`) become the result
   dict's keys — exactly. This is *the* core composition pattern: a plain `{...}` literal inside
   a pipe is sugar for `RunnableParallel`, which is why the RAG chain in Module 04 looks like
   `{"context": retriever | format, "question": RunnablePassthrough()} | prompt | model | parser`.

5. **Batch.** `chain.batch([...])` returns results **in input order**, one per input, so
   `len(results) == len(inputs)` always holds. It runs them concurrently for you — the payoff of
   everything being a Runnable.

6. **Parser swap & visualization.** `get_graph().print_ascii()` shows the chain as a pipeline of
   boxes. Dropping `StrOutputParser` from the end means the chain's last step is the **model**,
   so its output is the model's raw output: an `AIMessage` (you'd read `.content` for the text).
   Adding the parser back makes the last step `AIMessage → str`. The lesson: a chain's output
   type is just the output type of its **last Runnable**.

## The one idea to walk away with
Everything — prompt, model, parser, lambda, the whole chain — is a **Runnable** with the same
`invoke`/`stream`/`batch` interface. That uniformity is what lets the pipe `|` compose them and
what gives you streaming and batching "for free" on anything you build.
