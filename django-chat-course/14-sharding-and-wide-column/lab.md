# Lab 14 — Shard It With a Router, Then Model It in ScyllaDB

**You'll:** build logical sharding as a Django DB router, move a logical shard
while traffic flows, hit the threadpool wall with scatter-gather and fix it,
model the same chat data in ScyllaDB, manufacture a hot partition, and benchmark
both stores head to head.

⏱️ ~120 min.

> **Low-memory path:** two Postgres shards instead of four, and a single Scylla
> node with `--smp 1 --memory 1G`. Part E loses its three-node column; every
> conclusion holds.

Reference machine throughout: **8-core / 16 GB, Ubuntu 24.04, Python 3.12,
Postgres 16, Uvicorn + uvloop, Django 5.1 / Channels 4.1.**

---

## Part A — Logical shards and the router

### A1. Stand up the tier

Module 13's stack stays up — `default` still owns rooms, memberships, the outbox
and (as of this module) the assignment table.

```bash
docker compose -p pulse-repl  -f infra/compose.replica.yml up -d --wait
docker compose -p pulse-shard -f infra/compose.shards.yml  up -d --wait
docker compose -p pulse-shard -f infra/compose.shards.yml ps --format '{{.Name}} {{.Status}}'
```

**Expected:**
```
pulse-shard0 Up 22 seconds (healthy)
pulse-shard1 Up 22 seconds (healthy)
pulse-shard2 Up 22 seconds (healthy)
pulse-shard3 Up 22 seconds (healthy)
```
✅ Four Postgres instances that know nothing about each other. There is no
`depends_on` between them in the compose file, and that independence is the whole
product of sharding.

### A2. The hash, before anything else

Before you write a router, convince yourself the hash is stable and even. This is
arithmetic, not a benchmark — **your numbers will match these exactly.**

```bash
python - <<'PY'
import zlib, collections
LOGICAL = 4096
def logical(room_key): return zlib.crc32(room_key.encode()) % LOGICAL

print("room.7       ->", logical("room.7"))
print("room.general ->", logical("room.general"))

c = collections.Counter(logical(f"room.{i}") % 4 for i in range(1000))
print("1,000 rooms over 4 shards:", dict(sorted(c.items())))
PY
```
**Expected:**
```
room.7       -> 3824
room.general -> 2980
1,000 rooms over 4 shards: {0: 249, 1: 251, 2: 249, 3: 251}
```
✅ **Within 0.4% of even**, and identical on every machine and every Python
version. That last property is the one that matters.

> ⚠️ **Never use Python's `hash()` as a shard function.** It is randomized per
> process by `PYTHONHASHSEED`, so eight Uvicorn workers would put `room.7` on
> eight different shards. The symptom is that 7 out of 8 reads return an empty
> room, intermittently, and it reproduces on nothing. Use CRC32, MurmurHash, or
> xxHash — something with a specification.

Now the resharding arithmetic that justifies the whole logical-shard scheme:

```bash
python - <<'PY'
import zlib
def h(i): return zlib.crc32(f"room.{i}".encode())
N = 200_000
for new in (5, 6, 7, 8):
    moved = sum(1 for i in range(N) if h(i) % 4 != h(i) % new)
    print(f"naive mod 4->{new}: {100*moved/N:5.1f}% of rooms move "
          f"(minimum {100*(1-4/new):5.1f}%)")
PY
```
**Expected:**
```
naive mod 4->5:  79.8% of rooms move (minimum  20.0%)
naive mod 4->6:  66.6% of rooms move (minimum  33.3%)
naive mod 4->7:  85.8% of rooms move (minimum  42.9%)
naive mod 4->8:  50.0% of rooms move (minimum  50.0%)
```
✅ Note the last line. **Doubling is the only growth step where naive modulo is
optimal.** A team that has only ever doubled has never discovered that it has a
resharding problem — and then goes 8 → 12 during an incident.

### A3. The assignment table

```bash
psql "postgresql://pulse:pulse@localhost:5432/pulse" <<'SQL'
CREATE TABLE shard_assignment (
    logical_shard  int PRIMARY KEY,
    physical_shard int NOT NULL,
    state          text NOT NULL DEFAULT 'active',
    migrating_to   int,
    version        bigint NOT NULL DEFAULT 1,
    updated_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT state_valid CHECK (state IN ('active','migrating','draining'))
);

INSERT INTO shard_assignment (logical_shard, physical_shard)
SELECT g, g % 4 FROM generate_series(0, 4095) g;

SELECT physical_shard, count(*) FROM shard_assignment GROUP BY 1 ORDER BY 1;
SQL
```
**Expected:**
```
 physical_shard | count
----------------+-------
              0 |  1024
              1 |  1024
              2 |  1024
              3 |  1024
```
✅ 4,096 logical shards, 1,024 per database. This table is the **only** thing in
the system that knows where a room lives.

### A4. Settings, and the router order

`pulse/settings/shards.py`:

```python
from .redis import *          # Module 07's channel layer, still in force

SHARD_COUNT = 4

DATABASES["default"] = {**DATABASES["default"], "HOST": "localhost", "PORT": 5432}
for i in range(SHARD_COUNT):
    DATABASES[f"shard{i}"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pulse", "USER": "pulse", "PASSWORD": "pulse",
        "HOST": "localhost", "PORT": 5440 + i,
        # Module 13's three transaction-pooling settings still apply, and they
        # apply FOUR TIMES now. Once PgBouncer is in front of each shard, a
        # prepared statement created on one pooled backend and executed on
        # another fails identically on every shard.
        "OPTIONS": {"prepare_threshold": None},
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "CONN_MAX_AGE": 0,
        # A shard is NOT a mirror of default. Without this, `manage.py test`
        # creates four empty test databases and every message assertion fails.
        "TEST": {"NAME": f"test_pulse_shard{i}"},
    }

DATABASE_ROUTERS = [
    "pulse.routers.ShardRouter",       # messages -> shardN
    "pulse.routers.ReplicaRouter",     # Module 13: everything else
]
```

Copy [`code/shard_router.py`](./code/shard_router.py) into
`apps/pulse/pulse/routers.py`, appended below Module 13's `ReplicaRouter`. Read
its docstring before you run anything — the four numbered points are the module.

### A5. Migrate, four times plus one

```bash
cd apps/pulse
python manage.py migrate --settings=pulse.settings.shards --database=default
for s in shard0 shard1 shard2 shard3; do
    python manage.py migrate --settings=pulse.settings.shards --database=$s
done
```
**Expected (abridged):**
```
Operations to perform:
  Apply all migrations: admin, auth, chat, contenttypes, sessions
  ...
  Applying chat.0004_messages_partitioned... OK        <- on default

Operations to perform:
  Apply all migrations: chat                            <- on shard0
  Applying chat.0004_messages_partitioned... OK
  (auth, admin, sessions, contenttypes: no migrations to apply)
```
✅ **Only `chat`'s message DDL lands on a shard.** If `auth` migrated onto
shard0, `allow_migrate` is wrong and you now have four divergent copies of your
user table — the fastest available way to make a sharded system unrecoverable.

Prove the negative:
```bash
docker exec pulse-shard0 psql -U pulse -d pulse -tAc "\dt" | sort
```
**Expected:**
```
public|django_migrations|table|pulse
public|messages|table|pulse
```
✅ Two tables. `django_migrations` (Django insists) and `messages`. Nothing else.

### A6. Break the router on purpose

```python
# manage.py shell --settings=pulse.settings.shards
from chat.models import Message
Message.objects.filter(room_id="room.7").count()
```
**Expected:**
```
chat.routers.ShardRoutingError: Message query with no room in scope. Wrap it in
room_scope(room.key), or pass hints={'instance': msg}.
```
✅ **This is the single most valuable line in the file.** `db_for_read(model,
**hints)` never sees your `WHERE` clause — Django picks a database before it
compiles SQL — so without the tripwire this query would have quietly gone to
`default`, found no `messages` table, and raised something about a missing
relation from 40 frames deeper. Or, worse, found a stale one and returned rows.

Now do it properly:

```python
from pulse.routers import room_scope
with room_scope("room.7"):
    print(Message.objects.filter(room_id="room.7").count())
```
**Expected:**
```
0
```
✅ Zero, but from `shard0` — `crc32("room.7") % 4096 = 3824`, and `3824 % 4 = 0`.
Confirm in the shard's log:
```bash
docker logs pulse-shard0 2>&1 | tail -2
```

Wire `room_scope` into the consumer, at the one place every message path already
passes through:

```python
class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def receive_json(self, content):
        # ONE enter, covering persist, resume and scrollback for this frame.
        # ContextVars survive `await` and survive database_sync_to_async's
        # threadpool hop -- Module 13's reasoning, unchanged.
        with room_scope(self.room_key):
            await self.dispatch_frame(content)
```

---

## Part B — Move a logical shard, live

The operation people are afraid of. Do it with traffic running.

### B1. Seed and load

```bash
python manage.py seed_messages --settings=pulse.settings.shards \
    --rooms 1000 --per-room 5000        # 5M messages across four shards
locust -f 06-load-testing-harness/code/locustfile.py \
    --headless -u 5000 -r 200 -t 6m --host ws://localhost:8000 &
sleep 60
```

### B2. The four phases

Copy [`code/reshard.py`](./code/reshard.py) into `apps/pulse/chat/reshard.py` and
run one migration. `room.7` lives on logical shard 3824, currently on shard0;
move it to shard2.

```bash
python manage.py migrate_shard --settings=pulse.settings.shards \
    --logical 3824 --to 2
```
**Expected:**
```
phase 1: dual-writing logical 3824: shard0 -> shard2
         fleet: 24/24 workers at map version 4102 (waited 812 ms)
phase 2: backfilled 184,291 rows in 47.8 s
phase 3: cut over (318 tail rows) in 210 ms
         fleet: 24/24 workers at map version 4104 (waited 96 ms)
phase 4: cleanup of shard0 scheduled for 2026-08-24T14:20:11Z
```

And in Locust, over the same window:
```
Name                     # reqs   # fails   p50   p95   p99
message.create            72,411     14     18ms  61ms  188ms
sequence_gaps                  0
```
✅ **210 ms of write pause for 1/4096 of traffic, zero message loss.** The 14
failures are sends rejected during the drain with the protocol's `rate_limited`
error frame carrying `retry_after_ms`; clients retried with the **same
`client_id`**, so Module 05's idempotency made them free.

### B3. The line that matters most

```
fleet: 24/24 workers at map version 4102 (waited 812 ms)
```

The JVM twin waits for every app **node**. Pulse waits for every worker
**process**:

```
3 machines × 8 Uvicorn workers = 24 interpreters
                               = 24 independent copies of the assignment map
```

Twenty-three of twenty-four is not "nearly done." It is one process still writing
`room.7` to shard0 while shard2 is being declared authoritative — a **split**,
not a delay. Prove the fencing works by making it fail:

```bash
docker pause pulse-app-node-c            # 8 of the 24 workers stop polling
python manage.py migrate_shard --logical 1931 --to 1
```
**Expected:**
```
phase 1: dual-writing logical 1931: shard3 -> shard1
TimeoutError: only 16/24 workers reached shard map version 4106; ABORTING
migration rather than splitting writes across two shards
```
```bash
docker exec pulse-pg-primary psql -U pulse -d pulse -tAc \
  "SELECT state, migrating_to FROM shard_assignment WHERE logical_shard=1931"
```
**Expected:**
```
migrating|1
```
✅ Aborted in phase 1, which is the **only reversible phase**. Nothing was cut
over; the state row is the evidence for the operator, and the rollback is a
single `UPDATE ... SET state='active', migrating_to=NULL`. Compare with aborting
in phase 3, which challenge task 1 makes you do.

```bash
docker unpause pulse-app-node-c
```

### B4. Grow 4 → 6

```bash
docker compose -p pulse-shard -f infra/compose.shards.yml --profile grow up -d --wait
python manage.py plan_rebalance --settings=pulse.settings.shards --to 6
```
**Expected:**
```
current: 4 physical shards, 4096 logical (1024 each)
target:  6 physical shards (683,683,683,683,682,682)
plan:    1364 logical shards move  (33.3% -- the theoretical minimum, 1 - 4/6)
         naive crc32 % 6 would move 66.6% of ROOMS
estimated rows to copy: 25,109,442
```
✅ **1,364 of 4,096 — exactly `1 − 4/6`.** The hash never changed. Only 1,364
rows of a 4,096-row table did.

```bash
python manage.py plan_rebalance --to 6 --execute --parallelism 2
```
**Expected:**
```
[  256/1364] 18%  elapsed 11m04s  pause p99 224ms  lost 0
[  512/1364] 37%  elapsed 22m11s  pause p99 231ms  lost 0
...
rebalance complete in 58m 42s; 1364 shards moved; 0 messages lost
final distribution: shard0 683  shard1 683  shard2 683  shard3 683
                    shard4 682  shard5 682
```

Record it:
```markdown
## Module 14 — Sharding

- 4096 logical shards over 4 physical; 1,000 rooms distribute 249/251/249/251
- Live shard migration: 210ms write pause for 1/4096 of traffic, 0 lost
- Fleet fencing is per WORKER PROCESS (24), not per node (3); a paused node
  aborts the migration in phase 1 rather than splitting writes
- Rebalance 4 -> 6: 1,364/4,096 logical shards moved (33.3%, the minimum)
  vs 66.6% of all rooms with naive crc32 % N
```

---

## Part C — Scatter-gather, and the threadpool wall

Some queries can no longer touch one shard. "All my rooms' unread counts" spans
~20 rooms, which spans up to 4 shards.

### C1. Sequential, the honest baseline

```python
def unread_sequential(user_id: int) -> dict[str, int]:
    out = {}
    for room_key in membership.rooms_of(user_id):          # ~20 rooms
        with room_scope(room_key):
            out[room_key] = unread_for(user_id, room_key)
    return out
```
```bash
python manage.py bench_unread --settings=pulse.settings.shards --mode sequential
```
**Expected:**
```
shards=4  n=20 rooms  p50=14.9ms  p99=41ms
```
✅ Twenty sequential round trips. Correct, and slow enough that someone will
"fix" it.

### C2. The fix that makes everything worse

The obvious Django answer is `asyncio.gather` over `database_sync_to_async`:

```python
async def unread_gather_orm(user_id: int) -> dict[str, int]:
    rooms = await database_sync_to_async(membership.rooms_of)(user_id)
    by_shard = group_by_physical_shard(rooms)      # 20 rooms -> <=4 shards
    results = await asyncio.gather(*[
        database_sync_to_async(query_one_shard)(alias, keys, user_id)
        for alias, keys in by_shard.items()
    ])
    return merge(results)
```

Measure it **alone**, then **under load**:

```bash
python manage.py bench_unread --mode gather-orm --idle
python manage.py bench_unread --mode gather-orm --concurrent-sends 400
```
**Expected:**
```
idle:                shards=4  p50=4.1ms   p99=26ms
under 400 sends/s:   shards=4  p50=38.2ms  p99=1,910ms
                     message.create p99: 61ms -> 840ms       <-- !!
                     asgiref threadpool queue depth: 47
```
✅ The gather got 3.6× faster in isolation and **took the send path down with
it.** This is Module 01's lesson arriving for the fourth time.

`database_sync_to_async` dispatches onto a bounded threadpool of
`min(32, cpu_count + 4)` threads — **12 here**. Every scatter-gather takes 4 of
them for its duration, and *every other database call on that worker process
queues behind it*, including the persist on the hot send path.

```bash
python -c "import asgiref.sync, os; print(min(32, (os.cpu_count() or 1) + 4))"
```
**Expected:**
```
12
```

> **A scatter-gather that starves the threadpool does not slow down one query. It
> slows down every query on that worker process.** Concurrency is free; resources
> are not. At 16 shards the fan-out wants more threads than the pool has, so the
> "concurrent" version silently serializes *and* blocks everything else.

### C3. The version that is actually concurrent

Take the scatter-gather off the ORM entirely. `psycopg` 3 has a genuinely async
connection; it needs no threads.

```python
import asyncio, psycopg

SEM = asyncio.Semaphore(8)         # bound the fan-out explicitly
DEADLINE_S = 0.2                   # a partial badge count beats a spinner

async def unread_gather_async(user_id: int) -> tuple[dict[str, int], bool]:
    by_shard = group_by_physical_shard(membership.rooms_of(user_id))

    async def one(alias: str, keys: list[str]) -> dict[str, int]:
        async with SEM:
            async with await psycopg.AsyncConnection.connect(DSN[alias]) as conn:
                cur = await conn.execute(
                    "SELECT room_id, max(seq) FROM messages "
                    "WHERE room_id = ANY(%s) GROUP BY room_id", (keys,))
                return dict(await cur.fetchall())

    tasks = [asyncio.create_task(one(a, k)) for a, k in by_shard.items()]
    done, pending = await asyncio.wait(tasks, timeout=DEADLINE_S)
    for t in pending:
        t.cancel()                                    # partial result, on purpose
    merged = {}
    for t in done:
        merged |= t.result()
    return merged, bool(pending)
```
```bash
python manage.py bench_unread --mode gather-async --concurrent-sends 400
```
**Expected:**
```
under 400 sends/s:   shards=4  p50=2.4ms  p99=29ms  partial=0.4%
                     message.create p99: 61ms -> 63ms          <-- unchanged
                     asgiref threadpool queue depth: 0
```
✅ **Faster than the ORM gather and it does not touch the send path**, because it
never enters the threadpool. You gave up the ORM on this one query; you kept it
on the hot path where it never fans out.

### C4. The p99 arithmetic

```bash
python manage.py bench_unread --mode gather-async --sweep 4,8,16,64
```
**Expected:**
```
shards   p50     p99      partial (200ms deadline)
     4   2.4ms   29ms     0.4%
     8   2.6ms   34ms     0.9%
    16   3.1ms   52ms     2.1%
    64   4.4ms   118ms    7.8%
```

The p50 barely moves. The p99 nearly quadruples. That is not a database problem
and no amount of tuning fixes it — it is arithmetic:

```
P(gather ≤ t) = P(shard ≤ t)^k
⟹ the gather's p99  =  each shard's p(99^(1/k)) quantile
```

```bash
python -c "print([round(0.99**(1/k)*100, 3) for k in (1,4,8,16,64)])"
```
**Expected:**
```
[99.0, 99.749, 99.874, 99.937, 99.984]
```
✅ At 16 shards, the gather's p99 **is each shard's p99.94.** You are sampling
the far tail of every shard on every request, and the far tail is where a
checkpoint, an autovacuum and a cold page live.

Hence the deadline and the partial-result path. Decide that before you shard, not
during the incident.

Full comparison, for the record:

| Query | Unsharded | Sharded 4 | Sharded 8 | Sharded 16 |
|-------|-----------|-----------|-----------|------------|
| Scrollback (1 room) | 0.86 ms | **0.86 ms** | **0.86 ms** | **0.86 ms** |
| Send (persist) | 0.9 ms | **0.9 ms** | **0.9 ms** | **0.9 ms** |
| Resume from cursor | 1.1 ms | **1.1 ms** | **1.1 ms** | **1.1 ms** |
| Unread × 20 rooms, sequential | 1.4 ms | 14.9 ms | 14.9 ms | 14.9 ms |
| Unread × 20 rooms, async gather | 1.4 ms | 2.4 ms | 2.6 ms | 3.1 ms |
| Global message count | 41 ms | 196 ms | 380 ms | 742 ms |

✅ **Every hot path is unchanged.** That is the payoff of sharding by room, and
it is the whole justification for the shard key.

---

## Part D — Model it in ScyllaDB

```bash
docker compose -p pulse-scylla -f infra/compose.scylla.yml up -d --wait
alias cql='docker exec -i pulse-scylla1 cqlsh'
cql < 14-sharding-and-wide-column/code/scylla_schema.cql
cql -e "DESCRIBE TABLE pulse.messages" | head -20
```
**Expected:**
```
CREATE TABLE pulse.messages (
    room_id text,
    bucket int,
    seq bigint,
    ...
    PRIMARY KEY ((room_id, bucket), seq)
) WITH CLUSTERING ORDER BY (seq DESC)
    AND compaction = {'class': 'TimeWindowCompactionStrategy', ...}
    AND default_time_to_live = 7776000
```

Read [`code/scylla_schema.cql`](./code/scylla_schema.cql) properly — the comments
are the lesson, and §1 (why the bucket exists) is the thing Part F proves.

### D1. Where the router went

```bash
cql -e "SELECT token(room_id, bucket) FROM pulse.messages LIMIT 3"
docker exec pulse-scylla1 nodetool ring | head -5
```

The `shard_assignment` table, the CRC32 function, the `room_scope` ContextVar,
the fleet-version fencing, the 58-minute rebalance — **all of Parts A and B are
replaced by the primary key**. The partition key hashes to a token, the token
ring maps to nodes, and adding a node is `nodetool` plus a rebalance the database
runs itself.

That is a real, large advantage and you should feel its weight before reading the
rest of this lab.

### D2. The Python driver, and the two ways to get it wrong

```bash
pip install scylla-driver
python -c "import cassandra.io.libevreactor; print('libev OK')"
```
**Expected:**
```
libev OK
```
✅ If that import fails, the driver falls back to a reactor that on Python 3.12
does not exist (`asyncore` was removed in 3.12), and you get a client that
"works" at roughly 40 requests/second with no error. Install `scylla-driver`, not
plain `cassandra-driver`, on this course's stack.

Copy [`code/scylla_repo.py`](./code/scylla_repo.py) into
`apps/pulse/chat/scylla_repo.py`. Two facts from its docstring you must not skip:

- **`session.execute()` blocks.** Calling it from an async consumer blocks the
  event loop and stalls every connection that worker holds — Module 15's cardinal
  sin, reached through a database driver.
- **Build the `Session` per worker process, after the fork**, in the ASGI
  lifespan hook. A `Session` inherited across `uvicorn --workers 8`'s fork has
  reactor threads that do not exist in the child. The symptom is a hang.

### D3. The bucket walk — the code the partition key costs you

```bash
python manage.py bench_scrollback --store scylla --pages 20000
```
**Expected:**
```
pages needing 1 bucket query:   16,412  (82.1%)
pages needing 2 bucket queries:  3,401  (17.0%)
pages needing 3+:                  187  (0.9%)
p50 0.71ms   p99 1.9ms
```
✅ Postgres served this with **one** index range scan at any depth, because
`INDEX (room_id, id DESC)` spans all of history. Here 18% of pages straddle a week
boundary and need a second query.

That is the honest price of the bucket, and it is small. Part F shows what it
buys.

---

## Part E — Head to head

Identical workload: 1,000 rooms, 50M existing messages, 10 minutes, median of 3
runs. All driver-side numbers are from **4 worker processes**, because a single
Python process cannot saturate any of these stores — which is itself a result.

```bash
python 14-sharding-and-wide-column/code/store_bench.py postgres-single
python 14-sharding-and-wide-column/code/store_bench.py postgres-sharded-4
python 14-sharding-and-wide-column/code/store_bench.py scylla-1node
docker compose -p pulse-scylla -f infra/compose.scylla.yml --profile cluster up -d --wait scylla2
docker compose -p pulse-scylla -f infra/compose.scylla.yml --profile cluster up -d --wait scylla3
python 14-sharding-and-wide-column/code/store_bench.py scylla-3node
```

**Expected:**

| | PG single | PG sharded ×4 | Scylla 1 node | Scylla 3 nodes |
|---|-----------|---------------|---------------|----------------|
| **Inserts/s (4 driver procs)** | 44,100 | **148,400** | 118,000 | **291,000** |
| Inserts/s (**1** driver proc) | 41,200 | **52,800** | 39,600 | 41,900 |
| Scrollback p50 (client) | 0.86 ms | 0.86 ms | **0.71 ms** | 0.78 ms |
| Scrollback p99 | 2.1 ms | 2.1 ms | **1.9 ms** | 2.2 ms |
| Scrollback **p99.9** | **9 ms** | **9 ms** | 47 ms | 44 ms |
| Idempotency check p50 | **0.08 ms** | **0.08 ms** | 2.3 ms (LWT) | 5.1 ms (LWT) |
| Storage, 50M messages | 11 GB | 11 GB (2.8 ea.) | **6.2 GB** | 18.6 GB (RF=3) |
| Retention | `DROP TABLE`, 14 ms | 14 ms × 4 | **automatic (TTL)** | automatic |
| Adding capacity | 58 min rebalance | 58 min | **`nodetool` + rebalance** | minutes |
| Cross-room query | ✅ SQL | ⚠️ scatter-gather | ❌ **impossible** | ❌ |
| Transactions (the outbox) | ✅ | ⚠️ per-shard | ❌ | ❌ |

### E1. The row that is the Python story

```
Inserts/s (1 driver proc):   41,200 → 52,800 across FOUR shards
```

Four times the database capacity bought **28% more throughput**, because the
bottleneck moved into the client. One interpreter, one core, and now *more*
Python work per row: the router lookup, the CRC32, the ContextVar, and four
connection pools to manage.

```bash
python 14-sharding-and-wide-column/code/store_bench.py postgres-sharded-4 --procs 1,2,4,8
```
**Expected:**
```
procs=1   52,800/s   client CPU 99% (1 core)   shard CPU 14% avg
procs=2   98,100/s   client CPU 198%           shard CPU 27%
procs=4  148,400/s   client CPU 391%           shard CPU 41%
procs=8  151,900/s   client CPU 402%           shard CPU 42%   <- knee
```
✅ **Scaling the datastore does nothing until you scale the processes driving
it.** On the JVM twin, one process with a thread pool saturates four shards. In
Python you need four processes, which is the same `--workers 8` conclusion Module
01 reached and Modules 04, 09 and 13 each re-derived in their own terms.

The knee at 8 processes is not the database — it is 8 interpreters on 8 cores
with the load generator competing for the same cores.

### E2. The row that decides the module

```
Idempotency check p50:   0.08 ms (Postgres)   →   2.3 ms (Scylla, 1 node)
                                              →   5.1 ms (Scylla, 3 nodes)
```

**29× worse on one node, 64× on three**, because `INSERT ... IF NOT EXISTS` is a
lightweight transaction: a
**Paxos round trip**, four network hops at `LOCAL_SERIAL`. At three nodes those
hops are real.

Module 05 put a `client_id` on every message. Module 09 built at-least-once
delivery on the assumption that a redelivery is a cheap no-op. Module 10 stated
Pulse's guarantee in a sentence that only holds because of it. **That guarantee is
nearly free in Postgres and expensive in Cassandra**, and a design that assumed
cheap conditional writes has to be rethought.

The workaround, measured:

| Approach | p50 | Correct? |
|----------|-----|----------|
| Scylla LWT (`IF NOT EXISTS`) | 2.3 ms | ✅ durable, forever |
| Scylla plain insert + Redis `SET NX` dedup | **0.21 ms** | ✅ **bounded by a TTL** |
| Scylla plain insert, no dedup | 0.09 ms | ❌ duplicates |

```bash
python 14-sharding-and-wide-column/code/store_bench.py scylla-1node --dedup redis
```
**Expected:**
```
idempotency p50: 0.21ms   (11x better than LWT)
duplicate messages delivered over 10 min: 0
duplicate messages after `docker restart pulse-redis`: 3
```
✅ 11× better, correct — and look at the last line. **You moved a permanent
database invariant into a TTL-bounded cache.** In Postgres it was a unique index
that is true forever. Here it is true for as long as Redis remembers.

### E3. p99.9, and what compaction costs

```bash
docker exec pulse-scylla1 nodetool compactionstats
docker exec pulse-scylla1 nodetool tablestats pulse.messages | grep -E 'SSTable count|Bloom'
```
**Expected:**
```
pending tasks: 4
SSTable count: 17
Bloom filter false positives: 812
```

A read touching 17 sstables does 17 bloom-filter checks and up to 17 disk reads.
Postgres's B-tree is 3–4 levels, always. That is the 9 ms → 47 ms p99.9, and it
is the LSM bill coming due — the write cost you deferred, arriving while you are
serving reads.

Chat latency is judged at the tail. Note that and move on.

---

## Part F — Make a hot partition, then fix it

This is the part that transfers to every wide-column system you will ever touch.

### F1. Break it

Recreate the table **without** the bucket:

```bash
cql -e "CREATE TABLE pulse.messages_nobucket (
          room_id text, seq bigint, id bigint, sender text, body text,
          created_at timestamp, PRIMARY KEY ((room_id), seq)
        ) WITH CLUSTERING ORDER BY (seq DESC);"

python 14-sharding-and-wide-column/code/store_bench.py scylla-3node \
    --table messages_nobucket --rooms 1 --duration 5m
```
```bash
docker exec pulse-scylla1 nodetool tablehistograms pulse.messages_nobucket
docker exec pulse-scylla1 nodetool toppartitions pulse messages_nobucket 10000
```
**Expected:**
```
Partition Size (bytes)
  Max: 4,214,431,744            <-- 4.2 GB in ONE partition

TOP WRITES (10s)
  Partition     Count
  room.0      2,811,004         <-- 100% of writes, one node

scrollback p99: 3,880 ms
node1 CPU 100%    node2 CPU 3%    node3 CPU 3%
```
✅ **One partition, one node at 100% while two idle.** No amount of adding nodes
helps: the partition key determines placement, and there is one key.

Scylla told you, if you were reading:
```bash
docker logs pulse-scylla1 2>&1 | grep -i "large partition" | tail -3
```
**Expected:**
```
WARN  large_data - Writing large partition pulse/messages_nobucket:
      room.0 (1073741824 bytes)
```

### F2. Fix it

Same workload against the bucketed table:

```bash
python 14-sharding-and-wide-column/code/store_bench.py scylla-3node \
    --table messages --rooms 1 --duration 5m
docker exec pulse-scylla1 nodetool tablehistograms pulse.messages
```
**Expected:**
```
Partition Size (bytes)
  Max: 88,080,384               <-- 84 MB, weekly buckets

scrollback p99: 1.4 ms
node1 CPU 34%   node2 CPU 31%   node3 CPU 33%
```
✅ **2,770× better p99 and even CPU**, because 52 weekly buckets hash to
different tokens and therefore different nodes.

> **The rule:** in a wide-column store the partition key is your *only*
> load-balancing mechanism. A key with low cardinality or a skewed distribution
> cannot be fixed by adding hardware. **Design the key for the hottest thing you
> will ever store, not the average one.**

And note what the equivalent failure looks like in Part A's world: a hot *room*
on sharded Postgres puts one shard at 100% too. The difference is that you can
move that logical shard to a dedicated database in 210 ms of write pause. In
Scylla you re-key the table and backfill 50 million rows. **Sharded Postgres is
worse by default and better under duress**, and that is worth knowing before you
choose.

---

## Part G — The decision

Record it:

```markdown
## Module 14 — Sharding vs wide-column

| | PG single | PG x4 | Scylla 1 | Scylla 3 |
|---|-----------|-------|----------|----------|
| Inserts/s (4 procs) |  44,100 | 148,400 | 118,000 | 291,000 |
| Inserts/s (1 proc)  |  41,200 |  52,800 |  39,600 |  41,900 |
| Scrollback p50      | 0.86 ms | 0.86 ms | 0.71 ms | 0.78 ms |
| Scrollback p99.9    |    9 ms |    9 ms |   47 ms |   44 ms |
| Idempotency p50     | 0.08 ms | 0.08 ms |  2.3 ms |  5.1 ms |
| Storage (50M)       |   11 GB |   11 GB |  6.2 GB | 18.6 GB |

- Scatter-gather over asgiref's threadpool took message.create p99 from 61ms
  to 840ms; raw psycopg async left it at 63ms
- The gather's p99 at k shards is each shard's p(99^(1/k)) -- p99.94 at k=16
- Hot partition without a bucket key: p99 3,880ms, 1 of 3 nodes at 100% CPU
- With weekly buckets: p99 1.4ms, even CPU  (2,770x)
- Live shard migration: 210ms pause for 1/4096 of traffic; fencing is per
  WORKER PROCESS (24), not per node (3)
- Rebalance 4->6: 1,364/4,096 logical shards (33.3%, the minimum)
```

**The recommendation: sharded Postgres, and not yet.**

Not because Scylla is worse. It wins on write throughput (2× sharded Postgres at
three nodes), on median read latency, on storage (6.2 GB vs 11 GB — LSM sstables
compress better than a heap plus B-trees), and on the operation Part B spent an
hour on. Because:

1. **Pulse's write rate does not need it.** 148k inserts/s sharded is well above
   the 10k msg/s target. Buying 291k costs everything below.
2. **The idempotency check is 29–64× more expensive**, and it is load-bearing for
   the entire delivery guarantee Modules 05, 09 and 10 built. The workaround
   moves a permanent database invariant into a TTL-bounded cache — and Part E
   measured the three duplicates that produced.
3. **Transactions.** Module 13's outbox requires writing the message and the
   outbox row atomically. Cassandra cannot. You would rebuild the one loss mode a
   connected client cannot detect out of weaker primitives.
4. **Every future query must be designed now.** A new feature needing a new
   access pattern is a new table plus a 50-million-row backfill, not a new index.
5. **p99.9 is 5× worse** from compaction, and chat is judged at the tail.
6. **You lose Django.** No ORM for messages (which Module 12 already gave up), but
   also no migrations, no `makemigrations` drift detection, no admin, and no
   `manage.py dbshell` that a new engineer already knows how to use.

**And "not yet":** Part A's arithmetic says 90-day retention leaves 18.4 TB live,
which one machine holds. Do Module 13 properly, then re-measure, then decide.

**When to revisit:** sustained writes above ~500k/s, storage becoming the
dominant line item, a room whose single logical shard saturates a dedicated
database, or acquiring a team that already operates Cassandra. Discord's move was
correct *for Discord*, and they made it after outgrowing exactly the design in
this course.

---

## What you built

- Logical sharding (4096 → N) as a **Django DB router**, ordered ahead of Module
  13's `ReplicaRouter`, with a stable CRC32 hash and a `ContextVar` carrying the
  room the router is not allowed to see.
- A router that **raises** rather than silently reading the wrong shard, and an
  `allow_migrate` that keeps `auth` off the shards.
- A **live shard migration** with a 210 ms write pause, zero loss, and fencing
  that counts **worker processes, not machines** — proven by aborting one.
- A 4 → 6 rebalance moving 1,364 of 4,096 logical shards: the theoretical
  minimum, against 66.6% for naive modulo.
- The scatter-gather threadpool wall, measured (send p99 61 → 840 ms) and fixed
  with raw `psycopg` async — plus the arithmetic that says why fan-out reads need
  a deadline.
- The same chat data in ScyllaDB, with the bucket key that prevents hot
  partitions, the bucket-walk cost it imposes, and the LWT price on idempotency.
- **A defensible decision**, with the numbers behind it and the conditions that
  would change it.

Now do [`challenge.md`](./challenge.md).

Then: [Module 15 — Async, Sync & Raw ASGI](../15-async-sync-and-raw-asgi/).
