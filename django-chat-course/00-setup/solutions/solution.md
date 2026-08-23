# Solutions — Module 00

Reference numbers are from the course's reference machine: **8-core / 16 GB,
Ubuntu 24.04, Python 3.12**. Yours will differ; the *shapes* and *ratios* are
what matter.

---

## Task 1 — The hard connection ceiling

Three limits, in the order they typically bind:

```bash
ulimit -n                                          # 1024   ← process FD limit
cat /proc/sys/fs/file-max                          # 9223372036854775807  ← system FD
cat /proc/sys/net/ipv4/ip_local_port_range         # 32768  60999  ← ephemeral ports
```

**Which binds first: the process FD limit (1024).** It's tiny, per-process, and
the default on almost every Linux and macOS. It's the reason a server "stops at
~1016 clients" — the missing 8 descriptors are stdin/stdout/stderr, the listening
socket, and a few open files (logs, the Redis and Postgres connections).

Raise it with `ulimit -n 100000` (this shell only) or, persistently, in
`/etc/security/limits.conf` and the systemd unit's `LimitNOFILE`. Module 06 does
this properly, including inside containers (`ulimits:` in compose).

**Why the ephemeral port range is a *client* limit.** A server socket is
identified by the 4-tuple `(server_ip, server_port, client_ip, client_port)`.
The server reuses **one** listening port (say 8000) for every connection —
80,000 clients all connect to `:8000`, and the tuples differ only in the client
half. So the server is bounded by file descriptors and memory, not ports.

The **client**, connecting repeatedly to one `(server_ip, 8000)`, must pick a
distinct local ephemeral port for each connection. With ~28,000 ephemeral ports,
one client machine caps at ~28,000 connections *to a single destination*. This
is why your k6 load generator plateaus at ~28k and your server looks innocent —
the fix is more source IPs or more load boxes (Module 06), not a bigger server.

```
results.md
- Process FD limit (ulimit -n): 1024  ← binds first
- System FD limit: 9223372036854775807 (effectively unlimited)
- Ephemeral port range: 32768-60999 (~28k) — limits the LOAD GENERATOR
```

---

## Task 2 — Per-Task vs per-thread cost

This is the whole of Module 01 in two scripts. The point: an asyncio Task is a
heap object; an OS thread is a kernel scheduling entity with a reserved stack.
They are not the same order of magnitude of cost.

### `tasks.py`

```python
import asyncio, resource, sys, time

async def worker(barrier):
    await barrier.wait()
    await asyncio.sleep(30)

async def main(n):
    barrier = asyncio.Barrier(n + 1)
    t0 = time.perf_counter()
    tasks = [asyncio.create_task(worker(barrier)) for _ in range(n)]
    # let them all reach the sleep, then snapshot memory
    await barrier.wait()
    await asyncio.sleep(0.5)
    rss = rss_kb()
    print(f"{n:>9,} tasks | RSS {rss:>9,} KB | {rss*1024/n:6.0f} bytes/task | "
          f"created in {time.perf_counter()-t0:.2f}s")
    for t in tasks:
        t.cancel()

def rss_kb():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r // 1024 if sys.platform == "darwin" else r

asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000))
```

```bash
python tasks.py 10000
python tasks.py 1000000
```

**Expected:**
```
   10,000 tasks | RSS    58,120 KB |   5951 bytes/task | created in 0.05s
1,000,000 tasks | RSS 1,447,880 KB |   1483 bytes/task | created in 2.31s
```

A **million** concurrent tasks in ~1.4 GB, created in ~2 seconds. Per-task cost
*falls* with scale (fixed interpreter overhead amortizes): ~1.5 KB per task at a
million. There is no OS involvement per task — the event loop schedules them all
on one thread.

### `threads.py`

```python
import threading, resource, sys, time

def worker(ev):
    ev.wait()
    time.sleep(30)

def main(n):
    ev = threading.Event()
    t0 = time.perf_counter()
    threads = []
    try:
        for _ in range(n):
            t = threading.Thread(target=worker, args=(ev,))
            t.start()
            threads.append(t)
    except RuntimeError as e:
        print(f"FAILED at {len(threads):,} threads: {e}")
        ev.set()
        return
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = r // 1024 if sys.platform == "darwin" else r
    print(f"{n:>9,} threads | RSS {rss:>9,} KB | {rss*1024/n:7.0f} bytes/thread | "
          f"created in {time.perf_counter()-t0:.2f}s")
    ev.set()

main(int(sys.argv[1]) if len(sys.argv) > 1 else 10000)
```

```bash
python threads.py 10000
python threads.py 1000000
```

**Expected:**
```
   10,000 threads | RSS   803,240 KB |   82252 bytes/thread | created in 3.74s
FAILED at 32,001 threads: can't start new thread
```

✅ **Read the ratio.** 10,000 OS threads cost ~800 MB — *more than a million
asyncio Tasks* — and take 70× longer to create (each `start()` is a `clone()`
syscall and fights the GIL during startup). The thread version then dies at
**~32,000** with `RuntimeError: can't start new thread`, which is `pthread_create`
returning `EAGAIN` against `ulimit -u` / `threads-max` / `vm.max_map_count`.

**How the Python failure differs from the JVM's.** On the JVM twin the platform-
thread version throws `OutOfMemoryError: unable to create native thread` at a
similar count. Same kernel wall, different exception. The deeper difference is
what you *do about it*: the JVM's answer is virtual threads (keep the blocking
code, make threads cheap). Python has no virtual threads, so its answer is the
event loop — you stop writing thread-per-connection code entirely and write
coroutines instead. Module 01 is that pivot.

```
results.md
- asyncio Tasks: 1,000,000 in 1.4 GB (no failure), ~1.5 KB/task
- OS threads: died at ~32,000 (RuntimeError: can't start new thread)
- 10k threads (800 MB) cost MORE than 1M tasks (1.4 GB) — and 70x slower to create
```

---

## Task 3 — Docker overhead

```bash
docker compose -f infra/compose.dev.yml up -d
sleep 300
docker stats --no-stream
```

**Expected:**
```
CONTAINER        MEM USAGE / LIMIT
pulse-postgres   34.2MiB / 15.29GiB
pulse-redis      8.6MiB / 15.29GiB
```

~43 MB combined, idle. That's your floor — Postgres with a warmed-up but empty
schema sits around 30–40 MB, Redis around 8–10 MB with an empty keyspace. Note
this grows: by Phase 5 the data tier alone is several GB.

```
results.md
- Idle container RSS: postgres ~34 MB, redis ~9 MB
```

---

## Task 4 — Fan-out amplification

**Rooms of 50 members**, 10,000 users, 1 msg / 5 min / user:

```
inbound  = 10,000 users / 300 s              = 33.3 msg/s
outbound = 33.3 msg/s × 50 recipients        = 1,667 msg/s
amplification = outbound / inbound = 50×  (= room size)
```

**Rooms of 500 members**, everything else identical:

```
inbound  = 10,000 users / 300 s              = 33.3 msg/s   ← IDENTICAL
outbound = 33.3 msg/s × 500 recipients       = 16,667 msg/s
amplification = 500×
```

**The one-sentence explanation:** inbound depends only on how many people are
*typing* (unchanged), while outbound depends on how many people are *listening
per message* (the room size), so the same modest inbound load becomes a 10×
larger outbound load purely by making rooms bigger — which is why "how many
messages per second?" is unanswerable without "how big are the rooms?"

This is exactly why the course spends Phase 2 on the fan-out backbone. The
inbound number never scares anyone; the outbound number is what hockey-sticks
your p99. On Python this arrives sooner than on the JVM because each outbound
message is a JSON encode plus a Python-level write, all on one core per worker —
the reference single-node ceiling is ≈150,000 outbound msg/s (Module 06),
roughly a third of the JVM twin's, and Module 01 explains why.

```
results.md
- 50-member rooms:  inbound 33/s, outbound 1,667/s, amp 50x
- 500-member rooms: inbound 33/s (SAME), outbound 16,667/s, amp 500x
```

---

## Task 5 (stretch) — The true cost of an idle socket

### `idle_server.py`

```python
import asyncio, resource, sys, signal

held = []

async def handle(reader, writer):
    held.append((reader, writer))          # keep it open, do nothing

async def main():
    server = await asyncio.start_server(handle, "127.0.0.1", 9300)
    def report(*_):
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss = r // 1024 if sys.platform == "darwin" else r
        n = max(len(held), 1)
        print(f"\nserver: {len(held):,} sockets | RSS {rss:,} KB | "
              f"{rss*1024/n:.0f} bytes/conn (server side)")
    signal.signal(signal.SIGINT, report)
    async with server:
        await server.serve_forever()

asyncio.run(main())
```

### `idle_client.py`

```python
import asyncio, resource, sys

async def main(n):
    conns = []
    for _ in range(n):
        r, w = await asyncio.open_connection("127.0.0.1", 9300)
        conns.append((r, w))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = rss // 1024 if sys.platform == "darwin" else rss
    print(f"client: {n:,} sockets | RSS {rss:,} KB | {rss*1024/n:.0f} bytes/conn")
    await asyncio.sleep(3600)              # hold them so you can read the server

asyncio.run(main(10000))
```

```bash
ulimit -n 100000
python idle_server.py &          # then, in the client, after it connects, Ctrl-C the server to print
python idle_client.py
```

**Expected:**
```
client: 10,000 sockets | RSS 78,120 KB | 8,000 bytes/conn
server: 10,000 sockets | RSS 71,440 KB | 7,317 bytes/conn (server side)
```

✅ ~7–8 KB per idle socket on **each** side, for a socket that does *nothing* —
no protocol, no Django, no consumer object, no application state. That's a Python
`StreamReader`/`StreamWriter` pair, a transport, an entry in the event loop's
selector, and the kernel's socket buffers.

**Why this matters for the whole course.** This ~7 KB is the *floor*. Module 01
measures a real Django Channels WebSocket consumer and finds ~45 KB — the extra
~38 KB is the consumer instance, the channel-layer group subscription, the JSON
codec state, and the per-connection Python object graph. Multiply by your target:
40,000 connections/worker × 45 KB ≈ 1.8 GB, which is why the pinned "~40,000
connections per worker before memory pressure" number is what it is. You now
know where every kilobyte of a connected user comes from, and you measured it
instead of trusting a blog post.

```
results.md
- Idle socket floor: ~7-8 KB/conn each side (asyncio, no app)
- (Module 01 will add Channels overhead → ~45 KB/conn total, server side)
```
