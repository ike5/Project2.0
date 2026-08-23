# Solutions — Module 03

---

## Task 1 — A frame encoder, and a handshake from scratch

`code/ws_raw.py`:

```python
#!/usr/bin/env python3
"""A minimal WebSocket client: handshake + frame codec, no libraries."""
import base64, hashlib, os, socket, struct, sys

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def encode(payload: bytes, opcode: int = 0x1, mask: bool = True) -> bytes:
    frame = bytearray()
    frame.append(0x80 | opcode)                       # FIN=1

    n = len(payload)
    mask_bit = 0x80 if mask else 0x00
    if n < 126:
        frame.append(mask_bit | n)
    elif n < 65536:
        frame.append(mask_bit | 126)
        frame += struct.pack(">H", n)                 # 16-bit
    else:
        frame.append(mask_bit | 127)
        frame += struct.pack(">Q", n)                 # 64-bit

    if mask:
        key = os.urandom(4)
        frame += key
        frame += bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    else:
        frame += payload
    return bytes(frame)

def handshake(sock, host, path):
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f"GET {path} HTTP/1.1\r\n"
           f"Host: {host}\r\n"
           f"Upgrade: websocket\r\n"
           f"Connection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\n"
           f"Sec-WebSocket-Version: 13\r\n\r\n")
    sock.sendall(req.encode())

    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += sock.recv(4096)
    head = resp.split(b"\r\n\r\n")[0].decode()
    assert "101" in head.split("\r\n")[0], head

    expected = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    got = [l.split(": ", 1)[1] for l in head.split("\r\n")
           if l.lower().startswith("sec-websocket-accept")][0]
    assert got == expected, f"accept mismatch: {got} != {expected}"
    print(f"handshake OK  key={key}  accept={got}")
    return resp.split(b"\r\n\r\n", 1)[1]

def read_frame(sock, buffered=b""):
    def need(n, buf):
        while len(buf) < n:
            buf += sock.recv(4096)
        return buf
    buf = need(2, buffered)
    length = buf[1] & 0x7F
    i = 2
    if length == 126:
        buf = need(4, buf); length = struct.unpack(">H", buf[2:4])[0]; i = 4
    elif length == 127:
        buf = need(10, buf); length = struct.unpack(">Q", buf[2:10])[0]; i = 10
    buf = need(i + length, buf)
    return buf[i:i+length], buf[i+length:]

if __name__ == "__main__":
    s = socket.create_connection(("localhost", 8080))
    rest = handshake(s, "localhost:8080", "/ws-raw")
    payload, rest = read_frame(s, rest)
    print("server said:", payload.decode())

    for size in (2, 200, 70000):
        body = b"x" * size
        frame = encode(body)
        header_len = len(frame) - size - 4       # minus the 4-byte mask key
        print(f"payload={size:6d}  header={header_len} bytes  first_bytes={frame[:4].hex()}")

    s.sendall(encode(b"hello from raw python"))
    payload, rest = read_frame(s, rest)
    print("echo:", payload.decode())
    s.sendall(encode(b"", opcode=0x8))           # close
    s.close()
```

```bash
python3 code/ws_raw.py
```

**Expected:**
```
handshake OK  key=x3JJHMbDL1EzLkh9GBhXDw==  accept=HSmrc0sMlYUkAGmm5OPpG2HaGWk=
server said: welcome 7c2f8a11
payload=     2  header=2 bytes  first_bytes=81823f9c
payload=   200  header=4 bytes  first_bytes=81fe00c8
payload= 70000  header=10 bytes first_bytes=81ff0000
echo: hello from raw python
```

✅ Header is 2, 4, and 10 bytes as designed.

### Why sentinels 126/127 instead of always 64-bit

The 7-bit field can express 0–127 directly. Reserving the top two values as
escape hatches means:

- **The overwhelmingly common case costs nothing.** Chat messages, control
  frames, and heartbeats are all under 126 bytes, so they use a 2-byte header. If
  the length were always 64-bit, every frame would carry a 10-byte header — and
  8 of those 10 bytes would be zeros.
- For a 50-byte chat message, always-64-bit would mean **10 bytes of header for
  50 bytes of payload (20% overhead)** instead of 2 bytes (4%).
- The escape values are chosen so the encoding stays **self-describing and
  unambiguous**: you always know from byte 1 exactly how many more length bytes
  to read, with no lookahead.

This is the same variable-length-integer idea as UTF-8 or Protobuf varints:
optimize the common case, pay only when you need the range.

> The RFC also requires the 64-bit form's high bit be 0 (max 2⁶³−1) so the length
> can't be misread as negative in languages with signed 64-bit integers. A small
> detail that has prevented a large number of buffer bugs.

---

## Task 2 — Masking is not security

```bash
# capture a client frame
sudo tcpdump -i lo -s0 -X 'tcp port 8080 and greater 60' -c 5
```

Given wire bytes `81 82 37 fa 21 3d 5f 93`:

```python
masked  = bytes.fromhex("5f93")
key     = bytes.fromhex("37fa213d")
plain   = bytes(b ^ key[i % 4] for i, b in enumerate(masked))
print(plain)      # b'hi'
```

**Expected:** `b'hi'` — recovered using only bytes that were on the wire.

**Two sentences:**

> Masking defends transparent intermediaries — proxies and caches that don't
> understand WebSocket — against **cache poisoning**: without an unpredictable
> per-frame XOR, an attacker could craft a payload that a naive proxy parses as a
> second, valid HTTP request and caches under an attacker-chosen URL. It provides
> no confidentiality whatsoever because the key travels in the same frame, in the
> clear, four bytes before the data it masks.

**And `Sec-WebSocket-Key`:**

> It's a random nonce, not a credential — the server's response is a
> deterministic SHA-1 of it plus a public constant, computable by anyone. It
> proves the responder implements RFC 6455 (rather than being a cache replaying a
> stored response), and nothing more. Authentication has to come from a cookie,
> a token, or a `Sec-WebSocket-Protocol` value — Module 21.

---

## Task 3 — SSE with resume, keep-alives, and no leak

```java
@RestController
@RequestMapping("/transport")
public class ResilientSseController {

    record Msg(long id, String body, long ts) {}

    private final List<Msg> log = new CopyOnWriteArrayList<>();
    private final AtomicLong seq = new AtomicLong();
    private final Map<SseEmitter, Long> emitters = new ConcurrentHashMap<>();
    private final ScheduledExecutorService keepAlive =
            Executors.newSingleThreadScheduledExecutor(r -> Thread.ofVirtual().unstarted(r));

    @PostConstruct
    void startKeepAlive() {
        keepAlive.scheduleAtFixedRate(this::ping, 15, 15, TimeUnit.SECONDS);
    }

    @PreDestroy
    void stop() { keepAlive.shutdownNow(); }

    /**
     * The keep-alive doubles as the leak detector: an emitter whose client has
     * vanished throws on send, and that is the ONLY reliable signal we get.
     * onCompletion/onTimeout do not fire for a client that was NAT-evicted.
     */
    private void ping() {
        emitters.keySet().forEach(e -> {
            try {
                e.send(SseEmitter.event().comment("ping"));
            } catch (Exception ex) {
                emitters.remove(e);
                e.completeWithError(ex);
            }
        });
    }

    @GetMapping(value = "/sse", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter sse(@RequestHeader(value = "Last-Event-ID", required = false) String lastId) {
        var emitter = new SseEmitter(0L);
        long since = lastId == null ? 0L : Long.parseLong(lastId);

        emitter.onCompletion(() -> emitters.remove(emitter));
        emitter.onTimeout(()    -> { emitters.remove(emitter); emitter.complete(); });
        emitter.onError(t       -> emitters.remove(emitter));

        // Replay BEFORE registering, so a message published during replay is not
        // delivered twice (once by replay, once by the live push).
        try {
            for (Msg m : log) {
                if (m.id() > since) emitter.send(event(m));
                since = Math.max(since, m.id());
            }
        } catch (IOException e) {
            emitter.completeWithError(e);
            return emitter;
        }
        emitters.put(emitter, since);
        return emitter;
    }

    @PostMapping("/publish")
    public Msg publish(@RequestBody String body) {
        var m = new Msg(seq.incrementAndGet(), body.trim(), System.currentTimeMillis());
        log.add(m);
        emitters.forEach((e, lastSent) -> {
            try { e.send(event(m)); emitters.put(e, m.id()); }
            catch (Exception ex) { emitters.remove(e); }
        });
        return m;
    }

    int emitterCount() { return emitters.size(); }

    private static SseEmitter.SseEventBuilder event(Msg m) {
        return SseEmitter.event().id(String.valueOf(m.id())).name("message").data(m);
    }
}
```

### The two subtle bugs this avoids

**1. The replay/live race.** Registering the emitter *before* replaying means a
message published mid-replay is sent twice. Replaying first, then registering,
means it's sent once — by the replay loop if it made it into `log`, or by the
live push if it didn't. `CopyOnWriteArrayList`'s snapshot iteration makes the
boundary well-defined.

**2. The leak.** `onCompletion`/`onTimeout` do **not** fire when a client is
NAT-evicted or its laptop is closed — the server never learns. The emitter sits
in the map forever holding a request thread and its buffers. The only reliable
detection is *attempting a write and failing*, which is exactly what the 15-second
keep-alive does. **The keep-alive is not politeness; it's garbage collection.**

### The test

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
class SseResumeTest {

    @LocalServerPort int port;
    @Autowired ResilientSseController controller;

    @Test
    void resumesWithoutLossOrDuplication() throws Exception {
        var client = HttpClient.newHttpClient();
        var received = new CopyOnWriteArrayList<Long>();

        // 1. connect, receive one message, then hard-kill the connection
        publish("before");
        var first = openStream(client, null, received, 1);
        first.cancel(true);
        Thread.sleep(200);

        // 2. publish 5 while disconnected
        for (int i = 1; i <= 5; i++) publish("during-" + i);

        // 3. reconnect with Last-Event-ID
        long lastSeen = received.get(received.size() - 1);
        var second = openStream(client, String.valueOf(lastSeen), received, 5);
        second.get(5, TimeUnit.SECONDS);

        var afterResume = received.subList(1, received.size());
        assertEquals(List.of(2L, 3L, 4L, 5L, 6L), afterResume, "lost or duplicated");
        assertEquals(afterResume.size(), Set.copyOf(afterResume).size(), "duplicates");
    }

    @Test
    void emittersDoNotLeak() throws Exception {
        int before = controller.emitterCount();
        for (int i = 0; i < 50; i++) {
            var c = HttpClient.newHttpClient();
            openStream(c, null, new CopyOnWriteArrayList<>(), 0).cancel(true);
        }
        // force a keep-alive sweep
        Thread.sleep(16_000);
        assertEquals(before, controller.emitterCount(), "emitter leak");
    }
}
```

**Expected:**
```
SseResumeTest > resumesWithoutLossOrDuplication() PASSED
SseResumeTest > emittersDoNotLeak() PASSED
```

Removing the keep-alive makes the second test fail with `expected: <0> but was:
<50>` — the leak, demonstrated.

---

## Task 4 — Head-of-line blocking

```bash
sudo tc qdisc add dev lo root netem loss 2%
```

Reference results, 100 × 100-byte messages:

| Setup | p50 | p99 | max |
|-------|-----|-----|-----|
| No loss, 1 connection | 0.4 ms | 1.1 ms | 2 ms |
| **2% loss, 1 connection** | 0.5 ms | **214 ms** | 431 ms |
| **2% loss, 10 connections** | 0.5 ms | **28 ms** | 218 ms |

```bash
sudo tc qdisc del dev lo root
```

### Why

TCP guarantees **in-order delivery of a byte stream**. When a segment is lost,
the receiver's kernel has already got the bytes that came after it, but it
**cannot hand them to the application** — that would violate ordering. Everything
waits for the retransmission, which takes at least one RTO (~200 ms minimum on
Linux, `TCP_RTO_MIN`).

That's the 214 ms p99: not network latency, but *one* lost packet blocking every
message queued behind it.

Spreading across 10 connections means a loss only stalls the ~10% of messages on
that connection, so the aggregate p99 drops roughly 8×. But 10 connections costs
10× the handshakes, 10× the server-side state, and you've now got **no ordering
guarantee across connections** — which for chat is a correctness problem, not
just a cost.

**This is exactly what QUIC solves:** independent streams over one connection,
each with its own ordering, so a loss on one doesn't block the others.

### Which Pulse traffic belongs on datagrams

| Message type | Datagram? | Why |
|--------------|-----------|-----|
| **Typing indicator** | ✅ **Yes** | Superseded every ~2 s. A lost one is invisible. Retransmitting a stale "alice is typing" is actively *worse* than dropping it. |
| **Presence heartbeat** | ✅ **Yes** | Same logic — it's a TTL refresh; the next one is 15 s away and TTL is 45 s, so you tolerate two losses. |
| **Cursor position / scroll sync** | ✅ Yes | Latest value wins. |
| **Chat message** | ❌ **No** | Must not be lost, must be ordered. This is precisely what reliable streams are for. |
| **Read receipt** | ❌ No — but nearly | Idempotent and monotonic (a receipt for message 50 subsumes one for 40), so a loss self-heals on the next receipt. Still, they're rare and small; there's no throughput argument for datagrams, so use a stream and keep it simple. |
| **Message ack** | ❌ No | Losing an ack triggers a client retry, which costs a duplicate and a dedup-cache hit. Cheap but pointless. |

**The general rule:** a message belongs on a datagram when it is **state-latest
rather than event-log** — where the next update makes the lost one irrelevant. If
losing it leaves a permanent hole in the user's history, it needs a reliable
stream.

Practical note: today you get most of this benefit by simply *not* sending typing
indicators through the same ordering guarantees as messages — e.g. Redis Pub/Sub
for typing (at-most-once, Module 07) and Streams for messages (at-least-once,
Module 09). **You don't need QUIC to apply the insight**, and that's the useful
takeaway.

---

## Task 5 — The architecture note

> ### Pulse transport recommendation
>
> **Primary: WebSocket with STOMP. Fallback: SSE (down) + POST (up).**
>
> **Assumptions this rests on:**
> - Average room size 50–500 members; p95 room size under 5,000.
> - Steady-state 1 message per user per 60 s, bursting 10×.
> - Bidirectional chatter is significant: typing indicators, read receipts, and
>   per-message acks mean the client→server channel is not idle.
> - Clients are primarily browsers and mobile web on networks we don't control.
>
> **Evidence** (measured, Lab 03 Part D, 10 messages over 20 s):
>
> | Transport | Bytes/msg | Overhead/frame |
> |-----------|-----------|----------------|
> | Polling (1 s) | 6,843 | ~500 B headers |
> | SSE | 921 | ~10 B |
> | WebSocket | 610 | **2 B down / 6 B up** |
>
> **Why WebSocket over SSE:** with acks, typing, and receipts, an SSE design
> needs a POST per upstream event — at ~500 bytes of headers each, upstream
> chatter costs more than the entire downstream stream. WebSocket's 6-byte
> upstream frame removes that.
>
> **What would change the answer:**
> - If upstream traffic dropped to only chat sends (no typing, no per-message
>   acks), **SSE + POST wins** on operational simplicity: free reconnect, free
>   resume via `Last-Event-ID`, no proxy configuration, HTTP/2 multiplexing.
> - If we had to run behind customer-controlled corporate proxies that strip
>   `Upgrade`, SSE becomes primary, not fallback.
> - If average room size fell below ~10 and message rates were minutes apart,
>   **long polling would be adequate** and would eliminate all connection-state
>   complexity — which would delete Phases 2 and 5 of this design.
>
> **Not chosen: SockJS.** Its three-transport fallback matrix triples the
> integration test surface to support browsers that no longer exist. Plain SSE is
> a simpler, better fallback.

### The counter-argument, in three sentences

> SSE + POST would have been the better choice: it gets automatic reconnection
> and a standardized resume cursor for free, where WebSocket makes us hand-build
> both (Modules 10 and 17), and it works through every proxy on earth without
> configuration. The upstream POST overhead we cited is real but mostly
> theoretical — typing indicators can be debounced to one POST per 3 seconds and
> per-message acks can be batched, which collapses the upstream rate by an order
> of magnitude. We are, in effect, spending two modules of engineering to avoid a
> problem that a 3-second debounce would have solved.

---

## Task 6 (stretch) — `permessage-deflate`

Enable it:
```java
// Tomcat: the WsServerContainer negotiates permessage-deflate when the client offers it
@Bean
public ServletServerContainerFactoryBean wsContainer() {
    var c = new ServletServerContainerFactoryBean();
    c.setMaxTextMessageBufferSize(65536);
    return c;
}
```

Reference results:

| Payload | Raw bytes | Compressed | Ratio | CPU (server) |
|---------|-----------|-----------|-------|--------------|
| 50 B chat message | 52 | **61** | **1.17× (BIGGER)** | +38% |
| 500 B message w/ metadata | 502 | 310 | 0.62× | +31% |
| 5 KB JSON payload | 5,004 | 780 | **0.16×** | +22% |
| 50 KB history page | 50,004 | 4,120 | 0.08× | +19% |

**Crossover: ~200–300 bytes.** Below that, DEFLATE's block headers and the
dictionary reset cost more than the compression saves.

### Why enabling it globally on a chat server is usually wrong

1. **Typical chat messages are below the crossover.** A 50-byte message gets
   *bigger*, and you paid CPU for the privilege.
2. **CPU is the scarce resource in a fan-out server, not bandwidth.** One inbound
   message compressed once and broadcast to 500 people is fine — but Tomcat's
   implementation compresses **per connection**, so you compress the same payload
   500 times. That's the number that kills you.
3. **Memory.** Each connection with `permessage-deflate` and no
   `client_no_context_takeover` holds a zlib dictionary — roughly **32 KB per
   connection** by default. At 50,000 connections that's **1.6 GB** of off-heap
   memory doing nothing for your 50-byte messages.
4. **CRIME/BREACH-class concerns.** Compressing attacker-influenced content
   alongside secrets in the same stream can leak the secrets through size. Less
   acute for WebSocket than HTTPS, but not zero.

**What to do instead:**

- Enable compression **selectively** for large frames only — history pages, file
  metadata, initial room sync — and leave live messages uncompressed. Some
  servers let you set a size threshold; if yours doesn't, compress at the
  application layer and mark it with a header in your envelope (Module 05).
- Set `server_no_context_takeover` / `client_no_context_takeover` if you do
  enable it, trading ratio for a bounded per-connection memory cost.
- Shorten your JSON field names first. Renaming `"messageId"` to `"i"` across a
  chat envelope typically saves 30–40% with **zero** CPU cost, and Module 05's
  envelope design does exactly this.

> This is a good example of the course's recurring theme: the interesting
> question is never "is compression good?" but "what is scarce here?" On a
> fan-out server, CPU and per-connection memory are scarce and bandwidth usually
> isn't — so the default answer inverts.
