# Glossary

Plain-English definitions for every term this course uses. Organized by topic,
roughly in the order you meet them. Where the answer differs from the JVM twin
([`spring-boot-chat-course`](../spring-boot-chat-course/)), the difference is
called out — the runtime shifts the numbers more often than the shape.

---

## Real-time transports

**Polling** — The client asks "anything new?" on a timer. Simple, works
everywhere, wastes a request whenever the answer is "no." Latency is bounded
below by the poll interval.

**Long polling** — The client asks "anything new?" and the server *holds the
request open* until there is something to say (or a timeout fires). Latency
approaches real-time, but each message costs a full HTTP request/response cycle
and a held server-side connection — which under ASGI means a held coroutine.

**SSE (Server-Sent Events)** — A single long-lived HTTP response that the server
streams `data:` lines into. One-directional (server → client), auto-reconnects
with a `Last-Event-ID` header (which is a resume cursor you get for free), works
over plain HTTP/1.1 and HTTP/2. Great for feeds; can't carry client → server
messages without a second channel. Django can serve it from an async view
yielding from a `StreamingHttpResponse`.

**WebSocket** — A protocol (RFC 6455) that starts as an HTTP request with
`Upgrade: websocket`, then *stops being HTTP*. After the handshake both sides
send framed binary or text messages in either direction over the same TCP
connection. This is the default transport for chat, and the one Django Channels
speaks.

**Upgrade handshake** — The HTTP request/response pair that converts an HTTP
connection into a WebSocket. The client sends `Sec-WebSocket-Key`; the server
returns `Sec-WebSocket-Accept` (a SHA-1 of the key plus a fixed GUID) and status
`101 Switching Protocols`. In Channels this is the `websocket.connect` event your
consumer's `connect()` handles.

**Frame** — The unit of data on a WebSocket connection. Has an opcode (text,
binary, close, ping, pong, continuation), a FIN bit, a mask bit, and a
variable-length payload-length field. See
[`cheatsheets/websocket-channels.md`](./cheatsheets/websocket-channels.md) for
the byte layout.

**Masking** — Client → server WebSocket frames must XOR their payload with a
random 4-byte key. This exists to defeat cache-poisoning attacks against
intermediaries that don't understand WebSocket, not for security.

**Ping/pong** — WebSocket control frames used as a liveness check. A peer that
stops answering pings is presumed dead. Distinct from application-level
heartbeats (which you design yourself in Module 05, since there's no STOMP to
provide them).

**WebTransport** — A newer transport over HTTP/3 / QUIC offering multiple streams
and unreliable datagrams on one connection. Avoids head-of-line blocking.
Discussed in Module 03; not yet the default choice for chat, and not yet a
first-class Channels citizen.

**Head-of-line blocking** — When one slow or lost item stalls everything behind
it. TCP has it at the packet level (a lost segment stalls the stream); HTTP/1.1
has it at the request level. QUIC is designed to avoid it.

---

## WebSocket, Channels & ASGI

**ASGI (Asynchronous Server Gateway Interface)** — The async successor to WSGI.
Where WSGI is `def app(environ, start_response)` and handles one blocking request
per call, ASGI is `async def app(scope, receive, send)` and can handle
long-lived, bidirectional, event-driven connections — which is what a WebSocket
needs. Channels, Daphne, and Uvicorn all speak ASGI.

**WSGI** — The old synchronous Python web interface (what `runserver` and
gunicorn's default worker use). One request, one thread, blocking I/O, and *no
concept of a connection that outlives a request* — so it cannot serve WebSocket
at all. This course uses WSGI only as a contrast in Module 02.

**Scope** — The ASGI dictionary describing a single connection: its `type`
(`http`, `websocket`), path, headers, client address, and (after middleware) the
authenticated user. It is created once per connection and lives as long as the
connection. In Channels, `self.scope` is where your consumer finds the user, the
URL route kwargs, and the session.

**Consumer** — The Channels analog of a Django view, but for a whole connection
rather than one request. A class with `async def connect()`, `receive()` /
`receive_json()`, and `disconnect()` methods (plus custom handlers for events off
the channel layer). One consumer *instance* handles one connection for its whole
lifetime.

**`AsyncJsonWebsocketConsumer`** — The Channels base class this course builds on:
an async consumer that JSON-encodes/decodes for you, so you implement
`receive_json(content)` and call `self.send_json(...)`. The JSON envelope you
design in Module 05 *is* your wire protocol — there is no STOMP layer.

**Channel** — A named mailbox (a string) that a message can be sent to. Every
consumer instance gets a unique auto-generated channel name (`self.channel_name`)
so other parts of the system can address it directly. Do not confuse a *channel*
(this mailbox) with a *WebSocket* (the client connection) or a *Redis Pub/Sub
channel* (a backplane detail).

**Group** — A named set of channels. `group_add("room.7", self.channel_name)`
subscribes this connection; `group_send("room.7", event)` delivers to every
channel currently in the group. Groups are how a message reaches every member of
a room. The group registry lives in the **channel layer**.

**Channel layer** — The pluggable backend that moves messages between channels
and groups, *possibly across processes and machines*. `InMemoryChannelLayer`
keeps it in one process's memory (dev only); `RedisChannelLayer` (from
`channels_redis`) uses Redis Pub/Sub so any worker can reach any other. This is
the single most important abstraction in the course — Phase 2 is about what backs
it.

**`InMemoryChannelLayer`** — The default, dev-only channel layer. Fast, zero
dependencies, and **scoped to one Python process** — it cannot deliver a message
from one worker process to another *even on the same machine*. Module 04 proves
this, and it is a sharper wall than the JVM twin's simple broker (which at least
spans threads within one JVM).

**`RedisChannelLayer`** — The `channels_redis` channel layer, backed by Redis
**Pub/Sub**. Lets any worker deliver to any group member on any node. Its
delivery is **at-most-once** — a subscriber that was reconnecting misses the
message — which is exactly the loss you measure and then fix in Modules 07–09.

**Daphne** — The reference ASGI server from the Channels project. Pure-Python,
stable, HTTP + WebSocket. What you start on; fine for learning, out-benchmarked by
Uvicorn+uvloop for raw throughput.

**Uvicorn** — A fast ASGI server built on `uvloop` and `httptools`. Run with
`--workers N` it forks N worker *processes* (one per core is the rule), each with
its own event loop. The production ASGI server for most of this course.

**uvloop** — A drop-in event-loop policy built on libuv (the same C library
Node.js uses), replacing asyncio's pure-Python loop. Typically 2–4× faster for
socket-heavy workloads. You measure the difference in Module 01.

**Granian** — A newer Rust-based ASGI/WSGI/RSGI server. Mentioned as an
alternative and benchmarked in Module 15.

**`database_sync_to_async`** — The Channels helper that runs a **synchronous**
Django ORM call in a threadpool so it doesn't block the event loop. The Django
ORM is sync; calling it directly inside an `async` consumer stalls *every*
connection that worker holds. This wrapper (and Django 4.1+'s native async ORM
queries) is how you touch the database from an async consumer. See "sync-in-async"
below — it is the cardinal sin of this course.

**`sync_to_async` / `async_to_sync`** — The general asgiref bridges.
`sync_to_async` wraps a blocking function so an async caller can `await` it (on a
threadpool); `async_to_sync` lets synchronous code (a Celery task, a management
command, a signal handler) call an async function like `group_send`. Both have
footguns around thread-locals and the event loop — Module 15 catalogues them.

**Routing** — Channels' URL dispatch for connections. A `ProtocolTypeRouter`
splits `http` from `websocket`; a `URLRouter` maps WebSocket paths to consumers
(`re_path(r"ws/room/(?P<room>\w+)/$", RoomConsumer.as_asgi())`). The analog of
Django's `urls.py` for sockets.

**Worker (Channels sense)** — Historically, a separate process that consumes
background events off the channel layer. In the modern async-consumer model most
work happens in the consumer itself; this course uses "worker" to mean an
**ASGI worker process** (a Uvicorn/Daphne process), which is the unit you scale
per core.

---

## Python concurrency

**Event loop** — A single thread running a loop that reacts to I/O-readiness
events and never blocks. asyncio's core. Extremely efficient for I/O-bound work;
the cost is that *anything* you block on inside it stalls every coroutine that
loop is running — which, in a socket server, is every connection on that worker.

**Coroutine** — What `async def` defines. A function that can suspend at `await`
and hand control back to the event loop, letting other coroutines run while it
waits on I/O. Cheap — thousands per process — because suspending one costs a
heap object, not an OS thread.

**Task** — A coroutine scheduled to run on the event loop (`asyncio.create_task`).
The unit of concurrency in asyncio. Each live WebSocket connection is, roughly,
one Task plus its consumer instance. Forgetting to keep a reference to a Task is a
classic way to have it garbage-collected mid-flight.

**The GIL (Global Interpreter Lock)** — The lock in CPython that lets only one
thread execute Python bytecode at a time. Consequence: threads do **not** give you
parallel CPU in Python; they only help when they're blocked in I/O or C
extensions that release the GIL. This is *the* Python story of the course — it is
why asyncio gives cheap concurrency but not CPU parallelism, and why you scale CPU
with **processes**, not threads.

**Process-per-core worker model** — Because one Python process gets one core of
CPU (the GIL), you run **one worker process per core** (e.g. 8 Uvicorn workers on
an 8-core box) to use the whole machine. Each worker has its own event loop and
its own memory — which is *why* the in-memory channel layer can't span workers,
and why Redis is needed to cross **processes**, not just machines. The JVM twin
scales CPU inside one process with virtual threads; Python cannot, and that
single fact reshapes Phase 1.

**Why no virtual threads** — Java 21 has virtual threads: millions of cheap,
JVM-scheduled threads that make blocking I/O free and let one process saturate all
cores. Python has **nothing equivalent**. asyncio gives cheap concurrency but only
on one core and only for code written `async` all the way down; the GIL blocks the
CPU-parallelism half. So where the JVM twin's story is "virtual threads,"
this course's story is "asyncio + the GIL + processes" — the same problems,
solved with a different tool, with the wall arriving sooner.

**Blocking the event loop** — Calling any synchronous, CPU-bound, or blocking-I/O
function directly inside a coroutine, so the loop can't advance until it returns.
In a socket server this doesn't slow *one* request — it freezes *every connection
the worker holds*. Module 15 measures a single blocking ORM call taking p99 from
~60 ms to multiple seconds for everyone on the worker.

**Threadpool (asgiref)** — The bounded pool of OS threads that `sync_to_async` /
`database_sync_to_async` offload blocking work onto. It's how async code touches
the sync ORM without freezing the loop — but it's a *bounded resource*, so
concurrency is cheap while the pool has slots and suddenly a queue when it
doesn't. The Module-01 lesson "concurrency is free, resources are not" lives here.

**`asyncio.gather` / `TaskGroup`** — Ways to run several coroutines concurrently
and wait for them. `TaskGroup` (3.11+) is structured: if one child fails, the
rest are cancelled and the error propagates, preventing leaked Tasks in fan-out
code. The asyncio analog of the JVM twin's structured concurrency.

**Backpressure** — A consumer's ability to tell a producer "slow down." asyncio
does not give it to you automatically; a slow WebSocket client whose send buffer
fills will, without care, make your consumer's outbound queue grow until the
process OOMs. You add it deliberately (bounded queues, `send` timeouts).

**C10K / C10M** — Shorthand for "ten thousand / ten million concurrent
connections on one box." Names the class of problem, not a specific number.

---

## Redis

**RESP (REdis Serialization Protocol)** — Redis's wire format. RESP2 is
type-tagged text; RESP3 (negotiated with `HELLO 3`) adds native map/set/push
types and is what makes client-side caching and better Pub/Sub multiplexing
possible.

**Single-threaded event loop** — Redis executes commands one at a time on one
thread. This is *why* its operations are atomic without locks, and why one slow
command (`KEYS *`, a big `LRANGE`) stalls every other client. Module 08 makes you
stall live chat with `KEYS` on purpose.

**Pub/Sub** — Redis's fire-and-forget broadcast. `PUBLISH` delivers to whoever is
subscribed *right now*. No persistence, no acknowledgement, no replay:
**at-most-once**. A subscriber that was reconnecting simply misses the message.
This is what backs `RedisChannelLayer`.

**Sharded Pub/Sub** — `SPUBLISH`/`SSUBSCRIBE` (Redis 7+), which route by hash slot
so a message doesn't have to be broadcast to every node in a cluster. Essential
for Pub/Sub on Redis Cluster at scale (Module 18).

**Stream** — An append-only log data type with unique, monotonically increasing
IDs (`<ms>-<seq>`). Persistent, replayable, and trimmable. The durable
alternative to Pub/Sub, and what your custom fan-out layer is built on in
Module 09.

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

**Hash tag** — The `{...}` part of a key name. `room:{7}:stream` and
`room:{7}:seq` hash to the same slot, so multi-key commands and Lua scripts work
across them.

**Hot key** — A single key receiving disproportionate traffic (e.g. the
`#general` room in a big org). Cluster sharding does not help, because one key
lives on exactly one node. Module 11's challenge attacks this.

**RDB / AOF** — Redis's two persistence modes. RDB is periodic point-in-time
snapshots (fast restart, loses everything since the last snapshot); AOF logs every
write (slower restart, `appendfsync`-dependent loss). For a fan-out backbone where
Postgres is the source of truth, turning persistence *off* can be the correct,
defensible choice — Module 08 argues both sides.

---

## Delivery semantics

**At-most-once** — Every message is delivered zero or one times. Never
duplicated, sometimes lost. Redis Pub/Sub (and therefore the default Redis channel
layer). Fine for typing indicators.

**At-least-once** — Every message is delivered one or more times. Never lost,
sometimes duplicated. Redis Streams with `XACK`, Kafka with committed offsets.
The realistic target for chat — paired with client-side dedup.

**Exactly-once** — Delivered precisely once. Not achievable end-to-end across an
unreliable network in the general case; what systems actually sell is
at-least-once delivery plus **idempotent processing**, which is observationally
equivalent. Module 09 explains the sleight of hand.

**Idempotency key** — A client-generated unique ID attached to a message so the
server can recognize and discard a retry. In this course it's the `cid`
(client id) field of your envelope, enforced by a `UNIQUE (room_id, client_id)`
index. The single most valuable line in your protocol.

**Deduplication window** — How long you remember idempotency keys. Bounded memory
forces a bounded window; picking it is a real design decision.

**Sequence number** — A per-room (or per-user-inbox) monotonically increasing
counter. Lets a client detect a *gap* — "I have 41 and 43, I'm missing 42" —
which is the only way to know you lost something. Assigned server-side in
Module 05, atomically in Redis.

**Cursor / resume token** — What a reconnecting client sends to say "give me
everything after this point." Turns a reconnect from a data-loss event into a
catch-up. Module 10 proves a 2-minute disconnect loses 98 messages without one
and 0 with one.

**Fan-out on write** — When a message arrives, immediately write a copy into every
recipient's inbox. Reads are trivial; writes multiply by room size.

**Fan-out on read** — Store the message once; assemble each user's view at read
time. Writes are cheap; reads do work. Most large chat systems use a hybrid,
switching strategy above a room-size threshold.

**Write amplification** — One logical event causing many physical writes. A
1,000-member room with fan-out-on-write is 1,000× amplification. The number that
decides your storage architecture, and the reason for the **74 TB/year** figure
this course reuses from Module 12.

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
Snowflake, with first-class support in modern Postgres and Python libraries.

**Index locality** — Whether logically adjacent rows are physically adjacent in
the index. Random IDs (UUIDv4) destroy it, causing page splits and write
amplification. Time-sortable IDs preserve it.

**Keyset pagination** — Paginating with `WHERE id < :cursor ORDER BY id DESC
LIMIT n` instead of `OFFSET`. Constant-time regardless of how deep you scroll;
`OFFSET 100000` is not. In Django you express it with `.filter(id__lt=cursor)`,
not with a `Paginator`.

**Declarative partitioning** — Splitting one logical Postgres table into physical
child tables by a key (usually time, for chat). Lets you drop old data with
`DROP TABLE` instead of a `DELETE` that generates gigabytes of WAL. Django has no
native DDL for it, so you create the partitioned table and its children with a
`RunSQL` migration (Module 13).

**Partition pruning** — The planner skipping partitions that can't match the
query. What makes partitioning a read win as well as a maintenance win.

**WAL (Write-Ahead Log)** — Postgres's durability journal. Every change is written
here before the data files. It's also the replication stream and the CDC source.

**Streaming replication** — A replica connecting to a primary and continuously
applying its WAL. The basis of read replicas and HA failover.

**Replica lag** — How far behind a replica is. The reason "I sent a message and
then couldn't see it" bugs exist when you read from replicas naively.

**Read-your-writes** — The consistency guarantee that a client sees its own writes
immediately. Requires routing that user's reads to the primary (or waiting on an
LSN) for a window after a write. For chat there's a better answer: the sender
already has the message, so echo it optimistically.

**DB router (Django `DATABASE_ROUTERS`)** — A Django class with `db_for_read`,
`db_for_write`, and `allow_relation` hooks that decides which configured database
a query goes to. The **idiomatic** Django mechanism for read replicas (Module 13)
and for app-level sharding (Module 14) — you use it rather than hand-rolling
connection selection.

**Connection pooling / PgBouncer** — Postgres forks a process per connection, so
thousands of app connections will kill it. PgBouncer multiplexes many client
connections onto few server ones. Transaction pooling mode is the useful one, and
it breaks session-level features — with psycopg you must also disable server-side
prepared statements (`prepare_threshold=None`) or you get "prepared statement
already exists" errors. Module 13 covers this in detail.

**Transactional outbox** — Writing the message row *and* an "to be published" row
in the same database transaction, then having a separate relay (a **Celery** task
here) publish it. Solves the dual-write problem: you can never persist without
publishing or publish without persisting.

**Dual-write problem** — Writing to two systems (DB and broker) without a shared
transaction, so a crash between them leaves them inconsistent.

**CDC (Change Data Capture)** — Reading the WAL (via logical decoding, e.g.
Debezium) to publish changes downstream. An outbox alternative with different
operational tradeoffs — notably that a stalled replication slot pins WAL and fills
the disk.

**Sharding** — Splitting data across independent databases by a key (room ID,
user ID). Scales writes past one machine at the cost of cross-shard queries and
painful resharding. Implemented with a Django DB router in Module 14.

**Consistent hashing** — A key→node mapping that only remaps `1/n` of keys when a
node is added, instead of remapping everything. What makes resharding survivable.

**Wide-column store** — Cassandra/ScyllaDB's model: a partition key selects a
node, clustering keys order rows within the partition. Optimized for "give me the
last N rows of this partition" — which is precisely a chat scrollback query.
Module 14 models the same data both ways.

**LSM tree** — The write-optimized storage structure behind Cassandra, ScyllaDB,
and RocksDB. Buffers writes in memory and flushes sorted files, trading read
amplification and compaction work for very fast writes. Contrast Postgres's
B-tree + heap.

**Tombstone** — A deletion marker in an LSM store. Accumulating tombstones in a
partition make reads progressively slower; a classic Cassandra footgun.

---

## Kafka

**Topic / partition** — A topic is a named log; it's split into partitions, each
an ordered, append-only sequence. Partitions are the unit of parallelism *and* the
unit of ordering.

**Ordering guarantee** — Kafka guarantees order **within a partition only**.
Messages with the same key go to the same partition, which is how you get
per-room ordering.

**Offset** — A consumer's position in a partition. Committing it is what makes
progress durable — and *when* you commit determines at-least-once vs
at-most-once.

**Consumer group / rebalance** — Consumers sharing a group split the partitions.
When membership changes, partitions are reassigned — a *rebalance*, during which
consumption stalls. A real operational cost, measured against Redis Streams in
Module 16.

**KRaft mode** — Kafka's ZooKeeper-less mode, where a quorum of Kafka controllers
holds cluster metadata via a Raft log. What you run in Module 16 — one fewer
system to operate than the old ZooKeeper setup.

**Log compaction** — Retention that keeps only the latest value per key. Useful
for state-like topics (user profile, room settings); wrong for a message log.

**ISR (In-Sync Replicas)** — The replicas caught up with the leader. `acks=all` +
`min.insync.replicas` is how you trade throughput for durability.

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
by killing it or revoking its network access (e.g. HAProxy's
`on-marked-down shutdown-sessions`).

**Patroni** — A supervisor for Postgres HA that stores cluster state in a
distributed config store (etcd/Consul) and handles election, promotion, and
reconfiguration.

**PgBouncer** — A lightweight Postgres connection pooler that multiplexes many
client connections onto few server ones. Transaction-pooling mode is the useful
one for a socket fleet; see the psycopg caveats above.

**HAProxy** — A TCP/HTTP load balancer. In this course it fronts Postgres,
routing writes to whichever node currently answers Patroni's `/primary`
healthcheck with 200.

**Sticky session / session affinity** — A load balancer sending one client
consistently to one backend. Useful for stateful WebSocket connections; also the
thing that makes rolling deploys drop sockets. Once the Redis backplane exists you
need it less, but you still keep local per-connection state, so you still want it.

**Draining / graceful shutdown** — Telling a node to stop accepting new
connections and let existing ones finish (and ideally send a close frame) before
it dies. Under ASGI this is the server's lifespan-shutdown plus a `preStop sleep`
in Kubernetes. The difference between a deploy nobody notices and one that logs
everybody out.

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
saturation (queue depth, threadpool occupancy) is the one people forget and the
one that predicts outages.

**Cardinality** — The number of distinct label combinations on a metric. Putting a
user ID in a Prometheus label is how you take down your monitoring.

**Histogram vs summary** — Histograms bucket observations and can be aggregated
across instances; summaries compute quantiles locally and **cannot** be
meaningfully averaged. Use histograms.

**p99 / tail latency** — The 99th percentile. In a fan-out system, a user's
experience is the *max* over many deliveries, so tail latency dominates.

**Span / trace / context propagation** — A trace is a request's journey; spans are
its segments. Propagating trace context across a Redis Stream, a Celery task, or
the threadpool `database_sync_to_async` uses is manual work — Module 20's core
exercise.

**End-to-end delivery latency** — The metric that actually matters: from the
instant the sender calls `send` to the instant the receiver's socket has the
bytes. *Not* enqueue-to-Redis time, which flatters you. Module 20 measures the
real thing with a synthetic prober.

**SLI / SLO / error budget** — The *indicator* you measure, the *objective* you
promise, and the amount of failure you're allowed before you stop shipping
features.

---

## Security and abuse

**Origin check** — Validating the `Origin` header on the WebSocket handshake.
Browsers don't apply CORS to WebSocket, so without this any site can open a socket
to your server with the user's cookies. In Channels this goes in
`AllowedHostsOriginValidator` / a custom middleware.

**CSWSH (Cross-Site WebSocket Hijacking)** — The attack the origin check
prevents: a malicious page opening an authenticated WebSocket to your server.
Module 21 has you perform it, then block it.

**Ticket / token-in-query** — A short-lived credential passed as a query param (or
`Sec-WebSocket-Protocol`) at handshake time, because browsers can't set arbitrary
headers on `new WebSocket()` and cookies aren't reliably sent cross-origin. You
exchange a long-lived JWT for a one-time ticket over HTTP, then present the ticket
on the socket.

**Token rotation on a long-lived socket** — A JWT expires; a socket open for eight
hours does not. You need an in-band re-authentication message, or a socket that
outlives its own authorization — plus a way to revoke it cluster-wide the instant
a user is banned.

**Token bucket** — A rate-limiting algorithm: tokens refill at a fixed rate up to
a cap, each action costs one. Allows bursts while bounding sustained rate.
Implemented atomically in Lua in Module 11.

**Backpressure vs rate limiting** — Backpressure slows a producer you control;
rate limiting rejects one you don't. Chat needs both, in different places.

**E2EE (End-to-End Encryption)** — Encrypting so the server can't read messages.
Costs you server-side search, moderation, and push-notification previews — the
tradeoff discussed honestly in Module 21.
