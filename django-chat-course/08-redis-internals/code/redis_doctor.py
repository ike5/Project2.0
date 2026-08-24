#!/usr/bin/env python3
"""redis_doctor.py — the five questions to ask a Redis that is misbehaving.

`redis-cli --latency`, `--stat`, `SLOWLOG` and `MEMORY DOCTOR` each answer part
of it; this script asks all of them in the order that converges fastest, and
adds the two things `redis-cli` will not tell you: which commands own the
single thread, and which key patterns have no bound on their growth.

    ./redis_doctor.py                     # everything, once
    ./redis_doctor.py --watch             # everything, every 10 s
    ./redis_doctor.py --only thread       # one section

Sections, in diagnostic order:

  1. floor      what the MACHINE can do, before Redis is involved
  2. thread     who is spending the single thread (INFO commandstats)
  3. slow       what already blocked it (SLOWLOG)
  4. memory     used vs RSS vs peak, fragmentation, eviction policy
  5. keys       growth bounds: every pattern either has a TTL, a MAXLEN, or
                it is a leak

Nothing here writes to Redis except the `floor` section's PING loop, so it is
safe against a production instance -- with the single caveat that INFO itself
takes the thread for tens of microseconds, so do not run --watch at 1 Hz
against a Redis that is already at 95%.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time

try:
    import redis
except ImportError:                                          # pragma: no cover
    sys.exit("pip install redis")

# What Pulse stores, and what is supposed to bound each pattern. A pattern that
# reaches this table with bound=None is a bug, not a configuration.
BUDGETS = [
    # pattern,                type,     bound,              max
    ("pulse:group:*",         "zset",   "group_expiry TTL", 50_000),
    ("pulsespecific.*",       "zset",   "capacity + expiry", 3_000),
    ("room:*:stream",         "stream", "XADD MAXLEN ~",    20_000),
    ("room:*:seq",            "string", "one integer",           1),
    ("presence:*",            "string", "TTL 45 s",              1),
    ("rate:*",                "hash",   "PEXPIRE in Lua",        4),
    ("unread:*",              "hash",   "rooms per user",      500),
    ("wsticket:*",            "string", "TTL 30 s",              1),
]


def section(title: str) -> None:
    print(f"\n\033[1m== {title} {'=' * (66 - len(title))}\033[0m")


def floor(r, samples: int = 2000) -> None:
    section("1. the machine's floor")
    lat = []
    for _ in range(samples):
        t0 = time.perf_counter()
        r.ping()
        lat.append((time.perf_counter() - t0) * 1000)
    lat.sort()
    print(f"  PING round trip   p50 {lat[len(lat)//2]:.3f} ms   "
          f"p99 {lat[int(len(lat)*0.99)]:.3f} ms   max {lat[-1]:.3f} ms   "
          f"mean {statistics.fmean(lat):.3f} ms")
    print("  Compare with `redis-cli --intrinsic-latency 30`, which measures")
    print("  the KERNEL's scheduling floor with no Redis involved. If that")
    print("  reports milliseconds, you have a host problem -- a noisy")
    print("  neighbour, CPU frequency scaling, a hypervisor -- and no amount")
    print("  of Redis tuning will help.")


def thread(r, top: int = 10) -> None:
    section("2. who owns the single thread")
    stats = r.info("commandstats")
    rows = []
    for name, s in stats.items():
        cmd = name.removeprefix("cmdstat_")
        rows.append((s["usec"], s["calls"], s["usec_per_call"], cmd))
    if not rows:
        print("  no commandstats (CONFIG RESETSTAT was just run?)")
        return
    total = sum(r_[0] for r_ in rows)
    print(f"  {'total ms':>10} {'share':>7} {'calls':>12} {'us/call':>10}  command")
    for usec, calls, per, cmd in sorted(rows, reverse=True)[:top]:
        flag = "  <-- ONE CALL IS AN OUTAGE" if per > 100_000 else ""
        print(f"  {usec/1000:>10.1f} {usec/total*100:>6.1f}% {calls:>12,} "
              f"{per:>10.2f}  {cmd}{flag}")
    print(f"\n  Total single-thread time since last RESETSTAT: {total/1e6:.1f} s")
    print("  A command with a huge us/call and one call is the thing that")
    print("  broke your p99 and left nothing in your application logs.")


def slow(r, n: int = 10) -> None:
    section("3. what already blocked it")
    cfg = r.config_get("slowlog-log-slower-than")
    print(f"  slowlog-log-slower-than = {cfg.get('slowlog-log-slower-than')} us")
    entries = r.slowlog_get(n)
    if not entries:
        print("  slowlog empty -- either healthy, or the threshold is too high")
        return
    for e in entries:
        cmd = " ".join(str(a)[:40] for a in e["command"])[:100] \
            if isinstance(e["command"], (list, tuple)) else str(e["command"])[:100]
        print(f"  {e['duration']/1000:>9.1f} ms  {time.strftime('%H:%M:%S', time.localtime(e['start_time']))}  "
              f"{e.get('client_address', '?')}  {cmd}")


def memory(r) -> None:
    section("4. memory")
    m = r.info("memory")
    frag = m.get("mem_fragmentation_ratio", 0)
    verdict = ("healthy" if 0.99 <= frag <= 1.5 else
               "SWAPPED OUT -- this is an emergency, disable swap" if frag < 0.99
               else "fragmented -- consider activedefrag yes")
    print(f"  used           {m['used_memory_human']:>10}")
    print(f"  rss            {m['used_memory_rss_human']:>10}")
    print(f"  peak           {m['used_memory_peak_human']:>10}   "
          f"<- size containers on THIS, not on used")
    print(f"  maxmemory      {m.get('maxmemory_human', '0B'):>10}   "
          f"policy={m.get('maxmemory_policy')}")
    print(f"  fragmentation  {frag:>10.2f}   {verdict}")
    print(f"  allocator      {m.get('mem_allocator', '?')}")
    try:
        print(f"\n  MEMORY DOCTOR: {r.memory_doctor()}")
    except Exception as exc:                                 # noqa: BLE001
        print(f"\n  MEMORY DOCTOR unavailable: {exc}")
    if m.get("maxmemory_policy") not in (None, "noeviction"):
        print("\n  !! This Redis holds sequence counters, group membership and")
        print("     stream entries. An eviction policy other than noeviction")
        print("     turns memory pressure into SILENT data loss.")


def keys(r) -> None:
    section("5. growth bounds")
    print(f"  {'pattern':<22} {'count':>8} {'largest':>9} {'no TTL':>8}  bound")
    for pattern, ktype, bound, limit in BUDGETS:
        count = largest = no_ttl = 0
        biggest_key = ""
        for key in r.scan_iter(match=pattern, count=500):
            count += 1
            if count > 5000:                    # bounded work: this is a
                break                           # diagnostic, not an audit
            size = _size_of(r, key, ktype)
            if size > largest:
                largest, biggest_key = size, key
            if r.ttl(key) == -1:
                no_ttl += 1
        flag = "  <-- OVER BUDGET" if largest > limit else ""
        print(f"  {pattern:<22} {count:>8} {largest:>9} {no_ttl:>8}  "
              f"{bound}{flag}")
        if largest > limit:
            print(f"      largest: {biggest_key}")
    print("\n  Every pattern must have a TTL, a MAXLEN, or a documented bound.")
    print("  A pattern with none of those is a leak you have not noticed yet.")
    print("  Run `redis-cli --bigkeys` and `--memkeys` for the exhaustive view;")
    print("  both use SCAN, so both are safe against a live instance.")


def _size_of(r, key: str, ktype: str) -> int:
    try:
        return {"zset": r.zcard, "stream": r.xlen, "hash": r.hlen,
                "set": r.scard, "list": r.llen}.get(ktype, lambda _k: 1)(key)
    except redis.ResponseError:
        return 1


SECTIONS = {"floor": floor, "thread": thread, "slow": slow,
            "memory": memory, "keys": keys}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=6379)
    p.add_argument("--only", choices=sorted(SECTIONS), action="append")
    p.add_argument("--watch", type=float, nargs="?", const=10.0, default=None)
    a = p.parse_args()
    conn = redis.Redis(host=a.host, port=a.port, decode_responses=True)
    chosen = a.only or ["floor", "thread", "slow", "memory", "keys"]
    try:
        while True:
            for name in chosen:
                SECTIONS[name](conn)
            if a.watch is None:
                break
            time.sleep(a.watch)
    except KeyboardInterrupt:
        pass
