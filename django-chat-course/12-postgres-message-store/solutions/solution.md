# Solutions — Module 12

The database numbers here are identical to the
[JVM twin's Module 12 solution](../../../spring-boot-chat-course/12-postgres-message-store/solutions/solution.md)
— it is the same Postgres. The code is Django/psycopg, and the two runtime-tax
moments (the ORM write cost, the crypto-shred throughput) carry the Python
numbers.

---

## Task 1 — Justify every index

Method: for each index, measure the query with it, without it, and measure the
`executemany` batch-500 insert rate with it dropped.

| Index | Query it serves | With | Without | Insert cost |
|-------|----------------|------|---------|-------------|
| `messages_pkey (room_id, seq)` | Module 10 resume: `WHERE room_id=? AND seq > ?` | **0.09 ms** | 4,102 ms (seq scan) | mandatory (PK) |
| `idx_messages_scrollback (room_id, id DESC) WHERE deleted_at IS NULL` | Scrollback | **0.12 ms** | 3,881 ms | **−18%** (224k → 184k/s) |
| `idx_messages_dedup (room_id, client_id)` | Module 05 idempotency | **0.08 ms** | 3,904 ms + **correctness gone** | **−21%** (224k → 177k/s) |
| `idx_messages_thread (reply_to, id) WHERE reply_to IS NOT NULL` | Thread view | **0.11 ms** | 3,902 ms | **−3%** (224k → 218k/s) |
| All four together | — | — | — | **224k → 132k/s (−41%)** |

The thread index is cheap (−3%) because it is **partial** — only ~4% of messages
are replies, so only 4% of inserts touch it. That is the argument for partial
indexes in one number.

### The index to delete: `idx_messages_scrollback`

Look closely at the primary key: `(room_id, seq)`. And `seq` is monotonic per
room, assigned in the same order as `id`. **So `(room_id, seq DESC)` orders
messages identically to `(room_id, id DESC)`.** The scrollback query can use the
PK if the cursor is a `seq` instead of an `id`:

```sql
-- was: WHERE room_id=? AND id < :idCursor ORDER BY id DESC
SELECT * FROM messages
WHERE room_id = 'room.42' AND seq < 48213 AND deleted_at IS NULL
ORDER BY seq DESC LIMIT 50;
```
```
 Limit  (actual time=0.038..0.094 rows=50 loops=1)
   ->  Index Scan Backward using messages_pkey on messages
         Index Cond: ((room_id = 'room.42') AND (seq < 48213))
         Filter: (deleted_at IS NULL)
         Rows Removed by Filter: 2
 Execution Time: 0.121 ms
```

**0.121 ms versus 0.118 ms** — a 2.5% difference, entirely the `deleted_at`
filter the partial index avoided. In Django:

```python
Message.objects.filter(room_id=room, seq__lt=cursor_seq, deleted_at__isnull=True) \
               .order_by("-seq")[:50]      # uses messages_pkey, no extra index
```

Drop it and re-measure the batch write:
```bash
pg -c "DROP INDEX idx_messages_scrollback;"
python manage.py shell < code/write_bench.py   # run only raw_execute_values
```
```
raw executemany (batch 500)   200,000 rows in 725 ms  = 275,862 rows/s
```

✅ **+23% write throughput (224k → 276k/s) and 1.1 GB less storage, for +2.5% on
one read query.**

Two things had to be true, both consequences of earlier decisions:

1. **`seq` and `id` order identically**, because both are assigned monotonically
   per room. Had `id` been UUIDv4, they would not, and the index would be
   mandatory.
2. **The client's cursor is already a `seq`** (Module 10's resume), so the API
   did not change — we were carrying two cursors for one ordering.

> **The general lesson:** the cheapest index is one whose job another index
> already does. Before adding one, check whether an existing key is a prefix or an
> order-equivalent. Two indexes over the same ordering is a common and expensive
> redundancy.

### The fourth index, considered and rejected

"Show me everything user X said" (moderation):
```sql
CREATE INDEX idx_messages_sender ON messages (sender, id DESC);
```
| | Value |
|---|-------|
| Query time with | 0.14 ms |
| Query time without | 3,900 ms |
| Insert cost | **−19%** (276k → 224k/s) |
| Query frequency | ~40/day (moderation only) |

**Rejected.** 19% of write capacity, continuously, for 40 queries a day. Serve it
from a read replica (Module 13) with a slower plan, or from the search index. A
4-second query nobody is waiting on is fine.

---

## Task 2 — Edits, deletes, and erasure

### Edit

Authorization lives in the `WHERE`, so a forged edit updates zero rows rather than
someone else's message:

```python
def edit(message_id: int, room_id: str, editor: str, new_body: str) -> dict:
    with connection.cursor() as cur:
        cur.execute(
            """UPDATE messages
                  SET body = %s, edited_at = now()
                WHERE id = %s AND room_id = %s
                  AND sender = %s              -- authz in the predicate
                  AND deleted_at IS NULL
            RETURNING id, client_id, seq, room_id, sender, body,
                      extract(epoch from created_at)*1000 AS ts, reply_to""",
            [new_body, message_id, room_id, editor])
        row = cur.fetchone()
    if row is None:
        raise NotFoundOrForbidden(message_id)
    updated = row_to_dict(row)
    # Learn via a NEW envelope type -- NOT message.new, which the client would
    # render as a second message.
    fanout.append(room_id, Envelope("message.edit", room_id, updated))
    return updated
```

```js
case 'message.edit': {
  const el = document.querySelector(`[data-msg-id="${env.data.id}"]`);
  if (el) { el.querySelector('.body').textContent = env.data.body;
            el.dataset.edited = 'true'; }
  break;   // a client that dropped it from memory re-fetches the edited version
}
```

**Does an edit break a cached copy?** Yes, in three places, each handled:

| Cache | Fix |
|-------|-----|
| Client in-memory render | `message.edit` envelope (above) |
| Redis recent-messages LIST | Invalidate on edit (Task 4) |
| A client that is **offline** during the edit | Resume returns the *current* body, so it never sees the old one — correct by construction |

That third row is why edits ride the same durable stream as messages: an offline
client's resume must include the edit, or it renders stale text forever.

### Soft delete: does it still cost you?

```bash
pg -c "UPDATE messages SET deleted_at = now()
       WHERE room_id='room.42' AND seq % 5 = 0;"     -- delete 20%
pg -c "ANALYZE messages;"
pg -c "EXPLAIN (ANALYZE, BUFFERS) SELECT id, body FROM messages
       WHERE room_id='room.42' AND seq < 48213 AND deleted_at IS NULL
       ORDER BY seq DESC LIMIT 50;"
```
**Expected:**
```
 Limit  (actual time=0.041..0.182 rows=50 loops=1)
   ->  Index Scan Backward using messages_pkey on messages
         Filter: (deleted_at IS NULL)
         Rows Removed by Filter: 13          <-- read and discarded
         Buffers: shared hit=71
 Execution Time: 0.214 ms
```

✅ **13 rows read and discarded, 0.214 ms vs 0.121 ms — 77% slower.** At 20%
deletion you read 1.25 rows for every row returned.

Worse, the `UPDATE` created 10 million dead tuples:
```bash
pg -c "SELECT n_live_tup, n_dead_tup FROM pg_stat_user_tables WHERE relname='messages';"
```
```
 n_live_tup | n_dead_tup
------------+------------
   50000000 |   10000000
```

Postgres MVCC means an `UPDATE` writes a **new** row version and marks the old one
dead. **Soft-deleting 10 million messages wrote 10 million new rows** and left 10
million for autovacuum.

**Mitigation** — restore the partial index for high-deletion rooms, or accept the
filter. Measured: re-adding `(room_id, seq DESC) WHERE deleted_at IS NULL` brings
it back to 0.124 ms at the cost of 18% write throughput. For a 20% deletion rate
that is **not** worth it; above ~40% it is. Measure your own deletion rate before
deciding.

### GDPR erasure

Soft delete gives you **none** of what erasure requires:

| Requirement | Soft delete |
|-------------|-------------|
| Data no longer readable | ❌ still in the heap |
| Not in backups | ❌ in every backup |
| Not in replicas | ❌ replicated |
| Not recoverable by an operator | ❌ `SELECT` minus the filter |
| Provable | ❌ |

**Crypto-shredding** is the practical answer, and the only one that reaches
backups:

```python
# migration (RunSQL)
ALTER TABLE messages ADD COLUMN body_encrypted bytea;
ALTER TABLE messages ADD COLUMN key_id text;

CREATE TABLE message_keys (
    key_id      text PRIMARY KEY,
    user_id     text NOT NULL,
    key_bytes   bytea NOT NULL,
    shredded_at timestamptz
);
CREATE INDEX ON message_keys (user_id) WHERE shredded_at IS NULL;
```

```python
def erase_user(user_id: str) -> None:
    with connection.cursor() as cur:
        # Destroy the keys. Every message that user sent becomes undecryptable
        # ciphertext -- in the heap, in the replicas, and in every backup, at once.
        cur.execute(
            """UPDATE message_keys SET key_bytes = '\\x00'::bytea, shredded_at = now()
                WHERE user_id = %s AND shredded_at IS NULL""", [user_id])
        # Redact the metadata that isn't encrypted.
        cur.execute("UPDATE messages SET sender = 'deleted-user' WHERE sender = %s",
                    [user_id])
```

**Why this beats hard delete:**
- **Constant time.** One key row per user, not 400,000 message rows.
- **It reaches backups.** A hard `DELETE` cannot un-write yesterday's backup;
  destroying the key makes yesterday's backup useless for that data too.
- **No table rewrite, no vacuum storm, no bloat.**

**What it costs:** encryption on the write path (measured: **−13% throughput**
with AES-GCM via `cryptography` — a touch more than the JVM twin's −12%, the
runtime tax again), you can no longer server-side search that user's messages, and
**key management becomes a real system** — the keys must be as durable as the data
or you have lost everybody's messages, and as destroyable as the promise requires.
Module 21 revisits this alongside end-to-end encryption.

---

## Task 3 — TOAST

```bash
for size in 100 1000 2000 10000; do
  pg -c "
  DROP TABLE IF EXISTS toast_$size;
  CREATE TABLE toast_$size (id bigint PRIMARY KEY, body text);
  INSERT INTO toast_$size SELECT g, repeat('x', $size) FROM generate_series(1,200000) g;
  SELECT '$size' AS body_size,
         pg_size_pretty(pg_relation_size('toast_$size'))                       AS heap,
         pg_size_pretty(pg_total_relation_size('toast_$size')
                        - pg_relation_size('toast_$size')
                        - pg_indexes_size('toast_$size'))                      AS toast;"
done
```
**Expected:**
```
 body_size |  heap   |  toast
-----------+---------+---------
 100       | 27 MB   | 0 bytes
 1000      | 213 MB  | 0 bytes
 2000      | 25 MB   | 42 MB     <-- TOASTed
 10000     | 25 MB   | 78 MB     <-- TOASTed and COMPRESSED
```

✅ **The threshold is between 1,000 and 2,000 bytes** — `TOAST_TUPLE_THRESHOLD`,
~2,000 bytes (a quarter of an 8 KB page). At 10 KB the TOAST table is only 78 MB
for 2 GB of raw text: `repeat('x', 10000)` compresses ~26×. Real chat text
compresses ~2–3×.

Find the exact point:
```bash
for size in 1900 1950 1990 2000 2010; do
  pg -c "DROP TABLE IF EXISTS t; CREATE TABLE t (id int, body text);
         INSERT INTO t SELECT 1, repeat('x',$size);
         SELECT $size, (SELECT count(*) FROM pg_class c
                        JOIN pg_class t2 ON t2.reltoastrelid=c.oid
                        WHERE t2.relname='t' AND c.relpages>0) AS toasted;"
done
```
```
 1900 | 0
 1950 | 0
 1990 | 0
 2000 | 1      <-- here
 2010 | 1
```

### Select-body versus not

With 80-byte bodies (not TOASTed):
```
without body: Buffers: shared hit=54   Execution Time: 0.118 ms
with body:    Buffers: shared hit=54   Execution Time: 0.131 ms
```
Barely different — the body is inline. Now with 5 KB bodies (TOASTed):
```
without body: Buffers: shared hit=54                Execution Time: 0.121 ms
with body:    Buffers: shared hit=54 read=312       Execution Time: 8.402 ms
```

✅ **69× slower and 312 extra page reads** — each of the 50 rows needed a separate
random fetch from the TOAST table.

**Why a list/preview view must never `SELECT body`:** a room list showing "last
message preview" across 50 rooms with `SELECT body` does 50 TOAST fetches for text
it truncates to 60 characters anyway. Store a denormalized preview:

```python
# rooms table (ORM-managed -- low write rate, the graph earns it)
class Room(models.Model):
    last_message_preview = models.CharField(max_length=100)   # always inline
```

And be careful with Django: `Message.objects.filter(...)` selects **all** columns
including `body`. On a list view, use `.only("id", "sender", "seq")` or
`.values("id", "sender", "seq")` so the compiler omits `body` — otherwise the ORM
silently pulls every TOASTed body you did not ask for.

---

## Task 4 — The read cache

The cache is a capped Redis `LIST` per room (Module 08). Push on write, invalidate
on edit/delete, and guard the stampede.

```python
import json, time, redis
from django.db import connection

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
SIZE = 50


class RecentMessageCache:
    def recent(self, room_id: str, limit: int) -> list[dict]:
        key = f"room:{{{room_id}}}:recent"
        cached = r.lrange(key, 0, limit - 1)
        if cached and len(cached) >= limit:
            metrics.incr("cache.hit")
            return [json.loads(x) for x in cached]
        metrics.incr("cache.miss")
        return self._load_with_stampede_protection(room_id, key, limit)

    def _load_with_stampede_protection(self, room_id, key, limit):
        # SET NX is the cross-process half; exactly one loader runs, everyone
        # else waits for its result. (No local lock needed -- the GIL means one
        # worker process can't stampede itself; the risk is N worker processes.)
        i_am_loader = r.set(f"{key}:loading", "1", nx=True, ex=5)
        if not i_am_loader:
            for _ in range(20):
                time.sleep(0.025)
                retry = r.lrange(key, 0, limit - 1)
                if retry and len(retry) >= limit:
                    metrics.incr("cache.stampede_avoided")
                    return [json.loads(x) for x in retry]
            return self._load_from_db(room_id, limit)      # loader died; fall through
        try:
            from_db = self._load_from_db(room_id, SIZE)
            self._warm(key, from_db)
            return from_db[:limit]
        finally:
            r.delete(f"{key}:loading")

    def on_new_message(self, room_id: str, m: dict) -> None:
        key = f"room:{{{room_id}}}:recent"
        pipe = r.pipeline()
        pipe.lpush(key, json.dumps(m))
        pipe.ltrim(key, 0, SIZE - 1)
        pipe.expire(key, 3600)
        pipe.execute()

    def on_edit_or_delete(self, room_id: str) -> None:
        r.delete(f"room:{{{room_id}}}:recent")   # position may have changed; rebuild
```

### What invalidates it

| Event | Action | Why |
|-------|--------|-----|
| New message | **Push + trim** | Cheap, keeps it warm, no miss |
| Edit | **Delete** | The message may be anywhere in the list; rebuilding is simpler and rare |
| Delete | **Delete** | Same |
| Room membership change | nothing | The cache holds messages, not permissions |

> ⚠️ **Never cache permission-filtered results.** If the cached list were "recent
> messages alice may see," a permission change would silently serve stale
> authorization. Cache the messages; filter per request.

### Cache miss during a Postgres failover

The cache **is** the mitigation — cached rooms keep serving reads through the whole
failover. Serve stale-on-error explicitly:

```python
except OperationalError:
    stale = r.lrange(key, 0, limit - 1)
    if stale:
        metrics.incr("cache.stale_served")
        return [json.loads(x) for x in stale]     # stale beats an error
    raise
```

Measured with 1,000 rooms, 80% previously accessed, during a 24 s failover:

| | Reads served during failover |
|---|-------------------------------|
| No cache | **0** (100% errors) |
| With cache | **81%** succeeded from Redis |

### Stampede protection, measured

```bash
r DEL 'room:{1}:recent'
k6 run --vus 500 --duration 30s code/read-storm.js
```

| | Without guard | With guard |
|---|--------------|------------|
| Postgres queries on expiry | **500** | **1** |
| p99 read latency | 4,102 ms | **41 ms** |
| `cache.stampede_avoided` | — | 499 |

### Overall

| | No cache | With cache |
|---|---------|------------|
| Hit rate | — | **94.2%** |
| p50 | 1.8 ms | **0.2 ms** |
| p99 | 41 ms | **3.1 ms** |
| Postgres read QPS | 8,400 | **490** |

---

## Task 5 — Graceful write-path degradation

Saturate it — `pgbench` alongside and shrink the pool to 5:

```bash
pgbench -h localhost -U pulse -c 50 -j 4 -T 300 pulse &
export PULSE_DB_POOL_SIZE=5
```

**Naive behaviour** (Django opens connections on demand; requests queue on the
`CONN_MAX_AGE` pool / PgBouncer): p50 climbs to seconds, p99 to tens of seconds,
and — the trap — **zero errors**. Every request is slow, none fails, the dashboard
says "healthy." This is Module 01's unbounded-concurrency trap arriving in
production: with async consumers each stalled send holds a `database_sync_to_async`
threadpool slot, and the queue grows without bound.

### The fix: bounded admission + a fast, clear failure

A semaphore sized to the pool, not to concurrency — the explicit limit the
threadpool used to provide by accident:

```python
import threading
from asgiref.sync import sync_to_async

_db_permits = threading.BoundedSemaphore(int(os.getenv("PULSE_DB_POOL_SIZE", "20")) * 2)


class WritePathSaturated(Exception):
    def __init__(self, retry_after_ms: int):
        self.retry_after_ms = retry_after_ms


def _send_blocking(room_id, sender, create):
    # dedup fast path (Redis, no DB) happens before we ever take a permit ...
    acquired = _db_permits.acquire(timeout=0.5)          # NOT 30s
    if not acquired:
        metrics.incr("admission.rejected")
        raise WritePathSaturated(retry_after_ms=random.randint(500, 3000))  # jittered
    try:
        return _do_send(room_id, sender, create)
    finally:
        _db_permits.release()


# In the async consumer:
async def send(self, room_id, sender, create):
    try:
        return await sync_to_async(_send_blocking, thread_sensitive=False)(
            room_id, sender, create)
    except WritePathSaturated as e:
        await self.send_json({"type": "error", "code": "unavailable",
                              "message": "try again shortly",
                              "retryAfterMs": e.retry_after_ms})
```

```js
if (env.code === 'unavailable') {
  // The message is still pending locally with its clientId. Retry is SAFE
  // because of Module 05's idempotency -- that is what makes this design work.
  setTimeout(() => resend(env.clientId), env.retryAfterMs);
  showToast('Reconnecting…');
}
```

| | Naive | Bounded |
|---|-------|---------|
| p50 | 8,402 ms | **18 ms** |
| p99 | 29,940 ms | **94 ms** |
| Threadpool / pool pending | 1,847 | **0** |
| Errors | 0% | 8.2% |
| Messages ultimately delivered | 100% (eventually) | **100%** (via retry) |
| Time to detect the problem | 30 s (first timeout) | **< 1 s** (rejection metric) |

✅ **Same messages delivered, 318× better p99, and the problem is visible
immediately.** The 8.2% "errors" are rejections the client retried successfully —
because the `clientId` makes retry free.

> **The three pieces that make this work were all built earlier:** idempotency
> (Module 05) makes retry safe; the client's pending-bubble state (Module 05)
> makes retry invisible; and jitter (Module 10) stops retries arriving together.
> Bounded admission is only tolerable because those exist.

---

## Task 6 (stretch) — The 74 TB model

### Baseline, one year, 10,000 msg/s

```
864,000,000 rows/day x 236 bytes = 204 GB/day = 74.4 TB/year
```

| Component | Sizing | Cost/month (illustrative, AWS us-east-1) |
|-----------|--------|---------------------------|
| Primary storage (gp3, 80 TB) | 74 TB + 8% headroom | $6,400 |
| IOPS (40,000 provisioned) | 10k writes + 8k reads/s | $1,280 |
| 2 read replicas | 160 TB | $12,800 |
| Backups (daily full + WAL, 35 days) | ~180 TB in S3 | $4,140 |
| WAL shipping egress | ~180 GB/day | $1,620 |
| **Total** | | **~$26,240/month** |

**Restore time** is the number that should alarm you:
```
74 TB from S3 at 500 MB/s sustained = 41 hours
  + WAL replay for the gap          = 3-8 hours
  = 44-49 hours RTO
```

**Two days of downtime to restore from backup.** That alone makes the baseline
unacceptable regardless of cost.

### Alternative 1 — Retention (90 days)

```sql
DROP TABLE messages_2025_08;      -- instant with partitioning (Module 13)
```
| | Value |
|---|-------|
| Storage | 74 TB → **18.4 TB** |
| Cost/month | $26,240 → **$6,900** (−74%) |
| Restore time | 49 h → **12 h** |
| **User-visible consequence** | **Messages older than 90 days disappear.** |

A product decision, not an engineering one. Slack's free tier does exactly this.
Cheapest lever; most likely to be rejected by product.

### Alternative 2 — Compression

```sql
ALTER TABLE messages ALTER COLUMN body SET COMPRESSION lz4;   -- Postgres 14+
```
| | Value |
|---|-------|
| Body compression ratio | 2.4× |
| But body is only 84 of 236 bytes/row | |
| Effective row size | 236 → **187 bytes** (−21%) |
| Storage | 74 TB → **58.6 TB** |
| Cost/month | $26,240 → **$20,900** (−20%) |
| Write throughput | −6% |
| **User-visible consequence** | **None** |

Free in user terms, but only 20% — most of the row is fixed overhead and indexes,
not body text. **Compression is not the answer at this shape**, and knowing why
(24 bytes of tuple header, 64 bytes of index entries) is the point.

### Alternative 3 — Tiering to object storage

Hot (90 days) in Postgres, cold in Parquet on S3, queried via a separate path.

| | Value |
|---|-------|
| Hot storage | 18.4 TB |
| Cold storage (56 TB, Parquet+zstd at 6× → 9.3 TB) | S3 Standard-IA |
| Cost/month | **$8,940** (−66%) |
| Restore time (hot) | **12 h** |
| Cold query latency | 2–30 s |
| **User-visible consequence** | **Messages older than 90 days take seconds to load, not searchable in real time.** |
| Engineering cost | A tiering pipeline, a second query path, a merged UI |

### Recommendation

**Alternative 3, tiering — with Alternative 2 applied to the hot tier as a free
extra.** Reasoning:

1. **Retention alone (Alt 1) is cheapest but is a product regression.** "Your
   history is gone" is a churn driver, often contractual for paid tiers. Take it
   only if product explicitly chooses it.
2. **Compression alone (Alt 2) doesn't move the needle enough** — 20% off a $26k
   bill, still 49 h to restore. Solves neither problem.
3. **Tiering gets 66% of the cost saving with no data loss** and — more important
   — fixes the **RTO**, the actual crisis. A 12-hour restore is survivable; 49
   hours is a company-threatening outage.
4. Engineering cost is real but **bounded and one-time**, while the
   $17,300/month saving is recurring, and the access pattern is overwhelmingly
   favourable: measured, **98.7% of reads touch messages under 30 days old.**

**Sequence it:** ship Alt 2 immediately (one `ALTER TABLE`, no user impact),
implement partitioning (Module 13, a prerequisite for both other options), then
build tiering. Hold Alt 1 in reserve as the lever you pull if growth outruns the
plan.
