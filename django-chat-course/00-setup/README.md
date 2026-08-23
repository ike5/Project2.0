# Module 00 — Setup & Orientation

**Goal:** Install the toolchain, understand the resource budget, and — most
importantly — learn the **four separate problems** that hide inside the phrase
"build a chat app," so every later module has somewhere to land.

⏱️ ~2 hours · **Prerequisites:** a Mac or Linux machine and a terminal. You
should be comfortable in Python; you do not need to know Django or asyncio yet.

---

## Why "build a chat app" is a trick question

Chat looks like the simplest possible product. Two people, some text, a list.
Every framework has a 30-line demo, and Django Channels has one that fits on a
slide.

Those demos work. They also fall over somewhere between 500 and 5,000 concurrent
users, and the reason isn't that Django is slow or that Python is the wrong
language — it's that a real chat system is **four different distributed-systems
problems wearing one UI**. You cannot see them in the demo because the demo has
one room, two users, and no failures. Production has ten thousand rooms, a
hundred thousand sockets, a load balancer that closes idle connections, and a
Redis that occasionally pauses for a garbage collection you didn't know it did.

This module names the four problems. The rest of the course breaks each one on
purpose, measures exactly where it breaks on *your* laptop, and then teaches the
primitive that fixes it — and the alternative you rejected.

### Problem 1 — Connection state

HTTP is stateless and short-lived. Chat is stateful and long-lived. A Django app
served by Gunicorn might handle 5,000 requests/second while holding only a few
hundred connections at any instant, because a request arrives, does its work,
and the socket is recycled in milliseconds. Chat inverts that: a socket opens
when the user loads the page and stays open for the entire session — minutes,
hours, a forgotten browser tab for three days.

Every connected user costs you:

- A **file descriptor** (an integer the kernel hands you for each open socket;
  hard-limited per process and system-wide).
- A **socket buffer** (kernel memory, ~4–64 KB each way, tunable).
- **Application state** — who they are, which rooms they've joined, their
  outbound queue of undelivered frames.
- An **asyncio Task** — the Python object that represents their in-flight
  coroutine. This is the piece the whole runtime argument turns on.

Here is the equation that used to kill people, in the thread-per-connection
world Django's `runserver` and WSGI still live in:

```
10,000 users × 8 MB per OS-thread stack (reserved) = 80 GB of address space
                                                      doing nothing
```

Python threads reserve a large stack and cost a real kernel scheduling entity
each. You cannot hold 100,000 of them. The whole of Phase 1 is about *not* doing
that — Module 01 teaches the asyncio event loop, where a connection costs a
~45 KB heap object and a socket buffer instead of a thread, and Module 04 puts
Django Channels on top of it.

> **The JVM twin solves this same problem with virtual threads.** We solve it
> with an event loop plus a process-per-core worker model, and the GIL forces a
> sharper version of every scaling wall. That contrast is the reason to work
> [`spring-boot-chat-course`](../../spring-boot-chat-course/) alongside this one.

### Problem 2 — Fan-out

HTTP is 1 request → 1 response. Chat is **1 message in → N messages out**.

```
A 500-person room, 1 message:
   inbound:  1 message
   outbound: 499 messages         ← 499× amplification

100 such rooms, each with 1 msg/sec:
   inbound:  100 msg/s      (trivial)
   outbound: 49,900 msg/s   (not trivial)
```

Your inbound rate is a lie. **Amplification is the real load**, and it's why
Phase 2 exists. It's also why the answer to "can it handle 1,000 messages a
second?" is always "how big are the rooms?" — the same 1,000 msg/s is a yawn in
2-person DMs and a house fire in 1,000-person announcement channels.

For Python this problem bites *sooner* than on the JVM, and Module 06 measures
exactly how much sooner. Every outbound message is a JSON-encode, a Python
function call, and a write on the event loop, and all of that CPU work runs on
**one core per worker process** because of the GIL. The single-node fan-out
ceiling on the reference machine is ≈150,000 outbound messages/second across 8
worker processes — an honest, expected number that Module 01 explains and
Module 06 makes you reproduce.

### Problem 3 — Delivery semantics

The network will drop your messages. Clients will disconnect mid-send. Servers
will crash between "wrote to Postgres" and "published to Redis."

So you must answer, explicitly:

- If a user's phone loses signal for 30 seconds, do they get the messages they
  missed? (**Replay** / resume-from-cursor.)
- If the server crashes after saving to the database but before broadcasting,
  what happens? (**Dual-write** — the reason the transactional outbox exists.)
- If a client retries a send because it never saw an ack, does the message
  appear twice? (**Idempotency** — client-generated id + server dedup.)
- If a client sees message 41 and 43, does it *know* it missed 42? (**Gap
  detection** — per-room sequence numbers.)

Most demos answer all four with "we don't." Phase 2 answers them properly, and
Module 10 stages the failure — a 2-minute disconnect that loses 98 messages
without resume and 0 with it.

### Problem 4 — Write amplification in storage

Every message must be durable. Fine. But *how many rows* is one message?

```
Fan-out on read:   1 message = 1 row.        Reads do the work.
Fan-out on write:  1 message = N rows,       Writes do the work.
                   one per recipient inbox.
```

A 1,000-person room with fan-out-on-write is **1,000 inserts** for one typed
sentence. At 100 messages/second that's 100,000 writes/second — which is a
different database than the one you started with. And even fan-out-on-read has a
storage problem at volume: the course projects **74 TB/year** at 10,000 msg/s in
Module 12, which is what motivates time partitioning (Module 13) and sharding
(Module 14). Phase 3 is this problem.

---

## The four problems, and where this course solves them

| Problem | Naive answer | What you'll build | Module |
|---------|-------------|-------------------|--------|
| Connection state | Thread per connection (`runserver`) | asyncio event loop, then Channels; measure the real ceiling | 01, 04, 06, 15 |
| Fan-out | InMemoryChannelLayer | Redis channel layer, then a Streams backbone with consumer groups | 07, 09, 13 |
| Delivery semantics | Hope | Sequence numbers, idempotency keys, resume cursors, an outbox | 05, 10, 13 |
| Write amplification | One giant table | Snowflake/UUIDv7 IDs, keyset pagination, time partitioning, sharding | 12, 13, 14 |

Keep this table. When you're deep in Module 14 wondering why you're learning
about LSM trees and wide-column stores, it's Problem 4.

---

## What you're building: Pulse

`apps/pulse` — a Django project (the `pulse` project + a `chat` app) that, by
Module 22, does this:

```
   Next.js client ──ws──┐
   Next.js client ──ws──┤
   Next.js client ──ws──┤
                        ▼
                 ┌─────────────┐
                 │    nginx    │  sticky, WebSocket-aware, drains on deploy
                 └──┬───┬───┬──┘
              ┌─────┘   │   └─────┐
         ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐
         │ pulse-1│ │ pulse-2│ │ pulse-3│  Uvicorn + uvloop, N workers each
         │ (8 wk) │ │ (8 wk) │ │ (8 wk) │  ← one worker process per core
         └────┬───┘ └───┬────┘ └──┬─────┘
              └─────┬───┴─────┬───┘
          ┌─────────▼──┐   ┌──▼────────────┐
          │Redis Cluster│   │   Postgres    │
          │  channel   │   │  partitioned  │
          │  layer +   │   │  + replicas   │
          │  Streams:  │   │  + PgBouncer  │
          │  fan-out   │   │  + outbox     │
          │  Hashes:   │   │  (Celery      │
          │  presence  │   │   relay)      │
          └─────────────┘   └───────────────┘
```

Right now it's an empty directory with a `.gitkeep`. That's fine. **You build
Pulse incrementally in the labs** — the course never hands you a finished
project to run. Module 04 creates it as "an ASGI project with one echo
consumer," and every module after grows it. Reference implementations of the
tricky pieces live in each module's `solutions/`.

---

## The toolchain, and why each piece

| Tool | Version | Why this course needs it |
|------|---------|--------------------------|
| **Python** | 3.12 | Faster interpreter, better `asyncio` internals, per-interpreter GIL groundwork (PEP 684). 3.11+ is required; the labs pin 3.12. |
| **Docker + Compose v2** | 27+ / v2.29+ | Every data service. Phase 5 runs ~15 containers. |
| **Redis** | 7.x | Channel layer, Streams, sharded Pub/Sub (`SSUBSCRIBE`), RESP3 — all 7.x features. |
| **Postgres** | 16 | Declarative partitioning improvements, better parallel plans, the Django ORM's target. |
| **k6** | 0.50+ | WebSocket load generation. Go-based, so it holds tens of thousands of sockets on a laptop. **Primary** load tool. |
| **Locust** | 2.x | Python-native load generation. Slower per socket than k6, but it's *Python* and this audience is Python devs — shown beside k6 in Module 06, honestly, coordinated-omission caveats and all. |
| **Node** | 20+ | The Next.js client in Module 17. |
| **websocat** | 1.13+ | Talking to your server by hand. Invaluable for understanding WebSocket frames in Module 03. |
| **jq** | any | Reading JSON from the health/metrics endpoints in the labs. |

You install all of this in the lab. Two of these choices deserve a "why not"
right now, because they define the shape of the course.

### Why not `pip` + `virtualenv` — why `uv`?

The labs use **`uv`** (the Rust-based Python package manager) for environment and
dependency management, with plain `pip`/`venv` commands shown alongside for
anyone who prefers them. `uv` resolves and installs an entire Django + Channels
+ Celery environment in a second or two instead of thirty, and its lockfile is
reproducible. Nothing in the course *requires* it — every `uv pip install X` has
a `pip install X` equivalent — but you'll appreciate it by the fifth time you
rebuild an environment. If you'd rather use Poetry or PDM, the `pyproject.toml`
the labs generate works with both.

### Why not `runserver` for any of this?

Django's `runserver` is a WSGI development server. **WSGI cannot hold a
WebSocket** — the protocol is synchronous, one-request-one-thread, and has no
concept of a long-lived bidirectional connection. Every realtime thing in this
course runs under **ASGI** (Daphne or Uvicorn), and `runserver` appears only as
the thing we contrast against in Module 02 to make the WSGI/ASGI boundary
concrete. If you have ever seen "WebSocket connection failed" against a Django
app, this is very often why.

---

## Resource budget — read this before Module 18

The HA modules are the heavy ones. Plan for them now.

| Phase | What's running | RAM |
|-------|---------------|-----|
| 0–1 | postgres, redis, 1 app (on host, a few workers) | ~1.5 GB |
| 2 | + 2nd app instance, nginx | ~2.5 GB |
| 3 | + replica, pgbouncer | ~3.5 GB |
| 4 | + Kafka (KRaft mode, no ZooKeeper) | ~5 GB |
| 5 Compose HA | 3 redis, 3 sentinel, 3 patroni, 3 etcd, haproxy, 3 app, nginx | ~9 GB |
| 5 Kubernetes | kind with 3 nodes | ~10 GB |

**If you have 8–12 GB:** every heavy module has a **low-memory path** noted at
the top of its lab — usually "run 1 replica instead of 3," "use `kind` with a
single node," or "run 2 Uvicorn workers instead of 8." You lose some realism in
the failover drills (a 1-node quorum can't demonstrate split-brain) but every
concept still lands. The lab tells you what you're giving up.

**A Python-specific budget note.** The app tier's memory is dominated by two
things the JVM twin doesn't have in the same shape: **one Python interpreter per
worker process** (you run one worker per core, so an 8-core box runs 8 full
interpreters, each ~40–60 MB before it holds a single connection), and **per-
connection Python object overhead** (~45 KB per idle WebSocket, mostly Python
objects, not stacks — there are no per-connection threads in the async model).
Module 01 measures both.

**Reclaim space between phases:**
```bash
docker compose down -v          # in whichever infra dir you last used
docker system prune -a --volumes
```

---

## A note on how to work this course

Three habits that matter more here than in a normal course:

1. **Write down every number.** Module 06 asks for "connections per worker."
   Module 15 compares against it. Module 22 needs all of them. Keep a
   `results.md` — the labs will remind you, but start it in the lab that follows.

2. **Do the deliberate-failure steps.** When a lab says "now `docker pause` the
   Redis," that step *is* the lesson. Skipping it because you can predict the
   outcome is like skipping the test run because you're sure the code is right.
   The pinned failure moments — two workers can't see each other (04), the
   single-node knee (06), 15% message loss on a pause (07), a blocking call
   taking p99 to seconds (15) — are the spine of the course.

3. **Read the "why not" sections.** Every README has one. The entire thesis of
   this course is that you can *defend* a design in an architecture review, and
   you cannot defend a choice you didn't know you were making. "We used Channels"
   is not a defense. "We used Channels over raw ASGI because we needed groups,
   auth, and routing, and Module 15 measured the 12% throughput we paid for
   them" is.

---

## Where this course sits

- [`slack-clone-course`](../../slack-clone-course/) — also Django Channels, but a
  **build-a-Slack product tutorial**: breadth, features, a shipping UI. Go there
  to build a product.
- [`spring-boot-chat-course`](../../spring-boot-chat-course/) — the **same deep-
  architecture arc on the JVM** (Spring Boot, virtual threads, STOMP). Its
  Module 01 solves Problem 1 with virtual threads where we solve it with asyncio;
  its numbers are a running point of comparison.
- **This course** — the deep-architecture arc **on Django/Python**. You'll see
  where the two runtimes converge (Redis is Redis, Postgres is Postgres, the
  four problems are identical) and where they diverge (the GIL forces Redis on
  you *sooner*, and forces a process-per-core model the JVM never needs).

---

## What's next

The lab installs everything, brings up the data tier, and records your machine's
baseline connection limits — the numbers that cap everything before a line of
chat code runs.

See you in [`lab.md`](./lab.md).
