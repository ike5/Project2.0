# Challenge 03 — Choose and Defend a Transport

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Write a WebSocket frame encoder.**
   Extend `code/decode_frame.py` with an `encode(payload, opcode, mask)` function
   that produces valid frames. Prove it works by sending your hand-encoded bytes
   directly over a raw TCP socket (after performing the handshake yourself with
   `socket` + the SHA-1 computation) and getting an echo back — no WebSocket
   library allowed.

   Then encode a 200-byte payload and a 70,000-byte payload, and show the header
   is 4 and 10 bytes respectively. Explain why the 7-bit length field uses the
   sentinel values 126 and 127 rather than just always using 64 bits.

2. **Prove masking is not security.**
   Capture a masked client frame, then recover the plaintext using only the
   bytes on the wire. Write two sentences explaining what masking actually
   defends against, and why a `Sec-WebSocket-Key` provides no authentication.

3. **Build SSE-with-resume that survives a real disconnect.**
   Extend the `/transport/sse` endpoint so that:
   - it emits a keep-alive comment (`: ping`) every 15 seconds,
   - it survives the client dropping and reconnecting with `Last-Event-ID`
     without losing or duplicating a message,
   - it evicts emitters whose client vanished (prove your emitter list doesn't
     grow forever — this is a real memory leak in most SSE tutorials).

   Write a test that kills the connection mid-stream, publishes 5 messages, then
   reconnects and asserts exactly those 5 arrive, in order, once each.

4. **Measure the head-of-line blocking that WebSocket inherits from TCP.**
   Using `tc netem` on the loopback interface, add 2% packet loss. Then measure
   p99 latency for:
   - 100 small messages sent over one WebSocket connection,
   - the same 100 messages spread over 10 WebSocket connections.

   Explain the difference. Then explain which of Pulse's message types
   (chat message, typing indicator, presence, read receipt) you would move to
   QUIC **datagrams** if WebTransport were available, and — importantly — which
   ones you would not, and why.

5. **Make the transport decision, in writing.**
   Write a one-page architecture note for Pulse that:
   - recommends a primary transport and a fallback,
   - states the message-rate and room-size assumptions the recommendation
     depends on,
   - names the specific condition that would change the answer,
   - includes your measured bytes-per-message table as evidence.

   Then argue the *opposite* case in three sentences. If you can't, you don't
   understand the tradeoff yet.

6. **Stretch — measure `permessage-deflate`.**
   Enable WebSocket compression and measure its effect on (a) bytes on the wire
   and (b) CPU, for two workloads: 50-byte chat messages and 5 KB JSON payloads.
   Report the crossover point where compression starts paying for itself, and
   explain why enabling it globally on a chat server is usually wrong.

## Success criteria

- [ ] A hand-written encoder produces frames a real server accepts, with no
      WebSocket library involved
- [ ] Both extended length encodings are demonstrated and the sentinel design
      explained
- [ ] A masked frame is decoded from wire bytes alone, with the purpose of
      masking correctly stated
- [ ] SSE resume works across a real disconnect with no loss or duplication, and
      the emitter list provably doesn't leak
- [ ] Head-of-line blocking is measured under induced packet loss, with the
      1-connection vs 10-connection difference explained
- [ ] A written transport recommendation exists, with its assumptions,
      falsifying condition, and evidence — plus the counter-argument
- [ ] Stretch: the compression crossover point is measured, not guessed
