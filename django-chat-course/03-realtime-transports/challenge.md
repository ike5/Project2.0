# Challenge 03 — Choose and Defend a Transport

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Write a WebSocket frame encoder and a handshake from scratch.**
   Extend `code/decode_frame.py` (or write `code/ws_raw.py`) with an
   `encode(payload, opcode, mask)` function that produces valid frames. Prove it
   works by performing the handshake yourself over a raw `socket` (compute the
   `Sec-WebSocket-Accept` SHA-1 and verify the server's), then sending your
   hand-encoded bytes to `/ws-raw` and getting an echo back — **no WebSocket
   library allowed** (no `websockets`, no `websocat`, no Channels client).

   Then encode a 200-byte payload and a 70,000-byte payload, and show the header
   is 4 and 10 bytes respectively. Explain why the 7-bit length field uses the
   sentinel values 126 and 127 rather than always using 64 bits.

2. **Prove masking is not security.**
   Capture a masked client frame, then recover the plaintext using only the bytes
   on the wire. Write two sentences explaining what masking actually defends
   against, and why a `Sec-WebSocket-Key` provides no authentication.

3. **Build SSE-with-resume that survives a real disconnect — and doesn't leak.**
   Extend the `/transport/sse` view so that:
   - it emits a keep-alive comment (`: ping`) every 15 seconds (the lab already
     does this — keep it),
   - it survives the client dropping and reconnecting with `Last-Event-ID`
     without losing or duplicating a message,
   - it **removes its queue from `_WAITERS` when the client vanishes** — prove the
     set doesn't grow forever. Under ASGI, a client that disappears mid-stream
     eventually raises inside the generator; make sure your `finally` runs.

   Write an async test (`pytest-asyncio` + `httpx.AsyncClient` against the ASGI
   app) that kills the connection mid-stream, publishes 5 messages, then
   reconnects and asserts exactly those 5 arrive, in order, once each — and that
   `len(_WAITERS)` returns to its starting value.

4. **Measure the head-of-line blocking that WebSocket inherits from TCP.**
   Using `tc netem` on the loopback interface, add 2% packet loss. Then measure
   p99 latency for:
   - 100 small messages sent over one WebSocket connection,
   - the same 100 messages spread over 10 WebSocket connections.

   Explain the difference. Then explain which of Pulse's message types (chat
   message, typing indicator, presence, read receipt) you would move to QUIC
   **datagrams** if WebTransport were available on Daphne/Uvicorn — and,
   importantly, which ones you would *not*, and why. Connect your answer to the
   Pub/Sub-vs-Streams split Modules 07 and 09 build.

5. **Make the transport decision, in writing.**
   Write a one-page architecture note for Pulse that:
   - recommends a primary transport and a fallback,
   - states the message-rate and room-size assumptions the recommendation depends
     on,
   - names the specific condition that would change the answer,
   - includes your measured bytes-per-message table as evidence,
   - explicitly addresses the Django-specific constraint (ASGI required; no STOMP;
     Channels groups as the addressing primitive).

   Then argue the *opposite* case in three sentences. If you can't, you don't
   understand the tradeoff yet.

6. **Stretch — measure `permessage-deflate`.**
   Enable WebSocket compression (Uvicorn's `websockets` backend supports it) and
   measure its effect on (a) bytes on the wire and (b) CPU, for two workloads:
   50-byte chat messages and 5 KB JSON payloads. Report the crossover point where
   compression starts paying for itself, and explain why enabling it globally on a
   Python fan-out server is usually wrong — including the per-connection zlib
   context memory cost against the pinned ≈45 KB-per-connection budget.

## Success criteria

- [ ] A hand-written encoder produces frames Uvicorn accepts, with no WebSocket
      library involved, and the handshake SHA-1 is computed by your own code
- [ ] Both extended length encodings are demonstrated and the sentinel design
      explained
- [ ] A masked frame is decoded from wire bytes alone, with the purpose of
      masking correctly stated
- [ ] SSE resume works across a real disconnect with no loss or duplication, and
      `_WAITERS` provably returns to its starting size
- [ ] Head-of-line blocking is measured under induced packet loss, with the
      1-connection vs 10-connection difference explained and the datagram
      candidates justified
- [ ] A written transport recommendation exists, with its assumptions, falsifying
      condition, Django constraints, and evidence — plus the counter-argument
- [ ] Stretch: the compression crossover point is measured, not guessed, and the
      per-connection memory cost is quantified
