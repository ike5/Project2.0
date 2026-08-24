#!/usr/bin/env python3
"""layer_probe.py — read the channel layer's state straight out of Redis.

Module 04 printed the InMemoryChannelLayer as a Python dict. Now the same
state lives in Redis, and it is just as readable — which is the point of
choosing Redis over "some clustering feature". If you cannot inspect your
distributed primitive with a CLI, you cannot debug it at 3 a.m.

    ./layer_probe.py groups                 # who is subscribed to what
    ./layer_probe.py mailboxes              # per-worker inbox depth
    ./layer_probe.py amplification --room 7 # Redis writes per group_send
    ./layer_probe.py watch                  # 1 Hz live view

Works against both layers:

  RedisChannelLayer      groups are ZSETs   `<prefix>:group:<name>`
                         mailboxes are ZSETs `<prefix>specific.<worker>!`
                         (yes, the group key has a colon separator and the
                          mailbox key does not — that asymmetry is real, it
                          is in channels_redis/core.py, and it will confuse
                          you exactly once)

  RedisPubSubChannelLayer groups are Pub/Sub channels `<prefix>__group__<name>`
                          with NO server-side membership at all: the answer to
                          "who is in this group" lives in each worker's heap,
                          and Redis can only tell you how many worker
                          processes are subscribed.
"""

from __future__ import annotations

import argparse
import re
import sys
import time

try:
    import redis
except ImportError:                                          # pragma: no cover
    sys.exit("pip install redis")

WORKER_RE = re.compile(r"specific\.([0-9a-f]+)!")


def connect(args) -> "redis.Redis":
    return redis.Redis(host=args.redis_host, port=args.redis_port,
                       decode_responses=True)


# --------------------------------------------------------------------------
def cmd_groups(r, args) -> None:
    """Every group the core layer knows about, and its members by worker."""
    keys = sorted(r.scan_iter(match=f"{args.prefix}:group:*", count=500))
    if not keys:
        print(f"no core-layer groups under {args.prefix}:group:*")
    for key in keys:
        members = r.zrange(key, 0, -1)
        by_worker: dict[str, int] = {}
        for m in members:
            found = WORKER_RE.search(m)
            by_worker[found.group(1)[:8] if found else "?"] = \
                by_worker.get(found.group(1)[:8] if found else "?", 0) + 1
        ttl = r.ttl(key)
        print(f"{key}")
        print(f"    members {len(members):>6}   ttl {ttl:>7}s   "
              f"workers {len(by_worker)}")
        for worker, count in sorted(by_worker.items()):
            print(f"      worker {worker}  {count} channels")

    # The pubsub layer has no membership in Redis. All it can tell you is how
    # many worker processes hold a subscription -- which is exactly the number
    # that determines Redis's fan-out cost, so it is not nothing.
    chans = r.execute_command("PUBSUB", "CHANNELS", f"{args.prefix}__group__*")
    if chans:
        print("\npubsub-layer groups (subscriber counts are WORKER counts):")
        counts = r.execute_command("PUBSUB", "NUMSUB", *chans)
        for name, n in zip(counts[0::2], counts[1::2]):
            print(f"    {name}  <- {n} worker process(es)")


def cmd_mailboxes(r, args) -> None:
    """Per-worker inbox depth. This is the backpressure signal for the core
    layer: a mailbox that stays non-empty is a worker that cannot drain."""
    seen = []
    for key in r.scan_iter(match=f"{args.prefix}specific.*", count=500):
        if key.endswith("$inflight"):
            continue
        seen.append((r.zcard(key), r.ttl(key), key))
    if not seen:
        print("no core-layer mailboxes (are you on the pubsub layer?)")
        return
    print(f"{'depth':>7}  {'ttl':>5}  key")
    for depth, ttl, key in sorted(seen, reverse=True):
        flag = "  <-- AT CAPACITY" if depth >= args.capacity else ""
        print(f"{depth:>7}  {ttl:>5}  {key}{flag}")
    print(f"\n{len(seen)} mailbox(es) = {len(seen)} worker process(es) "
          f"currently holding connections.")


def cmd_amplification(r, args) -> None:
    """The number that decides whether Redis becomes your bottleneck.

    Redis writes per group_send = distinct worker processes with a subscriber,
    NOT the number of room members. Print both so the difference is impossible
    to miss.
    """
    group = f"room.{args.room}"
    key = f"{args.prefix}:group:{group}"
    members = r.zrange(key, 0, -1)
    if members:
        workers = {WORKER_RE.search(m).group(1) for m in members
                   if WORKER_RE.search(m)}
        print(f"group {group}")
        print(f"  room members (channels) : {len(members)}")
        print(f"  worker processes        : {len(workers)}")
        print(f"  Redis writes per send   : {len(workers)}")
        print(f"  socket writes per send  : {len(members)}  (done by the "
              f"workers, on their own cores)")
        if len(members):
            print(f"  amplification absorbed locally: "
                  f"{len(members) / max(len(workers), 1):.1f}x")
    else:
        nsub = r.execute_command("PUBSUB", "NUMSUB",
                                 f"{args.prefix}__group__{group}")
        print(f"group {group} (pubsub layer)")
        print(f"  worker processes subscribed : {nsub[1]}")
        print(f"  Redis writes per send       : 1 PUBLISH -> {nsub[1]} socket "
              f"writes by Redis's single thread")


def cmd_watch(r, args) -> None:
    prev = None
    while True:
        info = r.info("stats")
        mem = r.info("memory")
        cur = (info["total_commands_processed"],
               info.get("total_net_output_bytes", 0))
        rate = "" if prev is None else (
            f"  {cur[0] - prev[0]:>7} cmd/s"
            f"  {(cur[1] - prev[1]) / 131072:>7.1f} Mbit/s out")
        groups = len(list(r.scan_iter(match=f"{args.prefix}:group:*", count=500)))
        pchans = r.execute_command("PUBSUB", "CHANNELS",
                                   f"{args.prefix}__group__*")
        print(f"ops/s {info['instantaneous_ops_per_sec']:>7}"
              f"  mem {mem['used_memory_human']:>8}"
              f"  groups {groups:>5}  pubsub-groups {len(pchans):>5}{rate}")
        prev = cur
        time.sleep(1)


COMMANDS = {"groups": cmd_groups, "mailboxes": cmd_mailboxes,
            "amplification": cmd_amplification, "watch": cmd_watch}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("command", choices=sorted(COMMANDS))
    p.add_argument("--redis-host", default="localhost")
    p.add_argument("--redis-port", type=int, default=6379)
    p.add_argument("--prefix", default="pulse",
                   help="CHANNEL_LAYERS CONFIG['prefix']")
    p.add_argument("--room", default="7", help="bare room slug")
    p.add_argument("--capacity", type=int, default=1500)
    a = p.parse_args()
    try:
        COMMANDS[a.command](connect(a), a)
    except KeyboardInterrupt:
        pass
