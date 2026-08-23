# Module 00 — Setup & Orientation

**Goal:** Install the toolchain, understand the resource budget, and — most
importantly — learn the **four separate problems** that hide inside the phrase
"build a chat app," so every later module has somewhere to land.

⏱️ ~2 hours · **Prerequisites:** a Mac or Linux machine and a terminal.

---

## Why "build a chat app" is a trick question

Chat looks like the simplest possible product. Two people, some text, a list.
Every framework has a 30-line demo.

Those demos work. They also fall over somewhere between 500 and 5,000 concurrent
users, and the reason isn't that the framework is bad — it's that a real chat
system is **four different distributed-systems problems wearing one UI**.

### Problem 1 — Connection state

HTTP is stateless and short-lived. Chat is stateful and long-lived. A web server
that handles 50,000 requests/second might only hold 2,000 concurrent
connections, because those are completely different resources.

Every connected user costs you:

- A **file descriptor** (kernel resource, hard-limited).
- A **socket buffer** (kernel memory, ~4–64 KB each way).
- **Application state** — who they are, what they're subscribed to, their
  outbound queue.
- Possibly a **thread** — and this is the one that historically killed people.

```
10,000 users × 1 MB platform-thread stack = 10 GB of RAM doing nothing
```

That equation is why this course starts with Java 21 virtual threads (Module 01)
and revisits it with WebFlux (Module 15).

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
Phase 2 exists. It's also why the answer to "can it handle 1000 messages a
second?" is always "how big are the rooms?"

### Problem 3 — Delivery semantics

The network will drop your messages. Clients will disconnect mid-send. Servers
will crash between "wrote to database" and "published to subscribers."

So you must answer, explicitly:

- If a user's phone loses signal for 30 seconds, do they get the messages they
  missed? (**Replay**)
- If the server crashes after saving but before broadcasting, what happens?
  (**Dual-write**)
- If a client retries a send because it didn't see an ack, does the message
  appear twice? (**Idempotency**)
- If a client sees message 41 and 43, does it *know* it missed 42? (**Gap
  detection**)

Most demos answer all four with "we don't." Phase 2 answers them properly.

### Problem 4 — Write amplification in storage

Every message must be durable. Fine. But *how many rows* is one message?

```
Fan-out on read:   1 message = 1 row.        Reads do the work.
Fan-out on write:  1 message = N rows,       Writes do the work.
                   one per recipient inbox.
```

A 1,000-person room with fan-out-on-write is **1,000 inserts** for one typed
sentence. At 100 messages/second that's 100,000 writes/second — which is a
different database than the one you started with. Phase 3.

---

## The four problems, and where this course solves them

| Problem | Naive answer | What you'll build | Module |
|---------|-------------|-------------------|--------|
| Connection state | Thread per connection | Virtual threads, then measure the real ceiling; compare to an event loop | 01, 06, 15 |
| Fan-out | In-memory broker | Redis Streams backbone with consumer groups | 07, 09, 13 |
| Delivery semantics | Hope | Sequence numbers, idempotency keys, resume cursors, an outbox | 05, 10, 13 |
| Write amplification | One giant table | Snowflake IDs, keyset pagination, time partitioning, sharding | 12, 13, 14 |

Keep this table. When you're deep in Module 14 wondering why you're learning
about LSM trees, it's Problem 4.

---

## What you're building: Pulse

`apps/pulse` — a chat backend that, by Module 22, does this:

```
   Next.js client ──ws──┐
   Next.js client ──ws──┤
   Next.js client ──ws──┤
                        ▼
                 ┌─────────────┐
                 │    nginx    │ sticky, WebSocket-aware
                 └──┬───┬───┬──┘
              ┌─────┘   │   └─────┐
         ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐
         │ pulse-1│ │ pulse-2│ │ pulse-3│  Spring Boot + virtual threads
         └────┬───┘ └───┬────┘ └──┬─────┘
              └─────┬───┴─────┬───┘
          ┌─────────▼──┐   ┌──▼────────────┐
          │Redis Cluster│   │   Postgres    │
          │  Streams:   │   │  partitioned  │
          │   fan-out   │   │  + replicas   │
          │  Hashes:    │   │  + PgBouncer  │
          │  presence   │   │  + outbox     │
          └─────────────┘   └───────────────┘
```

Right now it's an empty directory. That's fine.

---

## The toolchain, and why each piece

| Tool | Version | Why this course needs it |
|------|---------|--------------------------|
| **JDK** | 21 LTS | Virtual threads (JEP 444). The entire Phase-1 argument depends on them. 17 will not work. |
| **Maven** | 3.9+ | Build tool. Gradle works too but every command in the labs is Maven. |
| **Docker + Compose v2** | 27+ / v2.29+ | Every data service. Phase 5 runs ~15 containers. |
| **Redis** | 7.x | Streams, sharded Pub/Sub (`SSUBSCRIBE`), and RESP3 are all 7.x features. |
| **Postgres** | 16 | Declarative partitioning improvements, better parallel plans. |
| **k6** | 0.50+ | WebSocket load generation. Go-based, so it holds tens of thousands of sockets on a laptop. |
| **Node** | 20+ | The Next.js client in Module 17. |
| **websocat** | 1.13+ | Talking to your server by hand. Invaluable for understanding frames. |
| **jq** | any | Reading Actuator JSON in the labs. |

### Why not Gradle / why not Java 17 / why not Redis 6?

- **Gradle** is fine. The labs use Maven because the dependency blocks are
  easier to read inline. Translate if you prefer.
- **Java 17** lacks virtual threads. You would have to use a thread pool and the
  course's central benchmark (Module 06 → 15) would be meaningless.
- **Redis 6** lacks `SSUBSCRIBE`/`SPUBLISH` (sharded Pub/Sub), which Module 13
  needs, and has RESP3 only as a preview.

---

## Resource budget — read this before Module 18

The HA modules are the heavy ones. Plan for them now.

| Phase | What's running | RAM |
|-------|---------------|-----|
| 0–1 | postgres, redis, 1 app (on host) | ~1.5 GB |
| 2 | + 2nd app instance, nginx | ~2.5 GB |
| 3 | + replica, pgbouncer | ~3.5 GB |
| 4 | + Kafka (KRaft mode, no ZooKeeper) | ~5 GB |
| 5 Compose HA | 3 redis, 3 sentinel, 3 patroni, 3 etcd, haproxy, 3 app, nginx | ~9 GB |
| 5 Kubernetes | kind with 3 nodes | ~10 GB |

**If you have 8–12 GB:** every heavy module has a **low-memory path** noted at
the top of its lab — usually "run 1 replica instead of 3" or "use `kind` with a
single node." You lose some realism in the failover drills (a 1-node quorum
can't demonstrate split-brain) but every concept still lands. The lab tells you
what you're giving up.

**Reclaim space between phases:**
```bash
docker compose down -v          # in whichever infra dir you last used
docker system prune -a --volumes
```

---

## A note on how to work this course

Three habits that matter more here than in a normal course:

1. **Write down every number.** Module 06 asks for "connections per node."
   Module 15 compares against it. Module 22 needs all of them. Keep a
   `results.md` — the labs will remind you, but start it now.

2. **Do the deliberate-failure steps.** When a lab says "now kill the primary,"
   that step *is* the lesson. Skipping it because you can predict the outcome is
   like skipping the compile because you're sure the code is right.

3. **Read the "why not" sections.** Every module has one. The point of this
   course is that you can defend a design, and you can't defend a choice you
   didn't know you were making.

---

## What's next

The lab installs everything and confirms it works. Then run
[`VERIFY.md`](../VERIFY.md) at the course root — it's the gate before Module 01.

See you in [`lab.md`](./lab.md).
