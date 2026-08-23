# Solutions — Module 18

---

## Task 1 — Sentinel to Cluster, live

### The migration

```bash
# 1. Stand up a 6-node cluster alongside the Sentinel setup
docker compose -f infra/ha/compose.cluster.yml up -d
docker exec pulse-ha-rc1-1 redis-cli --cluster create \
  rc1:6379 rc2:6379 rc3:6379 rc4:6379 rc5:6379 rc6:6379 \
  --cluster-replicas 1 --cluster-yes
```
```
[OK] All 16384 slots covered.
M: rc1 slots:[0-5460]      S: rc4 replicates rc1
M: rc2 slots:[5461-10922]  S: rc5 replicates rc2
M: rc3 slots:[10923-16383] S: rc6 replicates rc3
```

**2. Dual-write, drain, cut over** — the same four-phase shape as Module 14's
shard migration:

```java
@Component
public class RedisMigrationRouter {
    private volatile Mode mode = Mode.SENTINEL_ONLY;

    public void append(String roomId, Envelope e) {
        if (mode != Mode.CLUSTER_ONLY) sentinelFanout.append(roomId, e);
        if (mode != Mode.SENTINEL_ONLY) clusterFanout.append(roomId, e);
    }
    // Consumers read from whichever is authoritative for the current mode.
}
```
```bash
curl -X POST localhost:8080/api/admin/redis/mode -d '{"mode":"DUAL_WRITE"}'
sleep 300                                    # let the Streams replay window fill
curl -X POST localhost:8080/api/admin/redis/mode -d '{"mode":"CLUSTER_READ"}'
sleep 300
curl -X POST localhost:8080/api/admin/redis/mode -d '{"mode":"CLUSTER_ONLY"}'
```

**Measured with a load test running:**
```
migration downtime: 0.00s
messages lost: 0
p99 during DUAL_WRITE: 268ms (baseline 214ms — +25% from writing twice)
total migration time: 12m
```
✅ Zero downtime. The dual-write window costs 25% p99, which is why you don't
leave it running.

### The `CROSSSLOT` errors

```bash
k6 run -e ROOMS=100 --duration 3m ../../06-load-testing-harness/code/pulse-load.js
```
**Expected — three distinct failures:**

**(a) The rate limiter:**
```
io.lettuce.core.RedisCommandExecutionException:
  CROSSSLOT Keys in request don't hash to the same slot
    script: multi_bucket.lua
    keys: rate:{alice}:room:7, rate:{alice}:all, rate:{room.7}:room, rate:{room.7}:ip:1.2.3.4
```
Module 11's challenge predicted this exactly. Two of the four keys are tagged
`{alice}` and two `{room.7}` — different slots.

**Fix:** the two-script split from Module 11's solution, which was written for
this moment:
```java
check(scriptA, List.of("rate:{" + userId + "}:room:" + roomId,
                       "rate:{" + userId + "}:all"), ...);
check(scriptB, List.of("rate:{" + roomId + "}:room",
                       "rate:{" + roomId + "}:ip:" + ip), ...);
```

**(b) The presence `MGET`:**
```
CROSSSLOT Keys in request don't hash to the same slot
  MGET presence:{u1} presence:{u2} presence:{u3} ...
```
Different users hash to different slots, so one `MGET` can't span them.

**Fix — group by slot, then one `MGET` per slot, pipelined:**
```java
public Map<String, String> statusOf(Collection<String> userIds) {
    // Lettuce's cluster client CAN do this automatically for MGET, but only if
    // you use the cluster-aware API. With RedisTemplate you must group yourself.
    var bySlot = userIds.stream().collect(Collectors.groupingBy(
            id -> SlotHash.getSlot(key(id))));

    var result = new HashMap<String, String>();
    redis.executePipelined((RedisCallback<Object>) conn -> {
        bySlot.values().forEach(group -> conn.stringCommands()
                .mGet(group.stream().map(id -> key(id).getBytes()).toArray(byte[][]::new)));
        return null;
    }).forEach(/* zip back */);
    return result;
}
```
**Measured:** 1 round trip → **3 round trips** (one per primary). p50 went from
0.14 ms to 0.31 ms. Acceptable, and it's the irreducible cost of sharding.

**(c) The append script (Module 08's `append.lua`):**
```
No error!
```
✅ Because `room:{7}:seq` and `room:{7}:stream` share the tag `{7}`.

### Why the hash tags are where they are

**The tag defines your atomicity boundary.** Everything you will ever need to
touch in one script or one multi-key command must share it.

| Key | Tag | Why there |
|-----|-----|-----------|
| `room:{7}:stream` | `{7}` | must be atomic with the seq counter |
| `room:{7}:seq` | `{7}` | same |
| `unread:{42}` | `{42}` | per-user hash, only ever touched alone or with other user-42 keys |
| `presence:{42}` | `{42}` | ditto |
| `rate:{alice}:*` | `{alice}` | all of a user's buckets checked together |

The design rule: **choose the tag to be the entity whose operations must be
atomic.** For Pulse that's the room (for messages) and the user (for state) — the
same two entities the whole system is partitioned by, which is not a coincidence.

**The cost of getting it wrong is discovered only in Cluster**, which is why
tagging keys from Module 08 onward — while still on a single node — was the
right call. Retrofitting hash tags means changing every key name in a live
system.

---

## Task 2 — Three drills the lab missed

### Drill A — Disk full on the Postgres primary

```bash
./code/drill.sh "pg-disk-full" \
  "docker exec pulse-ha-patroni1-1 bash -c 'fallocate -l 20G /home/postgres/pgdata/ballast'" \
  "docker exec pulse-ha-patroni1-1 rm /home/postgres/pgdata/ballast"
```
**Expected:**
```
PANIC:  could not write to file "pg_wal/xlogtemp.42": No space left on device
LOG:  server process (PID 142) was terminated by signal 6: Aborted
patroni1: postgres is not running
patroni2: promoted self to leader
pg-disk-full                 RTO= 13.20s  RPO=0 msgs  p99=2,410ms
```
✅ Handled — Patroni saw the process die and failed over. **But:**

```bash
docker exec pulse-ha-patroni1-1 rm /home/postgres/pgdata/ballast
docker start pulse-ha-patroni1-1
docker exec pulse-ha-patroni1-1 patronictl -c /home/postgres/postgres.yml list
```
```
| patroni1 | Replica | stopped   |    |   unknown |
```
```
patroni1: pg_rewind required but no rewind is possible: the source is not a superuser
```
❌ **The old primary cannot rejoin.** It crashed mid-write with a diverged
timeline, and `pg_rewind` isn't configured. You are running on 2 of 3 nodes until
someone manually re-bases it, which is hours of reduced redundancy nobody noticed.

**The fix — enable automatic rewind and a fallback to reinit:**
```yaml
PATRONI_POSTGRESQL_USE_PG_REWIND: "true"
PATRONI_POSTGRESQL_REMOVE_DATA_DIRECTORY_ON_REWIND_FAILURE: "true"
PATRONI_POSTGRESQL_REMOVE_DATA_DIRECTORY_ON_DIVERGED_TIMELINES: "true"
PATRONI_POSTGRESQL_PARAMETERS_wal_log_hints: "on"     # required by pg_rewind
```
**And prevent it entirely** — a WAL ballast file, which is a standard Postgres
practice and almost nobody does:
```bash
# Reserve 2GB. When the disk fills, delete this to buy time for a graceful fix.
docker exec pulse-ha-patroni1-1 fallocate -l 2G /home/postgres/pgdata/emergency_ballast
```
Plus the alert that should have fired first:
```yaml
- alert: PostgresDiskRunway
  expr: predict_linear(node_filesystem_avail_bytes{mountpoint="/pgdata"}[6h], 24*3600) < 0
  for: 30m
  annotations: { summary: "pgdata will be full within 24h at current growth" }
```
**Re-run:**
```
pg-disk-full-v2              RTO= 12.90s  RPO=0 msgs
  old primary rejoined automatically via pg_rewind in 41s
```

### Drill B — Clock skew

```bash
./code/drill.sh "clock-skew" \
  "docker exec --privileged pulse-ha-pulse-1-1 date -s '+45 seconds'" \
  "docker exec --privileged pulse-ha-pulse-1-1 date -s '-45 seconds'"
```
**Expected:**
```
clock-skew                   RTO=  0.00s  RPO=0 msgs  p99=224ms
```
No visible failure — but check the data:
```bash
docker exec pulse-ha-patroni1-1 psql -U postgres -d pulse -c \
  "SELECT id, seq, created_at FROM messages WHERE room_id='room.5' ORDER BY seq DESC LIMIT 5;"
```
```
        id         | seq |          created_at
-------------------+-----+-------------------------------
 137204812048384   | 412 | 2026-08-23 14:41:02+00
 137204857438208   | 411 | 2026-08-23 14:41:47+00    <-- 45s in the FUTURE
 137204812048385   | 410 | 2026-08-23 14:41:02+00
```
❌ **Snowflake IDs and timestamps from the skewed node are 45 seconds ahead**, so
`id` order no longer matches `seq` order. Module 13's partition **time hint**
(derived from the Snowflake timestamp) can now look past a partition boundary and
return an incomplete page.

Worse:
```
java.lang.IllegalStateException: clock moved backwards by 45000ms
```
on recovery — Module 05's generator refuses to issue IDs, and that node stops
accepting sends for 45 seconds.

**Fixes:**
1. `chronyd`/`ntpd` with **slew, not step** (`makestep 0 -1` after startup), so
   the clock never jumps backwards.
2. Make the ID generator tolerate small backward steps instead of refusing:
```java
if (now < lastMillis) {
    long drift = lastMillis - now;
    if (drift <= MAX_TOLERATED_DRIFT_MS) {      // 5000
        now = lastMillis;                        // wait it out by reusing the ms
        clockDriftTolerated.increment();
    } else {
        throw new IllegalStateException("clock moved backwards by " + drift + "ms");
    }
}
```
3. **Widen the partition time hint** from 1 day to cover plausible skew — it
   already was, which is why it survived. Good design, confirmed by a drill.
4. Alert on skew:
```yaml
- alert: ClockSkew
  expr: abs(node_timex_offset_seconds) > 0.5
```

### Drill C — DNS failure

```bash
./code/drill.sh "dns-failure" \
  "docker exec pulse-ha-pulse-1-1 sh -c 'echo \"0.0.0.0 redis-1 redis-2 redis-3\" >> /etc/hosts'; sleep 60" \
  "docker exec pulse-ha-pulse-1-1 sh -c 'sed -i \"/0.0.0.0 redis/d\" /etc/hosts'"
```
**Expected:**
```
dns-failure                  RTO= 60.00s  RPO=2,104 msgs  p99=timeout
```
❌ **Worst result after the brownout.** Existing Redis connections kept working
(they're already established), but:
- The **Sentinel failover** couldn't complete, because the app resolves the new
  primary's hostname when Sentinel tells it to switch.
- **Reconnects failed**, so any connection that dropped never came back.
- The node stayed **healthy** in every check, because its existing connections
  worked.

**The fixes:**
1. Cache DNS in the JVM, but not forever:
```bash
-Dnetworkaddress.cache.ttl=30 -Dnetworkaddress.cache.negative.ttl=1
```
The default `networkaddress.cache.negative.ttl=10` means a failed lookup is
cached for 10 seconds — during a failover, that's 10 extra seconds of RTO.
2. Make DNS resolution part of readiness:
```java
@Component("dnsHealth")
public class DnsHealthIndicator implements HealthIndicator {
    public Health health() {
        for (String host : criticalHosts) {
            try { InetAddress.getByName(host); }
            catch (UnknownHostException e) {
                return Health.down().withDetail("unresolvable", host).build();
            }
        }
        return Health.up().build();
    }
}
```
**Re-run:**
```
dns-failure-v2               RTO=  9.40s  RPO=0 msgs
  pulse-1 readiness DOWN at t=6.1s, nginx removed it at t=9.4s
```
✅ The node removed itself once it could no longer resolve its dependencies.

> **The pattern across all three drills:** each failure was survivable, and each
> revealed that a component could be *broken but reporting healthy*. That is the
> single most valuable thing chaos testing finds.

---

## Task 3 — The cost of HA

```bash
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'
```

| | Single-node dev | Full HA |
|---|----------------|---------|
| Containers | 3 | **15** |
| RAM (idle) | 0.4 GB | **3.8 GB** |
| RAM (under load) | 4.2 GB | **11.4 GB** |
| CPU (under load) | 3.1 cores | **7.8 cores** |
| p50 fan-out | **19 ms** | 24 ms |
| p99 fan-out | **178 ms** | 214 ms |
| Throughput (knee) | 790k/s | **762k/s** |
| RTO | **hours** (manual) | 12 s |
| RPO | up to 24 h | **0** |

**Latency cost: +26% p50, +20% p99.** From: PgBouncer hop, HAProxy hop, nginx
hop, and `synchronous_commit=on` waiting for a replica.

### Cloud cost (AWS us-east-1, on-demand, monthly)

| Component | Single-node | HA |
|-----------|-------------|-----|
| App (c6i.2xlarge) | 1 × $248 | 3 × $248 = **$744** |
| Postgres (r6i.2xlarge + 500 GB gp3) | 1 × $412 | 3 × $412 = **$1,236** |
| Redis (r6i.xlarge) | 1 × $206 | 6 × $206 = **$1,236** |
| etcd (t3.small) | — | 3 × $15 = **$45** |
| HAProxy + nginx (t3.medium) | — | 2 × $30 = **$60** |
| Cross-AZ data transfer | $0 | **$310** |
| Backups (S3) | $28 | $28 |
| **Total** | **$894** | **$3,659** |

**4.1× the cost.**

### Halving it: what to give up

| Option | Saving | New RTO | New RPO | Verdict |
|--------|--------|---------|---------|---------|
| **A. Redis Sentinel (3 nodes) instead of Cluster (6)** | $618 | unchanged | unchanged | ✅ **do this first** — Cluster is for sharding, and we don't shard Redis yet |
| **B. 2 Postgres nodes instead of 3** | $412 | unchanged | unchanged... | ❌ **no** — 2 nodes cannot form a quorum; you lose automatic failover entirely |
| **C. Async replication instead of sync** | $0 | unchanged | **up to 200 ms of writes** | ⚠️ maybe |
| **D. 2 app nodes instead of 3** | $248 | unchanged | unchanged | ⚠️ one node loss = 50% capacity loss |
| **E. Single AZ** | $310 | unchanged | unchanged | ❌ an AZ failure takes everything |
| **F. Managed services (RDS Multi-AZ, ElastiCache)** | −$400 (**costs more**) | 60–120 s | 0 | ⚠️ worse RTO, much less ops work |

**Recommendation: A + D = $866 saved (24%), no change to RTO or RPO.**

To actually halve it you must take C or E:
- **C (async replication)** costs you RPO — up to ~200 ms of writes lost on
  failover. For chat that's ~2,000 messages at peak. **The outbox makes this
  survivable** (Module 13): the messages are in the outbox on the surviving node
  and get republished. So C is *cheaper than it looks* specifically because of an
  earlier design decision.
- **E (single AZ)** is the honest "we accept an AZ outage" trade. Many products
  make it. It should be a stated decision, not a default.

**Final: A + D + C = $1,278 saved (35%), RPO becomes ~200 ms of writes, mitigated
by the outbox.** Getting to 50% requires E, and that's a business decision.

> The interesting finding: **option B looks like the obvious saving and is the
> one that destroys your HA entirely.** Three nodes isn't redundancy for its own
> sake; it's the minimum quorum.

---

## Task 4 — Drills in CI

`code/ci-drills.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
FAILED=0

# Scaled down: 2,000 VUs, 90s per drill. Enough to measure, fast enough for CI.
run_drill() {
  local name="$1" inject="$2" recover="${3:-}" max_rto="$4" max_rpo="$5"
  local result; result=$(./code/drill.sh "$name" "$inject" "$recover" --ci)
  local rto rpo
  rto=$(jq -r .rto <<<"$result"); rpo=$(jq -r .rpo <<<"$result")

  if (( $(echo "$rto > $max_rto" | bc -l) )) || (( rpo > max_rpo )); then
    echo "FAIL $name: RTO=${rto}s (max ${max_rto}) RPO=${rpo} (max ${max_rpo})"
    FAILED=1
  else
    echo "PASS $name: RTO=${rto}s RPO=${rpo}"
  fi
}

# Thresholds: 2x the measured median, so normal variance doesn't fail the build.
run_drill redis-kill    "docker kill pulse-ha-redis-1-1"    "docker start pulse-ha-redis-1-1"    16  0
run_drill pg-kill       "docker kill pulse-ha-patroni1-1"   "docker start pulse-ha-patroni1-1"   26  0
run_drill app-kill      "docker kill pulse-ha-pulse-1-1"    "docker start pulse-ha-pulse-1-1"    10  0
run_drill rolling       "./code/rolling_deploy.sh --fast"   ""                                    3  0
run_drill brownout      "docker update --cpus 0.1 pulse-ha-pulse-1-1; sleep 30" \
                        "docker update --cpus 2.0 pulse-ha-pulse-1-1"                            24  0
exit $FAILED
```

```yaml
# .github/workflows/ha-drills.yml
name: HA drills
on: { push: { branches: [main] } }
jobs:
  drills:
    runs-on: ubuntu-latest-8-cores
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f infra/ha/compose.ha.yml up -d --wait
      - run: ./code/ci-drills.sh
      - if: failure()
        run: docker compose -f infra/ha/compose.ha.yml logs --tail=200
```

### Timing

```
stack startup:        3m 42s
redis-kill:           1m 30s
pg-kill:              1m 30s
app-kill:             1m 30s
rolling:              2m 10s
brownout:             1m 30s
teardown:               20s
------------------------------
total:               12m 12s     ✅ under 15
```

### False-positive rate over 20 runs

```
runs 1-20: 18 PASS, 2 FAIL
  run 7:  pg-kill RTO=27.4s (threshold 26)    -- GitHub runner contention
  run 14: brownout RTO=25.1s (threshold 24)   -- same
false positive rate: 10%
```
❌ **Too high.** A suite that fails 10% of the time gets disabled within a
fortnight.

**Two fixes:**
1. **Retry once on failure** — independent 10% failures give 1% combined:
```bash
run_drill ... || run_drill ...
```
2. **Threshold on the median of 3 short runs**, not one:
```bash
rtos=(); for i in 1 2 3; do rtos+=("$(./code/drill.sh ... --ci | jq -r .rto)"); done
median=$(printf '%s\n' "${rtos[@]}" | sort -n | sed -n 2p)
```
This costs 3× the time, which blows the 15-minute budget — so use it only for the
two flaky drills.

**Final measured over 20 runs with retry-once: 0/20 false positives, 13m 40s.**

✅ And it catches real regressions: reverting `PATRONI_TTL` to 30 gives
```
FAIL pg-kill: RTO=24.8s (max 26)  -- passes!
```
❌ **It doesn't.** The threshold was set at 2× the *tuned* median, which is
larger than the *untuned* value. **Set thresholds from the target, not from the
current measurement:**
```bash
run_drill pg-kill "..." "..." 15 0        # our stated RTO target, not 2x median
```
```
FAIL pg-kill: RTO=24.8s (max 15)
```
✅ Now it catches it.

> **The lesson:** a threshold derived from current behaviour ratifies whatever
> you currently do. Derive it from the SLO you committed to.

---

## Task 5 — The remaining split-brain

The lab proved fencing for Redis and Patroni. Three candidates remain; **two are
fine and one is a real bug.**

### Candidate 1: the presence sweeper — fine

Module 11 replaced the lock with hash partitioning. A partitioned node sweeps its
own share and double-announces at worst. Idempotent, harmless.

### Candidate 2: the shard assignment map — fine, and deliberately so

Module 14's solution added the freshness fence:
```java
if (System.nanoTime() - lastRefreshOk > Duration.ofSeconds(5).toNanos())
    throw new ServiceUnavailableException("shard map may be stale", 1000);
```
A partitioned node **stops writing**. Verified:
```bash
docker network disconnect pulse-ha_default pulse-ha-pulse-1-1
sleep 8
# from inside the container:
curl -s localhost:8080/api/test/send -d '{"room":"room.1"}'
```
```
{"error":"unavailable","message":"shard map may be stale"}
```
✅ Fenced.

### Candidate 3: the outbox relay — **the real bug**

```java
@Scheduled(fixedDelay = 50)
@Transactional
public void relay() {
    var batch = jdbc.sql("... FOR UPDATE SKIP LOCKED").query(...).list();
    for (var row : batch) streamFanout.append(...);          // publish
    jdbc.sql("UPDATE outbox SET published_at = now() ...").update();
}
```

`FOR UPDATE SKIP LOCKED` prevents two relays racing **through the database**. But
consider a **long GC pause or network partition on the relay node**:

```
t=0    relay-1 SELECTs 100 rows FOR UPDATE, holds the transaction open
t=1    relay-1 publishes rows 1-40 to Redis
t=2    relay-1 GC-pauses for 45 seconds
t=3    its Postgres connection times out; the transaction ABORTS, locks released
t=4    relay-2 SELECTs the same 100 rows (published_at still NULL) and
       publishes ALL 100
t=48   relay-1 resumes, finishes publishing rows 41-100, then UPDATEs
```

**Rows 1–40 are published twice, and rows 41–100 are published twice.** That's
absorbed by `clientId` idempotency — so is it a bug?

**Yes, for a subtler reason.** Relay-1's `UPDATE ... SET published_at` runs in a
**dead transaction** and fails, so it retries the whole batch on the next tick.
Under sustained pressure this becomes a loop:

```bash
./code/drill.sh "relay-pause" \
  "docker exec pulse-ha-pulse-1-1 kill -STOP 1; sleep 45; docker exec pulse-ha-pulse-1-1 kill -CONT 1"
```
**Expected:**
```
relay-pause                  RTO=  0.00s  RPO=0 msgs
```
But:
```bash
docker exec pulse-ha-redis-1-1 redis-cli XLEN 'room:{1}:stream'
docker exec pulse-ha-patroni1-1 psql -U postgres -d pulse -c \
  "SELECT count(*) FROM outbox WHERE published_at IS NULL;"
```
```
(integer) 84,102        <-- vs 41,204 messages actually sent
 12,841                 <-- backlog that isn't draining
```
❌ **2× stream amplification and a growing backlog.** Redis memory doubles, the
consumers do twice the work, and the dedup cache absorbs it silently — so nothing
alerts. It's a **capacity** bug masquerading as correctness.

### The fix: fence the relay with a generation token

```sql
ALTER TABLE outbox ADD COLUMN claimed_by text, ADD COLUMN claimed_at timestamptz;
CREATE INDEX ON outbox (claimed_at) WHERE published_at IS NULL;
```
```java
@Transactional
public void relay() {
    String claim = nodeId + ":" + claimGeneration.incrementAndGet();

    // Claim in one statement. The claim is DURABLE, unlike a row lock.
    var batch = jdbc.sql("""
            UPDATE outbox SET claimed_by = :claim, claimed_at = now()
            WHERE id IN (
                SELECT id FROM outbox
                WHERE published_at IS NULL
                  AND (claimed_at IS NULL OR claimed_at < now() - interval '60 seconds')
                ORDER BY id LIMIT 100
                FOR UPDATE SKIP LOCKED)
            RETURNING id, aggregate_id, payload::text
            """).param("claim", claim).query(OutboxRow.class).list();

    for (var row : batch) {
        streamFanout.append(row.aggregateId(), parse(row.payload()));
        // Publish AND mark, per row, with the claim as a fence. If another relay
        // reclaimed this row while we were paused, our UPDATE matches 0 rows and
        // we know not to keep going.
        int updated = jdbc.sql("""
                UPDATE outbox SET published_at = now()
                WHERE id = :id AND claimed_by = :claim
                """).param("id", row.id()).param("claim", claim).update();

        if (updated == 0) {
            staleClaimAborts.increment();
            log.warn("claim {} was superseded; aborting batch", claim);
            return;                          // stop immediately
        }
    }
}
```

**Re-run:**
```
relay-pause-fenced           RTO=  0.00s  RPO=0 msgs
  stream length: 41,204     (1.0x -- no amplification)
  outbox backlog: 3
  stale_claim_aborts: 1
```
✅ **2× amplification eliminated.** Relay-1 resumed, found its claim superseded on
the first row, and stopped.

> **The general lesson, and it's Module 11's fencing-token argument arriving in
> practice:** a database row lock is released when the *connection* dies, which
> is not the same as when the *work* stops. A durable claim with a comparison at
> write time is a fencing token, and this is the case where it was actually worth
> building.

---

## Task 6 (stretch) — The runbook, blind-tested

`docs/RUNBOOK.md` (excerpt):

```markdown
## Alert: RedisFailover

**Fires when:** `redis_sentinel_master_switches_total` increases.

**First three commands:**
1. `docker exec sentinel-1 redis-cli -p 26379 SENTINEL master pulse`
   -> confirms which node is primary NOW
2. `curl -s localhost:8080/actuator/health | jq .components.redis`
   -> confirms the app reconnected
3. `docker exec redis-<old> redis-cli INFO replication | head -3`
   -> confirms the old primary demoted to `role:slave`

**Expected:** app health UP within 15s; old primary shows `role:slave`.

**Remediation:** none if the above hold. This is designed behaviour.

**Escalate if:** the old primary still shows `role:master` after 60s
(SPLIT BRAIN -- page immediately), or app health stays DOWN after 60s
(check DNS: `docker exec pulse-1 getent hosts redis-2`).

---

## Alert: ChatP99High

**Fires when:** `chat_fanout_latency_p99 > 2000` for 3m.

**First three commands:**
1. `curl -s localhost:8080/actuator/prometheus | grep stomp_channel_queued`
   -> is the outbound queue backing up? (the leading indicator)
2. `docker exec redis-1 redis-cli --latency` and `SLOWLOG GET 5`
   -> is Redis the problem?
3. `docker stats --no-stream | grep pulse-`
   -> is ONE node hot (brownout) or all of them (capacity)?

**Decision tree:**
- One node hot, others fine -> BROWNOUT. It should have shed itself; check
  `curl localhost:8080/actuator/health/readiness` on that node. If UP, the
  capacity indicator is broken -- restart the node and file a bug.
- All nodes hot -> genuine capacity. Scale out; do NOT restart.
- Redis SLOWLOG shows a slow command -> find who ran it (Module 08).

**Escalate if:** scaling out doesn't reduce p99 within 5 minutes.
```

### The blind test

An engineer who didn't build the system, given the runbook, with a drill injected
without being told which:

| Drill injected | Found it? | Time | Where they got stuck |
|----------------|-----------|------|---------------------|
| Redis primary kill | ✅ | 2m | — |
| PG primary kill | ✅ | 3m | — |
| App node brownout | ⚠️ | **14m** | **The runbook said "check readiness on that node" but not HOW to reach a node behind nginx.** Spent 9 minutes trying to curl through the LB. |
| etcd quorum loss | ❌ | **gave up at 20m** | **No alert existed for it.** They saw "writes failing", followed the ChatP99High tree, concluded "capacity", and scaled out — which did nothing. |
| DNS failure | ⚠️ | 11m | Diagnosed correctly but the runbook's remediation was "fix DNS", which isn't actionable. |

### What the blind test revealed

**1. Missing alert (etcd) is worse than a missing runbook entry.** They never got
to the right page because nothing pointed there. Added:
```yaml
- alert: EtcdQuorumLost
  expr: count(up{job="etcd"} == 1) < 2
  for: 30s
  labels: { severity: page }
  annotations:
    summary: "etcd quorum lost -- Postgres is READ-ONLY"
    runbook: "docs/RUNBOOK.md#etcdquorumlost"
```

**2. Commands must be copy-pasteable, including how to reach the thing.**
```markdown
**First three commands:**
1. For each node: `docker exec pulse-<n> curl -s localhost:8080/actuator/health/readiness | jq`
   (bypass nginx -- you need the NODE's view, not the LB's)
```
That one line would have saved 9 minutes.

**3. "Fix DNS" is not a remediation.** Replaced with:
```markdown
**Remediation:**
1. `docker exec pulse-1 getent hosts redis-1` -- does it resolve?
2. If not: `docker network inspect pulse-ha_default | jq '.[0].Containers'`
   -- is the container still attached?
3. Reattach: `docker network connect pulse-ha_default pulse-1`
4. If DNS is broken cluster-wide, the node will shed itself (dnsHealth).
   Confirm with `curl -s localhost:8080/actuator/health | jq .components.dnsHealth`
```

> **The most valuable output of this exercise is not the runbook — it's the list
> of things that were obvious to the author and opaque to everyone else.** Run
> the blind test before the incident, not during it.
