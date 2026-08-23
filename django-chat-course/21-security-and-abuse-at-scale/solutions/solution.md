# Solutions — Module 21

> **Authorized testing only.** Everything here is run against your own local
> stack. The point of an attack in this course is to prove a defense works.

Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1 /
Channels 4.1, Uvicorn + uvloop, 3-node Compose stack from Module 18.**

---

## Task 1 — STRIDE, and the three holes the lab left

### The model

| STRIDE | Asset | Threat | Lab status |
|--------|-------|--------|-----------|
| **S**poofing | Handshake identity | Forged `?user=alice` | ✅ closed — ticket + RS256 JWT + identity cross-check |
| **S** | Another node | A rogue publisher writing straight to `asgi:group:room.7` | ✅ closed — Redis auth + network isolation; sends go through the consumer |
| **T**ampering | Message body in flight | MITM | ✅ TLS; ciphertext for E2EE DMs |
| **T** | Message body at rest | Admin edits a row | ⚠️ accepted — audited, not prevented (only E2EE prevents it) |
| **R**epudiation | "I never sent that" | No provenance | ⚠️ partial — server-side `sender_id` + `client_id`; no signature (see Task 5) |
| **I**nfo disclosure | Private room content | CSWSH | ✅ closed — `OriginValidator` + no cookie on the handshake |
| **I** | Private room **history** | **Resume from `seq=0` on a room you joined yesterday** | ❌ **FINDING 1** |
| **I** | Presence | Observing a user you share no room with | ❌ **FINDING 4** (low) |
| **I** | Node identity | Pod name leaked for room affinity | ✅ accepted — opaque token, Module 19 |
| **D**oS | The event loop | A blocking call on user input | ✅ closed — every user path async or threadpool-wrapped |
| **D** | **The `database_sync_to_async` threadpool** | **Compliant users, in aggregate, starve a shared 32-thread pool** | ❌ **FINDING 2** |
| **D** | Redis memory | **Ticket farming against a `noeviction` Redis** | ❌ **FINDING 3** |
| **D** | Connections | Handshake flood | ✅ closed — nginx `limit_req`/`limit_conn` |
| **D** | Fan-out | Zip-bomb payload | ✅ closed — length check before `json.loads` |
| **E**levation | Room membership | Delivery after removal | ✅ closed — cross-node eviction |
| **E** | Session lifetime | Revoked token on a live socket | ⚠️ **closed only in the common case** — see Task 3 |

Four findings. Three are exploitable today; one is a privacy issue. All are
things **one perfectly valid, authenticated, rate-limit-compliant user** can do
to the system or to another user — which is why none of the lab's defenses see
them.

---

### FINDING 1 — Resume reads history from before you joined

**Severity: High. Information disclosure. The most serious of the four.**

Module 10 clamps `from_seq` to bound the *cost* of a resume. Nothing bounds its
*visibility*.

```bash
# alice was added to the private room #board today. Its seq is at 41,208.
( echo '{"type":"hello","token":"'"$ALICE_TOKEN"'"}';
  sleep 0.3
  echo '{"type":"resume","room":"room.board","from_seq":0}';
  sleep 3 ) | websocat -n "ws://localhost:8080/ws/?ticket=$TICKET"
```
**Expected — the bug:**
```
{"type":"hello_ok","expiresAt":1755990000}
{"type":"history","room":"room.board","from":1,"to":2000,"count":2000}
{"type":"message.new","data":{"seq":1,"sender":"ceo","body":"kicking off the acquisition thread"}}
...
```
❌ **alice read 41,208 messages of a private room, of which she was a member for
the last 6.** The clamp did its job — it limited her to 2,000 per page — and then
happily paged her through the rest.

This is not a Channels bug or a resume bug. It is the **subscribe-time vs
delivery-time authorization split from the README, with a third case nobody
listed: *history-time* authorization.** "Is alice a member of room 7?" is true.
"Was alice a member at seq 1?" was never asked.

**The fix — a membership floor stamped at join time:**

```python
# chat/models.py
class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    joined_at_seq = models.BigIntegerField()      # the room's seq when they joined
    left_at_seq = models.BigIntegerField(null=True)
    history_visible_from = models.BigIntegerField()   # policy, see below

    class Meta:
        indexes = [models.Index(fields=["user", "room"])]
```

```python
# chat/consumers.py
    async def _resume(self, content):
        floor = await self._history_floor(content["room"])     # cached per connection
        if floor is None:
            return await self.send_json({"type": "error", "code": "not_a_member"})
        from_seq = max(int(content.get("from_seq", 0)), floor)          # <-- the fix
        count = min(await self._current_seq(content["room"]) - from_seq,
                    self.RESUME_PAGE)                          # Module 10's cost clamp
        ...

    async def _history_floor(self, room_id) -> int | None:
        """The lowest seq this user may EVER see in this room."""
        m = await Membership.objects.filter(
            user_id=self.user_id, room_id=room_id, left_at_seq__isnull=True
        ).values("history_visible_from").afirst()
        return None if m is None else m["history_visible_from"]
```

**`history_visible_from` is a product decision, not a security one**, and it must
be made explicitly per room type:

| Room type | `history_visible_from` | Rationale |
|-----------|------------------------|-----------|
| Public channel | `0` | Anyone can read it anyway |
| Private room | `joined_at_seq` | Slack's default for private channels |
| Compliance/legal | `joined_at_seq` | Non-negotiable |
| DM | `0` | Both parties were there from message 1 |
| Re-invited after removal | `new joined_at_seq` | ⚠️ **the subtle one** — do *not* restore the old floor, or removing someone becomes reversible by re-adding them |

**Verify** (`pytest -q tests/test_history_authz.py`, then re-run the attack):
```
{"type":"history","room":"room.board","from":41202,"to":41208,"count":6}
```
✅ Six messages — exactly her membership.

> **Why the lab missed it, and the generalizable lesson:** every authorization
> question in the lab was *"may this user do this now?"* Resume asks a different
> question — *"may this user see this **then**?"* — and a boolean membership row
> cannot answer a question about the past. **Any feature that reads history needs
> a time-bounded permission, not a permission.** Check your export endpoint, your
> search index, and your notification backfill for the same bug; in our audit,
> search had it too.

---

### FINDING 2 — Compliant users exhaust the shared threadpool

**Severity: High. Denial of service by valid traffic.**

The hint in the challenge is the whole exploit. After Module 15 the ORM pool is
32 threads **per worker process**, shared by every connection that worker holds
(up to ~40,000). Rate limits are **per user**. Nothing limits the *aggregate*
draw on the pool.

```bash
# 40 accounts, each sending at 4 msg/s — comfortably inside the per-account
# limit of 5/s. Each message is one Message.objects.create() on the pool.
python code/threadpool_dos.py --accounts 40 --rate 4 --target-worker 1
```
**Expected:**
```
[t=6s]  chat_db_threadpool_active: 32/32  queued: 412
[t=9s]  fanout p99 for ALL 4,980 connections on worker 1: 6,120 ms
[t=9s]  worker CPU: 44%
        rate-limit rejections: 0        <-- every attacker is compliant
        abuse detector: no alert        <-- 40 accounts is not a "flood"
```
❌ **160 messages/second — from users doing nothing wrong — made 4,980 other
people's chat unusable, with the CPU 56% idle.** No alarm fires anywhere,
because every per-entity check passes.

This is a security-relevant restatement of Module 01's lesson: **concurrency is
free, resources are not — and an attacker only has to be free-er than your
resource is.**

**The fix is two layers, and you need both.** Layer 1 is the `db()` admission
wrapper from [Module 15's solution](../../15-async-sync-and-raw-asgi/solutions/solution.md)
— `Semaphore(32)` plus a 400 ms `wait_for`, so an over-subscribed pool *rejects*
instead of queueing. Layer 2 is new here, and it is the one that makes this a
security control rather than a performance one:

```python
# chat/ratelimit.py — layer 2: a per-WORKER aggregate budget, charged per frame
WORKER_BUDGET = TokenBucket(capacity=600, refill_per_s=400)   # measured headroom

async def admit(self, content) -> bool:
    if not await self.user_bucket.take(1):        # per-entity  (Module 11)
        return False
    if not WORKER_BUDGET.take(1):                 # per-RESOURCE — the new one
        SHED.inc()
        await self.send_json({"type": "error", "code": "busy", "retryAfterMs": 1200})
        return False
    return True
```

**Re-run:**
```
[t=6s]  chat_db_threadpool_active: 31/32  queued: 6
[t=9s]  fanout p99 for the other 4,980 connections: 214 ms
        rejected with code "busy": 11.4% of the 40 attackers' sends
        legitimate users affected: 0
```
✅ **p99 6,120 ms → 214 ms.** The load is shed onto the accounts generating it
(their clients retry from the Module 17 outbox with jitter), and the bystanders
never notice.

> **The principle:** a limit scoped to one entity is bypassed by using many
> entities — the README says this about accounts and IPs. It is equally true of
> *resources*: **every shared, bounded resource needs a budget of its own, not
> just a fair-share policy over its consumers.** Audit the list: the ORM
> threadpool, the Redis connection pool, the outbound channel-layer capacity, the
> `sync_to_async` executor, and (Module 18) the readiness capacity signal.

---

### FINDING 3 — Ticket farming OOMs the Redis that runs chat

**Severity: High. Denial of service, with a nasty blast radius.**

`ws_ticket` is `IsAuthenticated` and otherwise unlimited. Each call writes a
`SETEX` with a 30-second TTL. And the course's Redis runs
**`--maxmemory-policy noeviction`** (deliberately — see
[`infra/README.md`](../../infra/README.md)), so it does not shed; it *errors*.

```bash
python code/ticket_farm.py --user alice --rate 8000 --seconds 60
```
**Expected:**
```
tickets minted: 480,000
redis used_memory: 512 MB -> 981 MB
[t=47s] channel layer: redis.exceptions.ResponseError:
        OOM command not allowed when used memory > 'maxmemory'
[t=47s] group_send failing on ALL THREE NODES — chat is down for everyone
```
❌ **One authenticated user, one unlimited HTTP endpoint, and the *fan-out
backbone* stops.**

Two independent mistakes compound here, and both are worth naming:

1. **A security control with no budget.** The ticket was introduced to stop
   credential leakage into logs. It is a *write primitive against shared memory*
   and nobody sized it.
2. **Shared blast radius.** Tickets, the channel layer, presence, sequences and
   rate-limit buckets all live in one Redis. The `noeviction` choice is correct
   (a silently evicted sequence counter is worse than an outage) — but it means
   *any* unbounded writer takes down *everything*.

**The fix, three parts:**

```python
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ws_ticket(request):
    uid = request.user.id
    # 1. Rate-limit issuance. Reuse Module 11's Lua bucket — don't invent one.
    ok, retry_ms = ticket_bucket(keys=[f"tkrate:{{{uid}}}"],
                                 args=[10, 0.5, now_ms(), 1])   # 10 burst, 0.5/s
    if not ok:
        return Response({"detail": "slow down", "retryAfterMs": retry_ms}, status=429)

    # 2. Cap OUTSTANDING tickets per user, so a slow drip can't accumulate either.
    outstanding = f"tkset:{{{uid}}}"
    if _redis.scard(outstanding) >= 5:
        return Response({"detail": "too many outstanding tickets"}, status=429)

    ticket = secrets.token_urlsafe(32)
    pipe = _redis.pipeline()
    pipe.setex(f"wsticket:{ticket}", 30, uid)
    pipe.sadd(outstanding, ticket)
    pipe.expire(outstanding, 30)
    pipe.execute()
    return Response({"ticket": ticket, "expiresIn": 30})
```

**3. Move tickets off the backbone Redis.** Auth ephemera belong somewhere whose
failure does not stop message delivery:

```python
REDIS_URL          = "redis://redis-backbone:6379/0"   # channel layer, streams, seq
REDIS_AUTH_URL     = "redis://redis-auth:6379/0"       # tickets, denylist, ticket rate
```
And give *that* instance `--maxmemory-policy allkeys-lru` with a small
`--maxmemory`: an evicted ticket means one failed handshake and a retry, which is
exactly the "cache-shaped data" case Module 08 argued for.

**Re-run:**
```
tickets minted: 612 (429s: 479,388)
redis-auth used_memory: 3 MB -> 3 MB
channel layer: healthy
chat p99: 141 ms (baseline 138 ms)
```
✅ Held.

> **The lesson worth carrying:** a security control is a feature, and features
> have capacity. Ask of every defense you add: *what does it write, how fast can
> an attacker make it write, and what else lives in that resource?* The blast
> radius question is the one people skip.

---

### FINDING 4 — Presence discloses activity to strangers (low)

`presence:{user_id}` is readable by anyone who can name a user id, so a
subscriber learns when a stranger is online, and by polling, their working hours.

**Fix:** answer presence only for users sharing at least one room with the
requester, and coarsen it — `online` / `away` / `offline`, never `last_seen` to
the second. Cost: one cached room-intersection check per presence subscribe, not
per update. Ship it; it's cheap and it's the kind of thing that becomes a press
story rather than an incident.

---

## Task 2 — Three rate-limit bypasses

### Bypass A — One user, twenty sockets

Module 11's bucket is keyed `rate:{user}:room:{room}`, but the *check* was
happening in the consumer instance, and each socket has its own consumer.

```bash
python code/multi_socket.py --user alice --sockets 20 --rate 5
```
```
per-socket limit:  5 msg/s
messages accepted: 100 msg/s        <-- 20x the intended budget
rejections: 0
```
❌ 20×.

**Fix:** the bucket must live in Redis keyed by *identity*, never per connection,
**and** concurrent sockets per user must be capped:

```python
# on connect
n = await _aredis.incr(f"socks:{{{self.user_id}}}")
await _aredis.expire(f"socks:{{{self.user_id}}}", 3600)
if n > MAX_SOCKETS_PER_USER:       # 6: phone + laptop + a few tabs
    await _aredis.decr(f"socks:{{{self.user_id}}}")
    return await self.close(code=4029)
```
```
messages accepted: 5 msg/s, sockets refused above 6 (code 4029)
```
✅ The counter needs a TTL and a `decr` in `disconnect` — and a periodic
reconciliation against the actual registry, because a hard-killed worker leaks
counts. (Same shape as Task 3's problem. Push plus reconcile, always.)

### Bypass B — The offline outbox replay *(the required one)*

Module 17's client queues sends while offline and flushes them on reconnect. To a
token bucket that is indistinguishable from an attack.

```bash
python code/outbox_replay.py --offline-seconds 300 --queued 40
```
**Expected, with the lab's bucket (capacity 20, refill 5/s):**
```
flushed on reconnect: 40 messages in 180ms
accepted: 20
REJECTED: 20        <-- a legitimate user permanently LOST 20 messages
```
❌ Not a bypass yet — a **correctness bug**. Now watch it become the bypass, via
the obvious fix:

```bash
# "just widen the burst so real reconnects work"  -> capacity 100
python code/outbox_replay.py --fake-reconnect-every 20s --queued 100
```
```
sustained rate achieved: 5 msg/s baseline + 100 per fake reconnect every 20s
                       = 10 msg/s, indefinitely     <-- 2x, forever
```
❌ **Widening the burst to accommodate honest replay hands the same allowance to
anyone who disconnects on purpose.** This is the interaction the challenge asks
about, and it's why "just raise the limit" is never the answer.

**The fix — a *separate, earned, bounded* catch-up allowance:**

```python
async def _admit_send(self, content) -> bool:
    if content.get("replay"):
        # A replayed frame must PROVE it belongs to a real absence:
        #  1. this connection resumed from a valid cursor (server-issued),
        #  2. the frame's clientTs falls inside the disconnected window,
        #  3. the clientId is not already in the dedup set (Module 05).
        if not self.resume_verified:
            return False
        if not (self.disconnected_from <= content["clientTs"] <= self.resumed_at):
            return False
        # Allowance = what they COULD have sent while away, capped.
        if self.catchup_remaining <= 0:
            return False
        self.catchup_remaining -= 1
        return True
    return await self.user_bucket.take(self._cost(content))

# on successful resume:
away_s = min(self.resumed_at - self.disconnected_from, 900)      # cap at 15 min
self.catchup_remaining = min(int(away_s * NORMAL_RATE), MAX_CATCHUP)   # cap at 120
```

Plus **pace the drain**: accept the burst but fan it out at the normal rate, so a
40-message replay doesn't become 40 × 199 = 7,960 deliveries in 180 ms.

```
honest 5-minute absence, 40 queued:  40 accepted, 0 lost, fanned out over 8s
fake reconnect every 20s:            allowance = 20s x 5/s = 100, but the
                                     clientTs check rejects fabricated
                                     timestamps and dedup rejects replays
                                     -> sustained rate stays 5 msg/s
```
✅ **Honest clients lose nothing; the bypass yields nothing.** The three
conditions matter together: the server-issued cursor makes the absence
attestable, `clientTs` bounds what may be backfilled, and dedup stops the same
message being replayed for extra allowance.

> The general principle: **when a legitimate behaviour looks like an attack,
> don't widen the limit — make the legitimacy *provable* and grant a separate,
> earned budget.** Widening a limit for one case grants it to every case.

### Bypass C — Room-hopping

`rate:{user}:room:{room}` means the budget is per room.

```bash
python code/room_hop.py --user alice --rooms 50 --rate 4
```
```
per-room limit: 5/s        rooms: 50       accepted: 200 msg/s
```
❌ 40× aggregate.

**Fix — two buckets, both checked, and split for Redis Cluster:**

```python
ok_user, _ = await bucket_user(keys=[f"rate:{{{uid}}}:all",
                                     f"rate:{{{uid}}}:room:{room}"],
                               args=[GLOBAL_CAP, GLOBAL_RATE, ROOM_CAP, ROOM_RATE, now])
ok_room, _ = await bucket_room(keys=[f"rate:{{{room}}}:room",
                                     f"rate:{{{room}}}:ip:{ip}"], args=[...])
```
Note the **hash tags**: all of script A's keys are `{uid}`-tagged and all of
script B's are `{room}`-tagged, so each script's keys land in one Cluster slot.
That's why Module 11 put the tags where it did — this is the moment it pays off,
and Module 18's Sentinel→Cluster migration is where you find out if you got it
right.

```
accepted: 5 msg/s aggregate, regardless of room count
```
✅

### The fourth one, which we found while fixing C

**Cost asymmetry.** A message to a 3-person DM and a message to a 5,000-member
room both cost **one token**, but one costs 3 deliveries and the other 5,000.
Charge for what it costs:

```python
def _cost(self, content) -> int:
    size = self.room_size_cache.get(content["room"], 1)
    return 1 + size // 100          # 200-member room = 3 tokens; 5,000 = 51
```
```
attacker in a 5,000-member room: 5 msg/s -> 0.1 msg/s effective
normal user in a 200-member room: unaffected (5/s costs 15 tokens/s of 25)
```
✅ **Rate-limit the amplification, not the message.** Fan-out amplification is
the load (Module 06); it should also be the price.

---

## Task 3 — Revocation that survives a partition

### Proving the gap

`group_send` rides the Redis channel layer, which is **Pub/Sub — at-most-once**
(Module 07). A node whose Pub/Sub connection is re-establishing at the moment of
the `PUBLISH` misses it. Permanently.

```bash
# alice is connected on node-a. Partition node-a from Redis for 3 seconds and
# revoke her token during the window.
docker network disconnect pulse-ha_default pulse-ha-pulse-1-1
sleep 1
curl -XPOST localhost:8081/api/admin/revoke -d "{\"jti\":\"$JTI\",\"ttl\":600}"
sleep 2
docker network connect pulse-ha_default pulse-ha-pulse-1-1
sleep 5

./code/publish.sh room.7 "post-revocation message"
```
**Expected:**
```
[node-b] revoked jti=7f3a… -> closed 2 sockets
[node-c] revoked jti=7f3a… -> closed 1 socket
[node-a] (nothing — pubsub was reconnecting)
[alice on node-a] {"type":"message.new","data":{"body":"post-revocation message"}}
```
❌ **A revoked user is still connected and still receiving**, and she stays that
way until her token expires — up to 15 minutes. The lab's revocation is
immediate *in the common case*, which is not the same as guaranteed.

### The fix: a durable revocation log + a reconciliation loop

**Use a Stream, not a Set.** `SMEMBERS` of a growing denylist every few seconds
is O(N) per worker per tick — the Module 08 mistake. A Redis Stream gives each
worker a cursor and O(new entries):

```python
# chat/revocation.py
REVOCATION_STREAM = "revocations"

def revoke(jti: str, remaining_life_s: int, user_id: int | None = None):
    # 1. Durable denylist (checked on hello + reauth + reconnect).
    _redis.setex(f"revoked:{jti}", remaining_life_s, "1")
    # 2. Durable, replayable LOG. This is what reconciliation reads.
    _redis.xadd(REVOCATION_STREAM, {"jti": jti, "user": user_id or ""},
                maxlen=100_000, approximate=True)
    # 3. Fast path: the immediate push. Best-effort, and now honestly labelled.
    async_to_sync(get_channel_layer().group_send)(f"jti.{jti}", {"type": "revoked"})
```

```python
# chat/reconcile.py — one task PER WORKER PROCESS, started at lifespan.startup
RECONCILE_INTERVAL = 10.0

async def reconciliation_loop(registry, redis):
    cursor = "$"                      # only entries from our startup onward
    while True:
        try:
            resp = await redis.xread({REVOCATION_STREAM: cursor},
                                     block=int(RECONCILE_INTERVAL * 1000), count=500)
            if not resp:
                continue
            _, entries = resp[0]
            revoked = {e[1][b"jti"].decode() for e in entries}
            cursor = entries[-1][0]
            evicted = 0
            for consumer in list(registry):          # process-local set (Module 18)
                if consumer.jti in revoked:
                    await consumer.close(code=4001)
                    evicted += 1
            if evicted:
                log.warning("reconciliation evicted %d socket(s)", evicted)
                RECONCILE_EVICTIONS.inc(evicted)     # ← alert on this being > 0
        except Exception:
            log.exception("reconciliation loop error")
            await asyncio.sleep(1)                   # never let this loop die
```

Start it once per worker from `lifespan.startup` in `pulse/asgi.py`, **in a clean
context** — creating it lazily inside a connection gives it that user's
`contextvars` forever (Module 15, Task 5). And keep the belt-and-braces denylist
`EXISTS` in `_hello`, so a reconnect can't outrun the loop.

**Re-run the partition drill:**
```
[t=1.0] revoke published (node-a partitioned, misses it)
[t=5.0] node-a rejoins the network
[t=8.4] node-a reconciliation tick: XREAD returned 1 entry
        pulse.reconcile WARNING reconciliation evicted 1 socket(s)
[alice] close 4001 revoked
```
✅ **Guaranteed, not merely usual.**

### The cost, stated exactly

| | Value |
|---|-------|
| **Worst-case window a revoked user stays connected** | `RECONCILE_INTERVAL` + eviction time ≈ **10.1 s** |
| Typical case (push arrives) | **< 5 ms**, unchanged |
| Redis load added | one blocking `XREAD` per worker; 3 nodes × 8 workers = 24 idle blocked readers, ~0 ops/s when nothing is revoked |
| Memory | ~100 B/revocation × `maxlen 100,000` ≈ 10 MB |
| App CPU | 0.3% of one core per worker (measured; it's a blocked read) |

**Choosing the interval is the design decision:**

| Interval | Worst-case window | Redis reads/s (24 workers) |
|----------|-------------------|----------------------------|
| 1 s | 1.1 s | 24 |
| **10 s** | **10.1 s** | **2.4** |
| 60 s | 60.1 s | 0.4 |

We chose **10 s**, and the argument is: the push covers the common case in
milliseconds, so the interval only bounds the *rare* case where the push was
lost. Ten seconds of exposure for a partition-during-revocation is acceptable
where 15 minutes was not. If your threat model is a compromised admin account
being revoked mid-attack, buy the 1-second interval — it costs 24 reads/s, which
is nothing.

> **The through-line:** this is Module 07 and Module 09's lesson arriving as a
> *security requirement*. Pub/Sub is at-most-once, so it is a latency
> optimization, never a guarantee. **Anything that must be true needs a durable
> log and a reconciler; anything that merely should be fast can ride the
> push.** Presence, typing indicators, and cursor positions ride the push.
> Revocation, membership changes, and shard reassignment need both.

---

## Task 4 — What security costs, measured

Module 06 harness: 20,000 connections, 100 rooms, 200 members, 1 msg/user/60 s,
3-node HA stack. "Insecure" = the Module 04/07 consumer with every defense
removed.

### Per-defense

| Defense | Where it runs | p50 cost | Scales with |
|---------|---------------|----------|-------------|
| `OriginValidator` | handshake | +0.2 ms | connections |
| Ticket `GETDEL` | handshake | +0.4 ms | connections |
| RS256 JWT verify (`hello`) | first frame | **+1.9 ms** | connections |
| Re-auth (every ~13 min) | in-band | +1.9 ms / 13 min | negligible |
| Denylist `EXISTS` on hello/reauth | Redis | +0.11 ms | connections |
| Reconciliation loop (Task 3) | background | 0 | nothing |
| Frame size check | per frame in | +0.01 ms | inbound |
| Content validation | per frame in | +0.31 ms | inbound |
| Rate limiting (2 Lua scripts) | per frame in | +0.62 ms | inbound |
| **Delivery-time authz (private rooms)** | **per delivery out** | **+0.40 ms** | ⚠️ **outbound = inbound × 199** |
| Abuse detector | Celery beat | 0 on the hot path (4% of one core) | rooms |
| nginx `limit_req`/`limit_conn` | edge | +0.05 ms | connections |

### Aggregate

| | Insecure | Full security stack | Δ |
|---|----------|--------------------|---|
| p50 fan-out | 11 ms | **12.4 ms** | +13% |
| p95 | 52 ms | **61 ms** | +17% |
| p99 | 138 ms | **166 ms** | +20% |
| p99.9 | 640 ms | **790 ms** | +23% |
| Node fan-out knee | 150,000/s | **128,000/s** | **−15%** |
| Connection setup | 4 ms | **6.5 ms** | +63% |
| RSS/conn | 45 KB | 47 KB | +4% |

✅ **A 15% capacity tax and a 20% p99 tax for the whole stack** — and 63% on
connection setup, which sounds alarming and isn't: it's a once-per-socket cost on
a socket that lives 8 hours, invisible except during a reconnect storm (where
nginx's handshake limit is doing more good than the 2.5 ms is doing harm).

### The most expensive defense, and the decision

**Delivery-time authorization for private rooms: 0.40 ms.** It looks like the
third-cheapest line in the table and it is by far the most expensive thing in the
system, because it is the **only defense on the outbound path** — and the
outbound path carries **199× the traffic** of the inbound one (Module 06's
amplification). Alone it accounts for **12 percentage points of the 15% capacity
loss.**

**Decision: keep it, and restructure it. Do not drop it.**

Dropping it re-opens the Module 05/21 hole — a user removed from a private room
keeps receiving it — which is the exact bug the module exists to close. But 0.40
ms is a *Redis round trip*, and the answer to a per-delivery round trip is never
"accept it":

Replace it with a **per-worker `dict[(user_id, room_id) -> bool]` cache**, and put
membership revocations on the *same durable stream* Task 3's reconciliation loop
already reads — each tick calls `invalidate_user(uid)`. **The cache is only safe
because the invalidation is durable**; a cache invalidated by Pub/Sub would be a
worse version of the bug it's optimizing.

| | Redis check per delivery | Cached + stream invalidation |
|---|--------------------------|------------------------------|
| Cost per private delivery | 0.40 ms | **0.002 ms** |
| Node knee | 128,000/s | **146,000/s** |
| Worst-case stale authorization | 0 | **≤ 10 s** (the reconciliation interval) |
| Memory | 0 | ~90 B × cached pairs (~4 MB at 40k conns) |

✅ **The knee comes back from 128,000 to 146,000 — a 3% total security tax
instead of 15%** — and the price is a ≤10 s staleness window on membership
removal, *identical to* and *bounded by* the window we already accepted for token
revocation in Task 3.

> **Note what happened there.** Task 3's durable log was built to fix a
> correctness gap; Task 4 reused it to make the most expensive defense 200×
> cheaper, and the staleness budget was already spent. **The right primitive pays
> twice.** If you had built Task 3 with a naive `SMEMBERS` poll, this
> optimization would have been unavailable.

**Keep/drop verdict on everything:** keep all of it. The only line worth arguing
about was delivery-time authz, and the answer was to restructure rather than
remove. The JVM twin reaches the same conclusion by the same route; the numbers
differ (Python's Redis hop and JSON work are heavier) but nothing about the shape
changes.

---

## Task 5 — Moderation in an E2EE room

Start from the sentence everything follows from: **the server cannot read the
messages.** Therefore no server-side classifier, no keyword filter, no automated
takedown of content it has never seen. Any design that pretends otherwise is
either not E2EE or is lying about being E2EE.

### The four honest options

| Option | Catches | Cannot catch | Privacy cost |
|--------|---------|--------------|--------------|
| **1. Franked reports** | Anything a participant *chooses to report*, with cryptographic non-repudiation | Anything nobody reports | **Low** — only the reporter's own messages, only when they act |
| **2. Metadata analysis** | Spam/flooding (rate, breadth), account farming, coordinated behaviour, one-to-many harassment patterns | Anything about *what was said*. A single abusive message is invisible | ⚠️ **High and under-discussed** — the graph plus timing is often more sensitive than content |
| **3. Client-side scanning** | Known-bad content, on *cooperating* clients | Novel content; **anything at all on a modified client** — and an abuser is the likeliest person to run one | 🚩 **Contested** — it builds an inspection mechanism whose policy is remotely updatable. The objection isn't today's list; it's the lever |
| **4. Reputation & friction** | The *economics* of abuse, which is what scaled abuse depends on | A determined individual attacking one person | Low, but it costs usability, hardest on new and pseudonymous users |

**Franking is the one most people don't know exists**, and it's the strongest:

```
sender:   commits to (plaintext, sender_id, ts) with an HMAC under a key the
          SERVER supplies but cannot invert; sends the commitment with the ciphertext
server:   stores the commitment, signs it, returns the signature (still reads nothing)
reporter: when reporting, reveals the plaintext + the opening
server:   verifies the commitment and its own signature -> it can now prove
          "this exact plaintext was really sent by this user at this time"
```

Without it, a report is one user's screenshot — trivially forged, so you cannot
act on it confidently. Franking turns "he said" into evidence, and closes the
**R**epudiation row of Task 1's STRIDE table as a side effect.

Also be honest that **Module 11's detector loses a signal** under E2EE:
`content_dup_frac` (MinHash similarity) is gone. You can partly recover it from
ciphertext *length* distribution — a spam campaign sends near-identical lengths
— but it is weaker and defeated by padding.

### What Pulse ships

```
E2EE scope:       DMs only. Group rooms stay server-readable.
Moderation:       (1) franked reports  + (2) metadata detection
                  + (4) reputation and graph friction
Explicitly NOT:   (3) client-side scanning; key escrow in any form
Retention:        metadata 30 days; franked commitments 90 days; no plaintext ever
Published:        a "what moderation cannot do in an encrypted DM" page, written
                  BEFORE launch and shown to support and legal
```

**Why DMs only.** The abuse profile differs: group rooms have bystanders who
report, and are where scaled spam lands; DMs are where privacy expectations are
highest and where server-side content moderation delivers least. Encrypting the
half where the tradeoff is favourable, and being honest about not encrypting the
other half, beats encrypting everything and quietly having no moderation story.

**The one thing that must not happen:** shipping E2EE and *then* discovering that
support cannot see what users complain about, moderators cannot action reports,
and search is gone. Every one of those is a product decision that must be made in
advance, by the people who own it. **E2EE is a product decision wearing a
security costume** — the README says so, and this task is where you write down
what you are actually giving up.

---

## Task 6 (stretch) — The red-team exercise

### Rules of engagement

```
Target:      the full 3-node HA stack on the operator's laptop, seeded with
             500 accounts and 40 rooms (12 private), realistic history
Attacker:    one valid account (`mallory`) and its password. No source access.
Goals (scored, in order):
  G1  read one message from a private room mallory is not in
  G2  send a message that appears to come from another user
  G3  make chat unavailable for other users for >30 s
  G4  exfiltrate >1,000 messages mallory should not have
Timebox:     3 hours.  Out of scope: the host OS, Docker itself, the laptop.
Recorded:    every command; time-to-first-compromise; the primitive used.
```

### Round 1 — before the Task 1–3 fixes

| t | Finding | Goal | Severity |
|---|---------|------|----------|
| **0:23** | **Ticket farming → Redis OOM → chat down for everyone** | **G3** | High |
| 0:51 | Resume `from_seq=0` on a room joined that morning → 41,208 messages | **G1 + G4** | High |
| 1:34 | 40 sock puppets at compliant rates → 6.1 s p99 for 4,980 bystanders | **G3** | High |
| 2:08 | 20 sockets on one account → 20× the message rate | — | Medium |
| 2:47 | Presence polling → mapped the CEO's working hours | — | Low |

**Time-to-first-compromise: 23 minutes.** Three of four goals achieved.

The interesting part is *how* they were found. The red-teamer's first move was
not a payload — it was `curl -XPOST /api/ws-ticket` in a `while true` loop
"to see what rate limiting looks like," and discovering there wasn't any. **G2
(sending as another user) was never achieved**, in either round: the ticket/JWT
identity cross-check held, which is the single control that most repaid its
complexity.

### Round 2 — after fixing everything above, blind re-run, different operator

| t | Finding | Goal | Severity |
|---|---------|------|----------|
| 0:47 | `429` on the ticket endpoint; enumerated valid user ids from timing differences in the 429 vs 404 path | — | Low |
| 1:52 | Confirmed the ≤10 s reconciliation window: kept a revoked socket alive 9.4 s and received 3 messages in it | (partial G1) | Low — accepted, documented |
| 2:31 | Multi-account catch-up allowance: 6 accounts × 120 = 720 messages in one burst, paced by fan-out control, no outage | — | Info |
| — | G1–G4 | **none achieved** | |

**Time-to-first-compromise: none.** Two low findings, one of which is a
documented accepted risk.

The timing oracle (0:47) is real and worth fixing — return an identical response
shape and add jitter — and it's exactly the class of bug that only a second pair
of eyes finds.

### What the exercise is actually for

Both rounds found things the author would not have. But the number that changed
the team's behaviour was neither of the finding counts:

> **Time-to-first-compromise went from 23 minutes to "not in 3 hours."** That is
> a number a non-security stakeholder understands, it is repeatable, and it gets
> better in a way a finding count does not (finding counts go *up* when you get
> better at looking).

Three process lessons:

1. **Run it against the *deployed* stack, not a dev server.** Finding 1 depended
   on `--maxmemory-policy noeviction`, which only exists in the real config. A
   dev-server red team would have missed the highest-severity issue.
2. **Someone who didn't build it.** Every finding in round 1 was in a component
   the author had personally hardened. You cannot attack your own assumptions;
   you can only attack your own code.
3. **The re-run is the deliverable.** A findings list is a to-do. A findings
   list, the fixes, and a blind re-run that fails to reproduce them is
   *evidence*, and it's what belongs in the Module 22 architecture review.

---

## Record it

```markdown
## Module 21 — challenge

4 findings the lab missed, ALL reachable by one valid, compliant user:
  1. Resume reads pre-membership history -> history_visible_from floor.
     History features need TIME-BOUNDED permissions, not permissions.
  2. 40 compliant accounts exhaust the shared 32-thread ORM pool ->
     Semaphore(32) + fast reject + a PER-WORKER budget. p99 6,120 -> 214 ms.
     Every shared bounded resource needs its OWN budget, not fair-share.
  3. Ticket farming OOMs the noeviction backbone Redis -> issuance bucket,
     outstanding cap, and tickets moved to a SEPARATE lru Redis.
  4. Presence leaks activity to strangers -> shared-room gate + coarsen.

Rate limits: 20 sockets (20x) -> identity-keyed bucket + socket cap.
  Outbox replay: widening the burst grants it to everyone -> an earned,
  bounded, ATTESTABLE catch-up allowance + paced fan-out. Room-hopping (40x)
  -> global + per-room buckets, hash-tagged. Plus: charge for amplification,
  not for the message.

Revocation: the Pub/Sub push is at-most-once, proven lost under a 3s
  partition. Durable Redis STREAM + per-worker reconciliation (10s) + a
  denylist check on connect. Worst case 10.1s; push still <5ms.

Cost: p99 138 -> 166 ms, knee 150k -> 128k. Most expensive by far is
  delivery-time authz — the ONLY defense on the outbound path, and outbound =
  inbound x 199. Kept and RESTRUCTURED: a per-worker cache invalidated by
  Task 3's stream -> knee back to 146k, paid for with the same <=10s
  staleness budget. The right primitive pays twice.

E2EE: franked reports + metadata + reputation. No client-side scanning, no
  escrow, DMs only. Module 11's detector loses content-similarity.

Red team: TTFC 23 min -> none in 3h. Send-as-another-user never achieved:
  the ticket/JWT identity cross-check was the best-value control we built.
```

Then: [`22-capstone`](../../22-capstone/) — where you put every one of these
numbers into an architecture review and argue for it.
