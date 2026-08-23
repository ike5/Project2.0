# Solutions — Module 21

---

## Task 1 — STRIDE, and the hole the lab missed

| STRIDE | Threat | Mitigation | Status |
|--------|--------|-----------|--------|
| **S**poofing | Impersonate another user | JWT + ticket identity match | ✅ |
| **T**ampering | Forge a message's sender | Server uses `principal.getName()`, never payload | ✅ |
| **R**epudiation | Deny sending a message | `client_id` + server `id` + `created_at` audit | ✅ |
| **I**nfo disclosure | Read another room | Subscribe + delivery authz | ✅ |
| **D**enial of service | Flood, slow consumer, zip bomb | Rate limits, buffer limits, size limits | ✅ |
| **E**levation | Gain unauthorized capability | ← **the gap** | ❌ |

### The finding: presence oracle + ticket-harvesting

Two issues the lab missed, both exploitable by a **valid** user against others.

**(a) Presence oracle.** `presence.watch` (Module 11) lets a user query presence
for anyone they "share a room with." But the membership check was:

```java
var allowed = membership.visibleTo(principal.getName(), request.users(), MAX_WATCH);
```

`visibleTo` checks *current* shared rooms. So: join a large public room, watch
every member's presence, **leave the room**, and keep the presence subscription —
the watch registry wasn't cleared on leave. **You now have a persistent
online/offline oracle for thousands of users you no longer share a room with.**

Proof:
```bash
# alice joins #general (50,000 members), watches 20 of them, then leaves
./code/exploit-presence-oracle.sh alice
```
```
watching 20 users' presence
alice left #general
alice STILL receiving presence updates for all 20   <-- oracle
```

At scale this is worse: cycle through rooms, harvesting a real-time presence map
of the entire user base. A stalker's dream, and a corporate-espionage tool ("is
the CEO online at 2am the night before earnings?").

**Fix:**
```java
@EventListener
public void onUnsubscribe(SessionUnsubscribeEvent e) { /* ... */ }

@EventListener
public void onLeaveRoom(RoomLeftEvent e) {
    // Recompute the watch set on ANY membership change, not just at watch time.
    var stillVisible = membership.visibleTo(e.userId(), watchRegistry.watchedBy(e.sessionId()));
    watchRegistry.set(e.sessionId(), stillVisible);      // drops the now-invisible ones
}
```
Plus a periodic revalidation, because events can be missed (Module 07):
```java
@Scheduled(fixedRate = 60_000)
public void revalidateWatches() {
    watchRegistry.forEachSession((sid, watched) ->
        watchRegistry.set(sid, membership.visibleTo(userOf(sid), watched)));
}
```

**(b) Ticket harvesting for DoS.** `/api/ws-ticket` had no rate limit. A valid
user can request thousands of tickets per second, each writing a Redis key with a
30-second TTL:
```
10,000 tickets/sec × 30s TTL = 300,000 keys, ~30 MB
```
Not catastrophic alone, but combined with other keys it's a memory-pressure
vector, and it's free reconnaissance (each ticket is a valid handshake credential
to stockpile). **Fix:** rate-limit ticket issuance (Module 11's bucket) to a few
per minute per user — nobody legitimately needs more.

> **The pattern the lab missed:** it secured the *documented* operations but not
> the *stateful side effects* of legitimate ones. A watch that outlives its
> justification, a ticket store with no bound — elevation through accumulated
> state, not through a broken check.

---

## Task 2 — Three rate-limit bypasses

### Bypass 1 — the client outbox replay (the interaction bug)

Module 17's offline outbox replays queued messages on reconnect. The replay
sends them all at once:
```ts
flushOutbox() {
  for (const m of this.outbox) this.conn.publish(...);   // 500 messages, instantly
}
```
A malicious client queues 500 messages "offline" (never actually connecting),
then connects — and 500 messages hit the server in one burst, **before the rate
limiter's bucket has context**.

Proof:
```bash
./code/exploit-outbox-flood.sh --queue 500
```
```
messages accepted before rate limit engaged: 47
messages accepted total: 500   <-- the bucket refilled during the burst processing
```

**Fix:** the outbox replay must respect the same limits, client- *and* server-side:
```ts
// Client: pace the replay
async flushOutbox() {
  for (const m of this.outbox) {
    if (!await this.rateLimiter.tryAcquire()) { await sleep(m.retryAfter); }
    this.conn.publish(...);
  }
}
```
And server-side, the limiter must not have a burst capacity larger than intended:
```java
// The bucket capacity IS the max burst. 10 was fine for typing; too high here.
new Limit("user-room", 5, 1.0);       // capacity 5, not 10
```
```
after fix: messages accepted 5, then 429s with retry-after
```

### Bypass 2 — the sharded limiter's slot gap

Module 11's two-script split (`{userId}` and `{roomId}` tags) means the per-room
and per-user limits are checked separately. Send to **many rooms** and the
per-room limit never trips while the per-user limit... also has headroom if you
stay just under it. But the real gap: the per-IP limit moved to nginx (Module
11's solution), and **nginx limits by connection, not by message**. One
connection, many messages, sprayed across rooms:
```
30 rooms × 5 msg/room/sec = 150 msg/sec from one connection
per-user global limit: 30/sec   <-- SHOULD have caught it
```
It did — *if* the per-user-global script ran. But a client sending to 30 rooms in
one batch, each `SEND` a separate frame, hits the per-user script 30 times, and if
those land on different Cluster slots... they don't, they're all `{alice}`. **So
this one is actually defended** — verify:
```bash
./code/exploit-multiroom-spray.sh --rooms 30 --rate 5
```
```
rejected by: user (global) after 30 messages   ✅ defended
```
Good. The bypass is theoretical here because the per-user tag keeps all of a
user's buckets on one slot. **Document why it's safe** so nobody "optimizes" the
tag later and reopens it.

### Bypass 3 — timestamp manipulation in the token bucket

Module 11's Lua bucket takes `now` as an argument (for determinism/testing).
What if the *client* could influence it? It can't directly — the server passes
`System.currentTimeMillis()`. But the **resume path** did something worse:
```java
if (!rateLimiter.tryAcquire("resume:{" + userId + "}", 5, ...)) { ... }
```
The resume limiter used the userId, but a user with **multiple sessions**
(multi-device, Module 17) got a *shared* bucket — so far so good. The bug: the
bucket key didn't include the room, so resuming 100 *different* rooms counted
against one bucket of 5. Legitimate multi-room users got throttled (a
false-positive DoS on yourself), while the actual expensive operation
(deep resume) wasn't specifically limited.

**Fix:** limit the expensive thing specifically:
```java
// Deep resumes (far behind) are the expensive ones. Limit THOSE hard.
if (behind > 1000) {
    if (!rateLimiter.tryAcquire("deep-resume:{" + userId + "}", 2,
                                Duration.ofMinutes(1))) {
        throw new RateLimitedException("too many deep resumes");
    }
}
// Shallow resumes are cheap; limit them loosely.
```

---

## Task 3 — Revocation under partition

### Prove the gap

Revocation uses Pub/Sub (at-most-once, Module 07). A node reconnecting to Redis
misses any revocation published during the disconnect.

```bash
# alice connected to node-b, holding a valid token
docker pause pulse-redis
curl -XPOST localhost:8080/api/admin/revoke -d "{\"jti\":\"$ALICE_JTI\"}"   # via node-a's local... wait, Redis is down
```
Better test — partition just node-b:
```bash
docker network disconnect pulse_default pulse-b
# revoke via node-a (Redis reachable)
curl -XPOST localhost:8080/api/admin/revoke -d "{\"jti\":\"$ALICE_JTI\"}"
sleep 5
docker network connect pulse_default pulse-b
# alice, on node-b, is STILL CONNECTED and can still send
./code/send-as.sh alice room.7 "I was revoked 5s ago"
```
**Expected:**
```
message sent successfully   ❌ revoked user still active
```
✅ node-b missed the Pub/Sub revocation during its partition. alice stays
connected until her token expires (up to 15 minutes) or she happens to re-auth.

### The fix: a durable denylist checked on a heartbeat

Pub/Sub for *speed* (the common case), plus a periodic reconciliation against a
durable set for *correctness*:

```java
@Scheduled(fixedRate = 30_000)
public void reconcileRevocations() {
    // The denylist is a Redis SET with TTLs (durable, unlike Pub/Sub).
    // Check every LOCAL session's jti against it. Catches anything Pub/Sub missed.
    for (var session : registry.allSessions()) {
        if (revocation.isRevoked(session.principal().jti())) {
            close(session, 4001, "revoked");
            revocationReconciled.increment();
        }
    }
}
```
And on Redis reconnect, reconcile immediately rather than waiting for the timer:
```java
connectionListener.onReconnect(() -> reconcileRevocations());
```

**Re-run:**
```
docker network connect pulse_default pulse-b
[node-b] Redis reconnected, reconciling revocations
[node-b] closing session for alice (jti revoked)
alice: close 4001 revoked
```
✅ Revoked within 30 seconds worst case (the reconcile interval), immediately on
reconnect, and instantly via Pub/Sub in the common case.

### What it costs

| | Value |
|---|-------|
| Reconcile scan (per node, per 30s) | O(local sessions) — 10,000 sessions × one `EXISTS` = pipelined, ~14 ms |
| Worst-case revocation delay (partition) | 30 s (was: up to 15 min) |
| Common-case revocation delay | <5 ms (Pub/Sub, unchanged) |
| Extra Redis ops | 10,000 `EXISTS`/30s/node = 333/s/node — negligible |

> **The pattern, third time in the course:** Pub/Sub for speed, a durable check
> for correctness. Presence (Module 11), the outbox (Module 13), and now
> revocation all use it. **At-most-once for the fast path, a reconciliation loop
> for the guarantee** — because you cannot make security depend on at-most-once
> delivery.

---

## Task 4 — Security overhead, measured

Full security stack versus the insecure Module 06 baseline, identical workload:

| Defense | p50 cost | p99 cost | Throughput cost |
|---------|----------|----------|-----------------|
| Origin check (handshake only) | 0 | 0 | 0 |
| JWT verification (CONNECT only) | 0 | 0 | 0 |
| Ticket lookup (handshake only) | 0 | 0 | 0 |
| **Per-message rate limiting (Lua)** | **+0.31 ms** | +1.8 ms | **−4%** |
| Revocation reconcile (background) | 0 | +0.2 ms (GC of the scan) | −0.5% |
| **Delivery-time authz (private rooms)** | **+0.4 ms** | +2.1 ms | **−3%** |
| Content validation | +0.1 ms | +0.3 ms | −1% |
| Anomaly detection (async) | 0 | 0 | −1% |
| **Aggregate** | **+0.8 ms** | +4.4 ms | **−9%** |

**+0.8 ms p50 and 9% throughput for the full security stack.** Most defenses cost
nothing on the hot path because they run at connect time or in the background.

### The most expensive: per-message rate limiting

At −4% throughput it's the single biggest cost, because it's the only defense on
the **per-message** path. Every message pays for a Lua round trip (even the
two-script Cluster version).

**Is it worth it?** Test removing it:
```bash
PULSE_RATE_LIMIT=off ./code/exploit-flood.sh --rate 10000
```
```
one account sent 600,000 messages/minute to room.general
room unusable, other users' p99 -> 40s (the fan-out amplified the flood)
```
✅ **Non-negotiable.** Without it, one account destroys a room for everyone,
because the flood is *amplified* by fan-out. The 4% is cheap insurance against a
100% outage.

**Can it be made cheaper?** Yes — a **local token bucket per node** as an L1, with
Redis as the L2 for cross-node accuracy:
```java
// L1: in-process bucket, no network. Catches the obvious floods for free.
if (!localBucket.tryAcquire(userId)) { throw new RateLimitedException(...); }
// L2: Redis, only when L1 passes -- for cross-node accuracy on the margin.
if (localBucket.nearLimit(userId) && !redisBucket.tryAcquire(userId)) { ... }
```
**Measured:** −4% → **−1%**, because 95% of messages are nowhere near the limit
and the L1 answers them without a round trip. The L2 only engages for users
approaching their limit — which is exactly who you want to check carefully.

> The general lesson: **a per-message defense should have a local fast path.** The
> Redis round trip is only needed for accuracy at the margin, and the margin is a
> tiny fraction of traffic.

---

## Task 5 — Moderation for E2EE rooms

E2EE means the server cannot read content. So content-based moderation is
impossible **by design** — and any workaround that defeats that is not really
E2EE. Be honest about each option:

| Approach | Catches | Cannot catch | Privacy cost |
|----------|---------|--------------|--------------|
| **User reporting** | What a recipient chooses to report | Anything nobody reports | ✅ none — the reporter chose to share |
| **Metadata analysis** | Spam patterns (blast to 500 strangers), account farming, timing | Content of any kind | ⚠️ metadata is itself sensitive |
| **Reputation / trust graph** | New accounts, no mutual contacts, blocked-by-many | Established-account abuse | ✅ low |
| **Client-side scanning** | Known illegal content (hash matching) | Novel content; and it's **contested** | ❌❌ **breaks the E2EE promise** |
| **Sender-side warnings** | Nudges before sending (client-detected) | A determined sender | ✅ none |

### The design: report-plus-reputation, no content scanning

```java
// 1. Reporting: the reporter voluntarily decrypts and shares the message.
@PostMapping("/api/report")
public void report(@RequestBody Report r) {
    // The client sends the DECRYPTED content it chose to report, plus proof
    // (the ciphertext + the reporter's key) so we can verify it's genuine.
    if (!verifyReportAuthenticity(r)) return;   // stops fabricated reports
    moderationQueue.add(r);
}

// 2. Metadata reputation -- available even for E2EE.
public double abuseScore(String userId) {
    return weighted(
        accountAgeDays(userId),                  // < 7 days: suspicious
        distinctRecipientsLast24h(userId),       // blasting strangers
        blockRateReceived(userId),               // how often others block them
        reportRateReceived(userId),              // even one verified report matters
        mutualContactFraction(userId));          // no social graph: suspicious
}
```

### What it can and cannot do, honestly

**Can:**
- Rate-limit and quarantine accounts that *behave* like spammers (blast patterns,
  new accounts, high block rate) — all metadata, no content.
- Act fast on verified reports.
- Prevent the *distribution* mechanics of spam even without reading it.

**Cannot:**
- Proactively detect harmful content nobody reports. This is the irreducible cost
  of E2EE, and pretending otherwise is dishonest.
- Catch a first offense against a single victim who doesn't report.

### The privacy analysis of client-side scanning

The tempting "solution" — scan on the client before encryption, against a
server-provided hash list — is why this task is worth doing:

- It **defeats the entire purpose of E2EE**: the server now decides what your
  device flags, and a compromised or coerced hash list scans for anything.
- It's a **surveillance infrastructure** that, once built, can be repurposed by
  legal or political pressure. Apple proposed and then withdrew exactly this for
  a reason.
- It has **false positives** with real consequences (a flagged message reported
  to authorities).

**Recommendation: report + reputation + metadata, and no client-side content
scanning.** Accept that E2EE rooms have weaker moderation — that is the deal E2EE
makes, and a product choosing E2EE is choosing it. **Do not build client-side
scanning to have it both ways; you get neither privacy nor trustworthy
moderation, and you build a tool that will be abused.**

> This is the module's hardest honest answer: some safety properties and some
> privacy properties are genuinely in tension, and no clever engineering
> dissolves it. The engineering job is to be clear about the tradeoff so the
> *product* can make the call, not to pretend the tradeoff doesn't exist.

---

## Task 6 (stretch) — Red team

Gave a colleague the deployed system, four goals, and no source access.

### Round 1

| Goal | Achieved? | Time | Method |
|------|-----------|------|--------|
| Read a room they're not in | ✅ | **18 min** | The presence oracle (Task 1a) — inferred activity, then found a public room bridging to a private one via a shared bot account |
| Send as another user | ❌ | (gave up at 45m) | JWT signature held; couldn't forge |
| Take the service down | ✅ | **31 min** | The outbox-replay flood (Task 2 bypass 1) — one account, 500 queued messages, to a 5,000-member room, repeated |
| Exfiltrate data | ⚠️ partial | 52 min | Harvested a presence map of ~8,000 users via the oracle; no message content |

**Two compromises in under 35 minutes**, both exploiting the same class the lab
missed: **stateful side effects of legitimate operations**, not broken checks.

### Fixes applied

1. Presence oracle → the revalidation from Task 1a.
2. Outbox flood → the paced replay + lower burst capacity from Task 2.
3. The bridging-bot path → bot accounts now require explicit per-room
   authorization and cannot be in a public and private room simultaneously
   without an audit log entry.

### Round 2 (same red-teamer, after fixes)

| Goal | Achieved? | Time |
|------|-----------|------|
| Read a room they're not in | ❌ | gave up at 60m |
| Send as another user | ❌ | gave up |
| Take the service down | ⚠️ **degraded, not down** | 40 min — found that 20 accounts × 20 IPs (just under the connection-flood limit) could raise p99 to 800 ms in one room, but the anomaly detector quarantined them in 14s |
| Exfiltrate data | ❌ | gave up |

**Round 2: zero full compromises, one partial degradation auto-mitigated in 14
seconds.**

### What the exercise proved

1. **The vulnerabilities the lab found were checks; the vulnerabilities the red
   team found were state.** A security review that only asks "is this operation
   authorized?" misses "what does this operation *leave behind*, and can that be
   accumulated?"
2. **Time-to-compromise is the metric that matters.** 18 minutes to read a private
   room is a failing grade regardless of how many checks pass. The scorecard in
   Part G said "all green"; the red team found two holes in half an hour. **A
   passing audit is a hypothesis, not a proof.**
3. **The anomaly detector earned its complexity.** The one Round-2 attack that
   worked at all was caught in 14 seconds — the distributed low-and-slow that no
   per-entity limit could stop. That's precisely the case Module 11 built it for.

> Run the red team *before* you ship, not after the incident. And run it again
> after you fix what they found — the second round is where you learn whether you
> fixed the bug or the class.
