#!/usr/bin/env python3
"""wsprobe — a small WebSocket probe for Module 04's measurements.

This is *not* a load generator. It has no open-model arrival process, it does
not report dropped iterations, and its latency numbers are closed-loop and
therefore prone to coordinated omission. Module 06 builds the honest rig with
k6 and Locust; this one exists so that Module 04 can measure five specific
things with no extra dependencies beyond `websockets` (which `uvicorn[standard]`
already pulled in).

    python wsprobe.py hold      --n 5000 --room general --user u0
    python wsprobe.py fanout    --room general --receivers 200 --rate 10 --seconds 60
    python wsprobe.py crosstalk --room general --pairs 50
    python wsprobe.py deadbeat  --room general --user u1
    python wsprobe.py blast     --room general --user u0 --n 2000

Every mode authenticates with the DEBUG-only `?as=<username>` shim from
chat/middleware.py. Module 21 replaces that with signed single-use tickets and
this script grows a --ticket flag.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time

try:
    import websockets
except ImportError:  # pragma: no cover
    sys.exit("pip install websockets  (or install uvicorn[standard])")

DEFAULT_HOST = "localhost:8000"


def url(args, user: str) -> str:
    return f"ws://{args.host}/ws/room/{args.room}/?as={user}"


def now_ms() -> int:
    return int(time.time() * 1000)


def pct(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    return s[min(len(s) - 1, int(len(s) * p))]


# --------------------------------------------------------------------------
# hold: open N connections and keep them idle, so you can measure the server's
# RSS delta and divide. This is the ~45 KB/connection measurement.
# --------------------------------------------------------------------------
async def mode_hold(args) -> None:
    conns = []
    t0 = time.perf_counter()
    for i in range(args.n):
        try:
            ws = await websockets.connect(
                url(args, args.user),
                open_timeout=20,
                # Disable the client's own ping so the server sees genuinely
                # idle sockets; we are measuring resting cost, not traffic.
                ping_interval=None,
                max_queue=None,
            )
        except OSError as exc:
            print(f"failed at {i:,} connections: {exc}", file=sys.stderr)
            print("  (check `ulimit -n` on BOTH ends, and ip_local_port_range)",
                  file=sys.stderr)
            break
        conns.append(ws)
        if (i + 1) % 500 == 0:
            print(f"  {i + 1:,} connections open "
                  f"({time.perf_counter() - t0:.1f}s)", flush=True)

    print(f"holding {len(conns):,} idle connections. "
          f"Measure the server now:  grep VmRSS /proc/$(pgrep -f 'uvicorn pulse.asgi' "
          f"| head -1)/status", flush=True)
    try:
        await asyncio.Future()          # hold until Ctrl-C / kill
    except asyncio.CancelledError:
        pass
    finally:
        await asyncio.gather(*(c.close() for c in conns), return_exceptions=True)


# --------------------------------------------------------------------------
# fanout: 1 sender + N receivers in one room. Measures TRUE end-to-end latency
# (sender's send() -> a different connection's recv()), which is the only
# latency number that corresponds to a human noticing something.
# --------------------------------------------------------------------------
async def mode_fanout(args) -> None:
    receivers = []
    for i in range(args.receivers):
        receivers.append(await websockets.connect(
            url(args, f"u{i % 50}"), ping_interval=None, max_queue=None))
    sender = await websockets.connect(url(args, args.user), ping_interval=None)

    latencies: list[float] = []
    received = 0
    stop = asyncio.Event()

    async def drain(ws):
        nonlocal received
        while not stop.is_set():
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
            except (asyncio.TimeoutError, websockets.ConnectionClosed):
                continue
            env = json.loads(raw)
            if env.get("type") != "message.new":
                continue
            received += 1
            # The sender stamps its clock into the body; both ends are this
            # process, so there is no clock skew to correct for.
            try:
                sent_at = int(env["body"].rsplit("|", 1)[1])
            except (KeyError, IndexError, ValueError):
                continue
            latencies.append(time.time() * 1000 - sent_at)

    drains = [asyncio.create_task(drain(ws)) for ws in receivers]

    sent = 0
    interval = 1.0 / args.rate
    deadline = time.perf_counter() + args.seconds
    next_at = time.perf_counter()
    while time.perf_counter() < deadline:
        await sender.send(json.dumps(
            {"type": "message.create", "body": f"probe|{now_ms()}"}))
        sent += 1
        next_at += interval
        await asyncio.sleep(max(0.0, next_at - time.perf_counter()))

    await asyncio.sleep(2.0)            # let the tail arrive
    stop.set()
    for t in drains:
        t.cancel()
    await asyncio.gather(*drains, return_exceptions=True)
    await asyncio.gather(sender.close(), *(r.close() for r in receivers),
                         return_exceptions=True)

    amp = received / sent if sent else 0
    print(f"receivers={args.receivers}  sent={sent:,}  received={received:,}  "
          f"(amplification {amp:.0f}x)")
    print("end-to-end latency (sender send() -> receiver recv()):")
    for label, p in (("p50", 0.50), ("p95", 0.95), ("p99", 0.99), ("p99.9", 0.999)):
        print(f"  {label:<6}{pct(latencies, p):6.1f} ms")
    if latencies:
        print(f"  mean  {statistics.mean(latencies):6.1f} ms   n={len(latencies):,}")
    print("server worker CPU: read it from `top -p $(pgrep -f uvicorn | head -1)`")


# --------------------------------------------------------------------------
# crosstalk: THE Module 04 measurement. Open `pairs` pairs of connections in
# the same room. For each pair, A sends and we check whether B received it.
# On one worker this is 100%. On N workers it is roughly 1/N.
# --------------------------------------------------------------------------
async def mode_crosstalk(args) -> None:
    delivered = 0
    for i in range(args.pairs):
        a = await websockets.connect(url(args, "u0"), ping_interval=None)
        b = await websockets.connect(url(args, "u1"), ping_interval=None)
        await a.recv()                                  # hello
        await b.recv()                                  # hello
        marker = f"crosstalk-{i}-{now_ms()}"
        await a.send(json.dumps({"type": "message.create", "body": marker}))

        deadline = time.perf_counter() + 1.5
        got = False
        while time.perf_counter() < deadline and not got:
            try:
                raw = await asyncio.wait_for(b.recv(), timeout=0.3)
            except (asyncio.TimeoutError, websockets.ConnectionClosed):
                break
            env = json.loads(raw)
            got = env.get("type") == "message.new" and env.get("body") == marker
        delivered += int(got)
        await asyncio.gather(a.close(), b.close(), return_exceptions=True)

    rate = 100.0 * delivered / args.pairs
    print(f"{delivered}/{args.pairs} message pairs delivered across connections  "
          f"({rate:.1f}%)")
    if rate < 99:
        print("\nNothing errored. Nothing logged. The message was persisted.")
        print("Two worker processes, two channel-layer dicts, no shared memory.")
        print("curl -s localhost:8000/api/layer-debug/  (a few times) to see both.")


# --------------------------------------------------------------------------
# deadbeat: complete the handshake, then never read. Wedges the server's
# transport write buffer, which stops the consumer draining its channel-layer
# mailbox, which fills at `capacity` and makes the NEXT group_send raise
# ChannelFull -- for the whole group.
# --------------------------------------------------------------------------
async def mode_deadbeat(args) -> None:
    ws = await websockets.connect(
        url(args, args.user),
        ping_interval=None,
        # max_queue=1 + never calling recv() means the library stops reading
        # from the socket almost immediately. That is the whole trick.
        max_queue=1,
    )
    print(f"deadbeat connected to room.{args.room} as {args.user}; not reading. "
          f"Now run:  python wsprobe.py blast --room {args.room} --user u0 --n 2000")
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        await ws.close()


# --------------------------------------------------------------------------
# blast: fire N messages into a room as fast as the socket accepts them.
# --------------------------------------------------------------------------
async def mode_blast(args) -> None:
    ws = await websockets.connect(url(args, args.user), ping_interval=None,
                                  max_queue=None)
    await ws.recv()                                     # hello
    t0 = time.perf_counter()
    for i in range(args.n):
        await ws.send(json.dumps({"type": "message.create", "body": f"blast-{i}"}))
    dt = time.perf_counter() - t0
    print(f"sent {args.n:,} messages in {dt:.2f}s ({args.n / dt:,.0f}/s). "
          f"Check the server log for ChannelFull.")
    await ws.close()


MODES = {
    "hold": mode_hold,
    "fanout": mode_fanout,
    "crosstalk": mode_crosstalk,
    "deadbeat": mode_deadbeat,
    "blast": mode_blast,
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("mode", choices=sorted(MODES))
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--room", default="general")
    p.add_argument("--user", default="u0")
    p.add_argument("--n", type=int, default=1000)
    p.add_argument("--receivers", type=int, default=200)
    p.add_argument("--pairs", type=int, default=50)
    p.add_argument("--rate", type=float, default=10.0, help="messages/second")
    p.add_argument("--seconds", type=float, default=60.0)
    args = p.parse_args()

    try:
        asyncio.run(MODES[args.mode](args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
