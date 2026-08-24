"""
apps/pulse/chat/sequence.py — atomic per-room sequence allocation + stream append.

Module 09 left `allocate_seq()` as a bare Redis INCR followed by a separate XADD.
Two awaits, two round trips, and two bugs:

  1. GAPS       — INCR succeeds, XADD raises, the sequence number is burned
                  forever. The protocol (Module 05 §2) says `seq` is gapless;
                  a burned number makes every client's gap detector spin.
  2. INVERSIONS — `await` is a yield point, so two coroutines in the same worker
                  can INCR in one order and XADD in the other. Stream order then
                  disagrees with sequence order, and every client sees it.

This module fixes both by making allocation and append a single Lua script.
Redis is single-threaded and a script runs to completion without interleaving
(Module 08), so a sequence number is allocated if and only if the entry is in the
stream, and stream order IS sequence order.

Run this file's self-test with:
    python -m chat.sequence          # requires REDIS_URL to point at a live Redis
"""

from __future__ import annotations

import asyncio
import json
import os
import time

import redis.asyncio as aioredis

# Keep these in sync with Module 09's streams.py.
STREAM_MAXLEN = int(os.environ.get("PULSE_STREAM_MAXLEN", "10000"))

# --------------------------------------------------------------------------
# Keys. Both carry the {room_id} hash tag Module 09 introduced, so they hash to
# the same Redis Cluster slot. Without the tag, this script is illegal under
# Cluster ("CROSSSLOT Keys in request don't hash to the same slot") and you find
# out in Module 18, under load, at the worst possible moment.
# --------------------------------------------------------------------------


def seq_key(room_id: str) -> str:
    return f"room:{{{room_id}}}:seq"


def stream_key(room_id: str) -> str:
    return f"room:{{{room_id}}}:stream"


# --------------------------------------------------------------------------
# The script.
#
# KEYS[1] = seq counter        KEYS[2] = stream
# ARGV[1] = envelope JSON with the literal token __SEQ__ where seq belongs
# ARGV[2] = MAXLEN target
#
# Returns {seq, entry_id}.
#
# Substituting a token into JSON rather than building the JSON in Lua is
# deliberate: cjson.encode in a Redis script does not preserve key order and
# will happily turn an empty object into an empty array. Do the encoding in
# Python where you control it, and let Lua do one string replace.
# --------------------------------------------------------------------------
SEQ_AND_APPEND = """
local seq = redis.call('INCR', KEYS[1])
local payload = string.gsub(ARGV[1], '__SEQ__', tostring(seq), 1)
local entry_id = redis.call('XADD', KEYS[2], 'MAXLEN', '~', ARGV[2], '*',
                            'payload', payload)
return {seq, entry_id}
"""

# The recovery script, used exactly once per room per Redis lifetime. See
# `SequenceAllocator.recover_high_water_mark`.
SET_IF_LOWER = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local floor = tonumber(ARGV[1])
if current < floor then
    redis.call('SET', KEYS[1], floor)
    return floor
end
return current
"""


class SequenceAllocator:
    """Owns the per-room sequence counter and the atomic send path."""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        # register_script() uses EVALSHA with an automatic EVAL fallback, so a
        # Redis restart (which clears the script cache) self-heals instead of
        # raising NOSCRIPT at 3 a.m.
        self._seq_and_append = self.redis.register_script(SEQ_AND_APPEND)
        self._set_if_lower = self.redis.register_script(SET_IF_LOWER)
        self._recovered: set[str] = set()

    async def send(self, room_id: str, envelope: dict) -> tuple[int, str]:
        """
        Allocate a seq and append the envelope to the room's stream, atomically.

        `envelope["data"]["seq"]` must be the string "__SEQ__" on the way in; it
        comes back as an int in the returned tuple and inside the stream entry.
        """
        assert envelope["data"]["seq"] == "__SEQ__", "seq placeholder missing"

        await self._ensure_recovered(room_id)

        payload = json.dumps(envelope, separators=(",", ":"))
        seq, entry_id = await self._seq_and_append(
            keys=[seq_key(room_id), stream_key(room_id)],
            args=[payload, STREAM_MAXLEN],
        )
        return int(seq), entry_id

    # ----------------------------------------------------------------------
    # High-water-mark recovery.
    #
    # compose.dev.yml runs Redis with `--save "" --appendonly no`. That is a
    # deliberate choice (see infra/README.md) and it has exactly one consequence
    # you must handle explicitly: a Redis restart loses every seq counter, and
    # the next INCR returns 1.
    #
    # Without this recovery, every room restarts its sequence at 1. Every client
    # sees a catastrophic backwards jump, every resume request returns the whole
    # room history, and `UNIQUE (room_id, seq)` starts rejecting inserts for
    # sequence numbers that already exist. It is the single nastiest failure mode
    # in this design.
    # ----------------------------------------------------------------------
    async def _ensure_recovered(self, room_id: str) -> None:
        if room_id in self._recovered:
            return
        await self.recover_high_water_mark(room_id)
        self._recovered.add(room_id)

    async def recover_high_water_mark(self, room_id: str) -> int:
        """
        Raise the Redis counter to at least max(seq) in the durable store.

        Idempotent (SET_IF_LOWER never lowers it) and safe to run concurrently
        from every worker process, which matters because all eight of them will
        do it within milliseconds of a Redis restart.
        """
        known = await _max_seq_in_store(room_id)
        if known == 0:
            return 0
        value = await self._set_if_lower(keys=[seq_key(room_id)], args=[known])
        return int(value)


async def _max_seq_in_store(room_id: str) -> int:
    """max(seq) for a room, from Postgres. Isolated so the lab can monkeypatch it."""
    from channels.db import database_sync_to_async
    from django.db import connection

    @database_sync_to_async
    def _query() -> int:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT coalesce(max(m.seq), 0) FROM chat_message m "
                "JOIN chat_room r ON r.id = m.room_id WHERE r.slug = %s",
                [room_id.removeprefix("room.")],
            )
            return int(cur.fetchone()[0])

    return await _query()


# --------------------------------------------------------------------------
# Self-test: prove the atomicity claim rather than asserting it.
# --------------------------------------------------------------------------
async def _selftest(concurrency: int = 64, per_task: int = 200) -> None:
    r = aioredis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )
    room = "room.selftest"
    await r.delete(seq_key(room), stream_key(room))

    alloc = SequenceAllocator(r)
    alloc._recovered.add(room)  # skip the Postgres round trip in the self-test

    async def sender(n: int) -> None:
        for i in range(per_task):
            await alloc.send(
                room,
                {
                    "v": 1,
                    "type": "message.new",
                    "room": room,
                    "ts": int(time.time() * 1000),
                    "data": {
                        "id": n * 100000 + i,
                        "client_id": f"c-{n}-{i}",
                        "seq": "__SEQ__",
                        "sender": f"u{n}",
                        "body": "x",
                        "reply_to": None,
                    },
                },
            )

    started = time.perf_counter()
    await asyncio.gather(*(sender(n) for n in range(concurrency)))
    elapsed = time.perf_counter() - started

    entries = await r.xrange(stream_key(room), "-", "+")
    seqs = [json.loads(fields["payload"])["data"]["seq"] for _id, fields in entries]

    inversions = sum(1 for a, b in zip(seqs, seqs[1:]) if b < a)
    expected = concurrency * per_task
    gaps = [s for s in range(1, expected + 1) if s not in set(seqs)]

    print(f"sent        : {expected}")
    print(f"in stream   : {len(seqs)}")
    print(f"inversions  : {inversions}")
    print(f"gaps        : {len(gaps)}")
    print(f"throughput  : {expected / elapsed:,.0f} sends/s")
    await r.aclose()


if __name__ == "__main__":
    asyncio.run(_selftest())
