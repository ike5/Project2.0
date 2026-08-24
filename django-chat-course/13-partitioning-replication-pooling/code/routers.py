"""
apps/pulse/pulse/routers.py — read/write splitting with a read-your-own-writes
sticky window.

    DATABASES = {
        "default": {... HOST: pgbouncer or pg-primary ...},
        "replica": {... HOST: pg-replica ..., "TEST": {"MIRROR": "default"}},
    }
    DATABASE_ROUTERS = ["pulse.routers.ReplicaRouter"]

THREE TRAPS THIS FILE EXISTS TO AVOID
-------------------------------------
1. `allow_migrate` MUST return False for the replica. Without it, `migrate` runs
   DDL against a read-only standby, fails partway, and leaves `django_migrations`
   on the primary claiming success. Recovering from that by hand is an afternoon.

2. `TEST: {"MIRROR": "default"}` in settings (not here, but you will forget it):
   without it, Django creates a SEPARATE empty test database for `replica`, and
   every test that writes and then reads fails with an empty result — which reads
   like a router bug and is not.

3. The router has NO REQUEST CONTEXT, and in an async consumer there is no
   request at all. `db_for_read` cannot know "this user wrote 40 ms ago" unless
   something puts that fact where the router can see it.

   The mechanism is a `contextvars.ContextVar`, NOT `threading.local()`. This is
   not a style preference:

     * asyncio runs thousands of coroutines on one thread, so a thread-local is
       shared by all of them — user A's sticky window would apply to user B.
     * `database_sync_to_async` hops to a threadpool. asgiref copies the current
       *context* into that thread, so a ContextVar set in the coroutine IS
       visible inside the ORM call. A threading.local set in the coroutine is
       not, because that is a different thread.

   ContextVar is the only one of the two that is correct on both counts.
"""

from __future__ import annotations

import contextvars
import time

from prometheus_client import Counter

# Seconds after a write during which THIS logical actor reads from the primary.
# Sized from the measured replica lag (lab Part C: p50 8 ms, p99 340 ms, p99.9
# 4.2 s under the outbox batch write) with headroom. 5 s covers p99.9; going to
# 30 s would cover every case and would also route most reads to the primary
# during a burst, which defeats the point of having a replica.
STICKY_WINDOW_S = 5.0

_routed = Counter("pulse_db_reads_total", "ORM reads by target", ["target"])

# The whole sticky mechanism: a timestamp, in a ContextVar.
_wrote_at: contextvars.ContextVar[float] = contextvars.ContextVar(
    "pulse_wrote_at", default=0.0
)

# Models that are ALWAYS read from the primary, regardless of stickiness.
# Anything whose staleness is a correctness bug rather than a cosmetic one.
PRIMARY_ONLY = {
    "outbox",       # the relay must not read a stale backlog and skip rows
    "roomsequence", # Module 05's allocator; a stale read hands out a used seq
    "sequencegap",  # Module 10's tombstones gate the resume `to_seq`
}


def mark_write() -> None:
    """Call after any write on behalf of a user. Idempotent, ~100 ns."""
    _wrote_at.set(time.monotonic())


def is_sticky() -> bool:
    return (time.monotonic() - _wrote_at.get()) < STICKY_WINDOW_S


class ReplicaRouter:
    def db_for_read(self, model, **hints):
        if model._meta.model_name in PRIMARY_ONLY:
            _routed.labels(target="primary_only").inc()
            return "default"
        if is_sticky():
            # READ-YOUR-OWN-WRITES. This actor wrote recently; the replica may
            # not have it yet. Chat mostly avoids needing this at all (the sender
            # already has its own message and renders it optimistically), but a
            # SECOND DEVICE has no such advantage — see the README.
            _routed.labels(target="primary_sticky").inc()
            return "default"
        _routed.labels(target="replica").inc()
        return "replica"

    def db_for_write(self, model, **hints):
        mark_write()
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        # Same physical data on both aliases, so cross-alias relations are fine.
        # Returning None here (the "no opinion" answer) would let Django fall
        # back to "only if the _state.db values match", which breaks the moment
        # an object read from the replica is related to one read from the
        # primary — exactly what the sticky window causes.
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # TRAP 1. Never migrate the replica: it is a physical standby and its
        # schema arrives through the WAL.
        return db == "default"


# ---------------------------------------------------------------------------
# Making the sticky window usable from the two places Pulse writes.
# ---------------------------------------------------------------------------

class StickyReadsMiddleware:
    """
    For DRF/HTTP. Each request gets a fresh context, so the window naturally
    scopes to one request... which is USELESS on its own, because the read that
    needs stickiness is in the NEXT request.

    So we persist the marker in the session (or a signed cookie) and restore it
    at the start of the request. This is the honest, boring implementation and it
    is worth seeing: "sticky sessions for reads" is not magic, it is a timestamp
    you carry.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        last = request.session.get("_wrote_at_wall", 0.0)
        if time.time() - last < STICKY_WINDOW_S:
            # Translate wall time into the monotonic clock the router uses.
            _wrote_at.set(time.monotonic() - (time.time() - last))

        response = self.get_response(request)

        if is_sticky():
            request.session["_wrote_at_wall"] = time.time()
        return response


def sticky_for_user(user_id: int, redis_client) -> "AsyncSticky":
    """
    For WebSocket consumers, where there is no session and no request.

    A socket is long-lived and belongs to one user, so the marker can live on
    the consumer instance — but a user's OTHER device is on a different socket,
    possibly a different worker process, and that is the case the sticky window
    actually exists for. Hence Redis:

        SET sticky:{user_id} 1 EX 5     on write
        EXISTS sticky:{user_id}         on read

    One SET per write and one EXISTS per read, both sub-millisecond. The lab
    measures the hit rate (18% of reads fall inside the window under load) and
    the alternative (LSN waiting), and explains why Pulse takes this one.
    """
    return AsyncSticky(user_id, redis_client)


class AsyncSticky:
    def __init__(self, user_id: int, redis_client):
        self.key = f"sticky:{{{user_id}}}"
        self.redis = redis_client

    async def mark(self) -> None:
        await self.redis.set(self.key, "1", ex=int(STICKY_WINDOW_S) + 1)

    async def apply(self) -> None:
        """Call before a read on this user's behalf."""
        if await self.redis.exists(self.key):
            mark_write()      # sets the ContextVar; the router does the rest
