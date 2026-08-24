#!/usr/bin/env python3
"""
store_bench.py — the head-to-head that Part E of the lab runs.

    python store_bench.py postgres-single
    python store_bench.py postgres-sharded-4  --procs 1,2,4,8
    python store_bench.py scylla-1node        --dedup redis
    python store_bench.py scylla-3node        --table messages_nobucket --rooms 1

WHY THIS IS A MULTIPROCESS BENCHMARK, AND WHY THAT IS THE POINT
---------------------------------------------------------------
A single CPython process is one core. Every driver here -- psycopg, the Scylla
driver -- releases the GIL around the socket, so a single process CAN overlap
I/O; what it cannot do is overlap the per-row Python work: building the tuple,
formatting the statement, decoding the response, and (for the sharded case) the
router lookup, the CRC32, and the ContextVar.

So a one-process benchmark measures YOUR CLIENT, not the store. Run it anyway
(`--procs 1`) because the gap between the one-process and four-process columns is
the most Python-specific result in Module 14:

    postgres-single      1 proc  41,200/s     4 procs   44,100/s   (+7%)
    postgres-sharded-4   1 proc  52,800/s     4 procs  148,400/s   (+181%)

Four times the database capacity bought 28% more throughput from one process.
Scaling the datastore does nothing until you scale the processes driving it --
which is Module 01's conclusion, arriving at the storage layer.

Reference machine: 8-core / 16 GB, Ubuntu 24.04, Python 3.12, Postgres 16,
ScyllaDB 6.0 (--smp 2 --memory 2G).
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import statistics
import sys
import time
import zlib
from dataclasses import dataclass, field

LOGICAL_SHARDS = 4096
PULSE_EPOCH_MS = 1_704_067_200_000          # Module 12's custom epoch


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

TARGETS: dict[str, dict] = {
    "postgres-single": {
        "kind": "pg",
        "dsns": ["postgresql://pulse:pulse@localhost:5432/pulse"],
    },
    "postgres-sharded-4": {
        "kind": "pg",
        "dsns": [f"postgresql://pulse:pulse@localhost:{5440 + i}/pulse"
                 for i in range(4)],
    },
    "postgres-sharded-6": {
        "kind": "pg",
        "dsns": [f"postgresql://pulse:pulse@localhost:{5440 + i}/pulse"
                 for i in range(6)],
    },
    "scylla-1node": {"kind": "scylla", "hosts": ["127.0.0.1"], "rf": 1},
    "scylla-3node": {"kind": "scylla", "hosts": ["127.0.0.1"], "rf": 3},
}


@dataclass
class Sample:
    op: str
    latencies_ms: list[float] = field(default_factory=list)

    def report(self) -> str:
        if not self.latencies_ms:
            return f"{self.op:<22} no samples"
        s = sorted(self.latencies_ms)
        def q(p): return s[min(len(s) - 1, int(len(s) * p))]
        return (f"{self.op:<22} n={len(s):>8}  "
                f"p50={q(.50):7.3f}ms  p99={q(.99):7.3f}ms  "
                f"p99.9={q(.999):8.3f}ms")


# ---------------------------------------------------------------------------
# Postgres path -- raw cursor, exactly Module 12's hot path
# ---------------------------------------------------------------------------

def pg_worker(dsns: list[str], rooms: list[str], seconds: float,
              out: mp.Queue, proc_id: int) -> None:
    import psycopg
    from snowflake import Snowflake                 # Module 12's code/

    conns = [psycopg.connect(d, autocommit=True) for d in dsns]
    gen = Snowflake(worker_id=proc_id)
    n_shards = len(conns)

    insert = Sample("insert")
    dedup = Sample("idempotency-check")
    scroll = Sample("scrollback")

    # Prepared once per connection. Module 13 taught you that psycopg promotes a
    # statement to server-side prepared after 5 executions and that this BREAKS
    # under PgBouncer transaction pooling -- which is why the lab's settings pass
    # prepare_threshold=None and why this benchmark connects DIRECTLY to Postgres
    # rather than through the pooler. Benchmark the store, not the pooler.
    seq = {r: 0 for r in rooms}
    deadline = time.monotonic() + seconds
    i = 0

    while time.monotonic() < deadline:
        room = rooms[i % len(rooms)]
        i += 1
        # The router, inlined: crc32 of the COMPOSED key, mod 4096, mod N.
        conn = conns[(zlib.crc32(room.encode()) % LOGICAL_SHARDS) % n_shards]
        seq[room] += 1
        mid = gen.next_id()

        t0 = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages (id, room_id, seq, sender, client_id, body,
                                      created_at)
                VALUES (%s,%s,%s,%s,%s,%s, now())
                ON CONFLICT (room_id, client_id) DO NOTHING
                RETURNING id, seq
                """,
                (mid, room, seq[room], f"u{i % 200}", f"c-{proc_id}-{i}",
                 "x" * 96),
            )
            cur.fetchone()
        insert.latencies_ms.append((time.perf_counter() - t0) * 1000)

        if i % 10 == 0:                       # 10% idempotency checks
            t0 = time.perf_counter()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, seq FROM messages WHERE room_id=%s AND client_id=%s",
                    (room, f"c-{proc_id}-{i - 1}"))
                cur.fetchone()
            dedup.latencies_ms.append((time.perf_counter() - t0) * 1000)

        if i % 20 == 0:                       # 5% scrollback pages
            t0 = time.perf_counter()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, seq, sender, body FROM messages "
                    "WHERE room_id=%s AND id < %s ORDER BY id DESC LIMIT 50",
                    (room, mid))
                cur.fetchall()
            scroll.latencies_ms.append((time.perf_counter() - t0) * 1000)

    out.put((insert, dedup, scroll))


# ---------------------------------------------------------------------------
# Scylla path
# ---------------------------------------------------------------------------

def scylla_worker(hosts: list[str], rooms: list[str], seconds: float,
                  out: mp.Queue, proc_id: int, table: str, dedup_mode: str) -> None:
    # Session built INSIDE the child process, after the fork. A Session
    # inherited across fork() has reactor threads that do not exist here, and
    # the symptom is a hang rather than an exception.
    from scylla_repo import build_session, bucket_of
    from snowflake import Snowflake

    session = build_session(hosts)
    gen = Snowflake(worker_id=proc_id)

    ins = session.prepare(
        f"INSERT INTO {table} (room_id, bucket, seq, id, sender, client_id, body,"
        f" created_at) VALUES (?,?,?,?,?,?,?,?)"
        if table == "messages" else
        f"INSERT INTO {table} (room_id, seq, id, sender, body, created_at)"
        f" VALUES (?,?,?,?,?,?)"
    )
    dedup_lwt = session.prepare(
        "INSERT INTO messages_by_client_id (room_id, client_id, seq, id) "
        "VALUES (?,?,?,?) IF NOT EXISTS")
    dedup_plain = session.prepare(
        "INSERT INTO messages_by_client_id (room_id, client_id, seq, id) "
        "VALUES (?,?,?,?)")
    scroll_stmt = session.prepare(
        f"SELECT seq, id, sender, body FROM {table} "
        f"WHERE room_id=? AND bucket=? AND seq < ? LIMIT 50"
        if table == "messages" else
        f"SELECT seq, id, sender, body FROM {table} "
        f"WHERE room_id=? AND seq < ? LIMIT 50")

    redis = None
    if dedup_mode == "redis":
        import redis as redis_lib
        redis = redis_lib.Redis(decode_responses=True)

    insert = Sample("insert")
    dedup = Sample("idempotency-check")
    scroll = Sample("scrollback")

    seq = {r: 0 for r in rooms}
    deadline = time.monotonic() + seconds
    i = 0
    bucketed = table == "messages"

    while time.monotonic() < deadline:
        room = rooms[i % len(rooms)]
        i += 1
        seq[room] += 1
        mid = gen.next_id()
        now = time.time()
        bucket = bucket_of(now)

        t0 = time.perf_counter()
        params = ((room, bucket, seq[room], mid, f"u{i % 200}",
                   f"c-{proc_id}-{i}", "x" * 96, int(now * 1000))
                  if bucketed else
                  (room, seq[room], mid, f"u{i % 200}", "x" * 96, int(now * 1000)))
        session.execute(ins, params)
        insert.latencies_ms.append((time.perf_counter() - t0) * 1000)

        if i % 10 == 0:
            t0 = time.perf_counter()
            if dedup_mode == "redis":
                # The workaround: a permanent database invariant becomes a
                # TTL-bounded cache entry. 11x faster, and gone on a restart.
                if redis.set(f"dedup:{{{room}}}:{i}", "1", nx=True, ex=300):
                    session.execute(dedup_plain, (room, f"c-{proc_id}-{i}",
                                                  seq[room], mid))
            elif dedup_mode == "lwt":
                session.execute(dedup_lwt, (room, f"c-{proc_id}-{i}",
                                            seq[room], mid))
            dedup.latencies_ms.append((time.perf_counter() - t0) * 1000)

        if i % 20 == 0:
            t0 = time.perf_counter()
            session.execute(scroll_stmt,
                            (room, bucket, 1 << 62) if bucketed
                            else (room, 1 << 62))
            scroll.latencies_ms.append((time.perf_counter() - t0) * 1000)

    out.put((insert, dedup, scroll))


# ---------------------------------------------------------------------------

def run(target: str, procs: int, rooms_n: int, seconds: float,
        table: str, dedup_mode: str) -> None:
    cfg = TARGETS[target]
    rooms = [f"room.{i}" for i in range(rooms_n)]
    q: mp.Queue = mp.Queue()

    workers = []
    for pid in range(procs):
        if cfg["kind"] == "pg":
            p = mp.Process(target=pg_worker,
                           args=(cfg["dsns"], rooms, seconds, q, pid))
        else:
            p = mp.Process(target=scylla_worker,
                           args=(cfg["hosts"], rooms, seconds, q, pid, table,
                                 dedup_mode))
        p.start()
        workers.append(p)

    merged = {"insert": Sample("insert"),
              "idempotency-check": Sample("idempotency-check"),
              "scrollback": Sample("scrollback")}
    for _ in workers:
        for s in q.get():
            merged[s.op].latencies_ms.extend(s.latencies_ms)
    for p in workers:
        p.join()

    total_inserts = len(merged["insert"].latencies_ms)
    print(f"\n== {target}  procs={procs}  rooms={rooms_n}  {seconds:.0f}s ==")
    print(f"{'throughput':<22} {total_inserts / seconds:>10,.0f} inserts/s")
    for s in merged.values():
        print(s.report())
    print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", choices=sorted(TARGETS))
    ap.add_argument("--procs", default="4",
                    help="comma-separated: sweep process counts, e.g. 1,2,4,8")
    ap.add_argument("--rooms", type=int, default=1000)
    ap.add_argument("--duration", default="600",
                    help="seconds, or 5m")
    ap.add_argument("--table", default="messages")
    ap.add_argument("--dedup", default="lwt", choices=["lwt", "redis", "none"])
    a = ap.parse_args()

    secs = float(a.duration[:-1]) * 60 if a.duration.endswith("m") else float(a.duration)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..",
        "12-postgres-message-store", "code"))

    for procs in (int(p) for p in a.procs.split(",")):
        run(a.target, procs, a.rooms, secs, a.table, a.dedup)


if __name__ == "__main__":
    mp.set_start_method("spawn")     # NOT fork: driver reactor threads again
    main()
