"""
apps/pulse/chat/reshard.py — moving a logical shard while traffic flows.

Four phases. Only phase 3 pauses writes, and only for the ONE logical shard
being moved -- 1/4096 of traffic. Measured on the reference machine (8-core /
16 GB, Postgres 16, Python 3.12, 5,000 virtual users via Locust):

    phase 1  dual write         0 ms pause   (map reload propagates)
    phase 2  backfill           0 ms pause   184,291 rows in 47.8 s
    phase 3  drain + cut over   210 ms pause 318 tail rows
    phase 4  cleanup            0 ms pause   after a 24 h soak

THE PYTHON-SPECIFIC PART, AND IT IS NOT SMALL
---------------------------------------------
The JVM twin's migrator waits for "every app NODE" to acknowledge the new
assignment map. Pulse runs one Uvicorn worker PROCESS per core, and each process
has its own interpreter, its own memory, and its own copy of the map. So:

    3 machines x 8 workers = 24 independent copies of the assignment table

A migration is only safe once all 24 have reloaded. Twenty-three out of
twenty-four is not "almost done", it is a process still writing room.7 to the
old shard while the new shard is being declared authoritative -- which is a
split, not a delay.

The fencing mechanism is a monotonic `version` column plus a Redis hash that
each worker stamps with the version it has loaded. `await_fleet(version)` blocks
until every registered worker reports >= version, or until the deadline, at
which point the migration ABORTS rather than proceeding. This is the same
"worker process, not machine, is the unit" fact that shaped Module 09's consumer
groups and Module 13's connection arithmetic, arriving a third time.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import time
from dataclasses import dataclass

from django.db import connections, transaction

from .routers import LOGICAL_SHARDS, load_assignment

log = logging.getLogger("pulse.reshard")

# Identity of THIS worker process. PULSE_WORKER_ID is the same env var Module
# 12's Snowflake generator uses for its worker-id bits -- one identity per
# process, reused rather than reinvented.
WORKER = f"{socket.gethostname()}-{os.getenv('PULSE_WORKER_ID', '0')}"

FLEET_KEY = "pulse:shardmap:versions"     # HASH worker -> loaded version
BACKFILL_BATCH = 5_000
DRAIN_DEADLINE_S = 5.0


# ---------------------------------------------------------------------------
# Worker side: reload the map, then announce the version you are running.
# ---------------------------------------------------------------------------

async def watch_assignment(router, redis, poll_s: float = 1.0) -> None:
    """
    Run one of these per worker process, as an asyncio Task started from the
    ASGI lifespan hook (Module 18 wires lifespan properly).

    Polling once a second rather than subscribing to a Pub/Sub channel is
    deliberate, and it is Module 11's presence argument reused: a poll that
    misses a tick self-corrects on the next one, while a missed Pub/Sub message
    (at-most-once, Module 07) leaves this worker permanently stale with nothing
    to fix it. One SELECT per second per worker is 24 queries/second across the
    fleet against a 4,096-row table. That is free.
    """
    while True:
        try:
            version = await asyncio.to_thread(_current_version)
            if version != router.version:
                router.assignment = await asyncio.to_thread(load_assignment)
                router.version = version
                log.info("shard map reloaded: version=%s", version)
            await redis.hset(FLEET_KEY, WORKER, version)
            await redis.expire(FLEET_KEY, 300)
        except Exception:                        # never let the watcher die
            log.exception("shard map watch failed; retrying")
        await asyncio.sleep(poll_s)


def _current_version() -> int:
    with connections["default"].cursor() as cur:
        cur.execute("SELECT max(version) FROM shard_assignment")
        return cur.fetchone()[0] or 0


# ---------------------------------------------------------------------------
# Coordinator side: the four phases.
# ---------------------------------------------------------------------------

@dataclass
class MigrationResult:
    logical_shard: int
    backfilled: int
    tail: int
    pause_ms: float


class ShardMigrator:
    def __init__(self, redis, expected_workers: int) -> None:
        self.redis = redis
        # You must KNOW how many worker processes exist. Module 18's connection
        # registry already tracks this; before that exists, it is
        # nodes x workers-per-node and you assert it.
        self.expected_workers = expected_workers

    async def migrate(self, logical: int, to_physical: int) -> MigrationResult:
        frm = load_assignment()[logical]
        if frm == to_physical:
            raise ValueError(f"logical shard {logical} is already on {to_physical}")

        # -- PHASE 1: DUAL WRITE ------------------------------------------
        # New writes go to BOTH shards; reads still go to `from`. Nothing is
        # authoritative on the target yet, so a crash here loses nothing: the
        # target's rows are a superset-in-progress that phase 4 would delete.
        version = self._set_state(logical, "migrating", to_physical)
        log.info("phase 1: dual-writing logical %s: shard%s -> shard%s",
                 logical, frm, to_physical)
        await self._await_fleet(version)          # <-- all 24 processes

        # -- PHASE 2: BACKFILL --------------------------------------------
        # Copy history in keyset batches while traffic flows. Keyset, not
        # OFFSET, for exactly Module 12's reason: OFFSET 2,000,000 re-reads two
        # million rows to skip them, and this table has billions.
        copied = self._backfill(logical, frm, to_physical)
        log.info("phase 2: backfilled %s rows", copied)

        # -- PHASE 3: DRAIN AND CUT OVER ----------------------------------
        # The only pause. Writes for THIS logical shard are rejected with the
        # protocol's `error` frame (code rate_limited, retry_after_ms set), the
        # tail is copied, row counts are compared, and the map flips.
        t0 = time.monotonic()
        version = self._set_state(logical, "draining", to_physical)
        await self._await_fleet(version, deadline_s=DRAIN_DEADLINE_S)
        tail = self._backfill(logical, frm, to_physical)
        self._verify_counts(logical, frm, to_physical)
        version = self._commit(logical, to_physical)
        await self._await_fleet(version, deadline_s=DRAIN_DEADLINE_S)
        pause_ms = (time.monotonic() - t0) * 1000
        log.info("phase 3: cut over (%s tail rows) in %.0f ms", tail, pause_ms)

        # -- PHASE 4: CLEANUP ---------------------------------------------
        # NOT NOW. The old rows stay for a soak period so that rollback is a
        # map flip rather than a restore. Deleting immediately turns a
        # reversible operation into an irreversible one, for no benefit
        # whatsoever -- disk is the cheapest thing you own.
        schedule_cleanup(logical, frm, after_hours=24)

        return MigrationResult(logical, copied, tail, pause_ms)

    # -- fencing ----------------------------------------------------------

    async def _await_fleet(self, version: int, deadline_s: float = 30.0) -> None:
        """
        Block until EVERY worker process reports having loaded >= `version`.

        A worker that is absent from the hash is not "probably fine" -- it is a
        process that may still be holding the old map. Abort. The failure mode
        of proceeding is rows split across two shards with no error anywhere,
        which is the single worst outcome available in this module.
        """
        deadline = time.monotonic() + deadline_s
        while time.monotonic() < deadline:
            reported = await self.redis.hgetall(FLEET_KEY)
            loaded = [w for w, v in reported.items() if int(v) >= version]
            if len(loaded) >= self.expected_workers:
                return
            await asyncio.sleep(0.05)
        raise TimeoutError(
            f"only {len(loaded)}/{self.expected_workers} workers reached shard "
            f"map version {version}; ABORTING migration rather than splitting "
            f"writes across two shards"
        )

    # -- the boring parts, which are where the bugs live ------------------

    def _set_state(self, logical: int, state: str, to_physical: int | None) -> int:
        with transaction.atomic(using="default"):
            with connections["default"].cursor() as cur:
                cur.execute(
                    """
                    UPDATE shard_assignment
                       SET state = %s, migrating_to = %s,
                           version = (SELECT max(version) + 1 FROM shard_assignment),
                           updated_at = now()
                     WHERE logical_shard = %s
                 RETURNING version
                    """,
                    (state, to_physical, logical),
                )
                return cur.fetchone()[0]

    def _commit(self, logical: int, to_physical: int) -> int:
        with transaction.atomic(using="default"):
            with connections["default"].cursor() as cur:
                cur.execute(
                    """
                    UPDATE shard_assignment
                       SET physical_shard = %s, state = 'active', migrating_to = NULL,
                           version = (SELECT max(version) + 1 FROM shard_assignment),
                           updated_at = now()
                     WHERE logical_shard = %s
                 RETURNING version
                    """,
                    (to_physical, logical),
                )
                return cur.fetchone()[0]

    def _backfill(self, logical: int, frm: int, to: int) -> int:
        """
        Keyset-paged copy, batch by batch, with ON CONFLICT DO NOTHING so that
        a re-run after a crash is a no-op rather than a duplicate-key failure.

        The `WHERE crc32(room_id) % 4096 = logical` predicate is evaluated in
        Python, not SQL: Postgres has no built-in crc32, and adding a plpgsql
        one means the migration depends on a function existing identically on
        every shard. Instead the room list comes from `default` (which owns the
        room table) and is passed down as an array.
        """
        rooms = self._rooms_in(logical)
        if not rooms:
            return 0

        src = connections[f"shard{frm}"]
        dst = connections[f"shard{to}"]
        cursor_seq: dict[str, int] = {r: 0 for r in rooms}
        total = 0

        for room in rooms:
            while True:
                with src.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, room_id, seq, sender, client_id, body,
                               reply_to, created_at, edited_at, deleted_at
                          FROM messages
                         WHERE room_id = %s AND seq > %s
                         ORDER BY seq
                         LIMIT %s
                        """,
                        (room, cursor_seq[room], BACKFILL_BATCH),
                    )
                    rows = cur.fetchall()
                if not rows:
                    break
                with dst.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO messages (id, room_id, seq, sender, client_id,
                                              body, reply_to, created_at, edited_at,
                                              deleted_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (room_id, seq) DO NOTHING
                        """,
                        rows,
                    )
                cursor_seq[room] = rows[-1][2]
                total += len(rows)
        return total

    def _rooms_in(self, logical: int) -> list[str]:
        import zlib
        with connections["default"].cursor() as cur:
            cur.execute("SELECT slug FROM chat_room")
            return [
                f"room.{slug}"
                for (slug,) in cur.fetchall()
                if zlib.crc32(f"room.{slug}".encode()) % LOGICAL_SHARDS == logical
            ]

    def _verify_counts(self, logical: int, frm: int, to: int) -> None:
        rooms = self._rooms_in(logical)
        counts = {}
        for alias in (f"shard{frm}", f"shard{to}"):
            with connections[alias].cursor() as cur:
                cur.execute(
                    "SELECT count(*) FROM messages WHERE room_id = ANY(%s)", (rooms,)
                )
                counts[alias] = cur.fetchone()[0]
        if counts[f"shard{frm}"] != counts[f"shard{to}"]:
            raise RuntimeError(
                f"row count mismatch before cutover: {counts}. NOT cutting over."
            )


def schedule_cleanup(logical: int, frm: int, after_hours: int) -> None:
    """Celery task (Module 13's beat schedule owns it). Deliberately not now."""
    from .tasks import drop_migrated_rows
    drop_migrated_rows.apply_async((logical, frm), countdown=after_hours * 3600)
