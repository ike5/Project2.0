-- code/scylla_schema.cql — Pulse's message store, modelled for a wide-column
-- database instead of a relational one.
--
--   cqlsh> SOURCE '/scylla_schema.cql'
--   $ docker exec -i pulse-scylla1 cqlsh < code/scylla_schema.cql
--
-- Read this file next to Module 12's `CREATE TABLE messages`. The columns are
-- almost identical. Everything interesting is in the PRIMARY KEY, and in what
-- is missing: no foreign keys, no CHECK constraints, no secondary indexes, no
-- sequences, and -- the one that reshapes the application -- no UNIQUE index.

DROP KEYSPACE IF EXISTS pulse;

-- NetworkTopologyStrategy even for a single node. SimpleStrategy works and is
-- one line shorter, and converting from it later requires a full repair. Start
-- with the one you will end with.
--   RF=1 on the single-node lab stack; lab Part E raises it to 3.
CREATE KEYSPACE pulse
  WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 1};

USE pulse;


-- ===========================================================================
-- messages -- the scrollback table
-- ===========================================================================
CREATE TABLE messages (
    room_id    text,          -- Room.key: "room.7". Same string as Postgres.
    bucket     int,           -- floor(epoch_seconds / 604800): weekly.
    seq        bigint,        -- per-room, gapless (Module 05/10).
    id         bigint,        -- Snowflake (Module 12). Still useful: it carries
                              -- its own timestamp, which is how a client cursor
                              -- derives its bucket without a lookup.
    sender     text,
    client_id  text,          -- idempotency key. NOT enforced here -- see below.
    body       text,
    reply_to   bigint,
    created_at timestamp,
    edited_at  timestamp,
    deleted_at timestamp,     -- SOFT delete, and now it is mandatory. See §3.

    PRIMARY KEY ((room_id, bucket), seq)
) WITH CLUSTERING ORDER BY (seq DESC)
  AND compaction = {
      'class': 'TimeWindowCompactionStrategy',
      'compaction_window_unit': 'DAYS',
      'compaction_window_size': 1
  }
  AND default_time_to_live = 7776000          -- 90 days, enforced by the DB
  AND gc_grace_seconds = 86400                -- 1 day, see §3
  AND comment = 'Pulse scrollback. One partition per (room, week).';

-- §1. ((room_id, bucket), seq) -- the composite PARTITION key.
--
-- `bucket` is floor(epoch_seconds / 604800), a week number. It is THE hot
-- partition fix. Without it, `#general` is one partition on one node, growing
-- forever, and no amount of adding nodes helps -- the partition key is the only
-- load-balancing mechanism a wide-column store has. This is precisely the
-- problem Discord published about before moving to Scylla.
--
-- It costs you the one thing Postgres gave for free: a scrollback page that
-- straddles a week boundary requires TWO queries. Lab Part D writes that loop,
-- and it is the clearest single illustration of the wide-column tax.
--
-- Week, not day, and not month:
--   day    -> a quiet room's 50-message page walks back 90 partitions
--   month  -> a busy room's partition reaches ~2 GB; Scylla warns past 100 MB
--   week   -> 84 MB for Pulse's busiest room at 10k msg/s across 1,000 rooms
-- Size the bucket from your BUSIEST partition, not your average one.

-- §2. CLUSTERING ORDER BY (seq DESC)
--
-- Rows are stored on disk in the order you read them. "Last 50 messages" is a
-- sequential read of adjacent bytes -- not an index seek plus 50 heap fetches.
-- Postgres achieved the same effect with `INDEX (room_id, id DESC)`; the
-- difference is that here it is the physical layout of the data itself, not a
-- second structure maintained alongside it.

-- §3. default_time_to_live + gc_grace_seconds
--
-- Retention is a table property. No partition-maintenance task, no Celery beat
-- job, no `DROP TABLE messages_2026_05`. The database expires rows itself, and
-- TimeWindowCompactionStrategy drops whole sstables once every row in them has
-- expired -- which is the LSM equivalent of Module 13's `DROP TABLE`, and just
-- as cheap.
--
-- gc_grace_seconds is lowered from the 864000 (10 day) default to 86400 (1 day)
-- because Pulse's data is append-only and TTL-expired. The default exists to
-- give `nodetool repair` time to propagate tombstones before they vanish; if
-- you lower it you MUST repair more often than the value you chose. Write that
-- down in your runbook, because getting it wrong resurrects deleted messages.


-- ===========================================================================
-- messages_by_client_id -- the idempotency lookup
-- ===========================================================================
-- Cassandra has no UNIQUE index and no efficient secondary lookup, so the same
-- fact is written twice, into a second table shaped for the second query. This
-- is the wide-column tax made concrete: Postgres gave you
--
--     CREATE UNIQUE INDEX ON messages (room_id, client_id);
--
-- and enforced it. Here you get a second table, a second write, and an
-- application that is responsible for keeping them consistent.
CREATE TABLE messages_by_client_id (
    room_id   text,
    client_id text,
    seq       bigint,
    id        bigint,
    PRIMARY KEY ((room_id, client_id))
) WITH default_time_to_live = 300             -- only the dedup window needs it
  AND compaction = {'class': 'LeveledCompactionStrategy'}
  AND comment = 'Retry dedup. 5-minute window. NOT a durable uniqueness guarantee.';

-- Note the TTL: 300 seconds. Postgres's unique index was true FOREVER. This one
-- is true for five minutes. A retry that arrives at 5 minutes and 1 second
-- inserts a duplicate message, and nothing anywhere reports an error.
--
-- You can close that with `INSERT ... IF NOT EXISTS`, which is a lightweight
-- transaction -- a Paxos round trip, four network hops at QUORUM. Lab Part E
-- measures it at 2.3 ms on one node and 5.1 ms on three, against 0.08 ms for
-- the Postgres unique index. That is the most important number in Module 14:
-- the guarantee the whole delivery chain rests on is nearly free in one store
-- and 60x more expensive in the other.


-- ===========================================================================
-- room_sequence -- what Module 05's INCR became
-- ===========================================================================
-- Redis provides the gapless per-room counter on the hot path (Module 10's Lua
-- script). This table is the durable high-water mark used to recover it after a
-- Redis restart. In Postgres it was `SELECT max(seq)` over a primary-key index:
-- one index scan, microseconds. Here `max()` over a partition is an aggregate,
-- and aggregates across partitions do not exist -- so the high-water mark must
-- be MAINTAINED rather than derived.
CREATE TABLE room_sequence (
    room_id  text PRIMARY KEY,
    last_seq bigint
) WITH comment = 'Maintained high-water mark. Cassandra cannot derive it.';

-- Updating it needs a counter or an LWT to be correct under concurrency, and
-- both are expensive. Pulse's answer: Redis stays authoritative on the hot
-- path, this table is written asynchronously as a recovery hint, and recovery
-- reconciles it by reading the newest bucket of each room. Lab Part D builds
-- that, and challenge task 4 asks you to do better.


-- ===========================================================================
-- What is NOT here, and what that means
-- ===========================================================================
--   * No `messages_by_sender`. Moderation ("show me everything this user
--     posted") has no table, so it is impossible without a full scan. In
--     Postgres it was a slow query on a replica. Here it is a Spark job, or a
--     third table and a backfill.
--   * No `outbox`. Module 13's transactional outbox requires writing the
--     message and the outbox row ATOMICALLY. Cassandra has no multi-partition
--     transaction; a LOGGED BATCH gives atomicity but not isolation, and costs
--     a coordinator-side batchlog write on every send. The outbox does not
--     port.
--   * No unique constraint on anything.
--   * No `count(*)`. `SELECT count(*) FROM messages` will time out, and that is
--     the documented behaviour, not a misconfiguration.
--
-- Every one of those absences is survivable. Together they are the answer to
-- "what does this actually cost?" -- and the reason Module 14 recommends
-- sharded Postgres for Pulse while acknowledging that Discord was right to
-- leave it.
