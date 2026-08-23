# Glossary

Plain-English definitions for every term this course uses. Organized by topic,
roughly in the order you meet them.

---

## Real-time transports

**Polling** — The client asks "anything new?" on a timer. Simple, works
everywhere, wastes a request whenever the answer is "no." Latency is bounded
below by the poll interval.

**Long polling** — The client asks "anything new?" and the server *holds the
request open* until there is something to say (or a timeout fires). Latency
approaches real-time, but each message costs a full HTTP request/response cycle
and a held server-side connection.

**SSE (Server-Sent Events)** — A single long-lived HTTP response that the server
streams `data:` lines into. One-directional (server → client), auto-reconnects
with a `Last-Event-ID` header, works over plain HTTP/1.1 and HTTP/2. Great for
feeds; can't carry client → server messages without a second channel.

**WebSocket** — A protocol (RFC 6455) that starts as an HTTP request with
`Upgrade: websocket`, then *stops being HTTP*. After the handshake both sides
send framed binary or text messages in either direction over the same TCP
connection. This is the default transport for chat.

**Upgrade handshake** — The HTTP request/response pair that converts an HTTP
connection into a WebSocket. The client sends `Sec-WebSocket-Key`; the server
returns `Sec-WebSocket-Accept` (a SHA-1 of the key plus a fixed GUID) and status
`101 Switching Protocols`.

**Frame** — The unit of data on a WebSocket connection. Has an opcode (text,
binary, close, ping, pong, continuation), a FIN bit, a mask bit, and a
variable-length payload-length field. See `cheatsheets/websocket-stomp.md` for
the byte layout.

**Masking** — Client → server WebSocket frames must XOR their payload with a
random 4-byte key. This exists to defeat cache-poisoning attacks against
intermediaries that don't understand WebSocket, not for security.

**Ping/pong** — WebSocket control frames used as a liveness check. A peer that
stops answering pings is presumed dead. Distinct from application-level
heartbeats (STOMP has its own).

**SockJS** — A fallback library that emulates a WebSocket API over long polling
or streaming when a real WebSocket can't be established. Historically essential;
now mostly needed only behind hostile corporate proxies.

**WebTransport** — A newer transport over HTTP/3 / QUIC offering multiple
streams and unreliable datagrams on one connection. Avoids head-of-line blocking.
Discussed in Module 03; not yet the default choice for chat.

**Head-of-line blocking** — When one slow or lost item stalls everything behind
it. TCP has it at the packet level (a lost segment stalls the stream); HTTP/1.1
has it at the request level. QUIC is designed to avoid it.

---

## STOMP and Spring messaging

**STOMP (Simple Text Oriented Messaging Protocol)** — A small, frame-based
messaging protocol that runs *on top of* WebSocket. Gives you `CONNECT`,
`SUBSCRIBE`, `SEND`, `MESSAGE`, `ACK`, `RECEIPT`, and destinations — i.e. a
publish/subscribe vocabulary you'd otherwise have to invent yourself.

**Destination** — A STOMP address like `/topic/room.42` or `/user/queue/replies`.
Purely a string convention; the broker decides what it means.

**Simple broker** — Spring's in-memory STOMP broker (`enableSimpleBroker`). It
keeps subscriptions in a `ConcurrentHashMap` inside your JVM. Fast, zero
dependencies, and **completely unaware of your other instances** — which is the
problem Phase 2 exists to solve.

**Relay broker** — Spring forwarding STOMP frames to an external broker
(RabbitMQ, ActiveMQ) over TCP via `enableStompBrokerRelay`. One alternative to
the Redis backplane you build; compared in Module 07.

**`@MessageMapping`** — Routes an inbound STOMP `SEND` frame to a handler method,
the way `@RequestMapping` routes an HTTP request.

**`@SendTo` / `SimpMessagingTemplate`** — Declarative and programmatic ways to
publish a message to a destination. `SimpMessagingTemplate` is what you use from
a background thread or a Redis listener.

**`clientInboundChannel` / `clientOutboundChannel` / `brokerChannel`** — The
three Spring `MessageChannel`s every STOMP frame flows through. Each has its own
thread pool, and each is a place you can add an interceptor — or create a
bottleneck. Tuning these is Module 06 work.

**Simp session** — Spring's per-WebSocket-connection session object, keyed by a
`simpSessionId`. Holds the authenticated principal and subscription registry.

---

## Java concurrency

**Platform thread** — A JVM thread backed 1:1 by an OS thread. Costs ~1 MB of
reserved stack and a kernel scheduling slot. A few thousand is a lot.

**Virtual thread** — A JVM thread scheduled by the JVM onto a small pool of
platform threads (Java 21, JEP 444). Costs a few hundred bytes and grows its
stack on the heap. Millions are feasible. Blocking a virtual thread on I/O
*unmounts* it rather than parking an OS thread.

**Carrier thread** — The platform thread a virtual thread is currently mounted
on. A virtual thread that blocks on I/O releases its carrier; one that blocks in
`synchronized` or a native call may **pin** it.

**Pinning** — When a virtual thread cannot unmount from its carrier, usually
because it's inside a `synchronized` block or a native frame. Pinned threads
reintroduce the platform-thread ceiling. Use `ReentrantLock` instead. (Java 24+
removes most `synchronized` pinning; Module 01 covers both worlds.)

**Structured concurrency** — Treating a group of concurrent subtasks as a single
unit with a scope, so failures and cancellation propagate predictably
(`StructuredTaskScope`). Prevents leaked threads in fan-out code.

**Event loop** — A single thread (or a small set) running a loop that reacts to
I/O readiness events and never blocks. Netty's model. Extremely efficient; the
cost is that *anything* you block on inside it stalls every connection that
thread owns.

**Backpressure** — A consumer's ability to tell a producer "slow down." Central
to Reactor and WebFlux; absent from naive callback code, where the failure mode
is an unbounded queue and then an OOM.

**C10K / C10M** — Shorthand for "ten thousand / ten million concurrent
connections on one box." Names the class of problem, not a specific number.

**JMM (Java Memory Model)** — The rules governing when one thread's writes become
visible to another. Underpins `volatile`, `synchronized`, and the concurrent
collections you use for connection registries.

---

## Redis

**RESP (REdis Serialization Protocol)** — Redis's wire format. RESP2 is
type-tagged text; RESP3 adds native map/set/push types and is what makes
client-side caching and better Pub/Sub multiplexing possible.

**Single-threaded event loop** — Redis executes commands one at a time on one
thread. This is *why* its operations are atomic without locks, and why one slow
command (`KEYS *`, a big `LRANGE`) stalls every other client.

**I/O threads** — Redis 6+ can parallelize *socket reads and writes* across
threads while still executing commands on one thread. Command execution remains
serial.

**Pub/Sub** — Redis's fire-and-forget broadcast. `PUBLISH` delivers to whoever is
subscribed *right now*. No persistence, no acknowledgement, no replay:
**at-most-once**. A subscriber that was reconnecting simply misses the message.

**Sharded Pub/Sub** — `SPUBLISH`/`SSUBSCRIBE` (Redis 7+), which route by hash
slot so a message doesn't have to be broadcast to every node in a cluster.
Essential for Pub/Sub on Redis Cluster at scale.

**Stream** — An append-only log data type with unique, monotonically increasing
IDs (`<ms>-<seq>`). Persistent, replayable, and trimmable. The durable
alternative to Pub/Sub.

**Consumer group** — A named set of consumers cooperatively reading one stream,
where each entry is delivered to exactly one member and must be acknowledged.
Gives you **at-least-once** delivery and work distribution.

**PEL (Pending Entries List)** — Per-consumer-group bookkeeping of entries that
were delivered but not yet `XACK`ed. This is the state that lets a crashed
consumer's work be reclaimed by another (`XAUTOCLAIM`).

**`MAXLEN` / `MINID` trimming** — How you stop a stream from growing forever.
`~` makes trimming approximate (and much cheaper) by only trimming whole macro
nodes.

**Keyspace notifications** — Redis events published when keys change or expire.
Tempting for presence ("tell me when the TTL expires"); unreliable in practice
because they're delivered over Pub/Sub (at-most-once). Module 11 covers why.

**Redlock** — A distributed-locking algorithm using multiple independent Redis
nodes. Contested in the literature; Module 11 presents both sides and when a lock
is the wrong tool entirely.

**Sentinel** — Redis's HA supervisor: a quorum of processes that monitor a
primary, agree it's down, elect a replica, and tell clients about the new
address. Failover for a *single* logical dataset.

**Redis Cluster** — Redis's sharding mode. 16384 hash slots distributed across
primaries, each with replicas. Clients are redirected (`MOVED`/`ASK`) to the
right node. Sharding *and* HA, at the cost of multi-key operation constraints.

**Hash tag** — The `{...}` part of a key name. `user:{42}:inbox` and
`user:{42}:seq` hash to the same slot, so multi-key commands and Lua scripts
work across them.

**Hot key** — A single key receiving disproportionate traffic (e.g. the
`#general` room in a big org). Cluster sharding does not help, because one key
lives on exactly one node. Module 13's challenge attacks this.

---

## Delivery semantics

**At-most-once** — Every message is delivered zero or one times. Never
duplicated, sometimes lost. Redis Pub/Sub. Fine for typing indicators.

**At-least-once** — Every message is delivered one or more times. Never lost,
sometimes duplicated. Redis Streams with `XACK`, Kafka with committed offsets.
The realistic target for chat — paired with client-side dedup.

**Exactly-once** — Delivered precisely once. Not achievable end-to-end across an
unreliable network in the general case; what systems actually sell is
at-least-once delivery plus **idempotent processing**, which is
observationally equivalent. Module 09 explains the sleight of hand.

**Idempotency key** — A client-generated unique ID attached to a message so the
server can recognize and discard a retry. The single most valuable line in your
protocol.

**Deduplication window** — How long you remember idempotency keys. Bounded
memory forces a bounded window; picking it is a real design decision.

**Sequence number** — A per-room (or per-user-inbox) monotonically increasing
counter. Lets a client detect a *gap* — "I have 41 and 43, I'm missing 42" —
which is the only way to know you lost something.

**Cursor / resume token** — What a reconnecting client sends to say "give me
everything after this point." Turns a reconnect from a data-loss event into a
catch-up.

**Fan-out on write** — When a message arrives, immediately write a copy into
every recipient's inbox. Reads are trivial; writes multiply by room size.

**Fan-out on read** — Store the message once; assemble each user's view at read
time. Writes are cheap; reads do work. Most large chat systems use a hybrid,
switching strategy above a room-size threshold.

**Write amplification** — One logical event causing many physical writes. A
1,000-member room with fan-out-on-write is 1,000× amplification. The number that
decides your storage architecture.

**Thundering herd** — Everyone reconnecting or re-subscribing at once (after a
deploy, a network blip, or a failover), overwhelming the thing that just came
back. Fixed with jittered backoff.

---

## Postgres and data modelling

**Snowflake ID** — A 64-bit ID built from a timestamp, a machine ID, and a
per-millisecond sequence. Sortable by time, generated without coordination, and
half the size of a UUID. Twitter's design; Discord's too.

**UUIDv7** — A UUID whose leading bits are a Unix timestamp, making it
time-sortable (unlike UUIDv4). 128 bits. The standards-blessed alternative to
Snowflake.

**Index locality** — Whether logically adjacent rows are physically adjacent in
the index. Random IDs (UUIDv4) destroy it, causing page splits and write
amplification. Time-sortable IDs preserve it.

**Keyset pagination** — Paginating with `WHERE id < :cursor ORDER BY id DESC
LIMIT n` instead of `OFFSET`. Constant-time regardless of how deep you scroll;
`OFFSET 100000` is not.

**Declarative partitioning** — Splitting one logical Postgres table into physical
child tables by a key (usually time, for chat). Lets you drop old data with
`DROP TABLE` instead of a `DELETE` that generates gigabytes of WAL.

**Partition pruning** — The planner skipping partitions that can't match the
query. What makes partitioning a read win as well as a maintenance win.

**WAL (Write-Ahead Log)** — Postgres's durability journal. Every change is
written here before the data files. It's also the replication stream and the CDC
source.

**Streaming replication** — A replica connecting to a primary and continuously
applying its WAL. The basis of read replicas and HA failover.

**Replica lag** — How far behind a replica is. The reason "I sent a message and
then couldn't see it" bugs exist when you read from replicas naively.

**Read-your-writes** — The consistency guarantee that a client sees its own
writes immediately. Requires routing that user's reads to the primary (or
waiting on an LSN) for a window after a write.

**Connection pooling / PgBouncer** — Postgres forks a process per connection, so
thousands of app connections will kill it. PgBouncer multiplexes many client
connections onto few server ones. Transaction pooling mode is the useful one, and
it breaks session-level features — Module 13 covers which.

**Transactional outbox** — Writing the message row *and* an "to be published"
row in the same database transaction, then having a separate relay publish it.
Solves the dual-write problem: you can never persist without publishing or
publish without persisting.

**Dual-write problem** — Writing to two systems (DB and broker) without a shared
transaction, so a crash between them leaves them inconsistent.

**CDC (Change Data Capture)** — Reading the WAL (via logical decoding, e.g.
Debezium) to publish changes downstream. An outbox alternative with different
operational tradeoffs.

**Sharding** — Splitting data across independent databases by a key (room ID,
user ID). Scales writes past one machine at the cost of cross-shard queries and
painful resharding.

**Consistent hashing** — A key→node mapping that only remaps `1/n` of keys when
a node is added, instead of remapping everything. What makes resharding
survivable.

**Wide-column store** — Cassandra/ScyllaDB's model: a partition key selects a
node, clustering keys order rows within the partition. Optimized for "give me
the last N rows of this partition" — which is precisely a chat scrollback query.

**LSM tree** — The write-optimized storage structure behind Cassandra, ScyllaDB,
and RocksDB. Buffers writes in memory and flushes sorted files, trading read
amplification and compaction work for very fast writes. Contrast Postgres's
B-tree + heap.

**Tombstone** — A deletion marker in an LSM store. Accumulating tombstones in a
partition make reads progressively slower; a classic Cassandra footgun.

---

## Kafka

**Topic / partition** — A topic is a named log; it's split into partitions, each
an ordered, append-only sequence. Partitions are the unit of parallelism *and*
the unit of ordering.

**Ordering guarantee** — Kafka guarantees order **within a partition only**.
Messages with the same key go to the same partition, which is how you get
per-room ordering.

**Offset** — A consumer's position in a partition. Committing it is what makes
progress durable — and *when* you commit determines at-least-once vs
at-most-once.

**Consumer group / rebalance** — Consumers sharing a group split the partitions.
When membership changes, partitions are reassigned — a *rebalance*, during which
consumption stalls. A real operational cost.

**Log compaction** — Retention that keeps only the latest value per key.
Useful for state-like topics (user profile, room settings); wrong for a message
log.

**ISR (In-Sync Replicas)** — The replicas caught up with the leader.
`acks=all` + `min.insync.replicas` is how you trade throughput for durability.

---

## High availability and infra

**High availability (HA)** — A system that continues serving when a component
fails. Measured in how much you lose and for how long, not as a binary.

**RTO / RPO** — *Recovery Time Objective*: how long you're down. *Recovery Point
Objective*: how much data you lose. Every HA design is a point on this plane.

**Failover** — Promoting a replica to primary when the primary dies. Automatic
failover needs a quorum to decide, or you get split-brain.

**Split-brain** — Two nodes both believing they're primary, both accepting
writes. The failure mode quorums exist to prevent.

**Quorum** — A majority (`n/2 + 1`) required to make a decision. Why HA clusters
have odd member counts.

**Fencing / STONITH** — Forcibly ensuring a demoted primary can't accept writes,
by killing it or revoking its network access.

**Patroni** — A supervisor for Postgres HA that stores cluster state in a
distributed config store (etcd/Consul) and handles election, promotion, and
reconfiguration.

**HAProxy** — A TCP/HTTP load balancer. In this course it fronts Postgres,
routing writes to whichever node currently answers "I am the primary."

**Sticky session / session affinity** — A load balancer sending one client
consistently to one backend. Necessary for stateful WebSocket connections; also
the thing that makes rolling deploys drop sockets.

**Draining / graceful shutdown** — Telling a node to stop accepting new
connections and let existing ones finish before it dies. The difference between
a deploy nobody notices and one that logs everybody out.

**Healthcheck (liveness vs readiness)** — *Liveness*: "should I be restarted?"
*Readiness*: "should I get traffic?" Conflating them causes restart storms.

**StatefulSet** — The Kubernetes controller for pods with stable identities and
per-pod storage. What you run Redis and Postgres under.

**PodDisruptionBudget (PDB)** — A rule limiting how many pods of a set may be
voluntarily down at once, so a node drain can't take out your whole quorum.

**Topology spread constraints** — Rules that spread pods across nodes/zones so a
single failure domain can't take out every replica.

**Chaos engineering** — Deliberately injecting failures into a running system to
verify it behaves as designed. Module 18 is an extended chaos drill.

---

## Observability

**RED metrics** — Rate, Errors, Duration. The service-level golden signals.

**USE metrics** — Utilization, Saturation, Errors. The resource-level view;
saturation (queue depth) is the one people forget and the one that predicts
outages.

**Cardinality** — The number of distinct label combinations on a metric. Putting
a user ID in a Prometheus label is how you take down your monitoring.

**Histogram vs summary** — Histograms bucket observations and can be aggregated
across instances; summaries compute quantiles locally and **cannot** be
meaningfully averaged. Use histograms.

**p99 / tail latency** — The 99th percentile. In a fan-out system, a user's
experience is the *max* over many operations, so tail latency dominates.

**Span / trace / context propagation** — A trace is a request's journey; spans
are its segments. Propagating trace context across a Redis Stream or a thread
pool is manual work — Module 20's core exercise.

**SLI / SLO / error budget** — The *indicator* you measure, the *objective* you
promise, and the amount of failure you're allowed before you stop shipping
features.

---

## Security and abuse

**Origin check** — Validating the `Origin` header on the WebSocket handshake.
Browsers don't apply CORS to WebSocket, so without this any site can open a
socket to your server with the user's cookies.

**CSWSH (Cross-Site WebSocket Hijacking)** — The attack the origin check
prevents: a malicious page opening an authenticated WebSocket to your server.

**Token rotation on a long-lived socket** — A JWT expires; a socket open for
eight hours does not. You need an in-band re-authentication message, or a socket
that outlives its own authorization.

**Token bucket** — A rate-limiting algorithm: tokens refill at a fixed rate up to
a cap, each action costs one. Allows bursts while bounding sustained rate.
Implemented atomically in Lua in Module 11.

**Backpressure vs rate limiting** — Backpressure slows a producer you control;
rate limiting rejects one you don't. Chat needs both, in different places.

**E2EE (End-to-End Encryption)** — Encrypting so the server can't read messages.
Costs you server-side search, moderation, and push notification previews — the
tradeoff discussed honestly in Module 21.
