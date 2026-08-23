# Cheatsheet — Troubleshooting Decision Trees

Symptom → cause → fix. Work top to bottom; the first matching branch is usually
right.

---

## 1. WebSocket connections fail or drop

```
Handshake never returns 101
├─ 403 / connection refused at the proxy?
│   ├─ nginx: missing `proxy_http_version 1.1`         -> add it
│   ├─ nginx: missing Upgrade/Connection headers       -> add the `map` block
│   └─ Spring: Origin rejected                         -> setAllowedOrigins(...)
├─ 401?
│   └─ Token not readable at handshake time. Cookies aren't sent cross-origin
│      and browsers can't set headers on `new WebSocket()`.
│      -> query param (short-lived ticket) or Sec-WebSocket-Protocol
└─ 404?
    └─ Endpoint path or SockJS suffix mismatch (`/ws` vs `/ws/websocket`)

Connects, then dies after a fixed interval
├─ ~60s, very consistent  -> nginx `proxy_read_timeout` (default 60s). Raise it.
├─ ~30-120s, cloud LB     -> LB idle timeout. Raise it AND enable heartbeats.
└─ Random                 -> NAT/firewall idle eviction -> STOMP heart-beat 10s

Connects, dies under load only
├─ `Too many open files`     -> ulimit -n on the container AND host
├─ Close code 1009           -> message exceeds setMessageSizeLimit
├─ Close code 1011 + OOM     -> see tree 3
└─ Server logs "session closed, send buffer full"
    -> a slow consumer. setSendBufferSizeLimit + setSendTimeLimit is
       WORKING AS DESIGNED. Investigate why that client is slow.

Works locally, fails in Docker
├─ Connecting to `localhost` from inside a container -> use the service name
└─ Port not published                                -> `ports:` in compose
```

---

## 2. Messages are lost

```
Lost only around a reconnect
└─ You're on Redis Pub/Sub. This is at-most-once — WORKING AS DESIGNED.
   -> Module 09: Redis Streams + consumer groups + a resume cursor

Lost only under load
├─ Channel queue overflow -> raise queueCapacity, or add backpressure (Module 06)
├─ Redis `evicted_keys` > 0 in INFO stats
│   -> maxmemory reached. Raise it, or trim streams (XTRIM MAXLEN ~)
└─ Consumer crashed mid-batch, entries stuck in PEL
   -> XPENDING to confirm, XAUTOCLAIM to recover

Lost only during a deploy/failover
├─ No graceful shutdown -> server.shutdown=graceful + stop_grace_period: 60s
├─ All replicas restarted at once -> maxUnavailable: 1, stagger
└─ Async replica promoted, lost its tail -> synchronous_commit for the outbox write

Persisted but never delivered (or vice versa)
└─ Classic dual-write. -> transactional outbox (Module 13)

"Lost" but actually just out of order
└─ Client rendered by arrival time. -> order by message id client-side,
   detect gaps by sequence number (Module 10)
```

---

## 3. Memory grows until OOM

```
Heap grows with connection count, linearly
└─ Normal — measure BYTES PER CONNECTION (heap after GC / connections).
   >500 KB/conn is a smell. Look for per-session caches and big buffers.

Heap grows while connection count is FLAT
├─ Unbounded channel queue (clientOutbound is unbounded by default)
│   -> set queueCapacity; a bounded queue that rejects beats a heap that dies
├─ Slow consumers accumulating outbound buffers
│   -> setSendBufferSizeLimit(512KB) + setSendTimeLimit(20s)
├─ Session/presence map never cleaned on disconnect
│   -> handle SessionDisconnectEvent; also expire by TTL as a backstop
└─ Dedup cache with no eviction
    -> bounded window (Caffeine maximumSize + expireAfterWrite)

Redis memory grows forever
├─ Streams never trimmed        -> XADD ... MAXLEN ~ 10000
├─ Keys without TTL             -> redis-cli --scan | check TTL; set EXPIRE
└─ mem_fragmentation_ratio > 1.5 -> activedefrag yes

Container OOM-killed but JVM heap looks fine
└─ The JVM doesn't know the cgroup limit, or off-heap/metaspace/thread stacks.
   -> -XX:MaxRAMPercentage=75 (not -Xmx), and count your PLATFORM threads:
      each is ~1 MB of stack, off-heap.
```

Diagnostics:
```bash
jcmd <pid> GC.heap_info
jcmd <pid> VM.native_memory summary     # needs -XX:NativeMemoryTracking=summary
jcmd <pid> GC.class_histogram | head -25
jmap -dump:live,format=b,file=/tmp/h.hprof <pid>
docker stats --no-stream
```

---

## 4. Latency is bad

```
p50 fine, p99 terrible
├─ GC pauses            -> check jvm_gc_pause_seconds_max; switch to ZGC
├─ A slow Redis command -> redis-cli SLOWLOG GET 10, INFO commandstats
├─ Connection pool wait -> hikaricp_connections_pending > 0; SHOW POOLS in PgBouncer
└─ Thread pool queueing -> channel executor activeCount pinned at max

Everything is uniformly slow
├─ Redis --latency > 1ms on loopback -> Redis is saturated or the host is
├─ CPU pinned                        -> profile; is JSON serialization the cost?
└─ Blocking call on the event loop (WebFlux only) -> BlockHound will name it

Latency grows over time, resets on restart
└─ A leak. Queue depth, PEL size, or a growing map. Graph them.

Fine with 1 node, bad with 3
├─ Every node subscribes to every room -> shard subscriptions (Module 13)
├─ Redis is now the bottleneck        -> INFO stats ops/sec; scale to Cluster
└─ Cross-node hop added a round trip  -> expected; measure, don't panic
```

---

## 5. Postgres problems

```
"too many connections"
└─ App pool x instances > max_connections. -> PgBouncer, transaction mode.
   Do NOT just raise max_connections.

Query suddenly slow, no code change
├─ Stale statistics       -> ANALYZE the table
├─ Table bloat            -> pg_stat_user_tables n_dead_tup; tune autovacuum
├─ Index no longer fits RAM -> check EXPLAIN Buffers; add partitioning
└─ Generic plan defeated pruning -> plan_cache_mode = force_custom_plan

Replica lag climbing
├─ Replica CPU/IO saturated by read traffic -> add a replica, or move reads
├─ A long query on the replica blocking replay
│   -> hot_standby_feedback / max_standby_streaming_delay tradeoff
└─ Write burst on primary -> expected; is it recovering? Graph replay_lag.

"I sent a message, then couldn't see it"
└─ Read-your-writes violation from a lagging replica.
   -> route the sender's reads to primary briefly, or echo optimistically

Disk filling up
├─ WAL not being archived/consumed  -> check pg_replication_slots
│   ** AN INACTIVE SLOT PINS WAL FOREVER. Most common Postgres disk outage. **
├─ Old partitions never dropped     -> DROP TABLE the old ones
└─ Bloat                            -> pg_repack, or partition + drop instead
```

```sql
SELECT slot_name, active, pg_size_pretty(
  pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
FROM pg_replication_slots;          -- run this BEFORE the disk fills
```

---

## 6. Redis problems

```
Intermittent timeouts
├─ SLOWLOG shows a slow command -> find it; KEYS/SMEMBERS/LRANGE on a big key
├─ RDB fork pause               -> INFO persistence latest_fork_usec; consider
│                                  disabling RDB on a pure-transport instance
└─ maxmemory + eviction churn   -> INFO stats evicted_keys

CROSSSLOT error
└─ Multi-key op across slots in Cluster. -> hash tags: room:{7}:a, room:{7}:b

MOVED / ASK errors reaching the app
└─ Client isn't cluster-aware. -> Lettuce cluster mode; redis-cli needs -c

Sentinel won't fail over
├─ Quorum not reachable (need odd count, >=3)
├─ Sentinels can't see each other -> same network, ports published
└─ down-after-milliseconds too high -> lower for drills

Everything slow right after a failover
└─ Full resync of replicas + thundering-herd reconnects. Expected.
   -> repl-diskless-sync yes, and jittered client backoff
```

---

## 7. Docker / Compose

```
"port is already allocated"        -> docker ps -a; docker rm -f <name>
"no space left on device"          -> docker system prune -a --volumes (careful)
Container restart-loops on startup -> healthcheck start_period too short for the JVM
depends_on didn't wait             -> needs `condition: service_healthy` + a healthcheck
Config change had no effect        -> docker compose up -d --force-recreate
Stale data after a config change   -> docker compose down -v   (the -v matters)
Can't reach another service        -> use the SERVICE NAME, not localhost
Sentinel container won't start     -> it rewrites its config; can't be read-only
```

---

## 8. The general method

When nothing in the trees fits:

1. **Reproduce it under load.** Bugs that only appear at scale are queue,
   timeout, or resource bugs. At scale they're reliable; at rest they're ghosts.
2. **Find the layer.** Client → LB → app → Redis → Postgres. Time each hop with
   a trace. Don't guess which one is slow.
3. **Graph the queue depths.** Every hang is a queue somewhere. Channel
   executors, Hikari pending, PgBouncer `cl_waiting`, Redis `XPENDING`, Kafka
   consumer lag.
4. **Compare against a known-good.** Same test, one node, no Redis. If that's
   also slow, the distribution isn't your problem.
5. **Read the logs of the thing that died, not the thing that complained.** The
   app logging "connection reset" is a witness, not a suspect.
