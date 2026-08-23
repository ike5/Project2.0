# Solutions — Module 18

Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1 /
Channels 4.1, Uvicorn + uvloop.** Every drill runs with the Part D harness and a
10,000-connection load test on. Baseline for comparison: **p99 261 ms, RTO 0,
RPO 0.**

---

## Task 1 — Moving the Redis tier, live

### The thing you find first, and it changes the whole plan

The obvious plan is "Sentinel → Redis Cluster," the way the JVM twin does it.
**Do not start there.** Check what your client can actually speak:

```bash
python - <<'PY'
import channels_redis, inspect
from channels_redis.pubsub import RedisPubSubChannelLayer
print(channels_redis.__version__)
print("consistent_hash" in dir(RedisPubSubChannelLayer)
      or "shards" in inspect.getsource(RedisPubSubChannelLayer))
PY
```
```
4.2.0
True
```

**`channels_redis` does not speak the Redis Cluster protocol.** It has no
`MOVED`/`ASK` handling and does not use `redis-py`'s `RedisCluster` client. What
it *does* have is its own **client-side sharding**: give it several entries in
`hosts` and it picks one per channel/group name by consistent hashing.

So if you point `hosts` at six Cluster node addresses, you do not get "the
channel layer on Cluster." You get:

```python
CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
                              "CONFIG": {"hosts": ["redis://rc1:6379", "redis://rc2:6379",
                                                   "redis://rc3:6379"]}}}   # <-- WRONG
```

- channels_redis picks a shard for `room.7` by hashing the *name*, with no idea
  which node owns the *slot*.
- `PUBLISH` is not slot-routed in Redis Cluster: a plain `PUBLISH` on any node is
  **broadcast to every node in the cluster**. So it works — and quietly does
  ~3× the network and CPU it should, on every message, forever.

**This is the "worse than an error" the challenge asks for.** An error stops you.
This gave the right answer at triple the cost, and would have shown up in Module
20 six weeks later as "Redis CPU is high and nobody knows why."

```bash
# The evidence. Publish once, count what each node saw.
for n in rc1 rc2 rc3; do
  docker exec pulse-ha-$n-1 redis-cli INFO stats | grep -E 'pubsub|instantaneous_ops'
done
```
```
rc1  instantaneous_ops_per_sec:41200
rc2  instantaneous_ops_per_sec:40980     <-- rc2 and rc3 hold no subscribers
rc3  instantaneous_ops_per_sec:41050         for these rooms and are relaying anyway
```

### The plan that is actually right: two topologies, two jobs

| Data | Client | Topology | Why |
|------|--------|----------|-----|
| **Channel layer** (groups, `group_send`) | `channels_redis` | **3 independent Sentinel-managed instances**, listed in `hosts` | The library already shards; each shard gets its own HA. Cluster buys nothing it can use. |
| **State** (Streams, `seq`, presence, buckets, tickets) | `redis.asyncio.RedisCluster` | **Redis Cluster, 3 primaries + 3 replicas** | A real cluster-aware client, real slot routing, real multi-key rules. |

```python
# pulse/settings/ha.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            "hosts": [                                  # THREE SHARDS, each HA
                {"sentinels": SENTINELS, "master_name": "pulse-cl-0",
                 "socket_timeout": 2.0, "socket_connect_timeout": 2.0},
                {"sentinels": SENTINELS, "master_name": "pulse-cl-1", "socket_timeout": 2.0},
                {"sentinels": SENTINELS, "master_name": "pulse-cl-2", "socket_timeout": 2.0},
            ],
        },
    },
}

# chat/state.py
from redis.asyncio import RedisCluster
state = RedisCluster(startup_nodes=[{"host": "rc1", "port": 6379}], decode_responses=False)
```

### The migration, with traffic on

Same four-phase shape as Module 14's shard migration:

```python
# chat/state_router.py — dual-write behind a runtime flag
class Mode(str, Enum):
    SENTINEL_ONLY = "sentinel_only"
    DUAL_WRITE    = "dual_write"      # write both, read old
    CLUSTER_READ  = "cluster_read"    # write both, read new
    CLUSTER_ONLY  = "cluster_only"

async def xadd(room, fields):
    if MODE != Mode.CLUSTER_ONLY:
        await old.xadd(f"room:{{{room}}}:stream", fields, maxlen=10_000, approximate=True)
    if MODE != Mode.SENTINEL_ONLY:
        await state.xadd(f"room:{{{room}}}:stream", fields, maxlen=10_000, approximate=True)
```

```bash
curl -XPOST localhost:8080/api/admin/redis/mode -d '{"mode":"dual_write"}'
sleep 300          # let the Streams replay window (Module 09) fill on the new side
curl -XPOST localhost:8080/api/admin/redis/mode -d '{"mode":"cluster_read"}'
sleep 300
curl -XPOST localhost:8080/api/admin/redis/mode -d '{"mode":"cluster_only"}'
```

**Expected, load test running throughout:**
```
migration downtime:      0.00 s
messages lost:           0
p99 during DUAL_WRITE:   322 ms   (baseline 261 ms — +23% from writing twice)
p99 after CLUSTER_ONLY:  268 ms
total migration time:    14m
```
✅ Zero downtime. The dual-write window costs 23% of p99, which is exactly why
you don't leave it running "just in case."

### The `CROSSSLOT` errors

```bash
k6 run -e ROOMS=100 --duration 3m ../../06-load-testing-harness/code/pulse-load.js
```
**Three distinct failures, and one non-failure that is the point of the exercise.**

**(a) The rate limiter — predicted by Module 11's challenge.**
```
redis.exceptions.ResponseError: CROSSSLOT Keys in request don't hash to the same slot
  script: multi_bucket.lua
  keys: rate:{alice}:all, rate:{alice}:room:7, rate:{room.7}:room, rate:{room.7}:ip:10.0.0.4
```
Two keys tagged `{alice}`, two tagged `{room.7}` — different slots. **Fix:** the
two-script split Module 11's solution was written for:
```python
ok_user, _ = await bucket_user(keys=[f"rate:{{{uid}}}:all", f"rate:{{{uid}}}:room:{room}"], ...)
ok_room, _ = await bucket_room(keys=[f"rate:{{{room}}}:room", f"rate:{{{room}}}:ip:{ip}"], ...)
```

**(b) Module 21's ticket pipeline — the one placed wrong.**
```
CROSSSLOT ... keys: wsticket:Xh2f…, tkset:{4711}
```
The ticket is tagged by its own random value; the outstanding-set is tagged by
user. They were never going to share a slot.
```python
# WRONG
pipe.setex(f"wsticket:{ticket}", 30, uid); pipe.sadd(f"tkset:{{{uid}}}", ticket)

# RIGHT — tag the ticket by the user it belongs to. The handshake knows the
# ticket string, so put the uid IN the ticket: "<uid>.<random>".
ticket = f"{uid}.{secrets.token_urlsafe(24)}"
pipe.setex(f"wsticket:{{{uid}}}:{ticket}", 30, uid)
pipe.sadd(f"tkset:{{{uid}}}", ticket)
```
**This is the "one place they were placed wrong."** Modules 08 and 11 established
the rule — *tag by the entity a multi-key operation groups on* — and Module 21
added a feature five modules later and tagged by the wrong entity, because at the
time there was one Redis and nothing enforced it. Nothing catches this until you
cluster. **Add a CI check** that greps for `pipeline`/Lua call sites and asserts
every key in each one shares a tag; it is 40 lines and it would have caught this.

**(c) Bulk presence.**
```
CROSSSLOT ... MGET presence:{7} presence:{12} presence:{41}
```
Users don't share a tag and shouldn't — a user is in many rooms; tagging presence
by room would duplicate it. **Fix:** stop using `MGET` and let the cluster client
split the work:
```python
async with state.pipeline(transaction=False) as pipe:      # RedisCluster routes per key
    for uid in uids:
        pipe.get(f"presence:{{{uid}}}")
    values = await pipe.execute()
```
You lose atomicity across the reads, which you never needed for a presence
snapshot. Measured: **+0.4 ms p50 vs `MGET`** for a 200-user room, because the
client fans out to 3 nodes in parallel instead of 1 round trip.

**(d) The non-failure: Streams and sequences just work.**
```bash
redis-cli -c -p 7000 CLUSTER KEYSLOT "room:{7}:stream"
redis-cli -c -p 7000 CLUSTER KEYSLOT "room:{7}:seq"
```
```
11267
11267
```
✅ **Same slot.** `XADD` to the stream and `INCR` on the sequence in one Lua
script still work, because Module 08 put `{room_id}` in the key names on a single
Redis where it made no difference at all. **A decision made five modules early,
for a reason that hadn't happened yet, turned a rewrite into a config change.**
That is the whole argument for hash tags, and it only becomes visible here.

---

## Task 2 — Three drills the lab didn't run

### Drill 12 — Disk full on the Patroni leader

```bash
./code/drill.sh "pg-disk-full" \
  "docker exec pulse-ha-patroni1-1 fallocate -l 9G /home/postgres/pgdata/BALLAST; sleep 60" \
  "docker exec pulse-ha-patroni1-1 rm -f /home/postgres/pgdata/BALLAST"
```
**Expected:**
```
patroni1 postgres: PANIC: could not write to file "pg_wal/xlogtemp.123": No space left on device
patroni1 patroni:  postgres is not running, demoting self
patroni2 patroni:  promoted self to leader by acquiring session lock
pg-disk-full            RTO= 38.40s  RPO=0 msgs  p99=11,900ms
```
⚠️ **RTO 38.4 s — over the 30 s target**, because Postgres does not fail *fast*
on a full disk: it retries, logs, and eventually PANICs, and only then does
Patroni notice its child is gone.

**The real weakness this exposed** is not the RTO. Investigating why 9 GB
mattered on a 40 GB volume:

```sql
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
FROM pg_replication_slots;
```
```
 slot_name        | active | retained
------------------+--------+----------
 outbox_decoding  | f      | 4212 MB     <-- INACTIVE. Retaining WAL forever.
```
❌ **An inactive logical replication slot left over from a Module 13 experiment
had been pinning 4.2 GB of WAL and growing.** The disk was already 60% consumed
by garbage before the drill touched it. This is the single most common cause of
real-world Postgres disk outages and it is completely silent.

**Fixes, in order of value:**
1. `SELECT pg_drop_replication_slot('outbox_decoding');` — reclaim 4.2 GB now.
2. Alert on `retained > 1GB OR (active = false AND age > 1h)`. **Before** the
   disk fills, not after.
3. `max_slot_wal_keep_size = '2GB'` (PG 13+) — the primary invalidates a slot
   rather than filling its own disk for it. **An invalidated slot is a broken
   replica; a full disk is a broken cluster.** Prefer the smaller failure.
4. Reserve the space you'll need to recover: a 1 GB ballast file you can delete
   to get enough room to run `DROP`.

**Re-run after the fixes:** `RTO=31.20s  RPO=0` — still slow (the PANIC path is
inherently slow), but no longer sitting on 4.2 GB of invisible debt.

### Drill 13 — Clock skew on one app node

```bash
# faketime in the entrypoint; +45s on pulse-2 only
./code/drill.sh "app-clock-skew" \
  "docker compose -f infra/ha/compose.ha.yml up -d --force-recreate \
     -e FAKETIME='+45s' pulse-2; sleep 90" \
  "docker compose -f infra/ha/compose.ha.yml up -d --force-recreate pulse-2"
```
**Expected:**
```
[pulse-2] jwt.exceptions.ImmatureSignatureError: The token is not yet valid (iat)
[pulse-2] 4,982 handshakes rejected with 4401 in 90s   (100% of its share)
[pulse-2] /readyz -> 200 OK          <-- HEALTHY. nginx keeps routing to it.
[pulse-2] /healthz -> 200 OK
app-clock-skew          RTO= 90.00s  RPO=0 msgs  p99=294ms
                        connections established: 66% of attempts
```
❌ **The worst kind of failure: a node that is broken in a way every health check
says is fine.** RTO is 90 seconds because that is how long the drill ran — nothing
would ever have recovered on its own. p99 looks *great* (294 ms) because the
users who got through are fine; the third who couldn't connect aren't in the
latency data at all. That's coordinated omission wearing an ops costume.

**Two fixes, and you need both:**

```python
# 1. Tolerate the skew you can't prevent.
claims = jwt.decode(token, KEY, algorithms=["RS256"], leeway=30,      # <-- seconds
                    options={"require": ["exp", "sub", "jti"]})
```

```python
# 2. Make readiness reflect whether the node is DOING ITS JOB, not whether the
#    process is up. This is the Part H lesson (capacity on readiness) applied to
#    correctness instead of throughput.
HELLO_OK, HELLO_FAIL = RollingCounter(30), RollingCounter(30)      # 30s windows

async def readyz(request):
    if not readiness.ready:
        return JsonResponse({"status": "draining"}, status=503)
    queued, p99 = outbound_queue_depth(), fanout_p99_ms()
    if queued > 5000 or p99 > 2000:
        return JsonResponse({"status": "capacity"}, status=503)
    ok, bad = HELLO_OK.sum(), HELLO_FAIL.sum()
    if ok + bad >= 20 and bad / (ok + bad) > 0.5:        # need a sample first
        return JsonResponse({"status": "auth_failing", "fail_rate": bad / (ok + bad)},
                            status=503)
    return JsonResponse({"status": "up"}, status=200)
```

**Re-run:**
```
[t=11.4s] pulse-2 readiness 503 status=auth_failing fail_rate=1.00
[t=14.9s] nginx removed pulse-2
app-clock-skew-guarded  RTO= 14.90s  RPO=0 msgs  p99=281ms
                        connections established: 99.7% of attempts
```
✅ **RTO 90 s → 14.9 s, and the failed-connection rate went from 33% to 0.3%.**

> **The generalizable rule:** liveness asks "is the process alive," readiness asks
> "should I get traffic." A node that is alive, fast, and **wrong** passes both of
> the checks you probably have. Add a *success-rate* signal to readiness for
> every function the node exists to perform.

### Drill 14 — One Uvicorn worker dies; its siblings don't

The lab kills containers. Each `pulse-N` container runs **four worker
processes**. Kill exactly one:

```bash
WPID=$(docker exec pulse-ha-pulse-1-1 sh -c "pgrep -f 'uvicorn' | tail -1")
./code/drill.sh "worker-process-kill" \
  "docker exec pulse-ha-pulse-1-1 kill -9 $WPID; sleep 120"
```
**Expected:**
```
[pulse-1] uvicorn: child process 47 died, restarting
[pulse-1] Started server process [93]
worker-process-kill     RTO=  1.10s  RPO=0 msgs  p99=1,240ms
                        connections dropped: 1,214 (code 1006)
                        container health: HEALTHY THROUGHOUT
```

Recovery looks excellent. Then look at Redis two minutes later:

```bash
docker exec pulse-ha-redis-1-1 redis-cli ZCARD asgi:group:room.7
docker exec pulse-ha-redis-1-1 redis-cli --scan --pattern 'asgi:group:*' | wc -l
```
```
214          # the room has 187 live subscribers
2,970        # and 27 dead channel names per room, cluster-wide
```
❌ **The dead worker's channel names are still in every group it had joined.**
`group_discard` runs in `disconnect()`, and a `kill -9` runs nothing. They expire
after `group_expiry`, whose **default is 86,400 seconds** — one full day. Until
then every `group_send` to room 7 fans out to 214 channels to reach 187 people.

```
fan-out waste:        14.4% of all deliveries go to dead channels
Redis CPU:            +9%
p99 (steady state):   138 ms -> 163 ms, for 24 hours, with no incident attached
```

**Fix:**
```python
CHANNEL_LAYERS["default"]["CONFIG"]["group_expiry"] = 300     # was 86400
```
```python
# chat/metrics.py — you cannot alert on what you don't count
DEAD_CHANNEL_SENDS = Counter("chat_dead_channel_sends_total",
                             "group_send targets with no live consumer")
```
And on the Module 21 reconciliation tick, prune groups this worker believes it
owns but whose consumers are gone.

**Re-run:** waste peaks at 14.4% and decays to 0 within 5 minutes; steady-state
p99 back to 138 ms.

> **Why the lab never found this:** every lab drill killed a *container*, and a
> container restart re-registers everything cleanly. The failure that hurt was one
> process inside a healthy container — the exact granularity the
> **process-per-core model** (Module 01) creates and that a JVM deployment does
> not have. `group_expiry`'s one-day default is safe for a system where processes
> only die with their container. Ours don't.

---

## Task 3 — The split-brain nobody fenced

### The finding: the Celery outbox relay

Redis is fenced by Sentinel. Postgres is fenced by Patroni's leader lock. **The
outbox relay is fenced by nothing** — it is a Celery task, and Celery beat's
famous property is that running two of it is a configuration mistake, not an
error.

```bash
./code/drill.sh "double-relay" \
  "docker compose -f infra/ha/compose.ha.yml up -d --scale celery-beat=2; sleep 60" \
  "docker compose -f infra/ha/compose.ha.yml up -d --scale celery-beat=1"
```
**Expected:**
```
double-relay            RTO=  0.00s  RPO=0 msgs  p99=390ms
  outbox rows relayed:      18,402
  XADD calls to Redis:      36,798      <-- ~2x
  duplicate deliveries:     18,396
  client-visible duplicates: 0          <-- dedup absorbed them (Module 05)
  ORDER VIOLATIONS observed: 41         <-- !!
```
❌ **Invisible in the RTO/RPO columns and real anyway.** Client-side dedup by
`clientId` hides the duplicates, so no user complains — but two relays racing the
same rows interleave their `XADD`s, and **41 messages entered the stream out of
sequence**, which the gap detector (Module 10) reports as a gap and answers with
a resume. Double Redis writes, double stream memory, and a resume storm you'd
blame on the network.

And it isn't hypothetical: a network partition during a Compose or Kubernetes
rollout produces exactly this, without anyone typing `--scale`.

### The fix that reuses something already fenced

The tempting fix is a Redis lock. **Don't** — you'd be adding an unfenced
coordinator to fix an unfenced coordinator, and Redlock's contested status
(Module 11) is a whole argument you don't need to have. You already run a
component with a real consensus protocol and real fencing: **Postgres.** Let the
database arbitrate.

```python
# chat/outbox.py
from django.db import transaction

CLAIM_SQL = """
UPDATE chat_outbox SET claimed_by = %s, claimed_at = now()
WHERE id IN (
    SELECT id FROM chat_outbox
    WHERE relayed_at IS NULL AND (claimed_at IS NULL OR claimed_at < now() - interval '30 s')
    ORDER BY id
    FOR UPDATE SKIP LOCKED          -- <-- the whole answer is these three words
    LIMIT %s
)
RETURNING id, room_id, payload;
"""

@shared_task
def relay_outbox(batch=500):
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(CLAIM_SQL, [WORKER_ID, batch])
            rows = cur.fetchall()
        for row_id, room, payload in rows:
            state_xadd(room, payload)                     # idempotent by client_id
        cur.execute("UPDATE chat_outbox SET relayed_at = now() WHERE id = ANY(%s)",
                    [[r[0] for r in rows]])
```

`FOR UPDATE SKIP LOCKED` means two relays **cannot** claim the same row: the
second one skips it and takes different work. And because all writes go through
PgBouncer → HAProxy `:5000` → the current Patroni leader, and HAProxy's
`on-marked-down shutdown-sessions` kills connections to a demoted node, **a relay
on the wrong side of a partition cannot claim anything at all** — it can't reach
a writable primary. Patroni's fencing now fences the relay too, for free.

**Re-run:**
```
double-relay-fixed      RTO=  0.00s  RPO=0 msgs  p99=268ms
  outbox rows relayed:      18,411
  XADD calls to Redis:      18,411      <-- exactly one each
  duplicate deliveries:     0
  order violations:         0
  throughput with 2 relays: 1.94x one relay     <-- SKIP LOCKED parallelizes cleanly
```
✅ **And it's now a feature**: two relays are a scaling knob rather than a bug.

> **The principle worth stealing:** when you need mutual exclusion, look for a
> component that *already* has consensus and fencing, and express your exclusion
> in its terms. Adding a second coordinator adds a second thing that can
> split-brain — and, unlike the first, one you have not tested.

### The second finding: the presence sweeper mass-evicts on recovery

```bash
./code/drill.sh "presence-storm-on-recovery" \
  "docker pause pulse-ha-redis-1-1; sleep 30; docker unpause pulse-ha-redis-1-1"
```
**Expected:**
```
[t=30s] redis unpaused; 18,412 presence keys had expired during the freeze
[t=31s] sweeper: emitting 18,412 presence.offline events
[t=33s] clients heartbeat; sweeper: emitting 18,412 presence.online events
presence-storm          RTO=  9.10s  RPO=0 msgs  p99=6,840ms   <-- 26x baseline
  presence events fanned out in 4s: 36,824
```
❌ **The Redis outage lasted 30 s; the presence storm it triggered hurt worse and
lasted longer.** Nobody was actually offline. This is the Module 11 presence-storm
lesson arriving as a *recovery* failure — the recovery, again, doing more damage
than the failure.

**Fix — the sweeper must know the difference between "user gone" and "Redis
gone":**

```python
async def sweep(self):
    # 1. Never trust the first tick after a reconnect.
    if time.monotonic() - self.layer_reconnected_at < GRACE_S:      # 60 s
        return
    # 2. Require TWO consecutive misses before declaring anyone offline.
    stale = await self._missing_heartbeats()
    confirmed = stale & self._stale_last_tick
    self._stale_last_tick = stale
    # 3. Cap the blast radius: if "everyone" is offline, the problem is us.
    if len(confirmed) > MAX_SWEEP_FRACTION * len(self.tracked):     # 5%
        log.error("sweeper refusing to evict %d/%d — treating as infra fault",
                  len(confirmed), len(self.tracked))
        SWEEP_REFUSED.inc()                       # alert on this
        return
    await self._emit_offline(confirmed)
```

```
presence-storm-guarded  RTO=  9.10s  RPO=0 msgs  p99=412ms
  presence events fanned out: 0
  sweeper refused once (18,412/19,900 = 92% > 5% threshold)
```
✅ **p99 6,840 → 412 ms.** Rule 3 is the important one: **any component that can
take a destructive action on many entities at once needs a sanity bound, because
"all of them" is almost always a bug in the detector rather than a truth about
the world.**

### The other two, briefly

- **Module 21's reconciliation loop** starts its `XREAD` cursor at `$`. A worker
  that starts *during* a partition misses every revocation published while it was
  booting. Fix: start from `0` bounded by the stream's `maxlen`, or persist the
  cursor per worker.
- **Module 14's shard-assignment map** is read from Redis with a TTL cache. Two
  nodes holding different versions during a resharding write the same room to two
  shards. Fix: version the map, carry the version on every write, and reject
  writes carrying a stale version — a **fencing token**, the same pattern Patroni
  uses. This one is not exploitable today only because we are not resharding.

---

## Task 4 — The drills in CI

### The suite

`ci/drills.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
# CI profile: 2 app nodes, Sentinel (not Cluster), 2,000 connections, 90s baseline.
export COMPOSE_FILE=infra/ha/compose.ha.yml:infra/ha/compose.ci.yml
docker compose up -d --wait                          # --wait, not `sleep 60`

fail=0
run() {  # name  inject  recover  max_rto  max_p99
  ./code/drill.sh "$1" "$2" "${3:-}"
  read -r rto rpo p99 < <(jq -r '[.rto,.rpo,.p99]|@tsv' "/tmp/drill-$1.json")
  base=$(jq -r .p99 /tmp/drill-baseline.json)
  # RELATIVE threshold on p99: CI hosts are noisy and an absolute one flaps.
  awk -v r="$rto" -v m="$4" 'BEGIN{exit !(r<=m)}' || { echo "FAIL $1 rto=$rto"; fail=1; }
  [ "$rpo" -eq 0 ] || { echo "FAIL $1 rpo=$rpo"; fail=1; }
  awk -v p="$p99" -v b="$base" -v m="$5" 'BEGIN{exit !(p<=b*m)}' \
      || { echo "FAIL $1 p99=$p99 (baseline $base)"; fail=1; }
}

run redis-pause    "docker pause pulse-ha-redis-1-1; sleep 20; docker unpause pulse-ha-redis-1-1" "" 15 12
run pg-kill        "docker kill pulse-ha-patroni1-1" "docker start pulse-ha-patroni1-1"           15 12
run rolling-deploy "./code/rolling_deploy.sh"        ""                                            2  3
exit $fail
```

**Thresholds: RTO ≤ 15 s, RPO = 0, p99 ≤ N× the run's own baseline.**

### Runtime

```
docker compose up -d --wait          3m 10s
baseline capture                     1m 30s
redis-pause                          3m 05s
pg-kill                              2m 55s
rolling-deploy                       3m 00s
--------------------------------------------
total                               13m 40s     ✅ under the 15-minute budget
```

Three drills, not eleven. Getting there required cutting: 10,000 → 2,000
connections, 3 → 2 app nodes, 120 → 90 s baselines, and Cluster → Sentinel. The
three kept are the ones that regress: the Redis timeout tuning, the Patroni TTL,
and the graceful drain — i.e. **the three configuration changes the lab's
scoreboard identified as buying the most.** A CI suite should guard the settings
most likely to be silently reverted, not sample the drill space evenly.

### The false-positive rate, honestly

**First 20 runs against known-good `main`: 2 failures (10%).** Causes:

| Cause | Fix |
|-------|-----|
| Absolute p99 threshold flapping on a noisy shared runner | Compare to the **run's own baseline**, not a constant |
| `sleep 60` occasionally not enough for 15 containers | `docker compose up -d --wait` |
| `rolling-deploy` RTO occasionally 0.4 s from a single unlucky reconnect | Take the **median of 3** injections for this drill only (+80 s, affordable) |

**Next 20 runs: 0 failures.**

And here is the part the challenge asks you to be honest about: **0 out of 20
does not demonstrate a rate below 5%.** With zero observed failures in 20 trials,
the 95% upper bound on the true rate is `1 − 0.05^(1/20) ≈ 13.9%` — consistent
with a 10% flake rate. To *claim* < 5% you need enough trials that the upper
bound lands there.

```
runs   failures   observed   95% upper bound
  20          0        0%             13.9%
  60          1      1.7%              8.9%
 120          1      0.8%              4.6%   <-- the first row that supports the claim
```

We ran **120 nightly runs against a pinned known-good commit: 1 failure (0.8%,
95% CI upper 4.6%).** That is the number to report. Reporting "0/20, so under
5%" is the same species of error as reporting a load test's p99 from a
closed-loop generator — a real measurement that does not support the sentence
built on it.

> **What CI drills are actually for:** not finding new failures (you find those by
> designing new drills, as in Task 2) but **stopping a fix from being silently
> reverted.** `socket_timeout: 2.0` is one line in a settings file that a
> refactor deletes without a test noticing. That line cost 5.7 seconds of RTO to
> discover. This suite is the thing that makes it stay.

---

## Task 5 — What HA costs, and the honest halving

### Four dimensions

| | `compose.dev.yml` | Full HA stack | Δ |
|---|-------------------|---------------|---|
| **p50 fan-out** | 11 ms | 14 ms | +27% |
| **p99 fan-out** | 138 ms | 210 ms | +52% |
| **Node fan-out knee** | 150,000/s | 138,000/s | −8% |
| **Containers** | 2 | 15 | 7.5× |
| **RAM** | 1.1 GB | 8.9 GB | 8.1× |
| **Host cores at idle** | 0.3 | 2.1 | 7× |
| **Cost/month (cloud list, 3× c6i.xlarge + 3× m6i.large + storage)** | **~$140** | **~$1,180** | **8.4×** |

The latency comes from real hops: nginx (+1 ms), PgBouncer (+0.5 ms), HAProxy
(+0.4 ms), and `synchronous_commit: on` on the Patroni leader (+1 ms on writes).
None of it is waste — each one is buying a specific failure mode — but it should
be stated as a cost, not absorbed.

### The halving that people reach for first, and why it's the wrong one

"Drop a replica everywhere": 2 Patroni members, 2 Redis, 2 app nodes → ~$610/mo.

| | Effect |
|---|-------|
| RTO | 11.8 → 12.5 s (barely changes — quorum lives in etcd, which we kept at 3) |
| RPO | 0 → **0 *unless* the failure happens during a write burst**; with one replica there is no second copy to fall back on if it is lagging |
| App capacity | **the survivor of two nodes carries 100%**, so the margin that absorbed a failure is gone — and Module 18's own brownout drill is the proof that a node at capacity is worse than a node that's dead |

**It halves the bill and eats the entire safety margin.** You have kept the HA
diagram and thrown away the reason it works.

### The halving that is actually defensible

**Reduce the ambition, not the redundancy.** Keep Redis HA (Sentinel, 3+3) —
because losing the fan-out backbone means chat is *down*. Drop Patroni, etcd and
HAProxy (7 containers) and run **one Postgres primary with one streaming replica
and a documented manual promotion**.

| | Full HA | Reduced ambition |
|---|---------|------------------|
| Containers / RAM | 15 / 8.9 GB | **8 / 4.3 GB** |
| Cost/month | ~$1,180 | **~$390 (−67%)** |
| Redis failure | RTO 9 s, RPO 0 | **unchanged** |
| App node failure | RTO 4 s, RPO 0 | **unchanged** |
| Rolling deploy | 0 s, 0 lost | **unchanged** |
| **Postgres primary failure** | RTO 11.8 s | **RTO ~5 min (a human promotes)**, RPO 0 |
| During those 5 minutes | — | **history and reading keep working** (the replica serves reads via the Module 13 DB router); **sending is down** |

The decision to put in front of a non-engineer is not "do you want HA." It is:

> *"Roughly twice a year, for about five minutes, people will be able to read
> chat but not send. That costs $790 a month less. Yes or no?"*

For a 50-person internal tool, that is obviously yes. For a paid product with an
SLA, obviously no. **Both answers are correct, and neither is available until you
have the number** — which is what the drills were for.

**What we would *not* cut at any price:** the Redis tier's HA and the graceful
drain. The drain costs **zero dollars** (it is application code) and turns a
routine deploy from an 18.4 s / 2,841-message outage into a non-event. The best
availability spend in this entire module is free, and it is the one most teams
never write.

---

## Task 6 (stretch) — The runbook, and the blind test

### The structure

One page per drill, four sections, in this order (which is the order a person at
3 a.m. needs them):

```
## Postgres primary unavailable
ALERT      PulsePrimaryWriteFailure — outbox backlog > 500 for 60s
           (NOT "postgres is down": the failure mode is a DEMOTED primary
            that is up, healthy, and read-only)
TRIAGE     1. docker exec pulse-ha-patroni1-1 patronictl -c /home/postgres/postgres.yml list
           2. curl -s localhost:7000 | grep -A2 postgres_write
           3. docker exec pulse-ha-etcd1-1 etcdctl endpoint health --cluster
REMEDIATE  Leader present, HAProxy shows it DOWN  -> HAProxy healthcheck; restart haproxy
           No leader, etcd healthy                -> patronictl failover
           etcd unhealthy                         -> restore etcd quorum FIRST;
                                                     Postgres is read-only BY DESIGN
                                                     until it returns. Do not force.
ESCALATE   No leader after 5 min, or any sign of divergent timelines in
           `patronictl list` (two members on different TL)  -> wake the DB owner.
           DO NOT run `patronictl reinit` on a node you have not confirmed is a
           replica: it destroys its data directory.
```

### The blind test

Three failures injected without telling the operator which. Findings:

| Where they got stuck | Minutes lost | Fix |
|---|---|---|
| `patronictl` needs `-c <path>` and the path differs by image | 6 | Put the **exact** command with the path in the runbook; ship a `pctl` shell alias in the image |
| The alert said "Postgres down"; `docker ps` showed it **up**, so they assumed a false alarm and looked elsewhere | 11 | **Rename the alert to describe the symptom, not the guess**: `PulsePrimaryWriteFailure`. This was the single most expensive line in the exercise |
| For the clock-skew drill (Task 2), no runbook entry existed at all — they found it by reading application logs | 14 | Add the entry; add `auth_fail_rate` to the dashboard's front page |
| They ran `patronictl reinit` on the *leader* while looking for a way to "resync" | ∞ (aborted) | The `DO NOT` line above did not exist. It does now |

**Total: 31 minutes of avoidable delay across three incidents, and one destructive
command that was only stopped because the exercise was supervised.**

> **The most valuable output of the blind test was not the missing entry — it was
> the alert name.** An alert that states a *conclusion* ("Postgres is down") sends
> the responder to verify the conclusion, and when they disprove it they stop
> trusting the alert. An alert that states a *symptom* ("writes are failing")
> sends them toward the cause. Module 20 makes this a rule for all four SLO alerts.

---

## Record it

```markdown
## Module 18 — challenge

1. channels_redis DOES NOT speak Redis Cluster — it shards client-side across
   `hosts`. Pointing it at cluster nodes "works" while broadcasting every
   PUBLISH to every node (~3x, silent). Answer: TWO topologies — Sentinel
   shards for the channel layer, a real Cluster for streams/presence/buckets.
   Migration 0.00s downtime, 0 lost, +23% p99 while dual-writing, 14 min.
   CROSSSLOT x3; Module 21's ticket pipeline was THE misplaced tag. Streams +
   seq worked untouched: Module 08's {room_id} tag turned a rewrite into a
   config change.
2. New drills: disk-full (38.4s; found an INACTIVE replication slot pinning
   4.2GB of WAL — the classic silent PG disk outage); clock skew +45s (a node
   alive, fast and WRONG passes every health check -> jwt leeway=30 AND an
   auth-success-rate signal on readiness: 90s -> 14.9s, failed connects 33% ->
   0.3%); one Uvicorn worker killed (container stays healthy while dead channel
   names sit in every group for group_expiry = 86,400s BY DEFAULT -> 14.4% of
   deliveries wasted for a day. Set 300.)
3. Split-brain: two Celery relays -> 2x XADD and 41 ORDER VIOLATIONS, invisible
   in RTO/RPO because dedup hides them. Fixed with FOR UPDATE SKIP LOCKED so
   POSTGRES arbitrates — reuse something already fenced instead of adding an
   unfenced lock; 2 relays now scale 1.94x. Also: the presence sweeper
   mass-evicts 18,412 users on Redis recovery (p99 6,840ms) -> reconnect grace
   + two-tick confirmation + a 5% blast-radius bound (412ms).
4. CI: 3 drills, 13m40s, p99 threshold relative to THIS RUN's baseline.
   0/20 only bounds the true flake rate at 13.9%; 1/120 = 0.8% (CI upper 4.6%)
   is the number that supports "under 5%".
5. HA costs 8.4x money, +52% p99, -8% knee. Dropping replicas keeps the diagram
   and deletes the margin. Honest halving = REDUCE THE AMBITION: keep Redis HA,
   drop Patroni/etcd/HAProxy, manual PG promotion. $1,180 -> $390/mo, PG RTO
   11.8s -> ~5 min, reads keep working. Never cut the graceful drain: $0, and
   the best availability spend in the module.
6. Blind runbook test: 31 min lost. Most expensive finding = an alert named
   after a CONCLUSION ("Postgres down") when the box was up and demoted.
   Name alerts after SYMPTOMS.
```

Then: [`19-kubernetes-ha-and-multiregion`](../../19-kubernetes-ha-and-multiregion/)
— where every one of these mechanisms gets a Kubernetes-native equivalent, and
the `preStop sleep` turns out to be the `DRAIN_DELAY` you already built.
