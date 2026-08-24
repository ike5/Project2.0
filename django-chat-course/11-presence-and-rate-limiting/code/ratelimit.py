"""
apps/pulse/chat/ratelimit.py — the six-tier limiter.

Design notes that are not obvious from the code:

* ONE TIER IS NEVER ENOUGH. A per-user limit is bypassed with more accounts, a
  per-IP limit with more hosts, a per-room limit with more rooms. Each tier below
  closes a dimension the others leave open, and the per-room tier is the one
  people forget — it is the only one that protects a room's *other* members from
  a flood that is individually within every per-user limit.

* CHECK CHEAP TIERS FIRST, and short-circuit. The connection tier is one key; the
  message tiers are four. Denying early saves round trips on exactly the traffic
  you least want to spend round trips on.

* THE TIERS ARE NOT ATOMIC WITH EACH OTHER, ON PURPOSE. Under Redis Cluster a Lua
  script may only touch one hash slot, and `rl:msg:{user}` and `rl:room:{room}`
  hash differently. You could force every limiter key into one slot with a fixed
  tag (`{rl}`) and check all four atomically — at the cost of routing 100% of
  limiter traffic to one Cluster node. We take the extra round trips instead:
  0.19 ms versus 0.11 ms, and cross-tier atomicity buys nothing anyway because
  the tiers answer independent questions.

* DENY DOES NOT MEAN DISCONNECT. Protocol §4: an `error` frame MUST NOT close the
  connection. Closing costs a handshake, an auth check, a group_add and a resume —
  answering "too much traffic" with "here, have some more". Escalation to close
  code 4429 is Module 21's job, with Module 21's evidence.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import redis.asyncio as aioredis
from prometheus_client import Counter, Gauge

_LUA = (Path(__file__).parent / "lua" / "ratelimit.lua").read_text()

_denied = Counter("pulse_ratelimit_denied_total", "requests denied", ["tier"])
_allowed = Counter("pulse_ratelimit_allowed_total", "requests allowed", ["tier"])
_tokens = Gauge("pulse_ratelimit_tokens", "tokens left at last check", ["tier"])


@dataclass(frozen=True)
class Tier:
    name: str
    capacity: float       # max burst
    refill_per_s: float   # sustained rate
    cost: float = 1.0


# The six tiers. Every number here is a product decision, not a technical one —
# write them down where a product person can argue with them.
TIERS = {
    # Handshake. 10/min per IP stops a reconnect storm from a single host without
    # touching a legitimate user, who reconnects a handful of times an hour.
    "conn": Tier("conn", capacity=10, refill_per_s=10 / 60),
    # The obvious one. 20 burst lets someone paste three messages and hit enter
    # four times; 5/s sustained is far above human typing and far below a script.
    "msg_user_room": Tier("msg_user_room", capacity=20, refill_per_s=5),
    # Global per user: stops spraying one message across 100 rooms, which every
    # per-room limit in the world would happily allow.
    "msg_user": Tier("msg_user", capacity=40, refill_per_s=10),
    # Per IP: one host running 500 accounts is 500 users under every per-user tier.
    "msg_ip": Tier("msg_ip", capacity=100, refill_per_s=20),
    # Per room: protects the other 199 members from one flood.
    "msg_room": Tier("msg_room", capacity=500, refill_per_s=200),
    # Resume is the most expensive thing a client can ask for (Module 10). Give it
    # its own bucket: 5 in a burst covers a genuine reconnect; 1 per 10 s does not
    # cover a loop.
    "resume": Tier("resume", capacity=5, refill_per_s=0.1),
}


class TokenBucket:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        # register_script() → EVALSHA with automatic EVAL fallback, so a Redis
        # restart (which empties the script cache) self-heals instead of raising
        # NOSCRIPT under load.
        self._script = self.redis.register_script(_LUA)

    async def take(self, tier: Tier, key: str) -> tuple[bool, int]:
        """Returns (allowed, retry_after_ms)."""
        allowed, retry_after_ms, tokens_x1000 = await self._script(
            keys=[key], args=[tier.capacity, tier.refill_per_s, tier.cost]
        )
        _tokens.labels(tier=tier.name).set(tokens_x1000 / 1000.0)
        if allowed:
            _allowed.labels(tier=tier.name).inc()
        else:
            _denied.labels(tier=tier.name).inc()
        return bool(allowed), int(retry_after_ms)


class Limiter:
    """Composes the tiers for the two call sites that need them."""

    def __init__(self, bucket: TokenBucket):
        self.bucket = bucket
        self.enabled = os.environ.get("PULSE_RATELIMIT", "1") == "1"

    async def allow_connection(self, ip: str) -> tuple[bool, int, str | None]:
        if not self.enabled:
            return True, 0, None
        ok, retry = await self.bucket.take(TIERS["conn"], f"rl:conn:{{{ip}}}")
        return ok, retry, None if ok else "conn"

    async def allow_message(
        self, user_id: int, room_key: str, ip: str
    ) -> tuple[bool, int, str | None]:
        """
        Cheapest and most specific tier first. Short-circuiting matters: a user
        who is flooding is denied after ONE round trip, not four, which is exactly
        the traffic you least want to spend round trips on.
        """
        if not self.enabled:
            return True, 0, None

        checks = [
            (TIERS["msg_user_room"], f"rl:msg:{{{user_id}}}:{room_key}"),
            (TIERS["msg_user"], f"rl:msg:{{{user_id}}}"),
            (TIERS["msg_ip"], f"rl:ip:{{{ip}}}"),
            (TIERS["msg_room"], f"rl:room:{{{room_key}}}"),
        ]
        for tier, key in checks:
            ok, retry = await self.bucket.take(tier, key)
            if not ok:
                return False, retry, tier.name
        return True, 0, None

    async def allow_resume(self, user_id: int, room_key: str) -> tuple[bool, int, str | None]:
        if not self.enabled:
            return True, 0, None
        ok, retry = await self.bucket.take(
            TIERS["resume"], f"rl:resume:{{{user_id}}}:{room_key}"
        )
        return ok, retry, None if ok else "resume"


# ---------------------------------------------------------------------------
# The consumer side. Note what this does NOT do: close the socket.
# ---------------------------------------------------------------------------
async def deny(consumer, room_key: str, tier: str, retry_after_ms: int,
               client_id: str | None) -> None:
    """Emit protocol §4's rate_limited error frame."""
    data = {
        "code": "rate_limited",
        "message": f"rate limit exceeded ({tier})",
        "retry_after_ms": retry_after_ms,
    }
    if client_id:
        # So a client with several messages in flight marks the RIGHT bubble
        # failed. Without it the UI has to guess, and it guesses wrong.
        data["client_id"] = client_id
    await consumer.send_json(
        {"v": 1, "type": "error", "room": room_key,
         "ts": consumer.now_ms(), "data": data}
    )
