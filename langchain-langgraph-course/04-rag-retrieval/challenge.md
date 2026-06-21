# Challenge 04 — RAG: Retrieval

Solutions in [`solutions/`](./solutions/). Try first — no peeking until you've attempted each
task. (Needs Ollama running; embeddings are local too.) A runnable reference is
[`solutions/challenge_solution.py`](./solutions/challenge_solution.py).

## Tasks

1. **Index your OWN small text.** Write 6–10 short factual paragraphs about *anything* you
   know that the model can't (your project's docs, a made-up product, your notes). Run it
   through the full pipeline — **load → split → embed → store → retrieve** — using the local
   `OllamaEmbeddings` and `InMemoryVectorStore`. Print the chunk count and the top-3
   chunks for a query, to confirm retrieval finds the right passage.

2. **Return the sources, not just the answer.** Build a grounded chain that returns **both**
   the answer **and** the chunks it used. Retrieve once, then fan out with `RunnableParallel`
   (or `RunnablePassthrough.assign`): one branch flattens the chunks into `{context}` for the
   prompt, the other passes the raw `Document`s straight through. The result should be a dict
   like `{"answer": "...", "context": [Document, ...]}`. Print the answer, then list the
   source snippets under it — this is how a real RAG app shows its citations.

3. **Confirm refusal outside the docs.** Ask a question whose answer is **not** in your text
   (e.g. a price you never wrote, a WiFi password). With "answer ONLY from context" in the
   system prompt, confirm the model **says it doesn't know** rather than inventing one.
   Contrast it once with a bare model (no context) on the same question — note how the bare
   model is liable to guess.

4. **Experiment with `chunk_size` / `chunk_overlap`.** Rebuild the index at a few settings
   (e.g. `chunk_size` ∈ {80, 300, 500}, vary `chunk_overlap`) and observe: the **number of
   chunks**, and whether a single fact stays **whole** in one chunk or gets **split** across
   two. Write 2–3 sentences on the tradeoff you saw — when tiny chunks hurt, when big chunks
   hurt.

5. **Stretch — two sources + metadata.** Index two different files in the same store. After a
   retrieval, print each chunk's `.metadata` (the `TextLoader` records its `source` path) so
   you can tell **which file** each retrieved chunk came from. Confirm a query about content
   in file B retrieves from file B.

## Success criteria
- [ ] Your own text is indexed through all five stages; retrieval returns the relevant
      top-k chunks for a query.
- [ ] The chain returns **both** a grounded answer **and** the source chunks it used
      (a `{"answer", "context"}` shape), and you print the sources under the answer.
- [ ] An out-of-context question yields a "don't know" refusal, not a hallucinated answer;
      you can contrast it with a bare model that guesses.
- [ ] You rebuilt the index at ≥2 `chunk_size` settings and can state, in your own words,
      what smaller vs larger chunks trade off (focus vs. keeping a fact whole).
- [ ] You can explain in one sentence why embeddings run locally here but the final answer
      step calls the API.
