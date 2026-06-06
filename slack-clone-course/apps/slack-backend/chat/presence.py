"""
Redis-backed presence, rate limiting, and unread counts.

These are all ephemeral / hot-path concerns that don't belong in Postgres:
- Presence: who's online *right now* (expires automatically if a client stops heartbeating).
- Rate limiting: cap how fast a socket can send.
- Unread counts: cheap reads backed by a cached "latest message id per channel".
"""
import time

import redis
from django.conf import settings

# One shared connection pool for the process.
_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

ONLINE_KEY = "presence:online"      # sorted set: member=user_id, score=last_seen_ts
PRESENCE_TTL = 30                   # seconds; a client heartbeats well within this


# ── Presence ──────────────────────────────────────────────────────────────────
def touch(user_id: int) -> None:
    """Mark a user online now. Call on connect and on every heartbeat."""
    _redis.zadd(ONLINE_KEY, {str(user_id): time.time()})


def go_offline(user_id: int) -> None:
    """Explicitly drop a user (called on disconnect)."""
    _redis.zrem(ONLINE_KEY, str(user_id))


def is_online(user_id: int) -> bool:
    score = _redis.zscore(ONLINE_KEY, str(user_id))
    return score is not None and score > time.time() - PRESENCE_TTL


def online_among(user_ids) -> set[int]:
    """Of the given user ids, which are currently online?"""
    cutoff = time.time() - PRESENCE_TTL
    # Prune stale entries occasionally, then read the fresh ones.
    _redis.zremrangebyscore(ONLINE_KEY, 0, cutoff)
    fresh = {int(m) for m in _redis.zrangebyscore(ONLINE_KEY, cutoff, "+inf")}
    return fresh & set(user_ids)


# ── Rate limiting ─────────────────────────────────────────────────────────────
def allow(bucket: str, limit: int, window: int) -> bool:
    """Fixed-window limiter: allow up to `limit` actions per `window` seconds.
    Returns False when the caller has exceeded the budget."""
    key = f"rl:{bucket}"
    count = _redis.incr(key)
    if count == 1:
        _redis.expire(key, window)
    return count <= limit


# ── Unread counts ─────────────────────────────────────────────────────────────
# Message ids are a *global* sequence, so "head − last_read" is NOT a count. We use
# the cached head only for a cheap "is there anything new?" boolean, and cache the
# exact COUNT (invalidated when a new message arrives).
def set_channel_head(channel_id: int, message_id: int) -> None:
    """Remember the newest message id in a channel; bust cached unread counts."""
    _redis.set(f"chan:head:{channel_id}", message_id)
    # New message → any cached unread counts for this channel are stale.
    for key in _redis.scan_iter(f"unread:{channel_id}:*"):
        _redis.delete(key)


def channel_head(channel_id: int) -> int:
    val = _redis.get(f"chan:head:{channel_id}")
    return int(val) if val else 0


def has_unread(channel_id: int, last_read_id: int) -> bool:
    """Cheap boolean: is the newest message newer than what the user has read?"""
    return channel_head(channel_id) > last_read_id


def unread_count(channel_id: int, last_read_id: int) -> int:
    """Exact unread count, cached in Redis and busted on each new message."""
    key = f"unread:{channel_id}:{last_read_id}"
    cached = _redis.get(key)
    if cached is not None:
        return int(cached)
    from .models import Message  # lazy import to avoid a circular import

    count = Message.objects.filter(channel_id=channel_id, id__gt=last_read_id).count()
    _redis.set(key, count, ex=300)   # short TTL as a safety net
    return count
