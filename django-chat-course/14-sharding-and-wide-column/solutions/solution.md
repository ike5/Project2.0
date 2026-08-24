# Solutions 14 — Sharding & Wide-Column

Reference answers with the reasoning, the rejected alternative, and the measured
numbers. Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12,
Postgres 16, ScyllaDB 6.0, Django 5.1 / Channels 4.1.**

---

## Task 1 — Break the migration in both dangerous phases

### Phase 1 (dual write): what actually happens

```bash
python manage.py migrate_shard --logical 3824 --to 2 &
sleep 3
docker kill pulse-app-node-b            # 8 of 24 worker processes die
```

**Result: nothing is lost, nothing is duplicated, nothing is split.** Phase 1 is
safe by construction, and it is worth being precise about *why*:

- Reads still go to the source shard. The map says `state='migrating'`, and
  `physical_shard` is unchanged.
- Writes go to both. The target's rows are a **superset-in-progress** of the
  source's, and nothing reads them.
- A killed worker's in-flight write to the target may be lost. It does not
  matter: phase 2's backfill and phase 3's tail copy both use
  `ON CONFLICT (room_id, seq) DO NOTHING`, so the row is copied again.

Prove it:
```sql
-- source
SELECT count(*), max(seq) FROM messages WHERE room_id = ANY(:rooms);
-- target
SELECT count(*), max(seq) FROM messages WHERE room_id = ANY(:rooms);
```
```
source: 184609 | 41221
target: 181044 | 41221        <- behind on history, current on the tail
```
✅ Target is behind by exactly the un-backfilled history. Resume the migration
and it converges.

> The general principle: **a phase in which nothing is authoritative on the
> target is a phase you can crash in.** Design your migrations so that the
> irreversible step is as short and as late as possible. Phase 3 is 210 ms out of
> 48 seconds.

### Phase 3 (drain and cutover): the real hazard

```bash
python manage.py migrate_shard --logical 3824 --to 2 --pause-before-commit &
sleep 50
docker kill pulse-app-node-b
```

Now the failure mode depends on **exactly where** you land, and there are three
distinct outcomes:

| Killed | Assignment says | Outcome |
|--------|----------------|---------|
| Before `_commit()` | `draining`, `migrating_to=2` | **Stuck.** Writes rejected until an operator intervenes. Safe, but a partial outage for 1/4096 of traffic. |
| Between `_commit()` and the second `_await_fleet` | `active`, `physical=2` | **SPLIT.** Surviving workers with the stale map write to shard0; reloaded workers write to shard2. |
| After the second `_await_fleet` | `active`, `physical=2` | Clean. |

The middle row is the one that hurts, and here is what it looks like:

```sql
-- shard0, AFTER cutover
SELECT max(seq) FROM messages WHERE room_id='room.7';   -- 41,388
-- shard2
SELECT max(seq) FROM messages WHERE room_id='room.7';   -- 41,402
```

Both shards have rows nobody else has. `seq` is per-room and allocated in Redis,
so there are **no duplicate seqs** — which is worse, not better: every row is
unique and real, and the two sets differ. There is no key collision to alert you.
A scrollback page reads shard2 and silently omits the 14 messages on shard0. The
client's gap detector sees `seq` 41,388 → 41,403 and issues a `resume` (Module
10), which reads the same shard and returns the same hole, forever.

**That is the worst outcome available in this module: silent, permanent,
undetectable-by-the-client message loss, produced by a migration that reported
success.**

### The fix: fence on version, count processes

Three mechanisms, and you need all three.

**1. A monotonic map version, and an acknowledgement per worker process.**

```python
FLEET_KEY = "pulse:shardmap:versions"    # HASH  worker -> loaded version

async def _await_fleet(self, version, deadline_s=30.0):
    deadline = time.monotonic() + deadline_s
    while time.monotonic() < deadline:
        reported = await self.redis.hgetall(FLEET_KEY)
        if sum(1 for v in reported.values() if int(v) >= version) >= self.expected_workers:
            return
        await asyncio.sleep(0.05)
    raise TimeoutError(...)              # ABORT, do not proceed
```

**Why counting nodes is not sufficient**, and this is the Python-specific half of
the answer: Pulse runs **one Uvicorn worker process per core**. Each process is a
separate interpreter with its own memory and its own copy of the assignment list.

```
3 machines × 8 workers = 24 independent copies of the map
```

A node-level health check tells you the *container* is up. It tells you nothing
about whether all eight interpreters inside it have polled `shard_assignment`
since version N. Worker 5 on node A can be blocked in a slow query, or its
watcher task can have died from an unhandled exception, while the node's
`/healthz` returns 200. Twenty-three of twenty-four is a split.

This is the same "the worker process is the unit, not the machine" fact that:
- made the `InMemoryChannelLayer` fail on a single box (Module 04),
- turned Streams read amplification from O(nodes) into O(nodes × cores) (Module 09),
- multiplied `max_connections` pressure by the core count (Module 13).

Fourth appearance. It never stops being true.

**2. A write fence on the shard itself.** Fleet acknowledgement is a distributed
consensus you built out of a Redis hash, and it can be wrong. Belt and braces:
stamp the map version into the write.

```sql
-- on each shard, before the write
CREATE TABLE shard_fence (fence_version bigint NOT NULL);

-- the send path, in the same transaction as the INSERT
INSERT INTO messages (...)
SELECT ... WHERE (SELECT fence_version FROM shard_fence) <= %s;
```

Cutover bumps the **source** shard's `fence_version` past the writer's version,
so a stale worker's insert affects zero rows and raises in the application rather
than landing in the wrong database. Cost: one extra subquery per insert,
**+0.04 ms** measured — 4.4% on a 0.9 ms write, and it converts the module's
worst failure mode into an exception.

**3. Make phase 3 idempotent and resumable.** Store the migration's own state:

```sql
CREATE TABLE shard_migration (
    logical_shard int PRIMARY KEY,
    from_physical int, to_physical int,
    phase text,                     -- dual_write|backfill|drain|committed|cleaned
    map_version bigint,
    started_at timestamptz, updated_at timestamptz
);
```

A coordinator that dies mid-phase-3 restarts, reads `phase='drain'`, re-runs the
tail copy (free — `ON CONFLICT DO NOTHING`), re-verifies counts, and re-commits.
`_commit()` is already idempotent because it is a single `UPDATE` to a known
value.

**Measured after the fix:**
```
kill during phase 1:  0 lost  0 duplicated  0 split   (resumed, converged)
kill during phase 3:  0 lost  0 duplicated  0 split   (12.4 s stall, then resumed)
```
✅ The 12.4 s stall is writes rejected for 1/4096 of traffic while a new
coordinator picks up. Clients see `error` frames with `retry_after_ms` and retry
with the same `client_id`. Nobody loses a message.

---

## Task 2 — Shrink 6 → 4

### Why it is harder

Growing is *additive*: an empty shard receives logical shards from several
donors, and every donor can push in parallel because the target rows do not
collide.

Shrinking is *subtractive and convergent*. Four survivors must absorb 1,364
logical shards from two shards that must then be **empty**. Three consequences:

**1. You cannot parallelize per-target the same way.** Every target is receiving
from both departing shards simultaneously, and each incoming logical shard is a
sustained write load on a database that is already serving its own traffic.
Growth spread the write load across new, idle hardware; shrink concentrates it on
the machines you are keeping.

**2. "Empty" must be *proven*, not assumed.** The dangerous case is a room
written to during the final merge whose logical shard the coordinator already
believes it has drained. Growth had no equivalent — the source stayed
authoritative until the flip.

**3. The order is forced.** Every logical shard on a departing physical shard must
reach `state='active'` on its new home **before** you may decommission the
container. Growth had no ordering constraint at all.

### The implementation

```python
def plan_shrink(assignment: list[int], new_n: int) -> dict[int, int]:
    old_n = max(assignment) + 1
    if new_n >= old_n:
        raise ValueError("use plan_rebalance for growth")

    base, extra = divmod(LOGICAL_SHARDS, new_n)
    target = [base + (1 if i < extra else 0) for i in range(new_n)]

    held: dict[int, list[int]] = {p: [] for p in range(old_n)}
    for logical, physical in enumerate(assignment):
        held[physical].append(logical)

    # EVERYTHING on a departing shard must move. That is not a choice, so it is
    # not part of the optimization -- and it is why shrink moves MORE than the
    # theoretical minimum for the surviving shards' own rebalance.
    evacuating = [l for p in range(new_n, old_n) for l in held[p]]

    # Then top up survivors that are still under target, taking from the
    # fullest survivor. Minimal movement among survivors, forced movement off
    # the departing ones.
    moves: dict[int, int] = {}
    for physical in range(new_n):
        while len(held[physical]) < target[physical] and evacuating:
            logical = evacuating.pop()
            held[physical].append(logical)
            moves[logical] = physical
    assert not evacuating, "target capacity does not fit the evacuated shards"
    return moves
```

**Measured, 6 → 4:**
```
shards moved:            1,364  (every logical shard on shard4 and shard5)
rows copied:        25,109,442
wall clock:              71m 18s   (vs 58m 42s for 4 -> 6)
pause p99 per shard:       238 ms  (vs 224 ms)
total write-unavailable:  5m 25s   summed across 1,364 x ~238 ms
messages lost:                 0
```

21% slower than the growth case for the same shard count and the same row count,
because the receiving databases are also serving production traffic. Budget for
that: **a shrink is not a growth run in reverse.**

### The hazard, made concrete

Add a room to a logical shard the coordinator has already drained but not yet
committed:

```bash
python manage.py migrate_shard --logical 3900 --to 1 --pause-after-drain &
sleep 20
# a write arrives for a room in logical shard 3900
curl -XPOST localhost:8000/api/rooms/room.912/messages -d '{"body":"hi"}'
```
**Without the fence:** the write lands on shard5, which is decommissioned an hour
later. The message is gone, and no gap detector fires, because `seq` 4,411 was
never delivered to anyone.

**With Task 1's `shard_fence`:** the insert matches zero rows, the application
raises, and the client gets an `error` frame with `retry_after_ms`. Retried with
the same `client_id` after the cutover, it lands on shard1.

✅ **The fence you built for growth is what makes shrink survivable.** That is
the argument for building it even though growth appeared safe without it.

---

## Task 3 — The scatter-gather ceiling

### Measured against the model

```bash
python manage.py bench_unread --mode gather-async --sweep 4,16,64,256
```

| Shards `k` | Predicted (each shard's p(99^(1/k))) | Measured p99 | Ratio |
|-----------|--------------------------------------|--------------|-------|
| 4 | shard p99.75 ≈ 24 ms | **29 ms** | 1.21 |
| 16 | shard p99.94 ≈ 44 ms | **52 ms** | 1.18 |
| 64 | shard p99.98 ≈ 96 ms | **118 ms** | 1.23 |
| 256 | shard p99.996 ≈ 210 ms | **deadline (200 ms), 31% partial** | — |

The model is right to within ~20%, consistently. The residual is not noise; it is
**two effects the independence assumption ignores**:

1. **Shared client resources.** All `k` requests come from one worker process,
   through one event loop, competing for the same `asyncio.Semaphore` and the
   same CPU to parse the responses. At `k=64` the *client* serializes work the
   model assumed was parallel.
2. **Correlated tails.** Shard latencies are not independent. A checkpoint on the
   host, a page-cache eviction from a big backfill, or the load generator's own
   GC hits several shards at once.

Both make the real p99 *worse* than the model, which is the safe direction to be
wrong in when you are choosing a deadline.

### The constant-time design

The only way to make p99 independent of `k` is to **stop fanning out**. Maintain
the answer instead of computing it.

```
Write path (already exists, Module 10):
    Lua: seq = INCR room:{7}:seq ; XADD ...

Add, in the same Lua script:
    HSET  room:last_seq  room.7  <seq>          -- one hash, all rooms

Read path:
    HMGET room:last_seq room.7 room.42 ...       -- ONE round trip, any k
    HMGET user:{u}:read  room.7 room.42 ...      -- ONE round trip
    unread = last_seq - last_read_seq            -- client-side subtraction
```

**Measured:**

| Shards | Scatter-gather p99 | Maintained-counter p99 |
|--------|--------------------|------------------------|
| 4 | 29 ms | **0.31 ms** |
| 16 | 52 ms | **0.31 ms** |
| 64 | 118 ms | **0.33 ms** |
| 256 | > 200 ms deadline | **0.36 ms** |

✅ **Flat.** Two Redis round trips, regardless of shard count, because the unread
count never touches Postgres at all.

### What it costs — state it honestly

**1. Staleness bounded by the Lua script's success.** The hash is updated inside
the same Lua script that allocates `seq`, so it is atomic with the allocation and
cannot drift *forward*. It can drift *backward* if Redis is restored from an RDB
snapshot — Module 08's persistence discussion, arriving as a correctness surface.
Recovery: recompute `last_seq` per room from the shards, which is the very
scatter-gather you were avoiding, run once at startup rather than per request.

**2. Memory.** One hash field per room. At 1M rooms:
```bash
redis-cli MEMORY USAGE room:last_seq
```
```
78,412,288        # ~78 MB for 1M rooms in one hash
```
78 MB against Module 09's ~6 GB of stream buffers. Free, in context.

**3. A Redis Cluster problem you must plan for now.** One hash key means one hash
slot means **one node holds 100% of unread traffic** (Module 18). The fix is to
shard the hash by room — `room:last_seq:{7}` — which restores `HMGET` to N round
trips for N slots. Module 11 made the identical call for rate-limit keys and took
the extra round trip. Take it here too, and note that `{7}` hashes to slot
**1716** (`redis-cli CLUSTER KEYSLOT 'room:last_seq:{7}'`) — the same slot as
Module 09's `room:{7}:stream`, which is exactly the co-location the hash tag is
for.

**4. It is now write-amplified, mildly.** One extra `HSET` per message, inside a
script that was already running. Measured: **31,904 → 31,102 sends/s**, a 2.5%
cost for eliminating an entire class of read.

**The rejected alternative:** caching the scatter-gather result with a 5-second
TTL. It reduces the *rate* of scatter-gathers but not the *tail* — every cache
miss still pays the `p(99^(1/k))` price, and misses cluster exactly when a room
is busy. **Caching a slow query makes it rarer, not faster.** For a p99 target you
must change the mechanism, not the frequency.

---

## Task 4 — A cross-shard schema migration, under load

### The runbook (written first — that is the task)

```markdown
# RB-014: add messages.thread_id across the sharded tier

Blast radius: all message writes. Rollback: yes, until step 6.
Fleet: 24 worker processes across 3 nodes. Shards: 4 (+ default).

1. PRE-FLIGHT
   - Confirm 24/24 workers reporting to pulse:shardmap:versions
   - Confirm no migration in flight: shard_migration WHERE phase <> 'cleaned'
   - Confirm autovacuum is not mid-run on `messages` on any shard

2. ADD THE COLUMN, NULLABLE, NO DEFAULT, one shard at a time
   ALTER TABLE messages ADD COLUMN thread_id bigint;      -- metadata-only in PG 11+
   Expected: < 50 ms per shard, ACCESS EXCLUSIVE held briefly.
   HARD RULE: no DEFAULT, no NOT NULL, no index. Any of those rewrites the
   table, and this table has 19 billion rows per shard.

3. VERIFY ALL SHARDS
   for s in 0..3: \d messages | grep thread_id
   ABORT if any shard is missing it. Skew here is the whole hazard.

4. DEPLOY CODE THAT *WRITES* IT (feature flag OFF for reads)
   Rolling, one node at a time. During this window some workers write it and
   some do not -- which is FINE, because the column is nullable.

5. VERIFY 24/24 WORKERS ON THE NEW BUILD
   pulse:build:versions hash, same mechanism as the shard map.

6. TURN READS ON. <-- irreversible point: clients now depend on the column.

7. BACKFILL (optional), in keyset batches of 5,000, rate-limited to keep
   replica lag < 1 s (Module 13's measured p99 340 ms + headroom).

8. INDEX, CONCURRENTLY, one shard at a time, off-peak
   CREATE INDEX CONCURRENTLY idx_messages_thread ON messages (room_id, thread_id)
     WHERE thread_id IS NOT NULL;
   Expected: ~18 min per shard. CONCURRENTLY does two passes and does not take
   a write lock. It CAN leave an INVALID index if it fails -- check and DROP.

ROLLBACK before step 6: turn the flag off; the column is inert.
ROLLBACK after step 6: forward-fix only.
```

### The three things that make it work

**1. Additive first, always.** Nullable, no default, no constraint. In Postgres 11+
`ADD COLUMN ... DEFAULT x` is also metadata-only, but `NOT NULL` without a default
is a full validation scan and `NOT NULL` with one is fine — the rules are subtle
enough that "nullable, no default" is the one you should memorize.

**2. Django must tolerate both schemas at once.** Module 12 made `Message` a
`managed = False` model, so `makemigrations` will not generate this DDL and the
`RunSQL` migration is hand-written per shard. During step 4:

```python
class Message(models.Model):
    thread_id = models.BigIntegerField(null=True)     # nullable in the model too
    class Meta:
        managed = False
```

**3. Version skew is the hazard, and it is a fleet problem.** Twenty-four worker
processes are deployed one node at a time. For the duration of step 4:

```
node-a (8 workers)  new build, writes thread_id
node-b (8 workers)  old build, writes NULL
node-c (8 workers)  old build, writes NULL
```

That is correct *because the column is nullable*. It is a data-loss bug the moment
anything in step 6 assumes non-null. The runbook's step 5 exists for exactly that
gate, and it reuses the fleet-acknowledgement mechanism from Task 1 rather than
inventing a second one.

**Measured, executed under 5,000 Locust users:**
```
ALTER TABLE, 4 shards:            31 ms, 28 ms, 34 ms, 29 ms
lock waits observed:              0
message.create errors:            0
message.create p99 during ALTER:  61 ms -> 74 ms -> 61 ms
CREATE INDEX CONCURRENTLY:        17m 41s, 18m 02s, 17m 55s, 18m 12s (serialized)
replica lag peak during backfill: 780 ms
messages lost:                    0
```
✅ Zero errors. The p99 blip is the brief `ACCESS EXCLUSIVE` lock; at 30 ms it is
inside one Locust sample.

---

## Task 5 — Durable Scylla idempotency without LWT on the hot path

### Why the lab's Redis answer is not good enough

```
Scylla LWT (IF NOT EXISTS)          2.3 ms   durable forever
Scylla + Redis SET NX               0.21 ms  durable for 300 s, gone on restart
```

Part E measured three duplicate messages delivered after `docker restart
pulse-redis`. Three is not zero, and the guarantee Modules 05/09/10 built the
delivery chain on was "a redelivery is a no-op," not "a redelivery is usually a
no-op."

### The design: make `client_id` part of the clustering key

The hint is the answer. Put `client_id` **in the primary key of the messages
table itself**, so that a duplicate insert is not a conflict to detect — it is
the same row.

```sql
CREATE TABLE messages (
    room_id    text,
    bucket     int,
    seq        bigint,
    client_id  text,
    id         bigint,
    sender text, body text, reply_to bigint, created_at timestamp,
    PRIMARY KEY ((room_id, bucket), seq, client_id)
) WITH CLUSTERING ORDER BY (seq DESC, client_id ASC);
```

Cassandra's write model is **last-write-wins upsert on the full primary key**. Two
inserts with the same `(room_id, bucket, seq, client_id)` produce one row, with
no read, no Paxos, and no conflict detection — because there is no conflict.

**Measured:**
```
insert p50:            0.09 ms   (unchanged -- it is a plain insert)
duplicate rows after 10 min of forced redelivery:  0
duplicate rows after `docker restart pulse-redis`: 0    (Redis is not involved)
duplicate rows after gc_grace + repair:            0
```

### What it costs — and it is not free

**1. It only works because `seq` is already allocated idempotently.** Module 10's
Lua script allocates `seq` and Module 05's retry rule says a client MUST reuse the
same `client_id`. But a retry that reaches a *different* worker gets a *different*
`seq` — a new `INCR`. Then `(seq=482, client_id=X)` and `(seq=483, client_id=X)`
are two different rows and you are back to duplicates.

So the design **requires** moving the seq allocation to be keyed by `client_id`:

```lua
-- allocate_seq.lua, extended
local existing = redis.call('HGET', KEYS[2], ARGV[1])   -- room:{7}:seqmap, client_id
if existing then return existing end                     -- SAME seq for a retry
local seq = redis.call('INCR', KEYS[1])
redis.call('HSET', KEYS[2], ARGV[1], seq)
redis.call('EXPIRE', KEYS[2], 300)
return seq
```

Which puts a five-minute window back in Redis — but a *different* one. If it is
lost, the retry gets a new `seq` and Scylla stores two rows. The client's gap
detector sees both, and Module 10's client-side dedup (`drop if seq <= contiguous`)
does **not** catch them, because they have different seqs.

**Honest verdict: the guarantee is now durable in the store and bounded in the
allocator.** That is strictly better than the lab's version (which was bounded in
both), and it is not the unconditional guarantee Postgres's unique index gave.

**2. The read path pays.** `client_id` in the clustering key means:
- Every scrollback row carries an extra ~26-byte clustering component. Storage:
  **6.2 GB → 7.4 GB** for 50M messages, +19%.
- Range reads by `seq` still work (`seq` is the first clustering column), but a
  point read of one message now needs both `seq` and `client_id`, so the reply-to
  lookup needs a third table or a `seq`-prefix range scan returning one row.
- Measured scrollback: **0.71 ms → 0.79 ms p50**, +11%.

**3. Deletes get worse.** Two clustering columns means a tombstone per
`(seq, client_id)` rather than per `seq`. For an append-only, TTL-expiring table
this is immaterial — which is only true because Pulse soft-deletes.

### The rejected alternatives

| Design | Why not |
|--------|---------|
| LWT on every send | 2.3 ms → 5.1 ms at RF=3. 25–60× the plain insert, on the hottest path in the system. |
| LWT only on *retries* (client sets a `retry=true` flag) | The client cannot be trusted to set it, and a retry that lost its flag is a duplicate. Correctness that depends on a client hint is not correctness. |
| Materialized view keyed on `client_id` | Cassandra MVs are asynchronously maintained and can diverge from the base table with no error. The Cassandra project itself marks them experimental. Do not build a correctness guarantee on them. |
| Accept duplicates; dedup on the client | Module 10's client dedup is `seq <= contiguous`, which two different seqs defeat. And a second device that was offline never sees the first copy to dedup against. |

---

## Task 6 — Compaction's real cost

### Drive it until it falls behind

```bash
python code/store_bench.py scylla-1node --duration 20m --rooms 200 &
watch -n 10 'docker exec pulse-scylla1 nodetool tablestats pulse.messages \
  | grep -E "SSTable count|Space used \(live\)"'
```

**Expected, over 20 minutes:**

| t (min) | SSTables | Pending compactions | Read amp | Scrollback p99 | p99.9 |
|---------|----------|---------------------|----------|----------------|-------|
| 0 | 3 | 0 | 1.2 | 1.9 ms | 44 ms |
| 5 | 9 | 1 | 2.8 | 2.4 ms | 61 ms |
| 10 | 17 | 4 | 5.1 | 3.8 ms | 112 ms |
| 15 | 26 | 9 | 7.9 | 6.1 ms | 208 ms |
| 20 | 34 | 14 | 10.4 | **9.2 ms** | **410 ms** |

✅ **p99.9 degrades 9× while throughput is constant.** Nothing errors, no alert
fires on inserts/s, and the only signal is a number in `nodetool`. This is why
`pending_compactions` and `sstables_per_read` belong on your dashboard from day
one (Module 20 puts them there).

Read amplification comes straight out of the structure:
```bash
docker exec pulse-scylla1 nodetool tablehistograms pulse.messages
```
```
SSTables per Read
  50%:     3.00
  95%:     8.00
  99%:    14.00
```
A p99 read touches 14 sstables: 14 bloom-filter checks, and up to 14 disk seeks
for the ones that lie. Postgres's B-tree is 3–4 levels, always, forever. That is
the entire p99.9 story.

### The three strategies, measured

Same workload, 20 minutes, 1 node, after the strategy has stabilized:

| | STCS | LCS | **TWCS** |
|---|------|-----|----------|
| Insert p50 | **0.09 ms** | 0.14 ms | **0.09 ms** |
| Insert throughput | **118,000/s** | 71,400/s | **116,900/s** |
| Scrollback p50 | 0.88 ms | **0.61 ms** | 0.71 ms |
| Scrollback p99.9 | 190 ms | **31 ms** | 47 ms |
| SSTables per read (p99) | 22 | **4** | 9 |
| Write amplification | 3.1× | **14.8×** | **1.9×** |
| Disk used, 50M msgs | 9.8 GB | 6.0 GB | **6.2 GB** |
| Space needed for compaction | **up to 2× table** | ~10% | one window |
| Expiring 90-day data | rewrites live+dead together | same | **drops whole sstables** |

**SizeTieredCompactionStrategy** merges similarly-sized sstables. It has the
cheapest writes and the worst reads, because old and new data mix into ever-larger
files and a read must check many of them. Its real disqualifier for Pulse is the
last row: TTL-expired rows sit in a 40 GB sstable alongside live ones, and are
only reclaimed when that whole file is rewritten. Retention stops being free.

**LeveledCompactionStrategy** guarantees ~90% of reads touch one sstable. Its reads
are the best of the three by a wide margin. Its **14.8× write amplification** is
disqualifying for an append-heavy workload — insert throughput drops 39%, and on
real disks that amplification is the thing that wears them out.

**TimeWindowCompactionStrategy** buckets sstables by write time and compacts only
within a window. For Pulse:
- Writes are append-only and time-ordered, so a window's data is written once and
  never touched again — **1.9× write amplification, the lowest of the three.**
- Reads are time-clustered (scrollback is recent), so a read touches recent
  windows, not all of history: **9 sstables at p99, not 22.**
- **Expiry drops whole sstables.** When every row in a window has passed its
  `default_time_to_live`, Scylla deletes the file. That is the LSM equivalent of
  Module 13's `DROP TABLE messages_2026_05` — and just as cheap.

✅ **The lab's choice stands: TWCS**, and the deciding column is not latency, it is
the write-amplification and expiry rows. LCS wins the p99.9 by 16 ms; it loses 39%
of write throughput and turns retention into a rewrite.

**The condition that would overturn it:** if reads stopped being time-clustered —
a full-text search feature that scans arbitrary history, or a compliance export —
TWCS's advantage evaporates and LCS's single-sstable read becomes worth the write
cost. Which is Task 7's point about falsifiable revisit conditions, arriving on
its own.

**One TWCS trap to write down:** rows written *out of order* (a backfill, or a
repair streaming old data) land in the current window with old timestamps, and
that sstable then cannot be dropped on expiry until its newest row expires. Never
backfill historical data into a TWCS table without `nodetool refresh` and a plan.

---

## Task 7 (stretch) — The ADR, attacked

### ADR-014: Message storage for Pulse at 10k msg/s

**Status:** Accepted · **Date:** 2026-08 · **Deciders:** platform

**Context.** Module 12 projects 204 GB/day, 864M rows/day, 74 TB/year. Module 13's
90-day retention leaves 18.4 TB live and 77.8 billion rows. A single Postgres
absorbs 41,200 raw inserts/s on a laptop; the target is 10,000 msg/s.

**Decision.** Stay on **PostgreSQL**, time-partitioned (Module 13), with
**application-level sharding by `Room.key` over 4,096 logical shards** behind a
Django DB router — and **do not deploy shards until a single primary is measurably
the constraint.** Build the router now; run one shard.

**Evidence.**

| | PG single | PG ×4 | Scylla ×1 | Scylla ×3 |
|---|-----------|-------|-----------|-----------|
| Inserts/s (4 procs) | 44,100 | 148,400 | 118,000 | 291,000 |
| Scrollback p99.9 | 9 ms | 9 ms | 47 ms | 44 ms |
| Idempotency p50 | 0.08 ms | 0.08 ms | 2.3 ms | 5.1 ms |
| Storage, 50M | 11 GB | 11 GB | 6.2 GB | 18.6 GB |

**Consequences we accept.**
- Unread counts become a maintained Redis counter (Task 3), not a query.
- Adding capacity is a 58-minute orchestrated rebalance, not `nodetool`.
- A single hot room can saturate one shard; the mitigation is a 210 ms migration
  to a dedicated database.
- We carry the router's complexity — `ContextVar`, fleet fencing, per-shard
  migrations — from the day we build it, for a capacity we do not yet need.

**Revisit if — three falsifiable conditions:**
1. Sustained writes exceed **300,000/s** for 7 consecutive days (75% of the
   measured 4-shard ceiling).
2. Storage exceeds **40% of the infrastructure bill** for two consecutive
   quarters (Scylla's 44% storage advantage becomes worth its costs).
3. A single logical shard exceeds **60% CPU on a dedicated database** — the point
   at which our only remaining mitigation is exhausted.

### The attack, and what it changed

> **"You built a router you are not using. That is speculative complexity, and
> the course spent Module 12 telling people not to do that."**

Partly fair, and it changed the decision. The original draft said "shard now." The
distinction that survives: **the router is cheap and reversible; the shards are
not.** `code/shard_router.py` is 180 lines, and with `SHARD_COUNT=1` it is a
`ContextVar` and a modulo. What it buys is that the *schema* stays shardable —
no cross-database FKs, no `bigserial`, no global unique constraints assumed. Those
are the decisions that are expensive to reverse, and they are made in Module 12,
not here. Ship the router, run one shard, and let condition 1 pull the trigger.

> **"Condition 2 is not falsifiable. Nobody knows what 40% of the bill means."**

Correct, and it was rewritten. The original said "if storage cost becomes
dominant," which is a feeling. It now names a percentage, a period, and where the
number comes from. If you cannot say what measurement would prove you wrong, you
have not made a decision — you have expressed a preference.

> **"You are comparing sharded Postgres against Scylla on write throughput, but
> your actual constraint is the Python client. Four shards only reached 148k/s
> because you ran four processes. Scylla at three nodes reached 291k/s on the same
> four processes — so Scylla is 2× better *per client core*, which is the resource
> you are actually short of."**

The strongest objection, and it stands. Part E's measurement supports it: the
Python driver reached 291k/s against Scylla and 148k/s against four Postgres
shards **from the same four processes**. Scylla is genuinely cheaper per client
core, and the ADR should say so instead of leading with a throughput number that
flatters Postgres.

What it does not overturn is the idempotency row (0.08 ms vs 2.3–5.1 ms, on the
path every single message takes) or the outbox (which requires a transaction
Cassandra does not have). Those are correctness, and correctness outranks cost per
core. **Amended:** condition 1's threshold drops from 300,000/s to **200,000/s**,
because the ceiling that binds is client cores, not shard capacity — and Task 5's
durable-idempotency design is now a documented prerequisite for any future move,
rather than something to figure out during the migration.
