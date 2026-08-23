# apps/ — the code you build across the course

Two applications grow here as you work the modules. **They are built
incrementally in the labs** — this directory starts nearly empty on purpose, the
same way a real project starts as an empty repo.

## `pulse/` — the Spring Boot backend

The service you build from Module 02 onward. By the capstone it is a
horizontally-scaled, HA, observable chat backbone.

| Milestone | Module | State of `pulse/` |
|-----------|--------|-------------------|
| Generated skeleton | 02 | `start.spring.io` project, virtual threads on, Actuator wired |
| Working chat | 04 | STOMP, rooms, presence, one node |
| Protocol | 05 | Envelope, Snowflake IDs, idempotent send, ack ladder |
| Measured | 06 | Metrics, the k6/Gatling harness (`../../06-*/code/`) |
| Scaled out | 07–11 | Redis backplane → Streams → resume → presence/rate-limit |
| Durable | 12–14 | Partitioned, sharded Postgres store + outbox |
| Alternatives | 15–16 | (a sibling `pulse-reactive/` in Module 15; Kafka profile in 16) |
| HA | 18–19 | Runs under the HA Compose / k8s stacks |
| Observable | 20 | Tracing, SLOs |
| Secured | 21 | JWT + ticket auth, revocation, abuse defense |
| Capstone | 22 | Everything, under the `capstone` profile |

Generate the skeleton with the exact command in
[`02-spring-fast-track/lab.md`](../02-spring-fast-track/lab.md) Part A.

## `pulse-web/` — the Next.js client

Built in Module 17. Virtualized message list, optimistic send with `clientId`
reconciliation, offline outbox, jittered reconnect, and a `SharedWorker` holding
one socket across tabs. Scaffold it with the command in
[`17-nextjs-realtime-client/lab.md`](../17-nextjs-realtime-client/lab.md) Part A.

## Why the code isn't pre-written here

This course's pedagogy (see [`../PEDAGOGY.md`](../../PEDAGOGY.md)) is *learn by
doing* — 80% hands-on-keys. Every file that belongs in these apps is written,
with full context, in a lab. Pre-populating them would turn "build it" into
"read it," which is the opposite of the point.

Reference implementations of the tricky pieces live in each module's
`solutions/`. When you're stuck, that's where to look — after you've tried.
