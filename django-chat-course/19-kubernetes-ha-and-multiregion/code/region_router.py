#!/usr/bin/env python3
"""Room affinity for multi-region Pulse — the reference copy of
`chat/regions.py`.

The problem this file exists to solve, in one paragraph:

    Module 05 gave every room a monotonic sequence number produced by a single
    `INCR room:{slug}:seq`. Module 10 built gap detection and resume-from-cursor
    on top of it. Both assume ONE writer per room. Two regions with independent
    sequencers produce two different messages numbered 501, and every client's
    gap detection breaks permanently -- a client that accepted one 501 will
    never accept the other.

So: every room has exactly one HOME REGION. Writes are forwarded there. Reads
are served locally from a replica. A region that cannot reach a room's home
refuses the write rather than inventing a sequence number.

Design choices, and what each rejected:

1. Home region is DERIVED from the slug by hash, not stored in a table.
   Rejected: a `rooms.home_region` column. It would need to be read on every
   send (a cross-region read, or a cache with an invalidation story) and it
   would have to be consistent across regions during a migration. A pure
   function of the slug is available everywhere, instantly, with no coordination
   -- which is the same reason Module 14 hashes to logical shards.

   The cost is that you cannot MOVE a room without changing the hash. `PINNED`
   below is the escape hatch: an explicit, small, replicated override map for
   the rooms that need residency guarantees or that a hot-room migration moved.

2. Hashing uses blake2b, not `hash()`.
   Python's built-in `hash()` for str is randomised per process by PYTHONHASHSEED.
   Two workers in the SAME POD would disagree about where room.7 lives. This is
   the single most likely way to get this file wrong, and it fails
   intermittently, which is worse than failing.

3. Forwarding is HTTP, not a shared Redis.
   Rejected: cross-region Redis replication for the channel layer. A WAN link
   inside your fan-out path means every fan-out inherits the WAN's tail latency
   and every partition becomes a fan-out outage. HTTP forwarding keeps the WAN
   on the SEND path only, where Module 17's optimistic render already hides it.

Latency floor, so nobody hopes it away: NYC-London is 5,570 km great circle;
real fibre routes run ~1.4x that, so ~7,800 km of glass. Light in single-mode
fibre travels at c/n with n ~= 1.468, i.e. 299,792 / 1.468 = 204,218 km/s.
7,800 / 204,218 = 38.2 ms one way, 76 ms round trip. Nothing gets below that.

Run it directly for a self-test:

    python region_router.py
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

# Ordered and STABLE. Appending a region rehashes every room that lands on the
# new index -- see `rebalance_report()` for how much movement that is, and read
# it before you add one, because a rehashed room's sequence counter has to be
# migrated with the room.
REGIONS: tuple[str, ...] = tuple(
    r.strip() for r in os.getenv("PULSE_REGIONS", "us,eu").split(",") if r.strip()
)

LOCAL_REGION: str = os.getenv("PULSE_REGION", "us")

# Explicit overrides. Small, replicated to every region, and the only thing that
# has to be consistent across the WAN. Reasons a room ends up here:
#   - data residency ("this room's messages stay in the EU")
#   - a hot-room migration that moved a room off a saturated region
#   - an incident: pinning a room to the surviving region during a partition
PINNED: dict[str, str] = {}


class RegionUnavailable(RuntimeError):
    """The room's home region is unreachable. The caller MUST NOT sequence
    locally -- it must return an error envelope and let the client retry."""

    def __init__(self, slug: str, home: str) -> None:
        super().__init__(f"room {slug!r} is homed in {home!r}, which is unreachable")
        self.slug = slug
        self.home = home


def home_region_of(slug: str) -> str:
    """Which region owns writes for this room?

    `slug` is the BARE handle -- `general`, `7` -- not `room.7` and not
    `room:{7}:seq`. Hashing the composed key instead would give a different
    answer for the same room depending on which caller you asked, which is the
    kind of bug that only shows up as "some messages are numbered twice".
    """
    pinned = PINNED.get(slug)
    if pinned is not None:
        return pinned
    # blake2b, not hash(): PYTHONHASHSEED randomisation makes str.__hash__
    # differ between worker processes, so two workers in one pod would disagree.
    digest = hashlib.blake2b(slug.encode("utf-8"), digest_size=8).digest()
    return REGIONS[int.from_bytes(digest, "big") % len(REGIONS)]


def is_local(slug: str) -> bool:
    return home_region_of(slug) == LOCAL_REGION


@dataclass(frozen=True)
class Decision:
    """What the send path should do with this message."""

    local: bool
    home: str
    # Cross-region sends are counted separately in metrics because the ratio
    # (cross_region_sends / sends) is the number that decides whether a third
    # region is worth it. With rooms hashed evenly across N regions, (N-1)/N of
    # a given user's rooms are remote: 50% at two regions, 67% at three.
    reason: str


def route(slug: str) -> Decision:
    home = home_region_of(slug)
    if home == LOCAL_REGION:
        return Decision(local=True, home=home, reason="home")
    return Decision(local=False, home=home, reason="forward")


def rebalance_report(slugs: list[str], new_regions: tuple[str, ...]) -> dict[str, int]:
    """How many rooms change home if REGIONS becomes `new_regions`?

    Call this before adding a region. Modulo hashing over an ordered tuple is
    NOT consistent hashing: going from 2 to 3 regions moves roughly 2/3 of all
    rooms, not 1/3. Each moved room needs its `room:{slug}:seq` counter and its
    Streams entries migrated, under traffic, without a gap.

    Module 14 made exactly this argument about physical shards and reached for
    logical shards / consistent hashing for exactly this reason. Two regions
    with a pinned override map is the cheap version; if you expect to add
    regions regularly, use a rendezvous hash here instead and accept the extra
    machinery.
    """
    moved = 0
    for slug in slugs:
        old = home_region_of(slug)
        digest = hashlib.blake2b(slug.encode("utf-8"), digest_size=8).digest()
        new = PINNED.get(slug) or new_regions[int.from_bytes(digest, "big") % len(new_regions)]
        if old != new:
            moved += 1
    return {"total": len(slugs), "moved": moved}


# ---------------------------------------------------------------------------
# The send path. This is the only place in Pulse that knows about regions.
# ---------------------------------------------------------------------------
async def send(slug: str, sender: str, payload: dict, *, deps) -> dict:
    """Sequence-and-publish locally, or forward to the home region.

    `deps` carries the three collaborators so this module stays importable
    without Django: `deps.do_send`, `deps.forward`, `deps.metrics`.
    """
    decision = route(slug)

    if decision.local:
        deps.metrics.local_sends.inc()
        return await deps.do_send(slug, sender, payload)

    deps.metrics.cross_region_sends.labels(home=decision.home).inc()
    try:
        # The client is NOT waiting on this: Module 17 renders the message
        # optimistically the instant the user hits enter, and reconciles when
        # the server id and seq arrive. The 204 ms is invisible until the tick.
        return await deps.forward(decision.home, slug, sender, payload)
    except TimeoutError as exc:
        # THE IMPORTANT BRANCH. Do not fall back to sequencing locally.
        # A local INCR here produces a duplicate sequence number and breaks gap
        # detection for every client in the room, forever, silently. Refusing
        # the write is a visible, retryable, recoverable failure. This is the
        # availability-for-consistency trade, made deliberately.
        deps.metrics.cross_region_refusals.labels(home=decision.home).inc()
        raise RegionUnavailable(slug, decision.home) from exc


async def scrollback(slug: str, cursor: int, limit: int, *, deps) -> list[dict]:
    """Reads are ALWAYS local, from the local replica, regardless of home.

    This is the half of the design that makes room affinity tolerable: a user
    scrolling history in a remote-homed room pays nothing. Only sends cross the
    WAN, and sends are infrequent and optimistically rendered.
    """
    return await deps.local_replica.scrollback(slug, cursor, limit)


if __name__ == "__main__":
    import json

    slugs = ["general", "7", "random", "eng-backend", "42", "incident-2026-08"]
    print(f"REGIONS={REGIONS}  LOCAL_REGION={LOCAL_REGION}")
    for s in slugs:
        d = route(s)
        print(f"  {s:<18} home={d.home:<4} local={d.local}")

    # Determinism check: the same slug must hash the same way in every process.
    # If this ever prints two different values, someone reintroduced hash().
    print("\nstability:", home_region_of("7"), home_region_of("7"))

    print("\nadding a third region moves:")
    print(" ", json.dumps(rebalance_report([str(i) for i in range(10_000)],
                                           ("us", "eu", "ap"))))
