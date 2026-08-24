# Lab 08 — Take Redis Apart

**You'll:** speak RESP with a raw socket and watch a RESP3 push land on a busy
connection; measure the pipelining win at 0 ms and at 1 ms RTT and find the
Python-specific wrinkle; profile the exact command mix *your* channel layer
issues and confirm Module 07's cost model; cross an encoding threshold and watch
memory jump 4× irreversibly; **stall live chat for 3.4 seconds with one
command** and then do the identical work for free; catch a fork pause inside your
own p99.9; settle persistence and eviction with measurements instead of
opinions; and load the Lua script that Modules 09 and 18 both depend on.

⏱️ ~110 min. Work in `django-chat-course/08-redis-internals/code/`, with Pulse
running under load from `../../06-load-testing-harness/code/`.

```bash
cd django-chat-course/08-redis-internals
source ../.venv/bin/activate
docker compose -p pulse-dev -f ../infra/compose.dev.yml up -d
pip install --quiet redis msgpack
alias r='docker exec -i pulse-redis redis-cli'
r PING && r INFO server | grep redis_version
```
**Expected:**
```
PONG
redis_version:7.4.1
```

Reference machine: **8-core / 16 GB, Ubuntu 24.04, Redis 7.4.1 in Docker,
Python 3.12.** Pulse runs 8 Uvicorn workers on `RedisChannelLayer` from
Module 07; its steady-state baseline is **p50 19 ms, p99 181 ms at 66,307
outbound msg/s**, and that is what "chat latency" means for the rest of this
lab.

---

## Part A — Speak RESP by hand

```bash
./code/resp.py ping
```
**Expected:**
```
-> b'*1\r\n$4\r\nPING\r\n'
<- b'+PONG\r\n'
```

`*1` — an array of one element. `$4` — a bulk string of four bytes. `+PONG` — a
simple string. You just spoke Redis's protocol with a socket and no library.

```bash
./code/resp.py raw SET hello world
./code/resp.py raw GET hello
./code/resp.py raw NOPE
```
**Expected:**
```
-> b'*3\r\n$3\r\nSET\r\n$5\r\nhello\r\n$5\r\nworld\r\n'
<- 'OK'
-> b'*2\r\n$3\r\nGET\r\n$5\r\nhello\r\n'
<- 'world'
-> b'*1\r\n$4\r\nNOPE\r\n'
<- RuntimeError("ERR unknown command 'NOPE', with args beginning with: ")
```

### RESP2 versus RESP3, on the same reply

```bash
./code/resp.py hello3
```
**Expected:**
```
RESP2: list  ['maxmemory-policy', 'noeviction']
RESP3: dict  {'maxmemory-policy': 'noeviction'}

RESP2 hands you a flat array you must re-pair by index -- a real,
recurring source of client bugs. RESP3 hands you a dict.
```

Now the type that matters to this course:

```bash
./code/resp.py push
```
**Expected:**
```
subscribed: ['subscribe', 'pulse.demo', 1]
SET on a subscribed connection: OK

now publish from another terminal:
  redis-cli -p 6379 PUBLISH pulse.demo hello
```
```bash
r PUBLISH pulse.demo hello
```
**Expected, back in the first terminal:**
```
received: ('PUSH', ['message', 'pulse.demo', 'hello'])
```

✅ **A normal command and an out-of-band delivery on one connection.** Try the
same thing in RESP2 and Redis refuses:

```bash
printf '*2\r\n$9\r\nSUBSCRIBE\r\n$10\r\npulse.demo\r\n*3\r\n$3\r\nSET\r\n$1\r\na\r\n$1\r\nb\r\n' \
  | nc -q1 localhost 6379 | tail -c 120
```
**Expected:**
```
-ERR Can't execute 'set': only (P|S)SUBSCRIBE / (P|S)UNSUBSCRIBE / PING / QUIT / RESET are allowed in this context
```

**That error is why `RedisPubSubChannelLayer` holds two connections per
worker** — `self._redis` for `PUBLISH`, `self._pubsub` for `SUBSCRIBE`. Confirm
it in your own running system:

```bash
r CLIENT LIST | awk '{print $1, $5, $9, $NF}' | head -8
r INFO clients | grep connected_clients
```
**Expected — 8 workers, two connections each, plus your CLI:**
```
id=142 addr=172.17.0.1:52104 name= cmd=publish
id=143 addr=172.17.0.1:52106 name= cmd=subscribe
...
connected_clients:19
```

---

## Part B — Measure the pipelining win

```bash
./code/pipeline_bench.py --n 10000
```

**Expected (loopback, so the RTT is already tiny):**
```
10,000 SETs of a 64-byte value, against localhost:6379

  serial          1842.1 ms        5,428 ops/s   redis     48.1 ms   network  97.4%
  pipelined         91.4 ms      109,890 ops/s   redis     47.9 ms   network  47.6%
  transaction       97.2 ms      102,881 ops/s   redis     48.4 ms   network  50.2%
  lua               88.0 ms      113,636 ops/s   redis     84.1 ms   network   4.4%
  async x32        312.4 ms       32,013 ops/s   redis     48.2 ms   network  84.6%
  async pipe        96.8 ms      103,306 ops/s   redis     48.0 ms   network  50.4%
```

✅ Read the **`redis` column**: 48 ms, in every mode. Redis did identical work in
all six. Everything else was round trips.

Now add a realistic network and re-run:

```bash
sudo tc qdisc add dev lo root netem delay 1ms
./code/pipeline_bench.py --n 10000
sudo tc qdisc del dev lo root
```

**Expected:**
```
  serial         21408.4 ms          467 ops/s   redis     48.3 ms   network 100.0%
  pipelined        118.2 ms       84,602 ops/s   redis     48.1 ms   network  59.3%
  transaction      124.9 ms       80,064 ops/s   redis     48.5 ms   network  61.2%
  lua               90.1 ms      110,988 ops/s   redis     84.4 ms   network   6.3%
  async x32        690.3 ms       14,486 ops/s   redis     48.1 ms   network  93.0%
  async pipe       121.7 ms       82,169 ops/s   redis     48.2 ms   network  60.4%
```

✅ **181× for the pipeline.** With a 1 ms RTT, the serial version spends 21.36 of
its 21.41 seconds waiting on the network.

### The Python-specific wrinkle

Compare `async x32` with `serial` and with `pipelined`:

| | loopback | 1 ms RTT |
|---|---------|----------|
| `serial` (sync, 1 in flight) | 5,428 ops/s | 467 ops/s |
| `async x32` (32 in flight, no pipeline) | 32,013 ops/s (**5.9×**) | 14,486 ops/s (**31×**) |
| `pipelined` (10,000 in flight) | 109,890 ops/s (**20×**) | 84,602 ops/s (**181×**) |

**Concurrency is not pipelining, but it is most of the way there for small N.**
Thirty-two coroutines each awaiting one command keep 32 requests in flight, so
their latencies overlap. That is why the naive async code in Modules 09–11 will
not be as catastrophic as the sync equivalent would be — and why it will still
be **5.8× slower** than an explicit pipeline at a real RTT.

**The rule for Pulse:** if you are issuing N commands for one logical operation
and N is known in advance, pipeline it. `asyncio.gather` over a connection pool
is the fallback when N is discovered as you go.

### And what `lua` cost

The `lua` row is the fastest *and* the only one whose `redis` column moved
(48 ms → 84 ms). It ran all 10,000 SETs inside Redis, atomically, in one round
trip — **and it held the single thread for 88 milliseconds.** Do it under load
and watch:

```bash
# terminal 1: chat load
k6 run -e ROOMS=100 -e SEND_EVERY=20000 --vus 5000 --duration 3m \
       ../06-load-testing-harness/code/pulse-load.js
# terminal 2
./code/pipeline_bench.py --n 200000
```
**Expected in k6's summary:**
```
     fanout_latency_ms..............: med=21  p(95)=78  p(99)=194  max=1,764
```

**A 1.7-second maximum**, and `SLOWLOG` names the culprit:
```bash
r SLOWLOG GET 1
```
```
1) 1) (integer) 41
   2) (integer) 1735689612
   3) (integer) 1741883                     <-- microseconds
   4) 1) "EVAL"
      2) "\n for i = 1, tonumber(ARGV[1]) do..."
```

✅ **Lua's atomicity is bought with everyone else's latency.** Keep scripts to
tens of operations. `append.lua` in Part H does exactly two.

---

## Part C — Profile your own channel layer

Generic advice is useless; measure your workload. Start Pulse with 8 workers and
run the Module 06 baseline, then ask Redis what it did.

```bash
uvicorn pulse.asgi:application --port 8000 --workers 8 --loop uvloop \
        --ws-per-message-deflate false &
sleep 5
r CONFIG RESETSTAT
k6 run -q -e ROOMS=100 -e SEND_EVERY=60000 --duration 5m \
       ../06-load-testing-harness/code/pulse-load.js
./code/redis_doctor.py --only thread
```

**Expected:**
```
== 2. who owns the single thread ===================================
    total ms  share        calls    us/call  command
       120.4  45.4%      160,096      25.00  bzpopmin
        48.2  18.2%       20,012      40.00  eval
        24.2   9.1%       20,012      35.00  zrange
        24.0   9.1%      180,108       5.00  zremrangebyscore
        16.0   6.1%      160,096       0.50  expire
        ...

  Total single-thread time since last RESETSTAT: 0.3 s
```

Check it against Module 07's model:

```
predicted per group_send = 55 us + 46 us x workers
measured  per group_send = 265,000 us / 20,012 sends = 13.2 us
```

**That does not match — and it should not.** The lab's model was measured *at
the knee*, with every worker holding a subscriber in every room. At the baseline
each `group_send` reaches far fewer workers:

```bash
../07-scale-out-redis-channel-layer/code/layer_probe.py amplification --room 7
```
```
  room members (channels) : 200
  worker processes        : 8
```
```
r INFO commandstats | awk -F'[:=,]' '/cmdstat_bzpopmin/{print $3/20012}'
```
**Expected:**
```
8.0
```

✅ **Eight `BZPOPMIN` wake-ups per `group_send`**, matching the model's
per-worker term exactly. The *total* is lower simply because 333 sends/s is 0.3%
of Redis's capacity. **The model predicts the shape; the load sets the
magnitude.** Being able to tell those apart is what lets you extrapolate.

### Try `io-threads`, honestly

Module 07 ended with Redis's single thread at 94%. `io-threads` is the
first thing anyone suggests. Test it:

```bash
docker exec pulse-redis redis-cli CONFIG SET io-threads 4        # 7.x: restart-only
docker compose -p pulse-dev -f ../infra/compose.dev.yml stop redis
docker run -d --name pulse-redis-io -p 6380:6379 redis:7-alpine \
  redis-server --io-threads 4 --io-threads-do-reads yes --save '' --appendonly no
```
Point the layer at 6380 and re-run the 8-worker knee hunt from Module 07.

**Expected:**

| | `io-threads 1` (default) | `io-threads 4` |
|---|-------------------------|----------------|
| 8-worker knee | 441,000 out msg/s | **476,000** (+7.9%) |
| Redis CPU at 441,000 | 94% (one core) | 71% + 38% across 4 threads |
| p50 at 66,307 out/s | 19 ms | 18 ms |
| `usec_per_call`, `eval` | 40.0 | **40.1** |

✅ **+7.9%, and `usec_per_call` did not move at all.** The I/O threads
parallelised socket reads, writes and protocol parsing — which is real, because
eight workers with two connections each generate a lot of syscalls — and did
**nothing** for command execution, which is still one thread.

**Verdict:** worth turning on (it is free), and nowhere near a fix. If you were
hoping for 4×, the shape of `usec_per_call` is the number that tells you why
you were never going to get it.

---

## Part D — Cross an encoding threshold

```bash
r DEL unread:probe
for i in $(seq 1 130); do
  r HSET unread:probe "room:$i" 3 > /dev/null
  if [ $((i % 20)) -eq 0 ] || [ $i -ge 126 ]; then
    printf "%3d fields: %-10s %6s bytes\n" "$i" \
      "$(r OBJECT ENCODING unread:probe)" "$(r MEMORY USAGE unread:probe)"
  fi
done
```

**Expected:**
```
 20 fields: listpack      458 bytes
 40 fields: listpack      842 bytes
 ...
120 fields: listpack     2264 bytes
126 fields: listpack     2372 bytes
127 fields: listpack     2390 bytes
128 fields: listpack     2408 bytes
129 fields: hashtable    9528 bytes      <-- THE CLIFF
130 fields: hashtable    9576 bytes
```

✅ **One field took it from 2,408 to 9,528 bytes.** And it is **irreversible**:

```bash
for i in $(seq 51 130); do r HDEL unread:probe "room:$i" > /dev/null; done
r OBJECT ENCODING unread:probe; r MEMORY USAGE unread:probe
```
**Expected:**
```
hashtable
5512
```

Still `hashtable`. **Redis converts up and never down.** A user who was briefly
in 129 rooms pays hashtable prices for the life of the key.

At a million users:

| Rooms per user | Encoding | Bytes each | Total |
|----------------|----------|-----------|-------|
| 100 | listpack | 1,928 | **1.9 GB** |
| 129 | hashtable | 9,528 | **9.5 GB** |

### The one nobody looks at: your group ZSETs

`pulse:group:room.<slug>` is a zset, and it crosses `zset-max-listpack-entries`
(128) the moment a room has 129 members.

```bash
r OBJECT ENCODING 'pulse:group:room.7'; r MEMORY USAGE 'pulse:group:room.7'
r ZCARD 'pulse:group:room.7'
```
**Expected, at 200 members:**
```
skiplist
17240
200
```
versus a 120-member room:
```
listpack
4912
```

```
100,000 rooms x 200 members x 86 B  =  1.72 GB of group membership alone
```

**That is memory `channels_redis` allocates on your behalf and never mentions.**
It is also the number that decides whether your fan-out Redis and your state
Redis can share a box.

Does the encoding change `group_send`'s cost? Measure rather than assume:

```bash
r CONFIG RESETSTAT
# 120-member room vs 200-member room, same message rate
r INFO commandstats | grep zrange
```
**Expected:**
```
cmdstat_zrange:calls=6000,usec=186000,usec_per_call=31.00     # listpack, 120
cmdstat_zrange:calls=6000,usec=210000,usec_per_call=35.00     # skiplist, 200
```

✅ **+13% on `ZRANGE` for +67% members** — the encoding is barely the issue;
building a 200-element reply is. **The cliff costs you memory, not latency**,
which is the opposite of what most people assume and the reason you measure both.

### Mitigations, priced

```bash
# (a) raise the threshold -- costs CPU, since listpack lookup is O(n)
r CONFIG SET hash-max-listpack-entries 512
r DEL unread:wide; for i in $(seq 1 500); do r HSET unread:wide "room:$i" 3 >/dev/null; done
r OBJECT ENCODING unread:wide; r MEMORY USAGE unread:wide
docker exec pulse-redis redis-benchmark -n 100000 -t hget -r 500 --csv 2>/dev/null | tail -1
```
**Expected:**
```
listpack
9744
"HGET","184501.84","0.271",...
```
versus `hashtable` at the default threshold: ~248,000 ops/s.

✅ **~26% slower reads for 4.7× less memory.** For unread counts — written often,
read rarely, stored for every user — that is a good trade. For a hot lookup path
it would not be. **Record the number and decide deliberately.**

```bash
# (b) split the key so each side stays small, keeping the hash tag intact
#     unread:{42}:a   unread:{42}:b   -- same slot in Cluster, both listpacks
```

---

## Part E — Stall your chat server with one command

**This is the module's centrepiece.** Pulse must be running under load.

```bash
# terminal 1: load
k6 run -e ROOMS=100 -e SEND_EVERY=20000 --vus 5000 --duration 6m \
       ../06-load-testing-harness/code/pulse-load.js
# terminal 2: watch chat latency, live
watch -n1 'curl -s localhost:8000/metrics | grep -E "chat_event_loop_lag|chat_fanout_failed"'
# terminal 3: the weapon
r DEBUG POPULATE 10000000 junk:
r DBSIZE
```
**Expected:**
```
OK
(integer) 10001102
```

> `DEBUG POPULATE` creates ten million keys inside Redis with no round trips.
> Doing the same thing with a Lua loop would itself be the outage you are about
> to cause, which is a lesson you get for free by reading this note.

Now, with ten million keys and live chat traffic:

```bash
time r KEYS 'junk:*' > /dev/null
```
**Expected:**
```
real    0m3.412s
```

**Expected in terminal 1's summary, and in the collector:**
```
     fanout_latency_ms..............: med=24 p(95)=91 p(99)=3,402 max=3,614
     ws_errors......................: 1.82%
     checks.........................: 98.11%
```
```
chat_event_loop_lag_seconds{worker="pid-61002"} 3.3812
```

✅ **One `KEYS` in a debug console added 3.4 seconds to every user's message
latency and dropped 1.8% of connections. Nothing crashed. Redis reported no
error.**

Note where the lag showed up: **in your workers' event loops**, because all
eight were parked in `BZPOPMIN` against a Redis that was not answering. The
symptom is a Python problem; the cause is three words someone typed into a
container.

Confirm the diagnosis after the fact — this is the workflow to internalise:

```bash
./code/redis_doctor.py --only slow --only thread
```
**Expected:**
```
== 3. what already blocked it ======================================
  slowlog-log-slower-than = 5000 us
     3412.1 ms  14:20:12  172.17.0.1:54322  KEYS junk:*

== 2. who owns the single thread ===================================
    total ms  share        calls    us/call  command
      3412.1  78.4%            1 3412100.00  keys  <-- ONE CALL IS AN OUTAGE
       484.9  11.1%      284,119       1.71  eval
```

**One call consumed seven times more single-thread time than 284,119 `EVAL`s.**

### The correct way, and its honest cost

```bash
time r --scan --pattern 'junk:*' | wc -l
```
**Expected:**
```
10000000
real    0m8.941s
```

**Expected in terminal 2, during those 8.9 seconds:**
```
chat_event_loop_lag_seconds{worker="pid-61002"} 0.0021
```
and in k6:
```
     fanout_latency_ms..............: med=21 p(95)=79 p(99)=196 max=241
```

✅ **2.6× longer in wall clock, and completely invisible to every user.**
`SCAN` does bounded work per call and yields between them. That is the trade
worth internalising: **throughput for one operation, versus latency for
everybody.** It is the same trade Module 07's batched group-repair made, and the
same one `XADD MAXLEN ~` makes in Module 09.

### Make it impossible

Redis 7 prefers ACLs to `rename-command`:

```bash
r ACL SETUSER app on '>pulsepass' '~*' '&*' '+@all' \
      '-keys' '-flushall' '-flushdb' '-debug' '-monitor' '-shutdown'
r ACL GETUSER app | head -6
```
**Expected:**
```
1) "flags"
2) 1) "on"
   2) "allkeys"
   3) "allchannels"
3) "passwords"
...
```
```bash
docker exec -i pulse-redis redis-cli --user app --pass pulsepass KEYS 'junk:*'
```
**Expected:**
```
(error) NOPERM User app has no permissions to run the 'keys' command
```

✅ Point Pulse's `REDIS_URL` at `redis://app:pulsepass@localhost:6379/0` and the
application literally cannot do this to itself. Keep an admin user for
operations, and be honest that the real control is that the admin credential is
not in anyone's shell history.

Clean up:
```bash
r FLUSHDB ASYNC      # ASYNC: frees in a background thread. Without it, FLUSHDB
                     # on 10M keys is itself a multi-second stall.
```

---

## Part F — Catch a fork pause inside your own p99.9

```bash
r CONFIG SET maxmemory 4gb                 # dev default is 1gb; we need room
r CONFIG SET save "900 1"
r DEBUG POPULATE 4000000 big: 512
r INFO memory | grep used_memory_human
```
**Expected:**
```
used_memory_human:2.31G
```

With chat load running:
```bash
r BGSAVE
sleep 3
r INFO persistence | grep -E 'latest_fork_usec|rdb_last_bgsave_status'
r INFO memory | grep -E 'used_memory_human|used_memory_rss_human'
```

**Expected:**
```
latest_fork_usec:271000
rdb_last_bgsave_status:ok
used_memory_human:2.31G
used_memory_rss_human:3.94G          <-- copy-on-write during the save
```

✅ **271 ms of fork pause** — every client blocked, including all eight
`BZPOPMIN` loops — and RSS spiked from 2.31 GB to 3.94 GB. On a 4 GB container
that spike is an OOM kill, and the OOM killer does not care that
`used_memory` said 2.31 GB.

Correlate it with chat:
```bash
curl -s localhost:8000/metrics | grep chat_event_loop_lag
```
**Expected:**
```
chat_event_loop_lag_seconds{worker="pid-61004"} 0.2894
```

**271 ms of fork, 289 ms of event-loop lag.** *That* is the mysterious p99.9
spike, and **nothing in your application logs will ever explain it.** Wire the
correlation now so you never have to guess:

```bash
while true; do
  echo "$(date +%s),$(r INFO persistence | awk -F: '/latest_fork_usec/{print $2}' | tr -d '\r')"
  sleep 5
done > /tmp/forks.csv &
```

Module 20 turns that into a Grafana annotation, which is the version you want
during an incident.

```bash
r CONFIG SET save ""; r FLUSHDB ASYNC; r CONFIG SET maxmemory 1gb
```

---

## Part G — Settle persistence and eviction with data

### Persistence

Run the identical 8-worker chat benchmark under three configurations.

```bash
# 1. nothing
r CONFIG SET save ""; r CONFIG SET appendonly no
# 2. RDB
r CONFIG SET save "60 1000"; r CONFIG SET appendonly no
# 3. AOF everysec
r CONFIG SET save ""; r CONFIG SET appendonly yes; r CONFIG SET appendfsync everysec
```

For each: `k6 run -e ROOMS=100 -e SEND_EVERY=20000 --vus 20000 --duration 5m …`

**Expected:**

| Config | p50 | p99 | **p99.9** | Redis CPU | Peak RSS | Loss on `docker kill` |
|--------|-----|-----|-----------|-----------|----------|----------------------|
| No persistence | 19 ms | 158 ms | **712 ms** | 21% | 41 MB | **everything** |
| RDB (60 s / 1000) | 20 ms | 164 ms | **1,940 ms** | 26% | **78 MB** | up to 60 s |
| AOF `everysec` | 21 ms | 171 ms | **810 ms** | 31% | 43 MB | ~1 s |

**RDB's p99.9 is 2.7× worse** than no persistence, entirely from fork pauses.
**AOF is gentler on the tail** (no periodic fork; the rewrite fork is rarer) and
costs 10 points of CPU continuously.

### But the interesting question is not durability

Module 07 already answered the durability question the hard way: a Redis restart
cost **139 of 200 messages and never recovered**, because the core channel
layer's group ZSETs lived in Redis and nothing rebuilt them.

So test the thing that actually matters:

```bash
r CONFIG SET appendonly yes; r CONFIG SET appendfsync everysec
../07-scale-out-redis-channel-layer/code/loss_test.py \
    --room 9 --fault kill --fault-at 4.0 --fault-for 3.0
```
**Expected:**
```
  acked (server seq)   : 200
  received (other node): 158
  LOST                 : 42   (21.0% of acked)
```

✅ **139 lost with no persistence; 42 with AOF.** The group ZSETs survived the
restart, so delivery resumed the instant Redis came back — and the 42 that
remain are the sends that genuinely failed during the three seconds it was down.

**That reframes the whole decision.** Persistence here is not buying you
durability of *messages* (Postgres has those). It is buying you durability of
**state you did not realise you had made Redis authoritative for**.

### The decision for Pulse: two Redises, different settings

```yaml
  redis-fanout:               # channel layer, streams -- transport
    command: >
      redis-server --save "" --appendonly no
                   --maxmemory 4gb --maxmemory-policy noeviction
                   --io-threads 4 --io-threads-do-reads yes
  redis-state:                # presence, unread, rate limits, tickets
    command: >
      redis-server --save "300 100" --appendonly yes --appendfsync everysec
                   --maxmemory 2gb --maxmemory-policy noeviction
```

**And the fan-out Redis keeps `--save ""` even after what you just measured**,
because the correct fix for the group-ZSET problem is Module 07's `LayerGuard` —
repair in 2.3 s — not persistence. Persistence would fix the symptom at the cost
of the worst p99.9 in the table.

> **Argue the other side before you accept this.** Two instances is two things
> to monitor, fail over and reason about. A single AOF instance is ~8% worse at
> p99, 100 ms worse at p99.9, and *much* simpler. If your team is small, take the
> simpler option — and now you know precisely what the 8% and the 100 ms buy.

### Eviction: `noeviction` versus `allkeys-lru`

```bash
r CONFIG SET maxmemory 64mb
r CONFIG SET maxmemory-policy noeviction
k6 run -e ROOMS=1000 -e SEND_EVERY=2000 --vus 20000 --duration 5m \
       ../06-load-testing-harness/code/pulse-load.js
```
**Expected — within about 40 seconds:**
```
WARNING  fanout failed for room.412: OutOfMemoryError("OOM command not allowed
         when used memory > 'maxmemory'.")
```
```
chat_fanout_failed_total 18402.0
     sequence_gaps..................: 4102
```

```bash
r CONFIG SET maxmemory-policy allkeys-lru
# same run
```
**Expected:**
```
(no application log output at all)
```
```
chat_fanout_failed_total 0.0
     sequence_gaps..................: 41884
```
```bash
r INFO stats | grep evicted_keys
```
```
evicted_keys:1284913
```

| | `noeviction` | `allkeys-lru` |
|---|-------------|---------------|
| Error surfaced to the app | ✅ `OOM command not allowed` | ❌ none |
| `chat_fanout_failed_total` | 18,402 | **0** |
| Client-visible sequence gaps | 4,102 | **41,884** |
| `evicted_keys` | 0 | 1,284,913 |
| **Time to detection** | **~12 s** (alert on the counter) | **days** ("messages go missing sometimes") |
| Recovery | add memory, clients retry | **impossible** — the state is gone |

✅ **`noeviction`, unambiguously**, and the reasoning is not "errors are good".
It is that these are the only two options and **one of them is undetectable**.
`allkeys-lru` produced ten times the client-visible damage and zero server-side
evidence, and among the 1.28 million evicted keys were sequence counters, group
memberships and rate-limit buckets — every one of them a correctness surface.

> ⚠️ **A callback you should feel uncomfortable about.** Module 07's `try/except`
> around `group_send` is what turned that OOM error into a counted, non-fatal
> event. That was the right call for a partition — and it means the loud failure
> `noeviction` gives you is only loud **because you kept the counter and alerted
> on it.** Error handling that swallows an exception without a metric converts
> `noeviction` back into `allkeys-lru`. Check yours.

```bash
r CONFIG SET maxmemory 1gb
```

---

## Part H — The Lua script Modules 09 and 18 depend on

Read [`code/append.lua`](./code/append.lua) — the comment block is longer than
the code and that is the correct ratio for a script that runs on a single
thread shared by your whole system.

```bash
SHA=$(docker exec -i pulse-redis redis-cli SCRIPT LOAD "$(cat code/append.lua)")
echo "$SHA"
r EVALSHA "$SHA" 2 'room:{7}:seq' 'room:{7}:stream' \
   10000 '01JQ8Z4K7M8YQ2VBXR3N5TDGWH' alice 'hello' 1735689600123
r EVALSHA "$SHA" 2 'room:{7}:seq' 'room:{7}:stream' \
   10000 '01JQ8Z4K7M8YQ2VBXR3N5TDGWJ' bob 'again' 1735689600456
```
**Expected:**
```
"a3f81c92e4d5f7b1082cc4d9e1f6a70b3c8d5e42"
1) (integer) 1
2) "1735689600123-0"
1) (integer) 2
2) "1735689600456-0"
```

✅ **The `INCR` and the `XADD` happened atomically.** No other client ran between
them. In application code that is a race — two senders both reading `seq = 41` —
and here it is free, because of the single thread you spent Part E cursing.

Confirm what landed:
```bash
r XRANGE 'room:{7}:stream' - + COUNT 1
r GET 'room:{7}:seq'
```
**Expected:**
```
1) 1) "1735689600123-0"
   2) 1) "seq"
      2) "1"
      3) "client_id"
      4) "01JQ8Z4K7M8YQ2VBXR3N5TDGWH"
      5) "sender"
      6) "alice"
      ...
"2"
```

### Now prove the hash tags do something

```bash
r CLUSTER KEYSLOT 'room:{7}:seq'
r CLUSTER KEYSLOT 'room:{7}:stream'
r CLUSTER KEYSLOT 'room:7:seq'
r CLUSTER KEYSLOT 'room:7:stream'
```
**Expected:**
```
(integer) 1716
(integer) 1716         <-- same slot: one node, script is legal
(integer) 12759
(integer) 6286         <-- different slots: CROSSSLOT in Cluster
```

`CLUSTER KEYSLOT` works on a standalone Redis, which makes it the cheapest CI
check in the course:

```bash
# code/check_slots.sh — run it in CI
grep -rhoE "'[a-z:{}<>_.-]*\{[^}]+\}[a-z:_.-]*'" ../apps/pulse/chat/*.py \
  | tr -d "'" | sort -u | while read -r key; do
      echo "$(r CLUSTER KEYSLOT "$key")  $key"
    done | sort -n
```
**Expected — keys that share a tag share a slot:**
```
 1716  room:{7}:seq
 1716  room:{7}:stream
 8000  presence:{42}
 8000  rate:{42}:all
```

Run the same command against a script whose keys are *not* tagged together and
you get two different numbers — which is the failure Module 18 finds in
Module 21's ticket code, five modules after the mistake was made.

> **On a single Redis, none of this matters at all.** That is the entire point.
> Renaming keys in a live system is a dual-write migration; adding braces to keys
> you have not shipped yet costs four characters. **Module 18 turns a rewrite
> into a config change because of the four characters you just typed.**

---

## Part I — The five questions, in one command

```bash
./code/redis_doctor.py
```

**Expected (healthy, under the baseline load):**
```
== 1. the machine's floor ==========================================
  PING round trip   p50 0.108 ms   p99 0.284 ms   max 1.912 ms   mean 0.121 ms

== 2. who owns the single thread ===================================
    total ms  share        calls    us/call  command
       120.4  45.4%      160,096      25.00  bzpopmin
        48.2  18.2%       20,012      40.00  eval
        ...

== 3. what already blocked it ======================================
  slowlog-log-slower-than = 5000 us
  slowlog empty -- either healthy, or the threshold is too high

== 4. memory =======================================================
  used              41.19M
  rss               52.31M
  peak             128.44M   <- size containers on THIS, not on used
  maxmemory          1.00G   policy=noeviction
  fragmentation       1.27   healthy
  MEMORY DOCTOR: Sam, I detected a few issues in this Redis instance memory implants:
   * Peak used memory is more than 150% of current used memory...

== 5. growth bounds ================================================
  pattern                   count   largest   no TTL  bound
  pulse:group:*               100       200        0  group_expiry TTL
  pulsespecific.*               8         3        0  capacity + expiry
  room:*:stream                 1         2        1  XADD MAXLEN ~
  room:*:seq                    1         1        1  one integer
  presence:*                    0         0        0  TTL 45 s
```

Compare `--intrinsic-latency` with the PING figure, because the difference is
Redis's entire contribution:

```bash
docker exec pulse-redis redis-cli --intrinsic-latency 30
```
**Expected:**
```
Max latency so far: 1 microseconds.
Max latency so far: 41 microseconds.
Max latency so far: 412 microseconds.
1948372910 total runs
Worst run took 412x longer than the average latency.
```

```
kernel scheduling floor :  41 us typical, 412 us worst
PING round trip         : 108 us typical
Redis's own contribution: 40 us EVAL + protocol
```

✅ **Redis is responsible for roughly a third of the round trip and none of the
tail.** The 412 µs worst case is the *kernel* failing to reschedule a busy loop
on a laptop — frequency scaling, background processes — and no Redis tuning
touches it. On a dedicated server you would expect under 100 µs; if you see
milliseconds, you have a host problem.

---

## What you measured

Record in `apps/pulse/results-08.md`:

```markdown
## Module 08 — Redis internals
Reference: 8-core/16GB, Redis 7.4.1 (docker), 8 uvicorn workers, RedisChannelLayer

- Intrinsic latency floor        41 us typical / 412 us worst (the KERNEL)
- PING round trip                108 us p50; Redis's own share ~40 us
- Pipelining, loopback           20.2x   (serial 5,428 -> pipelined 109,890 ops/s)
- Pipelining, 1 ms RTT           181x    (467 -> 84,602 ops/s)
- async x32 vs pipeline, 1ms RTT 14,486 vs 84,602 ops/s (5.8x apart)
- Redis work for 40,000 SETs     48 ms   (identical in every mode)
- Lua bulk of 200k ops           1.74 s single-thread stall, chat max 1,764 ms
- Channel-layer command mix      8 BZPOPMIN + 1 EVAL + 1 ZRANGE per group_send
- io-threads 4                   +7.9% knee, usec_per_call unchanged
- Hash encoding cliff            128->129 fields: 2,408 -> 9,528 B, irreversible
- Group ZSET at 200 members      skiplist, 17,240 B -> 1.72 GB at 100k rooms
- listpack at 512 entries        26% slower HGET, 4.7x less memory
- KEYS on 10M keys               3.41 s stall -> chat p99 181 ms -> 3,402 ms, 1.8% dropped
- SCAN equivalent                8.94 s wall clock, chat p99 196 ms (invisible)
- Fork pause at 2.31 GB          271 ms, RSS 2.31 -> 3.94 GB, loop lag 289 ms
- Persistence p99.9              none 712 | RDB 1,940 | AOF 810 ms
- Redis restart loss             none 139/200 | AOF 42/200
- noeviction vs allkeys-lru      4,102 vs 41,884 client gaps; 12 s vs days to detect
- Hash tags                      room:{7}:seq and room:{7}:stream -> slot 1716
```

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| Intrinsic latency (kernel floor) | 41 µs / 412 µs | |
| Pipelining speedup, 1 ms RTT | 181× | |
| Redis work for 40,000 SETs | 48 ms | |
| `BZPOPMIN` per `group_send` | 8 (= worker count) | |
| `io-threads 4` effect on the knee | +7.9% | |
| Hash cliff, 128 → 129 fields | 2,408 → 9,528 B | |
| Group ZSET memory at 100k rooms | 1.72 GB | |
| `KEYS` on 10M keys → chat p99 | 181 ms → 3,402 ms | |
| `SCAN` equivalent → chat p99 | 196 ms | |
| Fork pause / loop lag | 271 ms / 289 ms | |
| Restart loss, no persistence vs AOF | 139/200 vs 42/200 | |
| Client gaps, `noeviction` vs `allkeys-lru` | 4,102 vs 41,884 | |
| `CLUSTER KEYSLOT` of the two tagged keys | identical (1716) | |

---

## What you learned

- **RESP is simple enough to implement in sixty lines**, and RESP3's `>` push
  type is exactly what removes Module 07's two-connections-per-worker
  requirement.
- **Round trips, not Redis, are your cost.** 40,000 SETs is 48 ms of Redis work
  in every mode; the 21-second version was all network. And async concurrency
  gets you most of the way, not all of it.
- **Your channel layer issues 8 `BZPOPMIN` wake-ups per `group_send`**, which is
  Module 07's cost model confirmed from Redis's side of the wire.
- **`io-threads` is worth 7.9% and is not a fix**, and `usec_per_call` is the
  number that proves why.
- **Encoding thresholds create a silent, irreversible memory cliff** — including
  in keys `channels_redis` created for you.
- **One `KEYS` turned a 181 ms p99 into 3.4 seconds for every user** and dropped
  1.8% of connections. `SCAN` did the same work, 2.6× slower, invisibly.
- **Fork pauses are real, invisible to your application, and show up as
  unexplained p99.9 spikes** that correlate with nothing you log.
- **Persistence and eviction are semantic choices**, and the eviction one is
  between a failure you can page on and a failure nobody will ever attribute.
- **Four characters of hash tag today are Module 18's migration.**

Now do [`challenge.md`](./challenge.md).

Then: [Module 09 — Redis Streams & Consumer Groups](../09-redis-streams-delivery/),
which takes Module 07's 29-of-200 loss to zero using the `append.lua` you just
loaded — and charges you +5 ms p50 and roughly 600 bytes per message for it.
