# Challenge 15 — Defend the Runtime

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Close the connection-density gap between async Channels and raw ASGI.**
   The lab measured ~45 KB/conn for async Channels and ~28 KB/conn for raw ASGI.
   Find where the 17 KB goes — measure it, don't guess — with `tracemalloc` and
   `pympler`. Then reduce it as far as you can *without leaving Channels*, and
   report how close you got to raw ASGI. State what each reduction cost.

2. **Size the `database_sync_to_async` threadpool from data.**
   The default is `min(32, cpu+4)` = 12 on the reference box. Prove it's a bounded
   resource you can exhaust: saturate it, watch handlers queue, then find the pool
   size that maximizes throughput without so many threads that context-switching
   and GIL contention make it *worse*. This is the Module 01 "concurrency is free,
   resources are not" lesson, measured.

3. **Map the sync/async/raw crossover surface.**
   Three variables: connections/worker, fan-out rate, and room size. Find the
   region where each runtime wins, and plot where Pulse actually sits today and at
   3× projected growth. Name the two independent thresholds that move the answer.

4. **Measure the debugging tax honestly.**
   Inject three identical bugs (a stall from a blocking call, a connection leak, an
   off-by-one in the resume cursor) into the sync and async consumers. Time
   locating each, with and without `PYTHONASYNCIODEBUG` and `flake8-async`. Report
   the multiplier and say what causes it.

5. **Propagate request context through an async consumer with `contextvars`.**
   `threading.local` works in a sync consumer and is *dangerous* in an async one
   (one loop, many interleaved connections — you can read another user's context).
   Wire trace-id logging through the async fan-out with `contextvars`, then break
   it the way it actually breaks (a fire-and-forget `asyncio.create_task` that
   drops the context), and add a CI test that catches it.

## Stretch

6. **Build the hybrid: async Channels for connections, a raw-ASGI fan-out worker.**
   Module 06 proved the bottleneck is fan-out, not the connection layer. Keep
   Channels for everything Channels is good at (auth, routing, lifecycle, resume)
   and move *only* the hot fan-out delivery onto a dedicated raw-ASGI/`websockets`
   process fed by Redis. Measure all three (async, raw, hybrid) past the knee and
   argue whether the hybrid earns its complexity.

## Success criteria

- [ ] The 17 KB/conn gap attributed to specific objects and reduced, with each
      reduction's cost stated and the final number compared to raw ASGI
- [ ] Threadpool saturation demonstrated and the throughput-optimal size derived,
      with the "too many threads is worse" point shown
- [ ] The three-way crossover surface mapped, Pulse located on it now and at 3×,
      and the two thresholds named
- [ ] The debugging tax measured as a multiplier for each bug, with the cause
      explained
- [ ] Trace-id context propagated through async fan-out with `contextvars`, broken
      deliberately, and caught by a CI assertion
- [ ] Stretch: the hybrid measured against both pure models past the knee, with a
      defended verdict
