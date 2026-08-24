#!/usr/bin/env python3
"""
code/replica_lag.py — sample streaming replication lag from both ends.

    python code/replica_lag.py --duration 120 --interval 0.2

Two lags, and the difference between them is where the interesting failures
live:

  SEND lag    (primary side)  pg_current_wal_lsn() - sent_lsn
      How much WAL the primary has produced but not yet handed to the socket.
      Grows when the network is the bottleneck.

  REPLAY lag  (replica side)  now() - pg_last_xact_replay_timestamp()
      How far behind the replica's VISIBLE STATE is. This is the one that
      determines whether a read is stale, and therefore the one your router
      must care about.

A replica can have zero send lag and seconds of replay lag: the WAL arrived and
the startup process is still applying it, usually because a single long
recovery-conflict wait or a big index build is in the stream. Watching only the
primary side would tell you everything is fine while every read is wrong.

⚠️ `pg_last_xact_replay_timestamp()` returns the commit time of the last replayed
   TRANSACTION. On an idle primary it stops moving, so the computed lag grows
   forever even though the replica is perfectly caught up. Always pair it with
   an LSN comparison before you page anyone — this script prints both, and the
   `caught_up` column is the LSN answer.
"""

from __future__ import annotations

import argparse
import statistics
import time

import psycopg

PRIMARY = "postgresql://pulse:pulse@localhost:5432/pulse"
REPLICA = "postgresql://pulse:pulse@localhost:5433/pulse"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=60.0)
    ap.add_argument("--interval", type=float, default=0.2)
    ap.add_argument("--primary", default=PRIMARY)
    ap.add_argument("--replica", default=REPLICA)
    args = ap.parse_args()

    send_bytes: list[int] = []
    replay_ms: list[float] = []
    caught_up = 0
    samples = 0

    with psycopg.connect(args.primary, autocommit=True) as p, \
         psycopg.connect(args.replica, autocommit=True) as r:

        deadline = time.time() + args.duration
        while time.time() < deadline:
            samples += 1
            try:
                row = p.execute("""
                    SELECT coalesce(pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn), 0),
                           coalesce(pg_wal_lsn_diff(sent_lsn, replay_lsn), 0)
                      FROM pg_stat_replication LIMIT 1""").fetchone()
                send_bytes.append(int(row[0]) if row else 0)

                lag, is_current = r.execute("""
                    SELECT coalesce(extract(epoch FROM
                             now() - pg_last_xact_replay_timestamp()), 0) * 1000,
                           pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn()
                    """).fetchone()
                # If receive == replay the replica has applied everything it has,
                # so a large timestamp lag just means the primary is idle.
                if is_current:
                    caught_up += 1
                    replay_ms.append(0.0)
                else:
                    replay_ms.append(float(lag))
            except psycopg.OperationalError as exc:
                # A paused or partitioned replica does not error on SELECT — it
                # answers with stale data. An error here means it is genuinely
                # unreachable, which your router must treat as INFINITE lag, not
                # as "no sample this time".
                print(f"  probe failed: {exc}")
                replay_ms.append(float("inf"))
            time.sleep(args.interval)

    finite = sorted(x for x in replay_ms if x != float("inf"))

    def pct(p: float) -> float:
        return finite[min(len(finite) - 1, int(len(finite) * p))] if finite else 0.0

    print(f"samples            : {samples}")
    print(f"caught up (LSN)    : {caught_up} ({caught_up / max(samples, 1):.1%})")
    print(f"probe failures     : {sum(1 for x in replay_ms if x == float('inf'))}")
    print(f"replay lag p50     : {statistics.median(finite) if finite else 0:8.0f} ms")
    print(f"replay lag p95     : {pct(0.95):8.0f} ms")
    print(f"replay lag p99     : {pct(0.99):8.0f} ms")
    print(f"replay lag p99.9   : {pct(0.999):8.0f} ms")
    print(f"replay lag max     : {max(finite) if finite else 0:8.0f} ms")
    print(f"send backlog max   : {max(send_bytes) if send_bytes else 0:8,d} bytes")


if __name__ == "__main__":
    main()
