# Lab 10 — Close the Last Gap

**You'll:** build resume cursors, subscribe-before-resume, debounced gap repair,
permanent-gap marking, offline delivery and read receipts — then disconnect a
client for two minutes mid-conversation and prove it loses nothing.

⏱️ ~100 min. Work in `spring-boot-chat-course/apps/pulse`.

---

## Part A — Move the sequencer to Redis

Module 05 allocated sequences in Postgres, which serializes every send in a room
on a row lock. Move the hot path to Redis `INCR`; Postgres keeps the durable copy.

`src/main/resources/db/migration/V3__resume.sql`:

```sql
-- Per-(user, room) read cursor. This IS the offline queue: everything after
-- last_read_seq is unread, derivable with no per-message storage.
CREATE TABLE read_cursors (
    user_id       text        NOT NULL,
    room_id       text        NOT NULL,
    last_read_seq bigint      NOT NULL DEFAULT 0,
    updated_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, room_id)
);

-- Sequence numbers that were allocated but never used (Module 05's race).
-- A client asking for one of these must be told it will never arrive.
CREATE TABLE sequence_gaps (
    room_id    text        NOT NULL,
    seq        bigint      NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (room_id, seq)
);

-- Resume queries: WHERE room_id = ? AND seq > ? ORDER BY seq
CREATE INDEX idx_messages_resume ON messages (room_id, seq);
```

`src/main/java/com/pulse/chat/SequenceAllocator.java`:

```java
package com.pulse.chat;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Component
public class SequenceAllocator {

    private final StringRedisTemplate redis;
    private final JdbcClient jdbc;

    /** Hash tag so seq and stream share a slot (Module 08's Lua rule). */
    private static String key(String roomId) { return "room:{" + roomId + "}:seq"; }

    public long next(String roomId) {
        Long seq = redis.opsForValue().increment(key(roomId));
        if (seq == null) throw new IllegalStateException("INCR returned null for " + roomId);

        // First use after a Redis restart: the counter is gone and would restart
        // at 1, reusing sequence numbers. Recover the high-water mark from
        // Postgres exactly once.
        if (seq == 1L) {
            Long known = jdbc.sql("SELECT coalesce(max(seq), 0) FROM messages WHERE room_id = :r")
                             .param("r", roomId).query(Long.class).single();
            if (known > 0) {
                redis.opsForValue().set(key(roomId), String.valueOf(known + 1));
                return known + 1;
            }
        }
        return seq;
    }

    /** Record a sequence that was allocated but will never be used. */
    public void recordGap(String roomId, long seq) {
        jdbc.sql("""
                INSERT INTO sequence_gaps (room_id, seq) VALUES (:r, :s)
                ON CONFLICT DO NOTHING
                """).param("r", roomId).param("s", seq).update();
    }
}
```

> ⚠️ **The `seq == 1` recovery is not optional.** Without it, a Redis restart
> silently restarts every room's sequence at 1, every client sees a massive
> backwards jump, and every resume request returns the entire room history. This
> is the single nastiest failure mode in this design, and it's why the fan-out
> Redis being non-durable (Module 08) is a decision with consequences you must
> handle explicitly.

Test the recovery:
```bash
r DEL 'room:{7}:seq'
./code/publish.sh room.7 "after redis lost the counter"
docker exec pulse-postgres psql -U pulse -d pulse -c \
  "SELECT max(seq) FROM messages WHERE room_id='room.7';"
r GET 'room:{7}:seq'
```
**Expected — the counter resumed above the known maximum, not at 1:**
```
 max
-----
  42
"42"
```

---

## Part B — The resume endpoint

`src/main/java/com/pulse/chat/ResumeService.java`:

```java
package com.pulse.chat;

import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class ResumeService {

    private static final int MAX_BATCH = 200;
    private static final int ABANDON_THRESHOLD = 5_000;

    private final JdbcClient jdbc;

    public ResumeResult resume(String roomId, String userId, long fromSeq) {

        long currentMax = jdbc.sql("SELECT coalesce(max(seq),0) FROM messages WHERE room_id=:r")
                              .param("r", roomId).query(Long.class).single();

        long behind = currentMax - fromSeq;

        // Too far behind to stream over a socket. Tell the client to give up on
        // the cursor and page history through REST instead.
        if (behind > ABANDON_THRESHOLD) {
            return ResumeResult.abandon(currentMax, behind);
        }

        List<MessageNew> messages = jdbc.sql("""
                SELECT id, client_id, seq, room_id, sender, body,
                       extract(epoch from created_at)*1000 AS ts, reply_to
                FROM messages
                WHERE room_id = :r AND seq > :from AND deleted_at IS NULL
                ORDER BY seq
                LIMIT :limit
                """)
                .param("r", roomId).param("from", fromSeq).param("limit", MAX_BATCH + 1)
                .query(MessageNew.class).list();

        boolean hasMore = messages.size() > MAX_BATCH;
        if (hasMore) messages = messages.subList(0, MAX_BATCH);

        long upTo = messages.isEmpty() ? fromSeq : messages.get(messages.size() - 1).seq();

        // Sequences in this range that will NEVER be filled. Without these the
        // client's gap detector retries forever.
        List<Long> gaps = jdbc.sql("""
                SELECT seq FROM sequence_gaps
                WHERE room_id = :r AND seq > :from AND seq <= :upTo ORDER BY seq
                """)
                .param("r", roomId).param("from", fromSeq).param("upTo", upTo)
                .query(Long.class).list();

        return new ResumeResult(messages, gaps, hasMore, false, currentMax);
    }

    public record ResumeResult(List<MessageNew> messages, List<Long> gaps,
                               boolean hasMore, boolean abandon, long currentSeq) {
        static ResumeResult abandon(long currentSeq, long behind) {
            return new ResumeResult(List.of(), List.of(), false, true, currentSeq);
        }
    }
}
```

Controller:

```java
@MessageMapping("/room.{roomId}/resume")
public void resume(@DestinationVariable String roomId,
                   @Payload ResumeRequest request,
                   Principal principal) {

    if (!membership.isMember(principal.getName(), roomId))
        throw new AccessDeniedException("not a member of " + roomId);

    var result = resumeService.resume(roomId, principal.getName(), request.fromSeq());

    template.convertAndSendToUser(principal.getName(), "/queue/resume",
            Envelope.of("resume.batch", roomId, json.valueToTree(result)));

    resumeRequests.increment();
    resumeDepth.record(result.currentSeq() - request.fromSeq());
}
```

Test it by hand:

```bash
for i in $(seq 1 10); do ./code/publish.sh room.20 "history-$i"; done

printf 'CONNECT\naccept-version:1.2\nAuthorization:user:alice\n\n\x00\n'\
'SUBSCRIBE\nid:r\ndestination:/user/queue/resume\n\n\x00\n'\
'SEND\ndestination:/app/room.20/resume\ncontent-type:application/json\n\n{"fromSeq":4}\x00\n' \
  | websocat -n --text ws://localhost:8080/ws
```

**Expected — messages 5 through 10 only:**
```
MESSAGE
destination:/user/queue/resume

{"v":1,"type":"resume.batch","room":"20","data":{
  "messages":[{"seq":5,"body":"history-5",...},
              {"seq":6,"body":"history-6",...},
              ...
              {"seq":10,"body":"history-10",...}],
  "gaps":[],"hasMore":false,"abandon":false,"currentSeq":10}}
```

---

## Part C — The client: subscribe, then resume

`src/main/resources/static/pulse-client.js`:

```js
export class PulseRoom {
  constructor(client, roomId, onMessage) {
    this.client = client;
    this.roomId = roomId;
    this.onMessage = onMessage;

    this.lastContiguous = this.loadCursor();   // survives page reload
    this.buffer = new Map();                   // seq -> message, out of order
    this.knownGaps = new Set();                // permanently absent seqs
    this.repairTimer = null;
    this.resuming = false;
  }

  loadCursor() {
    try { return Number(localStorage.getItem(`pulse:cursor:${this.roomId}`) || 0); }
    catch (e) { return 0; }                    // private mode / storage disabled
  }

  saveCursor() {
    try { localStorage.setItem(`pulse:cursor:${this.roomId}`, String(this.lastContiguous)); }
    catch (e) { /* non-fatal: we just re-resume next time */ }
  }

  /** SUBSCRIBE FIRST, THEN RESUME. Order matters — see the README. */
  connect() {
    this.client.subscribe(`/topic/room.${this.roomId}`, f => {
      const env = JSON.parse(f.body);
      if (env.type === 'message.new') this.ingest(env.data);
    });

    this.client.subscribe('/user/queue/resume', f => {
      const env = JSON.parse(f.body);
      if (env.room === this.roomId) this.onResumeBatch(env.data);
    });

    // Live messages are now arriving and being buffered. Safe to ask for history.
    this.requestResume();
  }

  requestResume() {
    if (this.resuming) return;                 // one in flight at a time
    this.resuming = true;
    this.client.publish({
      destination: `/app/room.${this.roomId}/resume`,
      body: JSON.stringify({ fromSeq: this.lastContiguous }),
    });
  }

  onResumeBatch(batch) {
    this.resuming = false;

    if (batch.abandon) {
      // Too far behind. Drop the cursor, load a fresh page via REST.
      console.warn(`room ${this.roomId}: ${batch.currentSeq - this.lastContiguous} behind, abandoning cursor`);
      this.lastContiguous = batch.currentSeq;
      this.buffer.clear();
      this.saveCursor();
      this.onMessage({ type: 'history-reset', currentSeq: batch.currentSeq });
      return;
    }

    batch.gaps.forEach(seq => this.knownGaps.add(seq));
    batch.messages.forEach(m => this.ingest(m));

    if (batch.hasMore) this.requestResume();   // keep paging
  }

  ingest(msg) {
    const expected = this.lastContiguous + 1;

    if (msg.seq < expected)      return;       // duplicate — expected, harmless
    if (this.buffer.has(msg.seq)) return;      // already buffered

    if (msg.seq === expected) {
      this.deliver(msg);
      this.drain();
    } else {
      this.buffer.set(msg.seq, msg);
      this.scheduleRepair();                   // debounced — see below
    }
  }

  deliver(msg) {
    this.onMessage(msg);
    this.lastContiguous = msg.seq;
    this.saveCursor();
  }

  /** Advance past anything now contiguous, skipping known-permanent gaps. */
  drain() {
    for (;;) {
      const next = this.lastContiguous + 1;
      if (this.buffer.has(next)) {
        const m = this.buffer.get(next);
        this.buffer.delete(next);
        this.deliver(m);
      } else if (this.knownGaps.has(next)) {
        this.lastContiguous = next;            // will never arrive; step over it
        this.saveCursor();
      } else {
        break;
      }
    }
    if (this.buffer.size === 0 && this.repairTimer) {
      clearTimeout(this.repairTimer);
      this.repairTimer = null;
    }
  }

  /**
   * DEBOUNCED. Messages routinely arrive tens of milliseconds out of order under
   * load; firing a resume on every apparent gap turns transient reordering into
   * a request storm.
   */
  scheduleRepair() {
    if (this.repairTimer) return;
    this.repairTimer = setTimeout(() => {
      this.repairTimer = null;
      if (this.buffer.size > 0) {
        console.warn(`room ${this.roomId}: gap at ${this.lastContiguous + 1}, repairing`);
        this.requestResume();
      }
    }, 500);
  }
}
```

---

## Part D — Prove the gap closes itself

Add a debug endpoint that delivers messages out of order:

```java
@MessageMapping("/debug/reorder")
public void reorder(@Payload ReorderRequest r) {
    // Deliver 3,1,2 instead of 1,2,3 — with a delay on the first.
    var msgs = messages.recent(r.roomId(), 3);
    scheduler.schedule(() -> deliver(msgs.get(0)), 300, TimeUnit.MILLISECONDS);
    deliver(msgs.get(2));
    deliver(msgs.get(1));
}
```

**Expected in the browser console:**
```
(nothing — no gap warning)
```
and messages render in order 1, 2, 3.

✅ The 500 ms debounce absorbed a 300 ms reordering with **zero** repair
requests. Now make the delay exceed the debounce:

```bash
curl -X POST localhost:8080/debug/reorder -d '{"roomId":"room.20","delayMs":900}'
```
**Expected:**
```
room 20: gap at 41, repairing
```
and then messages 41, 42, 43 render in order.

✅ One repair request, not three. Set the debounce to 0 and re-run to see the
storm you avoided:
```
room 20: gap at 41, repairing
room 20: gap at 41, repairing
room 20: gap at 41, repairing
```

---

## Part E — The two-minute disconnect test

**The headline test of the module.**

`code/disconnect_test.sh`:

```bash
#!/usr/bin/env bash
# alice keeps talking; bob's connection is severed for 2 minutes.
# Bob must end up with EVERY message, exactly once, in order.
set -euo pipefail

ROOM=room.30
OUT=/tmp/bob-seqs.txt
: > "$OUT"

node code/bob-client.js "$ROOM" "$OUT" &
BOB=$!
sleep 3

for i in $(seq 1 40); do
  ./code/publish.sh "$ROOM" "before-$i"
  sleep 0.1
done

echo ">>> severing bob's connection for 120s"
# DROP, not REJECT: no RST, so it looks like a dead network, not a refusal.
sudo iptables -I OUTPUT -p tcp --dport 8080 -m owner --uid-owner "$(id -u)" -j DROP

for i in $(seq 1 100); do
  ./code/publish.sh "$ROOM" "during-$i"
  sleep 1
done

echo ">>> restoring"
sudo iptables -D OUTPUT -p tcp --dport 8080 -m owner --uid-owner "$(id -u)" -j DROP

for i in $(seq 1 20); do
  ./code/publish.sh "$ROOM" "after-$i"
  sleep 0.2
done

sleep 15
kill $BOB 2>/dev/null || true

TOTAL=160
GOT=$(sort -n "$OUT" | uniq | wc -l)
DUPES=$(( $(wc -l < "$OUT") - GOT ))
ORDERED=$(sort -nc "$OUT" 2>/dev/null && echo yes || echo no)

echo "expected: $TOTAL   distinct: $GOT   duplicates delivered: $DUPES   in order: $ORDERED"
sort -n "$OUT" | uniq | awk 'NR>1 && $1 != prev+1 {print "GAP: " prev " -> " $1} {prev=$1}'
```

```bash
chmod +x code/disconnect_test.sh
./code/disconnect_test.sh
```

**Expected — before you implement resume (comment out `requestResume()`):**
```
expected: 160   distinct: 62   duplicates delivered: 0   in order: yes
GAP: 40 -> 139
```
98 messages permanently missing.

**Expected — with resume:**
```
>>> severing bob's connection for 120s
>>> restoring
expected: 160   distinct: 160   duplicates delivered: 7   in order: yes
```

✅ **All 160 delivered, in order, with 7 duplicates that the client deduped.**

Those 7 duplicates are the subscribe-before-resume overlap working exactly as
designed: messages that arrived live *while* the resume query was running got
delivered twice, and `ingest()` dropped the second copy.

Confirm the client's log shows the recovery:
```
[bob] socket closed, code=1006
[bob] reconnect attempt 1 in 1,204ms
[bob] reconnect attempt 5 in 18,900ms
[bob] connected
[bob] resuming room.30 from seq 40
[bob] resume.batch: 200 messages, hasMore=true
[bob] resuming room.30 from seq 240
[bob] resume.batch: 100 messages, hasMore=false
[bob] caught up at seq 300
```

Record it:
```markdown
## Module 10 — Resume

- 2-minute disconnect, 100 messages missed
  - without resume: 98 lost permanently
  - with resume:    0 lost, 7 duplicates (deduped client-side), order preserved
- Resume batch size: 200; abandon threshold: 5,000
- Gap-repair debounce: 500ms (absorbs reordering up to ~500ms with 0 requests)
```

---

## Part F — Offline delivery from the message store

No per-user queues. The cursor table *is* the queue.

```java
@GetMapping("/api/rooms/{roomId}/unread")
public UnreadSummary unread(@PathVariable String roomId, Principal principal) {
    return jdbc.sql("""
            SELECT
              coalesce((SELECT max(seq) FROM messages WHERE room_id = :r), 0) AS room_seq,
              coalesce((SELECT last_read_seq FROM read_cursors
                        WHERE user_id = :u AND room_id = :r), 0)             AS read_seq
            """)
            .param("r", roomId).param("u", principal.getName())
            .query((rs, n) -> new UnreadSummary(
                    roomId, rs.getLong("room_seq"), rs.getLong("read_seq"),
                    rs.getLong("room_seq") - rs.getLong("read_seq")))
            .single();
}
```

```bash
curl -s -H 'X-User: bob' localhost:8080/api/rooms/room.30/unread | jq
```
**Expected:**
```json
{ "roomId": "room.30", "roomSeq": 300, "readSeq": 140, "unread": 160 }
```

✅ **160 unread messages, computed from two integers.** No queue, no per-message
storage, and it's correct after any outage because it's derived rather than
maintained.

Compare the storage cost:

| Approach | 1M users × 20 rooms × 100 unread |
|----------|----------------------------------|
| Per-user message queue | 2,000,000,000 rows |
| **Two sequence numbers** | **20,000,000 rows × 16 bytes = 320 MB** |

---

## Part G — Read receipts

```java
@MessageMapping("/room.{roomId}/read")
public void read(@DestinationVariable String roomId,
                 @Payload @Valid ReadUpto readUpto,
                 Principal principal) {

    // GREATEST() makes this idempotent and order-independent: an out-of-order
    // or duplicated receipt can never move the cursor backwards.
    jdbc.sql("""
            INSERT INTO read_cursors (user_id, room_id, last_read_seq)
            VALUES (:u, :r, :s)
            ON CONFLICT (user_id, room_id) DO UPDATE
              SET last_read_seq = GREATEST(read_cursors.last_read_seq, EXCLUDED.last_read_seq),
                  updated_at = now()
            """)
            .param("u", principal.getName()).param("r", roomId).param("s", readUpto.seq())
            .update();

    // Ephemeral: Pub/Sub is correct here. A lost receipt self-heals on the next
    // one, so paying for stream storage would be waste (Module 09's routing rule).
    fanout.publishEphemeral(roomId, Envelope.of("read.update", roomId,
            json.valueToTree(new ReadUpdate(principal.getName(), readUpto.seq()))));
}
```

Client, debounced:
```js
let pendingRead = 0, readTimer = null;

function markRead(seq) {
  pendingRead = Math.max(pendingRead, seq);
  if (readTimer) return;
  readTimer = setTimeout(() => {
    readTimer = null;
    client.publish({ destination: `/app/${room}/read`,
                     body: JSON.stringify({ seq: pendingRead }) });
  }, 2000);
}
```

Prove idempotency:
```bash
for s in 50 30 50 45 60 20; do ./code/read.sh room.30 bob "$s"; done
docker exec pulse-postgres psql -U pulse -d pulse -c \
  "SELECT last_read_seq FROM read_cursors WHERE user_id='bob' AND room_id='room.30';"
```
**Expected — the maximum, regardless of arrival order:**
```
 last_read_seq
---------------
            60
```

✅ Out-of-order and duplicate receipts are absorbed by `GREATEST`. This is why
they can ride lossy transport.

Measure the debounce win:

| | Receipts sent, 5 min of active reading |
|---|---------------------------------------|
| Per message rendered | 412 |
| Debounced 2 s | **18** |

**23× fewer**, and the user-visible behaviour is identical.

---

## Part H — Reconnect with jittered backoff

The client-side half of Module 18's thundering herd.

```js
const client = new Client({
  brokerURL: 'ws://localhost:8080/ws',
  connectHeaders: { Authorization: 'user:' + user },
  heartbeatIncoming: 10000,
  heartbeatOutgoing: 10000,
  reconnectDelay: 0,                    // OFF — we do it ourselves, with jitter
});

let attempt = 0;

client.onWebSocketClose = (e) => {
  // 4xxx codes are ours and are meaningful; 1006 means the network died.
  if (e.code === 4001) return refreshTokenThenReconnect();
  if (e.code === 4003) return showKicked();

  const base = Math.min(30000, 1000 * 2 ** attempt);
  const delay = Math.random() * base;          // FULL jitter, not base + jitter
  attempt++;
  console.log(`[${user}] reconnect attempt ${attempt} in ${Math.round(delay)}ms`);
  setTimeout(() => client.activate(), delay);
};

client.onConnect = () => {
  attempt = 0;
  rooms.forEach(r => r.connect());             // subscribe, then resume
};
```

> **Full jitter (`random() * base`), not `base + random()`.** With
> `base + jitter`, 10,000 clients all wait at least `base` and then arrive within
> a narrow window — you've delayed the herd, not dispersed it. Full jitter
> spreads arrivals uniformly across the whole window.

Prove it:
```bash
# kill the server with 5,000 clients connected, restart after 10s,
# and count connections per second on the way back
k6 run --vus 5000 --duration 3m code/reconnect-storm.js
```
**Expected — full jitter:**
```
peak reconnects/sec: 214    time to fully recover: 34s
```
**Expected — fixed 1s delay:**
```
peak reconnects/sec: 4,881  time to fully recover: 118s  (server briefly overloaded)
```

✅ **23× lower peak** and faster overall recovery, because the server never
saturates.

---

## What you built

- Redis-backed sequence allocation with **Postgres high-water-mark recovery** —
  the failure mode that would otherwise corrupt every client cursor.
- Resume with bounded batches, `hasMore` paging, and an abandon threshold.
- Permanent-gap marking so the client stops asking for sequences that will never
  exist.
- **Subscribe-before-resume**, preferring duplicates over gaps.
- Debounced gap repair that absorbs transient reordering with zero requests.
- Offline delivery derived from two integers instead of per-user queues.
- Idempotent read receipts, debounced 23×.
- Full-jitter reconnect with a 23× lower peak.

**The guarantee is now complete**, with its caveats stated in the README.

Now do [`challenge.md`](./challenge.md).

Then: [Module 11 — Presence, Typing & Rate Limiting](../11-presence-and-rate-limiting/).
