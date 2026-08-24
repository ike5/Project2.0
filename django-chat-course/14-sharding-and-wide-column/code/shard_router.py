"""
apps/pulse/pulse/routers.py (Module 14 half) — application-level sharding of
`chat_message` behind Django's DATABASE_ROUTERS hook.

    DATABASES = {
        "default": {... rooms, users, memberships, outbox, shard_assignment ...},
        "replica": {... Module 13's standby, TEST: {"MIRROR": "default"} ...},
        "shard0":  {... HOST: localhost, PORT: 5440 ...},
        "shard1":  {... PORT: 5441 ...},
        "shard2":  {... PORT: 5442 ...},
        "shard3":  {... PORT: 5443 ...},
    }
    DATABASE_ROUTERS = [
        "pulse.routers.ShardRouter",      # <-- FIRST. This file.
        "pulse.routers.ReplicaRouter",    # <-- Module 13. Everything else.
    ]

ORDER MATTERS. Django asks each router in list order and takes the first
non-None answer. ShardRouter answers ONLY for sharded models and returns None
for everything else, so ReplicaRouter still does read/write splitting for rooms,
memberships and the outbox exactly as Module 13 built it. A router that returns
a string for a model it does not own silently steals that model.

THE FOUR THINGS THIS FILE EXISTS TO GET RIGHT
---------------------------------------------
1. LOGICAL SHARDS, not `hash % physical`. 4096 logical shards mapped onto N
   physical databases through a table. Growing 4 -> 6 moves 1,364 of 4,096
   logical shards (33.3%, the theoretical minimum) instead of 66.6% of every
   room. The hash NEVER changes; only the mapping does.

2. A SPECIFIED HASH. zlib.crc32 over the UTF-8 bytes of `Room.key`, because it
   is a published algorithm with a fixed answer in every language. Python's
   built-in hash() is randomized per process by PYTHONHASHSEED and would put the
   same room on a different shard in every worker -- a bug that looks like data
   loss and reproduces on nothing.

3. THE ROUTER CANNOT SEE THE QUERY. `db_for_read(model, **hints)` receives no
   WHERE clause, because Django picks the database before compiling the SQL. So
   the room travels in a ContextVar (NOT threading.local -- asyncio shares one
   thread across thousands of coroutines, and database_sync_to_async copies the
   *context* into its threadpool worker but not thread-locals). Same mechanism
   and the same reasoning as Module 13's sticky-read window.

4. WHEN THE ROOM IS MISSING, RAISE. A Message query with no room in scope would
   otherwise silently hit `default`, find no table (or an empty one), and return
   a blank scrollback page for whichever rooms happen to hash elsewhere. Loud in
   development beats a silent 25% read failure in production.
"""

from __future__ import annotations

import contextlib
import contextvars
import zlib
from typing import Iterator

from django.db import connections

# ---------------------------------------------------------------------------
# The one number you may never change.
# ---------------------------------------------------------------------------
# 4096 logical shards. Chosen once, at the point where the cost of being wrong
# is a config edit rather than a migration. It must be:
#   * large enough that 4096 / N_physical stays granular at your largest planned
#     N (4096 / 64 = 64 logical shards per database is still fine),
#   * a power of two, so `logical % N` is exact for power-of-two N and the
#     rebalance planner's arithmetic is easy to reason about,
#   * fixed FOREVER. Changing it rehashes every room, which is the migration
#     logical shards exist to avoid.
# Redis Cluster picked 16384 for the same reasons and has never changed it.
LOGICAL_SHARDS = 4096

# Models that live on the sharded tier. Everything else -> None -> ReplicaRouter.
# `message` is Module 12's managed=False model over the raw `messages` table.
SHARDED_MODELS = {"message"}

# Set by room_scope(). Holds a Room.key ("room.7"), never a bare slug.
_room: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "pulse_shard_room", default=None
)


class ShardRoutingError(RuntimeError):
    """A sharded model was queried with no room in scope. Always a bug."""


@contextlib.contextmanager
def room_scope(room_key: str) -> Iterator[None]:
    """
    Declare which room the enclosed ORM work belongs to.

        with room_scope(room.key):
            rows = Message.objects.filter(room_id=room.key, id__lt=cursor)[:50]

    Survives `await` and survives database_sync_to_async's threadpool hop,
    because ContextVars are copied into the child context and thread-locals are
    not. Costs ~200 ns.
    """
    if not room_key.startswith("room."):
        # The composed key is the shard key. Hashing a bare slug puts the room
        # on a different shard than the one its messages were written to, and
        # the symptom is an empty room rather than an error.
        raise ShardRoutingError(
            f"room_scope() wants a Room.key like 'room.7', got {room_key!r}"
        )
    token = _room.set(room_key)
    try:
        yield
    finally:
        _room.reset(token)


def logical_shard_for(room_key: str) -> int:
    """
    CRC32 over UTF-8, mod 4096. Specified, stable across processes, Python
    versions, and languages -- which matters, because Module 16's Kafka producer
    and any future Go service must agree with this function about where
    'room.7' lives.

        >>> logical_shard_for("room.7")
        3824
        >>> logical_shard_for("room.general")
        2980

    Those two values are arithmetic, not measurements. If yours differ, you have
    hashed the wrong string -- almost always the bare slug.
    """
    return zlib.crc32(room_key.encode("utf-8")) % LOGICAL_SHARDS


class ShardRouter:
    """
    Reads the logical -> physical map once at import and on demand.

    `assignment` is a plain list, swapped by whole-object replacement rather
    than mutated in place. CPython list assignment is atomic under the GIL, so a
    reader either sees the entire old map or the entire new one -- never a
    half-updated one. That is the cheapest correct concurrency primitive
    available here, and it is worth knowing you have it.
    """

    def __init__(self) -> None:
        self.assignment: list[int] = load_assignment()

    # -- the Django hooks ---------------------------------------------------

    def _alias(self, model, hints) -> str | None:
        if model._meta.model_name not in SHARDED_MODELS:
            return None                       # not ours -> ReplicaRouter decides

        # On writes Django hands us the instance, which knows its own room.
        instance = hints.get("instance")
        room_key = getattr(instance, "room_id", None) or _room.get()

        if room_key is None:
            raise ShardRoutingError(
                f"{model.__name__} query with no room in scope. Wrap it in "
                f"room_scope(room.key), or pass hints={{'instance': msg}}."
            )
        return f"shard{self.assignment[logical_shard_for(room_key)]}"

    def db_for_read(self, model, **hints):
        return self._alias(model, hints)

    def db_for_write(self, model, **hints):
        return self._alias(model, hints)

    def allow_relation(self, obj1, obj2, **hints):
        # Two Messages on the same shard may relate (reply_to). A Message and a
        # Room may not -- they are on different databases and Django is right to
        # refuse. This is why Module 12 gave `messages` a plain `room_id text`
        # column and NOT a ForeignKey: the schema decision that made sharding
        # possible was made two modules before anyone sharded.
        dbs = {obj1._state.db, obj2._state.db}
        if len(dbs) == 1:
            return True
        if any(db and db.startswith("shard") for db in dbs):
            return False
        return None                            # no opinion -> ReplicaRouter

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        is_shard = db.startswith("shard")
        is_sharded_model = model_name in SHARDED_MODELS

        if is_shard:
            # ONLY the message table goes on a shard. Letting django_migrations'
            # other apps (auth, sessions, contenttypes) land here would create
            # four divergent copies of your user table, which is the single
            # fastest way to make a sharded system unrecoverable.
            return is_sharded_model
        if is_sharded_model:
            return False                       # never on default or replica
        return None                            # ReplicaRouter's rule applies


# ---------------------------------------------------------------------------
# The assignment map: the only mutable part of the scheme.
# ---------------------------------------------------------------------------
#   CREATE TABLE shard_assignment (
#       logical_shard  int  PRIMARY KEY,
#       physical_shard int  NOT NULL,
#       state          text NOT NULL DEFAULT 'active',  -- active|migrating|draining
#       migrating_to   int,
#       version        bigint NOT NULL DEFAULT 1,
#       updated_at     timestamptz NOT NULL DEFAULT now()
#   );
#
# It lives on `default`, alongside rooms and memberships. It is small (4,096
# rows), read constantly, and written only during a reshard.
# ---------------------------------------------------------------------------

def load_assignment(using: str = "default") -> list[int]:
    """Load logical -> physical as a dense list. ~1 ms; called at startup."""
    out = [0] * LOGICAL_SHARDS
    with connections[using].cursor() as cur:
        cur.execute(
            "SELECT logical_shard, physical_shard FROM shard_assignment"
        )
        for logical, physical in cur.fetchall():
            out[logical] = physical
    return out


def plan_rebalance(assignment: list[int], new_n: int) -> dict[int, int]:
    """
    Minimal-movement rebalance: which logical shards must move, and where.

    Returns {logical_shard: new_physical}. Its size is the number of shards that
    move, and for a balanced starting map it hits the theoretical minimum:

        4 -> 6   1,364 of 4,096   (33.3%  ==  1 - 4/6)
        4 -> 8   2,048 of 4,096   (50.0%  ==  1 - 4/8)
        8 -> 12  1,364 of 4,096   (33.3%  ==  1 - 8/12, rounded down by the
                                   uneven 4096/12 split)

    Compare with naive `crc32(room) % N`, measured over 200,000 room keys:

        4 -> 5   79.8% of ROOMS move   (minimum 20.0%)
        4 -> 6   66.6%                 (minimum 33.3%)
        4 -> 7   85.8%                 (minimum 42.9%)
        4 -> 8   50.0%                 (minimum 50.0%)   <-- the lucky case

    Doubling is the only growth step where naive modulo is optimal. A team that
    has only ever doubled has never discovered it has a problem.
    """
    old_n = max(assignment) + 1
    if new_n <= old_n:
        raise ValueError("shrinking is a different, harder plan -- see challenge 2")

    base, extra = divmod(LOGICAL_SHARDS, new_n)
    target = [base + (1 if i < extra else 0) for i in range(new_n)]

    held: dict[int, list[int]] = {p: [] for p in range(new_n)}
    for logical, physical in enumerate(assignment):
        held[physical].append(logical)

    # Take from over-full shards, give to under-full ones. Taking from the END
    # of each donor's list keeps low logical shards where they are, which makes
    # the plan stable across reruns -- an operator re-running the planner after
    # an aborted migration gets the same plan, not a different one.
    surplus: list[int] = []
    for physical in range(new_n):
        while len(held[physical]) > target[physical]:
            surplus.append(held[physical].pop())

    moves: dict[int, int] = {}
    for physical in range(new_n):
        while len(held[physical]) < target[physical]:
            logical = surplus.pop()
            held[physical].append(logical)
            moves[logical] = physical
    return moves
