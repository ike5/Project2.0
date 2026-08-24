"""
apps/pulse/chat/presence.py — TTL presence on a sorted set, computed per worker.

THE DATA STRUCTURE, AND WHY NOT THE OBVIOUS ONES
------------------------------------------------
Per-room ZSET:  member = username, score = expiry timestamp in ms.

    ZADD              room:{room.7}:presence  <now+30000>  alice     O(log N)
    ZREMRANGEBYSCORE  room:{room.7}:presence  -inf  <now>             O(log N + M)
    ZRANGE            room:{room.7}:presence  0 -1                    O(log N + M)

Rejected:

  * One key per user with a TTL (`SET presence:alice EX 30`). Reading a room's
    roster then needs N round trips or an MGET over a member list you do not
    have — and finding "who is in this room" needs SCAN or KEYS, which Module 08
    taught you never to run against a live Redis. (The lab measures `KEYS
    presence:*` at 41 ms of stall with 20,000 keys.)
  * A per-room SET plus per-user TTL keys. Now the SET and the TTLs can disagree,
    and the SET has no self-cleaning property — which was the entire reason to
    use TTLs.

The ZSET keeps the expiry IN the collection you have to read anyway, so cleanup
is a side effect of reading. That is the property to look for when you are
choosing a Redis structure: does the read do the maintenance for free?

WHY EVERY WORKER COMPUTES THE SAME ANSWER
-----------------------------------------
The naive design broadcasts presence changes across workers. That is O(users ×
rooms × members) frames — the presence storm, 2.3M msg/s in the lab.

Instead each worker, once a second, reads the roster for the rooms IT serves and
sends `presence.update` only to ITS OWN sockets. Eight workers do eight identical
cheap reads instead of one worker doing an expensive fan-out, which is the
process-per-core model working *for* you for once. It also cannot get
permanently stuck: a worker that misses a tick is correct again on the next one,
where an event-driven design stays wrong until something else happens.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import time

import redis.asyncio as aioredis
from prometheus_client import Counter, Gauge, Histogram

from .registry import registry  # Module 09

log = logging.getLogger("pulse.presence")

HEARTBEAT_S = 10           # protocol §3.4 — the client's ping interval
PRESENCE_TTL_S = 30        # 3 missed beats. 2x flaps on one lost frame; 6x
                           # leaves a crashed node's users green for a minute.
SWEEP_INTERVAL_S = 1.0     # aggregation window: outbound depends on TIME, not
                           # on the number of changes. A hard bound on the worst
                           # case is worth more than a better average.
MAX_MEMBERS = int(os.environ.get("PULSE_PRESENCE_MAX_MEMBERS", "500"))

_presence_frames = Counter("pulse_presence_frames_total", "presence.update sent")
_presence_sweeps = Counter("pulse_presence_sweeps_total", "roster sweeps run")
_presence_online = Gauge("pulse_presence_online", "online members", ["room"])
_sweep_seconds = Histogram("pulse_presence_sweep_seconds", "one sweep of one room")


def presence_key(room_key: str) -> str:
    # {room_key} hash tag: same Cluster slot as the room's stream and seq counter
    # (Modules 09 and 10), so a future script may touch them together.
    return f"room:{{{room_key}}}:presence"


class PresenceTracker:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self._announced: dict[str, set[str]] = {}
        self._task: asyncio.Task | None = None

    # ---------------------------------------------------------------- write

    async def touch(self, room_key: str, username: str) -> None:
        """
        Called on connect and on every heartbeat. One ZADD; the score IS the
        expiry, so there is no separate cleanup path to forget.
        """
        expires_at_ms = int((time.time() + PRESENCE_TTL_S) * 1000)
        await self.redis.zadd(presence_key(room_key), {username: expires_at_ms})

    async def leave(self, room_key: str, username: str) -> None:
        """
        Best-effort fast path for a GRACEFUL disconnect. Its only job is to make
        the green dot disappear in 50 ms instead of 30 s.

        It is explicitly NOT the mechanism — if this never runs (kill -9, OOM,
        an exception inside disconnect(), a NAT eviction), the score expires and
        the sweep removes the user anyway. Any cleanup that depends on a graceful
        event is a leak; this one is an optimization on top of a design that does
        not need it.
        """
        with contextlib.suppress(Exception):
            await self.redis.zrem(presence_key(room_key), username)

    # ----------------------------------------------------------------- read

    async def roster(self, room_key: str) -> list[str]:
        key = presence_key(room_key)
        now_ms = int(time.time() * 1000)
        # Cleanup is a side effect of the read. No sweeper job, no lock, no
        # "who is responsible for expiring this" question.
        pipe = self.redis.pipeline(transaction=False)
        pipe.zremrangebyscore(key, "-inf", now_ms)
        pipe.zrange(key, 0, -1)
        _removed, members = await pipe.execute()
        return list(members)

    # ---------------------------------------------------------------- sweep

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._sweep_forever())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _sweep_forever(self) -> None:
        while True:
            try:
                await self._sweep_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.warning("presence sweep failed", exc_info=True)
            await asyncio.sleep(SWEEP_INTERVAL_S)

    async def _sweep_once(self) -> None:
        for room_key in registry.active_rooms():
            with _sweep_seconds.time():
                await self._sweep_room(room_key)
        _presence_sweeps.inc()

    async def _sweep_room(self, room_key: str) -> None:
        members = await self.roster(room_key)
        _presence_online.labels(room=room_key).set(len(members))

        # SUPPRESSION. Nobody meaningfully consumes the online status of 500
        # people; above the threshold the green dots are decoration that costs
        # 500 x members frames per change. Say so in the design doc rather than
        # treating it as a bug you did not get to.
        if len(members) > MAX_MEMBERS:
            return

        current = set(members)
        previous = self._announced.get(room_key, set())
        if current == previous:
            return  # NOTHING CHANGED — the single biggest saving in this file

        self._announced[room_key] = current
        joined = sorted(current - previous)
        left = sorted(previous - current)

        envelope = {
            "v": 1,
            "type": "presence.update",
            "room": room_key,
            "ts": int(time.time() * 1000),
            # `online` is the full roster because a client that missed an update
            # must be able to resynchronize from any single frame — the same
            # reason a video codec sends keyframes. `joined`/`left` are additive
            # optional keys (protocol §1) so a client can animate the delta.
            "data": {"online": sorted(current), "joined": joined, "left": left},
        }

        # Local sockets only. No group_send, no cross-worker fan-out: every other
        # worker is computing this same answer from the same ZSET.
        for sub in registry.subscribers(room_key):
            await sub.send_json(envelope)
            _presence_frames.inc()

    def forget(self, room_key: str) -> None:
        """Called when this worker loses its last subscriber for a room."""
        self._announced.pop(room_key, None)
        _presence_online.remove(room_key)
