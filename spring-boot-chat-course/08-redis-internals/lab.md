# Lab 08 — Take Redis Apart

**You'll:** speak RESP with `nc`, measure the pipelining win, cross an encoding
threshold and watch memory jump 7×, stall your whole chat server with one
command, catch a fork pause in your p99, and decide persistence with data.

⏱️ ~100 min. Work in `spring-boot-chat-course/08-redis-internals/code/`.

```bash
docker compose -f ../../infra/compose.dev.yml up -d
alias r='docker exec -i pulse-redis redis-cli'
r PING
```
**Expected:** `PONG`

---

## Part A — Speak RESP by hand

```bash
printf '*1\r\n$4\r\nPING\r\n' | nc -q1 localhost 6379 | xxd
```

**Expected:**
```
00000000: 2b50 4f4e 470d 0a                        +PONG..
```

`+PONG\r\n` — a simple string. You just spoke Redis's protocol with no client
library.

Now a `SET` and a `GET`:

```bash
printf '*3\r\n$3\r\nSET\r\n$5\r\nhello\r\n$5\r\nworld\r\n*2\r\n$3\r\nGET\r\n$5\r\nhello\r\n' \
  | nc -q1 localhost 6379 | xxd
```

**Expected:**
```
00000000: 2b4f 4b0d 0a24 350d 0a77 6f72 6c64 0d0a  +OK..$5..world..
```

Read it: `+OK\r\n` then `$5\r\nworld\r\n`. A bulk string prefixed with its byte
length.

An error:
```bash
printf '*1\r\n$6\r\nNOPE!!\r\n' | nc -q1 localhost 6379
```
**Expected:**
```
-ERR unknown command 'NOPE!!', with args beginning with:
```

### Now see RESP3

```bash
r -3 HELLO 3 | head -12
```
**Expected:**
```
1# "server" => "redis"
2# "version" => "7.4.1"
3# "proto" => (integer) 3
4# "id" => (integer) 42
5# "mode" => "standalone"
6# "role" => "master"
```

`1#` marks a **map** entry. In RESP2 the same reply is a flat array you have to
re-pair by index — a genuine source of client bugs.

Compare directly:
```bash
r    CONFIG GET maxmemory        # RESP2
r -3 CONFIG GET maxmemory        # RESP3
```
**Expected:**
```
1) "maxmemory"
2) "536870912"
```
```
1# "maxmemory" => "536870912"
```

---

## Part B — Measure the pipelining win

`code/pipeline_bench.java`:

```java
import redis.clients.jedis.*;          // or use Lettuce; Jedis is clearer here
import java.time.*;

public class PipelineBench {
    public static void main(String[] args) {
        int n = 10_000;
        try (var jedis = new Jedis("localhost", 6379)) {

            Instant t0 = Instant.now();
            for (int i = 0; i < n; i++) jedis.set("bench:seq:" + i, "v" + i);
            long serial = Duration.between(t0, Instant.now()).toMillis();

            t0 = Instant.now();
            var pipeline = jedis.pipelined();
            for (int i = 0; i < n; i++) pipeline.set("bench:pipe:" + i, "v" + i);
            pipeline.sync();
            long piped = Duration.between(t0, Instant.now()).toMillis();

            System.out.printf("serial:   %,6d ms  (%,d ops/s)%n", serial, n * 1000L / serial);
            System.out.printf("pipelined:%,6d ms  (%,d ops/s)%n", piped, n * 1000L / piped);
            System.out.printf("speedup:  %.1fx%n", serial / (double) piped);
        }
    }
}
```

**Expected (loopback, so RTT is already tiny):**
```
serial:    1,842 ms  (5,428 ops/s)
pipelined:    91 ms  (109,890 ops/s)
speedup:  20.2x
```

Now add realistic network latency and re-run:

```bash
sudo tc qdisc add dev lo root netem delay 1ms
java code/pipeline_bench.java
sudo tc qdisc del dev lo root
```

**Expected:**
```
serial:   21,408 ms  (467 ops/s)
pipelined:   118 ms  (84,745 ops/s)
speedup:  181.4x
```

✅ **181×.** With a 1 ms RTT, the serial version spends 21 of its 21.4 seconds
waiting on the network. Redis did identical work in both runs — confirm it:

```bash
r INFO commandstats | grep cmdstat_set
```
**Expected:**
```
cmdstat_set:calls=40000,usec=48122,usec_per_call=1.20
```

**48 ms of actual Redis work** for 40,000 SETs. Everything else was round trips.

> This is why Module 09's stream consumer reads with `COUNT 100` and why the
> outbox relay (Module 13) batches. Round trips, not Redis, are your cost.

---

## Part C — Cross an encoding threshold

```bash
r DEL unread:small unread:big

# 100 rooms — under the 128 threshold
for i in $(seq 1 100); do r HSET unread:small "room:$i" 3 > /dev/null; done

# 200 rooms — over it
for i in $(seq 1 200); do r HSET unread:big "room:$i" 3 > /dev/null; done

r OBJECT ENCODING unread:small
r OBJECT ENCODING unread:big
r MEMORY USAGE unread:small
r MEMORY USAGE unread:big
```

**Expected:**
```
listpack
hashtable
1928
14488
```

✅ **100 fields: 1,928 bytes. 200 fields: 14,488 bytes.** Twice the data, **7.5×
the memory.**

Watch the exact crossover:

```bash
r DEL unread:probe
for i in $(seq 1 130); do
  r HSET unread:probe "room:$i" 3 > /dev/null
  if [ $((i % 10)) -eq 0 ] || [ $i -ge 126 ]; then
    printf "%3d fields: %-10s %6s bytes\n" "$i" \
      "$(r OBJECT ENCODING unread:probe)" "$(r MEMORY USAGE unread:probe)"
  fi
done
```

**Expected:**
```
 10 fields: listpack      338 bytes
 ...
120 fields: listpack     2264 bytes
126 fields: listpack     2372 bytes
127 fields: listpack     2390 bytes
128 fields: listpack     2408 bytes
129 fields: hashtable    9528 bytes      <-- THE CLIFF
130 fields: hashtable    9576 bytes
```

✅ **One field took it from 2,408 to 9,528 bytes.** And it is **irreversible** —
delete fields back down to 50 and check:

```bash
for i in $(seq 51 130); do r HDEL unread:probe "room:$i" > /dev/null; done
r OBJECT ENCODING unread:probe
r MEMORY USAGE unread:probe
```
**Expected:**
```
hashtable
5512
```

Still `hashtable`. Redis converts up, never down. A user who was briefly in 129
rooms pays hashtable prices forever.

### The Pulse implication

At 1,000,000 users:

| Rooms per user | Encoding | Bytes each | Total |
|----------------|----------|-----------|-------|
| 100 | listpack | 1,928 | **1.9 GB** |
| 129 | hashtable | 9,528 | **9.5 GB** |

**Mitigation options:**
```bash
# (a) raise the threshold — costs CPU, since listpack lookup is O(n)
r CONFIG SET hash-max-listpack-entries 512

# (b) split the key so each stays small
#     unread:{42}:a  (rooms hashing to a)
#     unread:{42}:b
```

Measure (a)'s CPU cost before adopting it:
```bash
r CONFIG SET hash-max-listpack-entries 512
r DEL unread:wide; for i in $(seq 1 500); do r HSET unread:wide "room:$i" 3 >/dev/null; done
r OBJECT ENCODING unread:wide
redis-benchmark -h localhost -n 100000 -t hget -r 500 --csv 2>/dev/null | tail -1
```
**Expected:**
```
listpack
"HGET","184501.84","0.271","0.104","0.263","0.399","0.535","1.111"
```
versus with `hashtable` at the default threshold: ~248,000 ops/s.

✅ **~26% slower reads for ~5× less memory.** For unread counts — read rarely,
stored for every user — that's a good trade. For a hot lookup path it wouldn't
be. Record the number and decide deliberately.

---

## Part D — Stall your chat server with one command

**This is the module's centrepiece.** Have Pulse running under load while you do
this.

```bash
# Terminal 1: load
k6 run -e ROOMS=100 -e SEND_EVERY=10000 --vus 5000 --duration 5m \
       ../../06-load-testing-harness/code/pulse-load.js

# Terminal 2: watch chat latency
watch -n1 'curl -s localhost:8080/actuator/metrics/chat.fanout.latency \
  | jq -r ".measurements[] | \"\(.statistic) \(.value)\""'

# Terminal 3: fill Redis with keys, then run the bad command
for i in $(seq 1 200); do
  r EVAL "for i=1,50000 do redis.call('SET', 'junk:'..ARGV[1]..':'..i, i) end" 0 "$i" > /dev/null
done
r DBSIZE
```
**Expected:**
```
(integer) 10000341
```

Now, with 10 million keys and live chat traffic:

```bash
time r KEYS 'junk:*' > /dev/null
```

**Expected:**
```
real    0m3.412s
```

And in terminal 2, during those 3.4 seconds:

**Expected:**
```
COUNT 48211
TOTAL_TIME 891.2
MAX 3408.0          <-- your chat p-max just became 3.4 seconds
```

k6, in terminal 1:
```
WARN[0184] Request Failed  error="websocket: close 1006"
fanout_latency_ms: p(99)=3,402ms   (was 161ms)
```

✅ **One `KEYS` in a debug console added 3.4 seconds to every user's message
latency and dropped connections.** Nothing crashed. Redis reported no error.

Confirm the diagnosis after the fact:
```bash
r SLOWLOG GET 3
```
**Expected:**
```
1) 1) (integer) 14
   2) (integer) 1735689612
   3) (integer) 3408122          <-- microseconds
   4) 1) "KEYS"
      2) "junk:*"
   5) "172.17.0.1:54322"
```
```bash
r INFO commandstats | grep -E 'cmdstat_(keys|xadd|publish)'
```
```
cmdstat_keys:calls=1,usec=3408122,usec_per_call=3408122.00
cmdstat_publish:calls=284119,usec=497208,usec_per_call=1.75
```

**One call consumed 6.8× more single-thread time than 284,119 publishes.**

### The correct way

```bash
time r --scan --pattern 'junk:*' | wc -l
```
**Expected:**
```
10000000
real    0m8.941s
```

Slower in wall-clock (8.9 s vs 3.4 s) but chat latency during it:

**Expected in terminal 2:**
```
MAX 178.0
```

✅ `SCAN` does bounded work per call and yields between them. **Longer total,
zero impact on everyone else.** That's the tradeoff worth internalizing:
throughput for a single operation versus latency for everybody.

Ban `KEYS` in production:
```bash
r CONFIG SET rename-command "KEYS KEYS_DANGEROUS_a8f3c1"
```
(or in `redis.conf`; note Redis 7 prefers ACLs for this.)

Clean up:
```bash
r --scan --pattern 'junk:*' | xargs -L 1000 docker exec -i pulse-redis redis-cli DEL > /dev/null
```

---

## Part E — Catch a fork pause

```bash
r CONFIG SET save "900 1"
r DBSIZE
```

Fill Redis with a few GB, run chat load, then force a snapshot:

```bash
for i in $(seq 1 400); do
  r EVAL "for i=1,20000 do redis.call('SET','big:'..ARGV[1]..':'..i, string.rep('x',200)) end" 0 "$i" >/dev/null
done
r INFO memory | grep used_memory_human
```
**Expected:**
```
used_memory_human:2.31G
```

With load running:
```bash
r BGSAVE
sleep 3
r INFO persistence | grep -E 'latest_fork_usec|rdb_bgsave_in_progress|rdb_last_bgsave_status'
r INFO memory | grep -E 'used_memory_rss_human|used_memory_human'
```

**Expected:**
```
latest_fork_usec:271000
rdb_bgsave_in_progress:0
rdb_last_bgsave_status:ok
used_memory_human:2.31G
used_memory_rss_human:3.94G          <-- copy-on-write during the save
```

✅ **271 ms of fork pause** — every client blocked — and RSS spiked from 2.3 GB
to 3.9 GB from copy-on-write. On an 8 GB container with a 4 GB dataset, that
spike is an OOM kill.

Correlate it with chat:
```bash
curl -s localhost:8080/actuator/metrics/chat.fanout.latency | jq '.measurements[]|select(.statistic=="MAX")'
```
**Expected:**
```
{ "statistic": "MAX", "value": 289.4 }
```

271 ms of fork, 289 ms of worst-case chat latency. **That is your mysterious
p99.9 spike, and nothing in your application logs will ever explain it.**

Graph the correlation:
```bash
while true; do
  echo "$(date +%s),$(r INFO persistence | awk -F: '/latest_fork_usec/{print $2}' | tr -d '\r')"
  sleep 5
done > /tmp/forks.csv &
```

---

## Part F — Decide persistence with data

Run the identical chat benchmark under three configurations.

```bash
# 1. Everything off
r CONFIG SET save ""
r CONFIG SET appendonly no

# 2. RDB only
r CONFIG SET save "60 1000"
r CONFIG SET appendonly no

# 3. AOF everysec
r CONFIG SET save ""
r CONFIG SET appendonly yes
r CONFIG SET appendfsync everysec
```

For each: `k6 run -e SEND_EVERY=5000 --vus 10000 --duration 5m ...`

**Expected:**

| Config | p50 | p99 | **p99.9** | Redis CPU | Peak RSS | Loss on `docker kill` |
|--------|-----|-----|-----------|-----------|----------|----------------------|
| No persistence | 16 ms | 148 ms | **412 ms** | 51% | 2.3 GB | **everything** |
| RDB (60s/1000) | 17 ms | 154 ms | **1,890 ms** | 58% | **4.1 GB** | up to 60 s |
| AOF everysec | 18 ms | 161 ms | **604 ms** | 71% | 2.4 GB | ~1 s |

### Reading this

**RDB's p99.9 is 4.6× worse** than no persistence — entirely the fork pauses.
And its peak RSS is 78% higher, which is a container-sizing problem, not a
performance one.

**AOF is gentler on the tail** (no periodic fork; the rewrite fork is rarer) but
costs 20% more CPU continuously.

### The decision for Pulse

**Two Redis instances, different settings.**

```yaml
  redis-fanout:                 # streams, pub/sub — transport, not truth
    command: >
      redis-server --save "" --appendonly no
                   --maxmemory 4gb --maxmemory-policy noeviction

  redis-state:                  # presence, unread, rate limits
    command: >
      redis-server --save "300 100" --appendonly yes --appendfsync everysec
                   --maxmemory 2gb --maxmemory-policy noeviction
```

**Justification:**

- **Fan-out Redis:** Postgres is the source of truth (Module 12) and the outbox
  can replay (Module 13), so a restart losing in-flight streams costs a replay,
  not data. In exchange you get the best p99.9 and no RSS spike. `noeviction`
  because a silently-evicted stream is invisible data loss; a failing `XADD` is a
  page.
- **State Redis:** presence is TTL-based and self-heals, but unread counts and
  rate-limit buckets are genuinely more expensive to rebuild. AOF `everysec`
  bounds loss to ~1 second at 20% CPU on a much smaller dataset.

> **Argue the other side before you accept this.** The strongest counter is that
> two Redis instances is two things to monitor, fail over, and reason about, and
> that a single AOF instance is 8% worse at p99 and *much* simpler. If your team
> is small, take the simpler option — and now you know exactly what the 8% and
> the 604 ms p99.9 are buying you.

Record it:
```markdown
## Module 08 — Redis internals

- Pipelining speedup: 20x on loopback, 181x at 1ms RTT
- Redis work for 40,000 SETs: 48ms (the rest was round trips)
- Hash encoding cliff: 128->129 fields = 2,408 -> 9,528 bytes (4x), irreversible
- listpack at 512 entries: 26% slower reads, 5x less memory
- KEYS on 10M keys: 3.4s single-thread stall -> chat p99 161ms -> 3,402ms
- SCAN equivalent: 8.9s wall clock, chat max 178ms (no impact)
- Fork pause at 2.3GB: 271ms, RSS spike to 3.9GB
- Persistence p99.9: none 412ms | RDB 1,890ms | AOF 604ms
```

---

## Part G — A Lua script you'll reuse

Atomic "reserve a sequence and append", which Module 09 builds on:

`code/append.lua`:
```lua
-- KEYS[1] = seq counter,  KEYS[2] = stream
-- ARGV[1] = maxlen,       ARGV[2..] = field/value pairs
-- Both keys share a hash tag so this works in Cluster.
local seq = redis.call('INCR', KEYS[1])
local args = {'XADD', KEYS[2], 'MAXLEN', '~', ARGV[1], '*', 'seq', seq}
for i = 2, #ARGV do
    table.insert(args, ARGV[i])
end
local id = redis.call(unpack(args))
return {seq, id}
```

```bash
SHA=$(r SCRIPT LOAD "$(cat code/append.lua)")
echo "$SHA"
r EVALSHA "$SHA" 2 'room:{7}:seq' 'room:{7}:stream' 10000 body 'hello' sender 'alice'
r EVALSHA "$SHA" 2 'room:{7}:seq' 'room:{7}:stream' 10000 body 'again' sender 'bob'
```

**Expected:**
```
"a3f81c92e4d5..."
1) (integer) 1
2) "1735689600123-0"
1) (integer) 2
2) "1735689600456-0"
```

✅ The sequence increment and the stream append happened **atomically**. No other
client ran between them. In application code that's a race; here it's free.

Prove the same-slot rule:
```bash
r EVALSHA "$SHA" 2 'room:7:seq' 'room:9:stream' 10000 body 'x'
```
On a single node this works. **In Cluster it fails** with:
```
(error) CROSSSLOT Keys in request don't hash to the same slot
```
Which is why the hash tags `{7}` are there.

Verify:
```bash
r CLUSTER KEYSLOT 'room:{7}:seq'
r CLUSTER KEYSLOT 'room:{7}:stream'
```
**Expected — identical:**
```
(integer) 13429
(integer) 13429
```

---

## What you learned

- RESP is simple enough to speak with `nc`, and RESP3's push type is what removes
  Module 07's second-connection requirement.
- **Round trips, not Redis, are your cost.** 40,000 SETs = 48 ms of Redis work.
- Encoding thresholds create a silent, irreversible memory cliff.
- One `KEYS` turned a 161 ms p99 into 3.4 seconds for every user.
- Fork pauses are real, invisible to your application, and show up as
  unexplained p99.9 spikes.
- Persistence is a **semantic** choice about what data means, not a checkbox.

Now do [`challenge.md`](./challenge.md).

Then: [Module 09 — Redis Streams & Consumer Groups](../09-redis-streams-delivery/).
