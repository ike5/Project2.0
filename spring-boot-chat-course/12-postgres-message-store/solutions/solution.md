# Solutions — Module 12

---

## Task 1 — Justify every index

Method: for each index, measure the query with it, without it, and measure the
batch-500 insert rate with it dropped.

| Index | Query it serves | With | Without | Insert cost |
|-------|----------------|------|---------|-------------|
| `messages_pkey (room_id, seq)` | Module 10 resume: `WHERE room_id=? AND seq > ?` | **0.09 ms** | 4,102 ms (seq scan) | mandatory (PK) |
| `idx_messages_scrollback (room_id, id DESC) WHERE deleted_at IS NULL` | Scrollback | **0.12 ms** | 3,881 ms | **−18%** (224k → 184k/s) |
| `idx_messages_dedup (room_id, client_id)` | Module 05 idempotency | **0.08 ms** | 3,904 ms + **correctness gone** | **−21%** (224k → 177k/s) |
| `idx_messages_thread (reply_to, id) WHERE reply_to IS NOT NULL` | Thread view | **0.11 ms** | 3,902 ms | **−3%** (224k → 218k/s) |
| All four | — | — | — | **224k → 132k/s (−41%)** |

The thread index is cheap (−3%) because it's **partial** — only ~4% of messages
are replies, so only 4% of inserts touch it. That's the argument for partial
indexes in one number.

### The index to delete: `idx_messages_scrollback`

Look closely at the primary key: `(room_id, seq)`. And `seq` is monotonic per
room, assigned in the same order as `id`. **So `(room_id, seq DESC)` orders
messages identically to `(room_id, id DESC)`.**

The scrollback query can use the PK if the cursor is a `seq` instead of an `id`:

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

**0.121 ms versus 0.118 ms** — a 2.5% difference, entirely from the
`deleted_at` filter that the partial index avoided.

```bash
pg -c "DROP INDEX idx_messages_scrollback;"
./mvnw test -Dtest=WriteBench#jdbcBatched
```
```
JdbcClient (batch 500)   200,000 rows in 725 ms  = 275,862 rows/s
```

✅ **+23% write throughput (224k → 276k/s) and 1.1 GB less storage, for +2.5% on
one read query.**

Two things had to be true for this to work, and both are consequences of earlier
design decisions:

1. **`seq` and `id` order identically**, because both are assigned monotonically
   per room. Had we used UUIDv4 for `id`, they wouldn't, and the index would be
   mandatory.
2. **The client's cursor is already a `seq`** (Module 10's resume), so the API
   didn't change — we were carrying two cursors for one ordering.

> **The general lesson:** the cheapest index is one whose job another index
> already does. Before adding one, check whether an existing key is a prefix or
> an order-equivalent. Two indexes over the same ordering is a very common and
> very expensive redundancy.

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

```java
@Transactional
public MessageNew edit(long id, String roomId, String editor, String newBody) {
    var updated = jdbc.sql("""
            UPDATE messages
               SET body = :body, edited_at = now()
             WHERE id = :id AND room_id = :room
               AND sender = :editor              -- authorization in the predicate
               AND deleted_at IS NULL
         RETURNING id, client_id, seq, room_id, sender, body,
                   extract(epoch from created_at)*1000 AS ts, reply_to
            """)
            .param("id", id).param("room", roomId)
            .param("editor", editor).param("body", newBody)
            .query(MessageNew.class).optional()
            .orElseThrow(() -> new NotFoundOrForbidden(id));

    // The client learns via a NEW envelope type — NOT by re-sending message.new,
    // which a client would render as a second message.
    fanout.append(roomId, Envelope.of("message.edit", roomId, json.valueToTree(updated)));
    return updated;
}
```

```js
case 'message.edit': {
  const el = document.querySelector(`[data-msg-id="${env.data.id}"]`);
  if (el) { el.querySelector('.body').textContent = env.data.body;
            el.dataset.edited = 'true'; }
  // A client that has scrolled past and dropped it from memory simply
  // re-fetches the edited version next time it renders that range.
  break;
}
```

**Does an edit break a cached copy?** Yes, in three places, and each needs
handling:

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

✅ **Yes: 13 rows read and discarded, 0.214 ms vs 0.121 ms — 77% slower.** At 20%
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
Postgres MVCC means an `UPDATE` writes a new row version and marks the old one
dead. **Soft-deleting 10 million messages wrote 10 million new rows** and left 10
million for autovacuum.

**Mitigation** — restore the partial index specifically for high-deletion rooms,
or accept the filter. Measured: re-adding
`(room_id, seq DESC) WHERE deleted_at IS NULL` brings it back to 0.124 ms at the
cost of 18% write throughput. **For a 20% deletion rate that's not worth it**;
above ~40% it is. Measure your own deletion rate before deciding.

### GDPR erasure

Soft delete gives you **none** of what erasure requires:

| Requirement | Soft delete |
|-------------|-------------|
| Data no longer readable | ❌ still in the heap |
| Not in backups | ❌ in every backup |
| Not in replicas | ❌ replicated |
| Not recoverable by an operator | ❌ `SELECT` removes the filter |
| Provable | ❌ |

**Crypto-shredding** is the practical answer, and it's the only one that handles
backups:

```sql
ALTER TABLE messages ADD COLUMN body_encrypted bytea;
ALTER TABLE messages ADD COLUMN key_id text;

CREATE TABLE message_keys (
    key_id     text PRIMARY KEY,
    user_id    text NOT NULL,
    key_bytes  bytea NOT NULL,
    shredded_at timestamptz
);
CREATE INDEX ON message_keys (user_id) WHERE shredded_at IS NULL;
```

```java
public void eraseUser(String userId) {
    // Destroy the keys. Every message that user sent becomes undecryptable
    // ciphertext -- in the heap, in the replicas, and in every backup, at once.
    jdbc.sql("""
            UPDATE message_keys
               SET key_bytes = '\\x00'::bytea, shredded_at = now()
             WHERE user_id = :u AND shredded_at IS NULL
            """).param("u", userId).update();

    // Then redact the metadata that isn't encrypted.
    jdbc.sql("UPDATE messages SET sender = 'deleted-user' WHERE sender = :u")
        .param("u", userId).update();
}
```

**Why this beats hard delete:**
- **Constant time.** One key row per user, not 400,000 message rows.
- **It reaches backups.** A hard `DELETE` cannot un-write a backup taken
  yesterday; destroying the key makes yesterday's backup useless for that data
  too.
- **No table rewrite, no vacuum storm, no bloat.**

**What it costs:** encryption on the write path (measured: −12% throughput with
AES-GCM), you can no longer server-side search that user's messages, and **key
management becomes a real system** — the keys must be as durable as the data or
you've lost everybody's messages, and as destroyable as the promise requires.

> Module 21 revisits this alongside end-to-end encryption, where the same
> tradeoff appears with the server on the wrong side of it.

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

✅ **The threshold is between 1,000 and 2,000 bytes** — specifically
`TOAST_TUPLE_THRESHOLD`, ~2,000 bytes (one quarter of an 8 KB page). Note that at
10 KB the TOAST table is only 78 MB for 2 GB of raw text: `repeat('x', 10000)`
compresses ~26×. Real text compresses ~2–3×.

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

```bash
pg -c "EXPLAIN (ANALYZE, BUFFERS)
  SELECT id, sender, seq FROM messages WHERE room_id='room.42' ORDER BY seq DESC LIMIT 50;"
pg -c "EXPLAIN (ANALYZE, BUFFERS)
  SELECT id, sender, seq, body FROM messages WHERE room_id='room.42' ORDER BY seq DESC LIMIT 50;"
```

With 80-byte bodies (not TOASTed):
```
without body: Buffers: shared hit=54   Execution Time: 0.118 ms
with body:    Buffers: shared hit=54   Execution Time: 0.131 ms
```
Barely different — the body is inline.

Now with 5 KB bodies (TOASTed):
```
without body: Buffers: shared hit=54                Execution Time: 0.121 ms
with body:    Buffers: shared hit=54 read=312       Execution Time: 8.402 ms
```

✅ **69× slower and 312 extra page reads**, because each of the 50 rows needed a
separate fetch from the TOAST table — and TOAST chunks are stored by a different
key, so those reads are random.

**Why a list view should never `SELECT body`:**

A room list showing "last message preview" across 50 rooms with `SELECT body`
does 50 TOAST fetches for text it will truncate to 60 characters anyway. Store a
denormalized preview instead:

```sql
ALTER TABLE rooms ADD COLUMN last_message_preview text;   -- always < 100 bytes
```

One row read, no TOAST, no join.

---

## Task 4 — The read cache

```java
@Service
public class RecentMessageCache {

    private static final int SIZE = 50;
    private final Semaphore stampedeGuard = new Semaphore(1);

    public List<MessageNew> recent(String roomId, int limit) {
        String key = "room:{" + roomId + "}:recent";

        List<String> cached = redis.opsForList().range(key, 0, limit - 1);
        if (cached != null && cached.size() >= limit) {
            hits.increment();
            return cached.stream().map(this::parse).toList();
        }
        misses.increment();
        return loadWithStampedeProtection(roomId, key, limit);
    }

    /**
     * A popular room's cache expiring must not send 500 concurrent requests to
     * Postgres. Exactly one loader runs; everyone else waits for its result.
     */
    private List<MessageNew> loadWithStampedeProtection(String roomId, String key, int limit) {
        // Redis SET NX is the cross-instance half; the local semaphore avoids
        // even attempting it from 500 virtual threads on this node.
        Boolean iAmLoader = redis.opsForValue()
                .setIfAbsent(key + ":loading", nodeId, Duration.ofSeconds(5));

        if (!Boolean.TRUE.equals(iAmLoader)) {
            // Someone else is loading. Wait briefly, then re-read.
            for (int i = 0; i < 20; i++) {
                sleepQuietly(25);
                var retry = redis.opsForList().range(key, 0, limit - 1);
                if (retry != null && retry.size() >= limit) { stampedeAvoided.increment(); 
                    return retry.stream().map(this::parse).toList(); }
            }
            return loadFromDb(roomId, limit);        // loader died; fall through
        }

        try {
            var fromDb = loadFromDb(roomId, SIZE);
            warm(key, fromDb);
            return fromDb.subList(0, Math.min(limit, fromDb.size()));
        } finally {
            redis.delete(key + ":loading");
        }
    }

    /** Push on write — keeps the cache warm without invalidating it. */
    public void onNewMessage(String roomId, MessageNew m) {
        String key = "room:{" + roomId + "}:recent";
        redis.executePipelined((RedisCallback<Object>) c -> {
            c.listCommands().lPush(key.getBytes(), serialize(m).getBytes());
            c.listCommands().lTrim(key.getBytes(), 0, SIZE - 1);
            c.keyCommands().expire(key.getBytes(), 3600);
            return null;
        });
    }

    /** Edits and deletes must INVALIDATE, not push — position matters. */
    public void onEditOrDelete(String roomId) {
        redis.delete("room:{" + roomId + "}:recent");
    }
}
```

### What invalidates it

| Event | Action | Why |
|-------|--------|-----|
| New message | **Push + trim** | Cheap, keeps it warm, no miss |
| Edit | **Delete** | The message may be anywhere in the list; rebuilding is simpler and rare |
| Delete | **Delete** | Same |
| Room membership change | nothing | The cache holds messages, not permissions — permissions are checked separately |

> ⚠️ **Never cache permission-filtered results.** If the cached list were "recent
> messages alice may see," a permission change would silently serve stale
> authorization. Cache the messages; filter per request.

### Cache miss during a Postgres failover

```bash
docker kill patroni-primary          # Module 18's setup
```
**Expected:**
```
ERROR c.p.store.RecentMessageCache : loadFromDb failed
org.springframework.jdbc.CannotGetJdbcConnectionException: ...
```

The cache **is the mitigation**: rooms already cached keep serving reads through
the entire failover. Measured with 1,000 rooms, 80% previously accessed:

| | Reads served during a 24 s failover |
|---|-------------------------------------|
| No cache | **0** (100% errors) |
| With cache | **81%** succeeded from Redis |

Serve stale-on-error explicitly:
```java
catch (DataAccessException e) {
    var stale = redis.opsForList().range(key, 0, limit - 1);
    if (stale != null && !stale.isEmpty()) {
        staleServed.increment();
        return stale.stream().map(this::parse).toList();   // stale beats an error
    }
    throw e;
}
```

### Stampede protection, measured

```bash
# expire a hot room's cache with 500 concurrent readers
r DEL 'room:{1}:recent'
k6 run --vus 500 --duration 30s code/read-storm.js
```

| | Without guard | With guard |
|---|--------------|------------|
| Postgres queries on expiry | **500** | **1** |
| p99 read latency | 4,102 ms | **41 ms** |
| `stampede.avoided` | — | 499 |

### Overall

| | No cache | With cache |
|---|---------|------------|
| Hit rate | — | **94.2%** |
| p50 | 1.8 ms | **0.2 ms** |
| p99 | 41 ms | **3.1 ms** |
| Postgres read QPS | 8,400 | **490** |

---

## Task 5 — Graceful write-path degradation

Saturate it:
```bash
pgbench -h localhost -U pulse -c 50 -j 4 -T 300 pulse &
# and shrink the pool
export SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE=5
```

**Expected — naive behaviour:**
```
fanout_latency_ms: p50=8,402  p99=29,940
hikaricp_connections_pending: 1,847
ws_errors: 0.00%
```

✅ **p99 of 30 seconds and zero errors.** This is Module 01's unbounded-concurrency
trap arriving in production: 1,847 virtual threads queued on a 5-connection pool,
each holding a request, none failing, all slow. The dashboard says "healthy."

Eventually Hikari's own timeout fires:
```
java.sql.SQLTransientConnectionException: pulse-pool - Connection is not available,
request timed out after 30000ms.
```
30 seconds is far too long to wait to find out.

### The fix: bounded admission + a fast, clear failure

```java
@Service
public class MessageService {

    // Sized to the connection pool, not to concurrency. This is the explicit
    // limit that the thread pool used to provide by accident.
    private final Semaphore dbPermits;

    public MessageService(@Value("${spring.datasource.hikari.maximum-pool-size}") int poolSize) {
        this.dbPermits = new Semaphore(poolSize * 2, true);    // fair: FIFO, no starvation
    }

    public SendResult send(String roomId, String sender, MessageCreate create) {
        // ... dedup cache fast path (no DB) ...

        boolean acquired;
        try {
            acquired = dbPermits.tryAcquire(500, TimeUnit.MILLISECONDS);   // NOT 30s
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new ServiceUnavailableException("interrupted", 1000);
        }
        if (!acquired) {
            admissionRejections.increment();
            throw new ServiceUnavailableException("write path saturated", retryAfterMs());
        }

        try {
            return doSend(roomId, sender, create);
        } finally {
            dbPermits.release();
        }
    }

    /** Jittered, so rejected clients don't all return at the same instant. */
    private long retryAfterMs() {
        return ThreadLocalRandom.current().nextLong(500, 3000);
    }
}
```

```java
@MessageExceptionHandler(ServiceUnavailableException.class)
@SendToUser("/queue/errors")
public Envelope onUnavailable(ServiceUnavailableException e) {
    return Envelope.of("error", null, json.valueToTree(
            new Payloads.Error("unavailable", "try again shortly", null, e.retryAfterMs())));
}
```

```js
if (err.code === 'unavailable') {
  // The message is still pending locally with its clientId. Retry is SAFE
  // because of Module 05's idempotency — that is what makes this design work.
  setTimeout(() => resend(err.clientId), err.retryAfterMs);
  showToast('Reconnecting…');
}
```

**Expected after:**
```
fanout_latency_ms: p50=18  p99=94
hikaricp_connections_pending: 0
admission_rejections_total: 4,821
ws_errors: 8.20%
```

| | Naive | Bounded |
|---|-------|---------|
| p50 | 8,402 ms | **18 ms** |
| p99 | 29,940 ms | **94 ms** |
| Hikari pending | 1,847 | **0** |
| Errors | 0% | 8.2% |
| Messages ultimately delivered | 100% (eventually) | **100%** (via retry) |
| Time to detect the problem | 30 s (first timeout) | **< 1 s** (rejection metric) |

✅ **Same messages delivered, 318× better p99, and the problem is visible
immediately.** The 8.2% "errors" are rejections that the client retried
successfully — because the `clientId` makes retry free.

> **The three pieces that make this work were all built earlier:** idempotency
> (Module 05) makes retry safe; the client's pending-bubble state (Module 05)
> makes retry invisible to the user; and jitter (Module 10) stops the retries
> arriving together. Bounded admission is only tolerable because those exist.

---

## Task 6 (stretch) — The 74 TB model

### Baseline, one year, 10,000 msg/s

```
864,000,000 rows/day x 236 bytes = 204 GB/day
                                 = 74.4 TB/year
```

| Component | Sizing | Cost/month (AWS us-east-1) |
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

That last row is a product decision, not an engineering one. Slack's free tier
does exactly this. It is by far the cheapest lever and the one most likely to be
rejected by product.

### Alternative 2 — Compression

```sql
-- Postgres 14+: LZ4 is ~4x faster than pglz at similar ratios
ALTER TABLE messages ALTER COLUMN body SET COMPRESSION lz4;
```
Measured on real chat text:

| | Value |
|---|-------|
| Body compression ratio | 2.4× |
| But body is only 84 of 236 bytes/row | |
| Effective row size | 236 → **187 bytes** (−21%) |
| Storage | 74 TB → **58.6 TB** |
| Cost/month | $26,240 → **$20,900** (−20%) |
| Write throughput | −6% |
| **User-visible consequence** | **None** |

Free in user terms, but only 20% — because most of the row is fixed overhead and
indexes, not body text. **Compression is not the answer at this shape**, and
knowing why (24 bytes of tuple header, 64 bytes of index entries) is the point.

### Alternative 3 — Tiering to object storage

Hot (90 days) in Postgres, cold in Parquet on S3, queried via a separate path.

| | Value |
|---|-------|
| Hot storage | 18.4 TB |
| Cold storage (56 TB, Parquet+zstd at 6× → 9.3 TB) | S3 Standard-IA |
| Cost/month | **$8,940** (−66%) |
| Restore time (hot) | **12 h** |
| Cold query latency | 2–30 s |
| **User-visible consequence** | **Messages older than 90 days take seconds to load, and aren't searchable in real time.** |
| Engineering cost | A tiering pipeline, a second query path, a merged UI |

### Recommendation

**Alternative 3, tiering — with Alternative 2 applied to the hot tier as a free
extra.**

Reasoning:

1. **Retention alone (Alt 1) is cheapest but is a product regression.** "Your
   history is gone" is a churn driver, and for paid tiers usually a contractual
   problem. Take it only if product explicitly chooses it.
2. **Compression alone (Alt 2) doesn't move the needle enough** — 20% off a
   $26k bill, still 49 hours to restore. It solves neither problem.
3. **Tiering gets 66% of the cost saving with no data loss**, and — more
   importantly — it fixes the **RTO**, which is the actual crisis. A 12-hour
   restore is survivable; 49 hours is a company-threatening outage.
4. The engineering cost is real (a pipeline, a second query path) but it's
   **bounded and one-time**, whereas the $17,300/month saving is recurring, and
   the access pattern is overwhelmingly favourable: measured, **98.7% of reads
   touch messages under 30 days old.**

**Sequence it:** ship Alt 2 immediately (one `ALTER TABLE`, no user impact),
implement partitioning (Module 13) which is a prerequisite for both other
options, then build tiering. Hold Alt 1 in reserve as the lever you pull if
growth outruns the plan.
