#!/usr/bin/env python3
"""pipeline_bench.py — prove that round trips, not Redis, are your cost.

Four ways to issue N writes, timed, with Redis's own view of how much work it
did printed alongside. The gap between "wall clock" and "Redis usec" is the
network, and on a real network it is 99% of the number.

    ./pipeline_bench.py --n 10000
    sudo tc qdisc add dev lo root netem delay 1ms   # simulate a real network
    ./pipeline_bench.py --n 10000
    sudo tc qdisc del dev lo root

Modes:
    serial      N round trips.                     The obvious way.
    pipelined   1 round trip, N commands.          Not atomic.
    transaction MULTI/EXEC.                        Atomic, still 1 round trip.
    lua         One EVALSHA doing all N.           Atomic, 1 round trip,
                                                   and it BLOCKS Redis for its
                                                   whole duration -- which is
                                                   the tradeoff to understand.

Async variants are included because Pulse's hot path is async and
`redis.asyncio`'s pipeline behaves differently under concurrency: many
coroutines each doing one command can be almost as good as a pipeline, because
the connection pool interleaves them. Measure it rather than guessing.
"""

from __future__ import annotations

import argparse
import asyncio
import time

import redis
import redis.asyncio as aioredis

LUA_BULK = """
for i = 1, tonumber(ARGV[1]) do
    redis.call('SET', KEYS[1] .. ':' .. i, ARGV[2])
end
return tonumber(ARGV[1])
"""


def commandstats(r: "redis.Redis", name: str) -> tuple[int, int]:
    stats = r.info("commandstats").get(f"cmdstat_{name}")
    if not stats:
        return 0, 0
    return stats["calls"], stats["usec"]


def bench(label: str, fn, r: "redis.Redis", n: int) -> None:
    r.execute_command("CONFIG", "RESETSTAT")
    t0 = time.perf_counter()
    fn()
    wall = time.perf_counter() - t0
    calls, usec = commandstats(r, "set")
    calls2, usec2 = commandstats(r, "eval")
    usec += usec2
    print(f"  {label:<12} {wall * 1000:>9.1f} ms   "
          f"{n / wall:>10,.0f} ops/s   "
          f"redis {usec / 1000:>8.1f} ms   "
          f"network {(wall * 1000 - usec / 1000) / (wall * 1000) * 100:>5.1f}%")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=6379)
    ap.add_argument("--n", type=int, default=10_000)
    ap.add_argument("--value", default="v" * 64)
    args = ap.parse_args()

    r = redis.Redis(host=args.host, port=args.port, decode_responses=True)
    r.ping()
    n, val = args.n, args.value

    print(f"\n{n:,} SETs of a {len(val)}-byte value, against "
          f"{args.host}:{args.port}\n")

    def serial() -> None:
        for i in range(n):
            r.set(f"bench:serial:{i}", val)

    def pipelined() -> None:
        pipe = r.pipeline(transaction=False)
        for i in range(n):
            pipe.set(f"bench:pipe:{i}", val)
        pipe.execute()

    def transaction() -> None:
        pipe = r.pipeline(transaction=True)          # wraps in MULTI/EXEC
        for i in range(n):
            pipe.set(f"bench:multi:{i}", val)
        pipe.execute()

    script = r.register_script(LUA_BULK)             # SCRIPT LOAD + EVALSHA

    def lua() -> None:
        script(keys=["bench:lua"], args=[n, val])

    bench("serial", serial, r, n)
    bench("pipelined", pipelined, r, n)
    bench("transaction", transaction, r, n)
    bench("lua", lua, r, n)

    # --- async, because that is what the app actually runs -----------------
    async def async_modes() -> None:
        ar = aioredis.Redis(host=args.host, port=args.port,
                            decode_responses=True, max_connections=32)

        async def concurrent() -> None:
            # 32 coroutines x n/32 commands each. No pipeline, but the pool
            # keeps 32 requests in flight, so latency overlaps.
            async def worker(w: int) -> None:
                for i in range(w, n, 32):
                    await ar.set(f"bench:async:{i}", val)
            await asyncio.gather(*(worker(w) for w in range(32)))

        async def apipe() -> None:
            async with ar.pipeline(transaction=False) as pipe:
                for i in range(n):
                    pipe.set(f"bench:apipe:{i}", val)
                await pipe.execute()

        for label, fn in (("async x32", concurrent), ("async pipe", apipe)):
            await ar.execute_command("CONFIG", "RESETSTAT")
            t0 = time.perf_counter()
            await fn()
            wall = time.perf_counter() - t0
            info = await ar.info("commandstats")
            usec = info.get("cmdstat_set", {}).get("usec", 0)
            print(f"  {label:<12} {wall * 1000:>9.1f} ms   "
                  f"{n / wall:>10,.0f} ops/s   "
                  f"redis {usec / 1000:>8.1f} ms   "
                  f"network {(wall * 1000 - usec / 1000) / (wall * 1000) * 100:>5.1f}%")
        await ar.aclose()

    asyncio.run(async_modes())

    print("\nRead the 'redis' column: it barely changes. Every millisecond of")
    print("difference between the modes was spent on the network, not in Redis.")
    print("\nAnd note what `lua` bought and cost: one round trip AND atomicity,")
    print("paid for by holding Redis's single thread for the whole script. A")
    print("script that loops over unbounded input is an outage; Module 08's")
    print("Part D shows you what that looks like from a chat client's side.")

    r.execute_command("FLUSHDB", "ASYNC")


if __name__ == "__main__":
    main()
