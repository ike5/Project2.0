# Solution 04 — notes

Run the reference: `python 04-rag-retrieval/solutions/challenge_solution.py`
(builds the index, prints grounded answers **with sources**, shows a refusal, and prints the
effect of chunk size). Needs Ollama running; embeddings run locally too.

## Key points

1. **The five stages, and where the API enters.** Load (`TextLoader`) → split
   (`RecursiveCharacterTextSplitter`) → embed (`OllamaEmbeddings`, **local**) → store
   (`InMemoryVectorStore`) → retrieve (`store.as_retriever`). Four of the five run entirely
   on your machine. The **only** API call is the final generation step — the model writing
   the answer from the retrieved context. That's why the lab's retrieval parts need no key.

2. **Why local embeddings.** The embedding model is small and free to run offline, so the
   course needs no second API key and you can re-index as much as you like at zero cost. The
   *same* model must embed both your stored chunks and each incoming query — that shared space
   is what makes "nearest vector" mean "most similar in meaning."

3. **Chunking tradeoffs.** `chunk_size` is the big knob:
   - **Too small** → a single fact gets split across two chunks, and neither chunk alone is a
     complete answer; retrieval may return half of it. (You can see this at `chunk_size=80` in
     the reference — the charge time and the sentence it belongs to can land apart.)
   - **Too large** → each chunk bundles several unrelated sentences, so the match is diluted
     and you waste prompt tokens on noise.
   - **`chunk_overlap`** is the cushion: repeating ~10–20% of characters between neighbors
     keeps a fact that straddles a boundary recoverable. `chunk_size=300, chunk_overlap=50` is
     a reasonable default for short documents; tune to your content.

4. **The grounding prompt is the safety rail.** "Answer using ONLY the context below; if it's
   not there, say you don't know" is what turns retrieved text into a *constraint*. Without
   it, the model falls back on training-memory and will confidently answer questions your docs
   don't cover. **With** it, a miss becomes an honest "I don't know" — a detectable signal,
   not a silent hallucination. Contrast the grounded chain with a bare model on the same
   out-of-context question to feel the difference.

5. **Returning sources (the citation pattern).** Users trust answers they can verify, so
   return the chunks the answer was built from. Retrieve **once**, then fan out:
   ```python
   chain = RunnableParallel(
       context=(lambda q: q) | retriever,    # raw Documents pass through
       question=RunnablePassthrough(),
   ).assign(
       answer=(                              # this branch consumes the SAME context
           RunnablePassthrough.assign(context=lambda x: format_docs(x["context"]))
           | prompt | model | StrOutputParser()
       )
   )
   chain.invoke("...")        # -> {"context": [Document, ...], "question": "...", "answer": "..."}
   ```
   The key move: retrieve once and reuse those Documents for *both* the prompt and the
   displayed sources — don't run the retriever twice (it's wasteful and the two runs could
   even differ). `format_docs` flattens them for the `{context}` slot; the raw list stays
   available for printing citations.

6. **`k` vs `chunk_size` — two different knobs.** `k` is *how many* chunks you retrieve per
   query; `chunk_size` is *how big* each chunk is. Small `k` risks missing the answer, large
   `k` floods the prompt; they interact with chunk size (smaller chunks usually want a larger
   `k` to gather a whole fact). Tune them together against real questions.

7. **Where this goes next.** This module is RAG as a straight-line **chain**: retrieve →
   answer, one pass. In the capstone you'll put retrieval *inside an agent* (Modules 05–07),
   where the model decides **when** to retrieve, can retrieve **again** after seeing results,
   and remembers across turns — retrieval as a tool in a loop, not a fixed first step.
