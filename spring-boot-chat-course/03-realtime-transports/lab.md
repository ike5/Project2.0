# Lab 03 — Speak the Protocols by Hand

**You'll:** perform a WebSocket handshake with `curl`, decode raw frames byte by
byte, build all four transports in Pulse, measure real bytes-on-the-wire, and
watch an nginx timeout silently kill a connection.

⏱️ ~90 min. Work in `spring-boot-chat-course/apps/pulse`.

---

## Part A — The handshake, by hand

```bash
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8080/ws
```

You don't have a `/ws` endpoint yet — that's Module 04 — so expect a 404. First
add a bare one so this lab has something to talk to.

`src/main/java/com/pulse/transport/EchoWebSocketConfig.java`:

```java
package com.pulse.transport;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.*;
import org.springframework.web.socket.config.annotation.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

@Configuration
@EnableWebSocket
public class EchoWebSocketConfig implements WebSocketConfigurer {

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(new EchoHandler(), "/ws-raw").setAllowedOrigins("*");
    }

    static class EchoHandler extends TextWebSocketHandler {
        @Override
        public void afterConnectionEstablished(WebSocketSession session) throws Exception {
            session.sendMessage(new TextMessage("welcome " + session.getId()));
        }

        @Override
        protected void handleTextMessage(WebSocketSession session, TextMessage m) throws Exception {
            session.sendMessage(new TextMessage("echo: " + m.getPayload()));
        }
    }
}
```

> ⚠️ `setAllowedOrigins("*")` is for this lab only. Module 21 explains why it's a
> Cross-Site WebSocket Hijacking hole in production.

Restart, then:

```bash
curl -i -N \
  -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8080/ws-raw
```

**Expected:**
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

✅ Verify that `Sec-WebSocket-Accept` yourself — this is the whole handshake
proof, and computing it once makes it permanently unmysterious:

```bash
printf 'dGhlIHNhbXBsZSBub25jZQ==258EAFA5-E914-47DA-95CA-C5AB0DC85B11' \
  | openssl dgst -binary -sha1 | base64
```
**Expected:**
```
s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

Identical. Now break it — change one character of the key and watch the accept
value change completely:

```bash
printf 'XGhlIHNhbXBsZSBub25jZQ==258EAFA5-E914-47DA-95CA-C5AB0DC85B11' \
  | openssl dgst -binary -sha1 | base64
```
**Expected:** a totally different string. A browser receiving that would abort
the connection.

---

## Part B — Decode raw frames

Capture the actual bytes. In one terminal:

```bash
websocat -v ws://localhost:8080/ws-raw
```
Type `hi` and press Enter.

**Expected:**
```
[INFO  websocat::ws_client_peer] get_ws_client_peer
[INFO  websocat::ws_client_peer] Connected to ws
welcome 0f3a91c2
hi
echo: hi
```

Now see the bytes. Use `tcpdump` (or Wireshark if you prefer a GUI):

```bash
sudo tcpdump -i lo -s0 -X 'tcp port 8080' -c 40 2>/dev/null | grep -A3 -B1 'echo'
```

**Expected** (excerpt — the server→client frame for `echo: hi`):
```
0x0000:  4500 0039 ... 
0x0030:  8108 6563 686f 3a20 6869
         │ │  └──────────────────┴── payload: "echo: hi"  (8 bytes)
         │ └── 0x08 = MASK 0, length 8
         └── 0x81 = FIN 1, opcode 0x1 (text)
```

Decode it yourself with a script. `code/decode_frame.py`:

```python
#!/usr/bin/env python3
"""Decode a WebSocket frame given as hex. Usage: decode_frame.py 8108656368...  """
import sys

OPCODES = {0x0: "continuation", 0x1: "text", 0x2: "binary",
           0x8: "close", 0x9: "ping", 0xA: "pong"}

data = bytes.fromhex(sys.argv[1].replace(" ", ""))
b0, b1 = data[0], data[1]

fin    = (b0 & 0b10000000) >> 7
rsv    = (b0 & 0b01110000) >> 4
opcode =  b0 & 0b00001111
masked = (b1 & 0b10000000) >> 7
length =  b1 & 0b01111111

i = 2
if length == 126:
    length = int.from_bytes(data[2:4], "big"); i = 4
elif length == 127:
    length = int.from_bytes(data[2:10], "big"); i = 10

key = b""
if masked:
    key = data[i:i+4]; i += 4

payload = data[i:i+length]
if masked:
    payload = bytes(b ^ key[j % 4] for j, b in enumerate(payload))

print(f"FIN      : {fin}")
print(f"RSV      : {rsv:03b}   (nonzero means an extension like permessage-deflate)")
print(f"opcode   : 0x{opcode:x} ({OPCODES.get(opcode, '?')})")
print(f"MASK     : {masked}" + (f"  key={key.hex()}" if masked else ""))
print(f"length   : {length}")
print(f"overhead : {i} bytes for {length} bytes of payload")
print(f"payload  : {payload!r}")
```

```bash
chmod +x code/decode_frame.py
./code/decode_frame.py 8108 6563 686f 3a20 6869
```

**Expected:**
```
FIN      : 1
RSV      : 000   (nonzero means an extension like permessage-deflate)
opcode   : 0x1 (text)
MASK     : 0
length   : 8
overhead : 2 bytes for 8 bytes of payload
payload  : b'echo: hi'
```

Now a **masked client frame**:

```bash
./code/decode_frame.py 8182 37fa 213d 5f93
```

**Expected:**
```
FIN      : 1
opcode   : 0x1 (text)
MASK     : 1  key=37fa213d
length   : 2
overhead : 6 bytes for 2 bytes of payload
payload  : b'hi'
```

✅ **6 bytes of overhead to send 2 bytes.** Note the asymmetry: server→client
costs 2 bytes of overhead, client→server costs 6. For chat that's the right way
round — fan-out is the direction that scales.

Try the length encodings:
```bash
./code/decode_frame.py 817e 0100 $(python3 -c "print('41'*256)")   # length 126 -> 16-bit
```
**Expected:**
```
length   : 256
overhead : 4 bytes for 256 bytes of payload
```

---

## Part C — Build all four transports

Add one controller exposing the same "give me messages" capability four ways, so
you can measure them against each other.

`src/main/java/com/pulse/transport/TransportDemoController.java`:

```java
package com.pulse.transport;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.async.DeferredResult;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/transport")
public class TransportDemoController {

    record Msg(long id, String body, long ts) {}

    private final List<Msg> log = new CopyOnWriteArrayList<>();
    private final AtomicLong seq = new AtomicLong();
    private final List<DeferredResult<List<Msg>>> waiting = new CopyOnWriteArrayList<>();
    private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();

    /** Anyone can inject a message: curl -X POST .../publish -d 'hello' */
    @PostMapping("/publish")
    public Msg publish(@RequestBody String body) {
        var m = new Msg(seq.incrementAndGet(), body.trim(), System.currentTimeMillis());
        log.add(m);

        waiting.forEach(d -> d.setResult(List.of(m)));       // wake long-pollers
        waiting.clear();

        emitters.forEach(e -> {                              // push to SSE
            try {
                e.send(SseEmitter.event().id(String.valueOf(m.id)).name("message").data(m));
            } catch (IOException ex) {
                emitters.remove(e);
            }
        });
        return m;
    }

    // ---- 1. POLLING ----
    @GetMapping("/poll")
    public List<Msg> poll(@RequestParam(defaultValue = "0") long since) {
        return log.stream().filter(m -> m.id() > since).toList();
    }

    // ---- 2. LONG POLLING ----
    @GetMapping("/longpoll")
    public DeferredResult<List<Msg>> longPoll(@RequestParam(defaultValue = "0") long since) {
        var newer = log.stream().filter(m -> m.id() > since).toList();
        var result = new DeferredResult<List<Msg>>(30_000L, List.<Msg>of());
        if (!newer.isEmpty()) {
            result.setResult(newer);                          // data already there
        } else {
            waiting.add(result);
            result.onCompletion(() -> waiting.remove(result));
            result.onTimeout(()    -> waiting.remove(result));
        }
        return result;
    }

    // ---- 3. SSE ----
    @GetMapping(value = "/sse", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter sse(@RequestHeader(value = "Last-Event-ID", required = false) String lastId) {
        var emitter = new SseEmitter(0L);                     // 0 = never time out
        emitters.add(emitter);
        emitter.onCompletion(() -> emitters.remove(emitter));
        emitter.onTimeout(()    -> emitters.remove(emitter));

        // Replay anything missed — this is the resume cursor, built into the protocol
        if (lastId != null) {
            long since = Long.parseLong(lastId);
            log.stream().filter(m -> m.id() > since).forEach(m -> {
                try { emitter.send(SseEmitter.event().id(String.valueOf(m.id)).name("message").data(m)); }
                catch (IOException ignored) {}
            });
        }
        return emitter;
    }

    // ---- 4. WebSocket is the /ws-raw handler from Part A ----
}
```

Restart and try each:

```bash
# polling
curl -s "localhost:8080/transport/poll?since=0" | jq
curl -s -X POST localhost:8080/transport/publish -d 'first' -H 'Content-Type: text/plain'
curl -s "localhost:8080/transport/poll?since=0" | jq
```

**Expected:**
```json
[]
{"id":1,"body":"first","ts":1735689600123}
[{"id":1,"body":"first","ts":1735689600123}]
```

```bash
# long polling — this BLOCKS until you publish from another terminal
curl -s "localhost:8080/transport/longpoll?since=1" &
sleep 1
curl -s -X POST localhost:8080/transport/publish -d 'second' -H 'Content-Type: text/plain'
wait
```

**Expected** — the long poll returns the instant you publish, not on a timer:
```json
[{"id":2,"body":"second","ts":1735689612456}]
```

```bash
# SSE — leave this running
curl -N -H 'Accept: text/event-stream' localhost:8080/transport/sse
```
In another terminal:
```bash
curl -s -X POST localhost:8080/transport/publish -d 'third' -H 'Content-Type: text/plain'
```

**Expected in the SSE terminal:**
```
id:3
event:message
data:{"id":3,"body":"third","ts":1735689620789}

```

✅ Now test **resume**. Kill the `curl -N` with Ctrl-C, publish two more
messages, then reconnect with a `Last-Event-ID`:

```bash
curl -s -X POST localhost:8080/transport/publish -d 'fourth' -H 'Content-Type: text/plain'
curl -s -X POST localhost:8080/transport/publish -d 'fifth'  -H 'Content-Type: text/plain'
curl -N -H 'Accept: text/event-stream' -H 'Last-Event-ID: 3' localhost:8080/transport/sse
```

**Expected — both missed messages replay immediately:**
```
id:4
event:message
data:{"id":4,"body":"fourth","ts":...}

id:5
event:message
data:{"id":5,"body":"fifth","ts":...}

```

✅ **That is a resume cursor, and it took four lines of code because the protocol
provides it.** WebSocket gives you nothing equivalent — you build it yourself in
Module 10. Note this now; it's a genuine point in SSE's favour.

---

## Part D — Measure the bytes

`code/measure_transports.sh`:

```bash
#!/usr/bin/env bash
# Measure bytes-on-the-wire per delivered message for each transport.
set -euo pipefail
IFACE=lo
DUR=20

measure() {
  local label="$1"; shift
  sudo timeout "$DUR" tcpdump -i "$IFACE" -q -n 'tcp port 8080' -w /tmp/cap.pcap 2>/dev/null &
  local tcpd=$!
  sleep 1
  "$@" >/dev/null 2>&1 &
  local client=$!
  for i in $(seq 1 10); do
    sleep 1
    curl -s -X POST localhost:8080/transport/publish -d "msg-$i" -H 'Content-Type: text/plain' >/dev/null
  done
  sleep 2
  kill $client 2>/dev/null || true
  wait $tcpd 2>/dev/null || true
  local bytes
  bytes=$(sudo tcpdump -r /tmp/cap.pcap 2>/dev/null | wc -l)
  local total
  total=$(stat -c%s /tmp/cap.pcap)
  printf "%-14s packets=%-6s capture_bytes=%-8s per_msg=%s\n" \
         "$label" "$bytes" "$total" "$((total / 10))"
}

poll_client()   { while true; do curl -s "localhost:8080/transport/poll?since=0" >/dev/null; sleep 1; done; }
sse_client()    { curl -sN -H 'Accept: text/event-stream' localhost:8080/transport/sse; }
ws_client()     { websocat -n ws://localhost:8080/ws-raw; }

measure "polling(1s)"  poll_client
measure "sse"          sse_client
measure "websocket"    ws_client
```

```bash
chmod +x code/measure_transports.sh
./code/measure_transports.sh
```

**Expected** (order-of-magnitude; absolute numbers vary):
```
polling(1s)    packets=412    capture_bytes=68432    per_msg=6843
sse            packets=64     capture_bytes=9218     per_msg=921
websocket      packets=48     capture_bytes=6104     per_msg=610
```

✅ Roughly **11× more bytes for polling than WebSocket** at a one-second poll
interval — and polling's cost is paid whether or not there's anything to say,
which is the real point. Record these in `results.md`.

> Note that SSE is much closer to WebSocket than to polling. Most of polling's
> cost is HTTP headers and TCP setup, not the payload. This is why "SSE is
> basically fine" is a defensible position.

---

## Part E — Watch a proxy kill your connection

This is the single most common WebSocket production bug. Cause it deliberately.

`infra/nginx-broken.conf`:
```nginx
events {}
http {
  upstream pulse { server host.docker.internal:8080; }
  server {
    listen 80;
    location / {
      proxy_pass http://pulse;
      proxy_http_version 1.1;
      proxy_set_header Upgrade    $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_read_timeout 20s;          # <-- deliberately short (default is 60s)
    }
  }
}
```

```bash
docker run -d --name nginx-broken -p 8090:80 \
  --add-host=host.docker.internal:host-gateway \
  -v "$PWD/infra/nginx-broken.conf:/etc/nginx/nginx.conf:ro" nginx:alpine

# connect through the proxy and just WAIT — send nothing
websocat -v ws://localhost:8090/ws-raw
```

**Expected — after exactly 20 seconds, with no warning:**
```
welcome 4b1e7c39
[INFO  websocat] Connection finished
```

✅ The connection died silently at the proxy's `proxy_read_timeout`. Neither the
client nor the server did anything wrong, and nothing was logged as an error.
This is what "my WebSockets drop every 60 seconds" always is.

**Confirm the diagnosis** — connect directly, bypassing nginx, and wait 30 s:

```bash
websocat -v ws://localhost:8080/ws-raw
```
**Expected:** still connected after a minute. The server is innocent.

Now fix it two ways and verify both:

```nginx
proxy_read_timeout 3600s;
```
```bash
docker restart nginx-broken
websocat -v ws://localhost:8090/ws-raw    # survives well past 20s
```

...and, better, **keep the connection non-idle** so no proxy anywhere can decide
it's dead:

```bash
# a heartbeat every 10s keeps it alive even with the 20s timeout restored
websocat -v --ping-interval 10 ws://localhost:8090/ws-raw
```

**Expected:** survives indefinitely, even with `proxy_read_timeout 20s`.

✅ **This is why Module 04 configures STOMP heartbeats at 10 seconds.** Fixing the
proxy config only fixes proxies you control; heartbeats fix the NAT gateway in a
customer's office that you'll never see.

Now break it the other way — remove `proxy_http_version 1.1`:

```nginx
      # proxy_http_version 1.1;
```
```bash
docker restart nginx-broken
websocat -v ws://localhost:8090/ws-raw
```

**Expected — the handshake fails outright:**
```
[ERROR websocat] Error: WebSocketError: Received unexpected status code (400 Bad Request)
```

Because HTTP/1.0 has no `Upgrade` semantics. Two config lines, two completely
different failure modes, both extremely common.

Clean up:
```bash
docker rm -f nginx-broken
```

---

## What you measured

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| WS overhead server→client | 2 bytes | |
| WS overhead client→server | 6 bytes (mask) | |
| Bytes/msg: polling vs SSE vs WS | 6843 / 921 / 610 | |
| Time to silent death behind a 20 s proxy timeout | 20 s | |
| Heartbeat interval that survives it | 10 s | |

---

## What you learned

- The handshake is a SHA-1 of a nonce plus a fixed GUID — you computed it.
- A WebSocket frame costs 2 bytes server→client, 6 client→server, and you can
  decode one from hex.
- SSE has resume (`Last-Event-ID`) **built into the protocol**; WebSocket makes
  you build it (Module 10).
- Proxies kill idle connections silently, and **heartbeats — not proxy config —
  are the portable fix**.

Now do [`challenge.md`](./challenge.md).

Then: [Module 04 — STOMP Chat on a Single Node](../04-stomp-chat-single-node/).
