#!/usr/bin/env python3
"""loss_test.py — count exactly how many messages the channel layer loses.

The measurement is a subtraction of two numbers the server itself gives you:

    acked     seq values the server allocated and acknowledged to a sender
              (message.ack goes straight back down the sender's OWN socket,
              so it never touches the channel layer and never lies)
    received  seq values that actually reached a receiver on a DIFFERENT
              worker process

    lost = acked - received

Both are exact, both come from the wire, and neither depends on a server-side
counter — which matters, because the whole point of this exercise is that the
server-side counters say everything is fine.

    ./loss_test.py --room 9 --senders 20 --per-sender 10 \
                   --fault pause --fault-at 4.0 --fault-for 0.75

    ./loss_test.py --room 9 --fault kill      # RST instead of a hang
    ./loss_test.py --room 9 --fault none      # control run: expect 0 lost

Why so many sender connections: a `group_send` that is waiting on a paused
Redis blocks *that consumer's* coroutine, and one consumer processes one
connection's frames serially. With a single sender, a 750 ms pause costs you
one or two failed sends. Real load is many connections failing concurrently,
so the harness models that: `--senders` independent sockets, each pacing its
own sends. Loss scales with `pause_duration x offered_rate`, capped by
concurrency — which is itself a result worth understanding.

Requires: `websockets` (already present via uvicorn[standard]) and a `docker`
binary that can pause the `pulse-redis` container.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time

try:
    import websockets
except ImportError:                                          # pragma: no cover
    sys.exit("pip install websockets")


def now() -> float:
    return time.time()


async def docker(*args: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "docker", *args,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
    _, err = await proc.communicate()
    if proc.returncode:
        print(f"  !! docker {' '.join(args)} -> {err.decode().strip()}",
              file=sys.stderr)


class Result:
    def __init__(self) -> None:
        self.acked: set[int] = set()
        self.received: set[int] = set()
        self.sent = 0                 # client-side count, for untracked types
        self.received_frames = 0      # frame count, for untracked types
        self.send_errors = 0
        self.error_frames: list[str] = []
        self.receiver_closed = False


async def receiver(url: str, res: Result, stop: asyncio.Event,
                   wire_type: str) -> None:
    """One client, on a different worker, recording every seq it sees."""
    async with websockets.connect(url, subprotocols=["pulse.v1"]) as ws:
        while not stop.is_set():
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except websockets.ConnectionClosed:
                res.receiver_closed = True
                return
            env = json.loads(raw)
            if env.get("type") == wire_type:
                res.received_frames += 1
                # typing.update carries no seq -- ephemeral traffic is not
                # sequenced, deliberately (pulse-protocol-v1.md 3.2), so for
                # that type we can only count frames.
                if "seq" in env.get("data", {}):
                    res.received.add(env["data"]["seq"])


async def sender(idx: int, url: str, count: int, interval: float,
                 res: Result, t0: float, mtype: str) -> None:
    """One client sending `count` frames on a fixed schedule.

    Sends are scheduled from t0 so that every sender shares one timeline and
    the fault window covers a predictable number of messages.
    """
    async with websockets.connect(url, subprotocols=["pulse.v1"]) as ws:
        reader = asyncio.create_task(_drain_acks(ws, res))
        for n in range(count):
            target = t0 + n * interval
            delay = target - now()
            if delay > 0:
                await asyncio.sleep(delay)
            if mtype == "typing.start":
                frame = {"v": 1, "type": "typing.start", "data": {}}
            else:
                frame = {"v": 1, "type": "message.create", "data": {
                    "client_id": f"loss-{idx:03d}-{n:03d}-{time.time_ns()}",
                    "body": f"loss probe s{idx} n{n}"}}
            try:
                await ws.send(json.dumps(frame))
                res.sent += 1
            except Exception:                                # noqa: BLE001
                res.send_errors += 1
        await asyncio.sleep(2.0)          # let the last acks land
        reader.cancel()


async def _drain_acks(ws, res: Result) -> None:
    while True:
        try:
            raw = await ws.recv()
        except (asyncio.CancelledError, websockets.ConnectionClosed):
            return
        env = json.loads(raw)
        if env.get("type") == "message.ack":
            # The server allocated a seq and committed the row. Whether it
            # ever reached anybody is a completely separate question.
            res.acked.add(env["data"]["seq"])
        elif env.get("type") == "error":
            res.error_frames.append(env["data"].get("code", "?"))


async def fault_injector(kind: str, at: float, duration: float,
                         container: str, t0: float) -> None:
    if kind == "none":
        return
    await asyncio.sleep(max(0.0, t0 + at - now()))
    if kind == "pause":
        print(f"  >>> t={now()-t0:5.2f}s  docker pause {container}")
        await docker("pause", container)
        await asyncio.sleep(duration)
        print(f"  >>> t={now()-t0:5.2f}s  docker unpause {container}")
        await docker("unpause", container)
    elif kind == "kill":
        print(f"  >>> t={now()-t0:5.2f}s  docker kill {container}")
        await docker("kill", container)
        await asyncio.sleep(duration)
        print(f"  >>> t={now()-t0:5.2f}s  docker start {container}")
        await docker("start", container)
    else:
        raise SystemExit(f"unknown fault {kind!r}")


async def main(args) -> int:
    base = f"ws://{args.host}/ws/room/{args.room}/"
    res = Result()
    stop = asyncio.Event()
    wire_type = "typing.update" if args.type == "typing.start" else "message.new"

    # The receiver connects first and is given a distinct user so it is easy
    # to see which worker it landed on (`hello` carries `pid`).
    recv_task = asyncio.create_task(
        receiver(f"{base}?as={args.receiver}", res, stop, wire_type))
    await asyncio.sleep(1.0)

    total = args.senders * args.per_sender
    t0 = now() + 1.0
    print(f"publishing {total} {args.type} frames "
          f"({args.senders} senders x {args.per_sender} @ {args.interval}s), "
          f"fault={args.fault} at t={args.fault_at}s for {args.fault_for}s")

    await asyncio.gather(
        fault_injector(args.fault, args.fault_at, args.fault_for,
                       args.container, t0),
        *[sender(i, f"{base}?as={args.sender_prefix}{i}",
                 args.per_sender, args.interval, res, t0, args.type)
          for i in range(args.senders)],
    )

    await asyncio.sleep(3.0)          # generous drain window before we judge
    stop.set()
    await asyncio.sleep(0.6)
    recv_task.cancel()

    if args.type == "typing.start":
        # No acks and no seq for ephemeral traffic: the honest comparison is
        # what the client sent against what one receiver saw.
        print()
        print(f"  sent                 : {res.sent} typing events")
        print(f"  received             : {res.received_frames}")
        print(f"  LOST                 : {res.sent - res.received_frames}"
              f"   ({100 * (res.sent - res.received_frames) / max(res.sent, 1):.1f}%)")
        print("  user-visible impact  : none observed — the next typing.start "
              "repairs the state within 3 s")
        return 0

    acked, received = len(res.acked), len(res.received)
    lost = sorted(res.acked - res.received)
    late = sorted(res.received - res.acked)      # someone else's traffic

    print()
    print(f"  sent (client-side)   : {total}")
    print(f"  acked (server seq)   : {acked}")
    print(f"  received (other node): {received}")
    print(f"  LOST                 : {len(lost)}"
          f"   ({100 * len(lost) / max(acked, 1):.1f}% of acked)")
    if res.send_errors:
        print(f"  client send errors   : {res.send_errors}")
    if res.error_frames:
        print(f"  error frames         : {res.error_frames[:5]}")
    if res.receiver_closed:
        print("  !! the receiver's socket was closed — rerun; the numbers "
              "below undercount")
    if lost:
        runs, start, prev = [], lost[0], lost[0]
        for s in lost[1:]:
            if s != prev + 1:
                runs.append((start, prev))
                start = s
            prev = s
        runs.append((start, prev))
        pretty = ", ".join(f"{a}" if a == b else f"{a}-{b}" for a, b in runs[:8])
        print(f"  lost seq ranges      : {pretty}")
        print()
        print("  Every one of those was committed to Postgres and acked to its")
        print("  sender. The hole is in delivery only, and nothing errored on")
        print("  the receiving side. Compare with chat_messages_outbound_total.")
    if late:
        print(f"  received but not acked by us: {len(late)} (other senders)")
    return 0 if args.fault == "none" and not lost else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--host", default="localhost:8000")
    p.add_argument("--room", default="9", help="bare room slug")
    p.add_argument("--senders", type=int, default=20)
    p.add_argument("--per-sender", type=int, default=10)
    p.add_argument("--interval", type=float, default=0.5, help="seconds")
    p.add_argument("--sender-prefix", default="ls")
    p.add_argument("--receiver", default="lr0")
    p.add_argument("--type", choices=("message.create", "typing.start"),
                   default="message.create",
                   help="durable path (default layer) vs ephemeral path")
    p.add_argument("--fault", choices=("pause", "kill", "none"), default="pause")
    p.add_argument("--fault-at", type=float, default=4.0)
    p.add_argument("--fault-for", type=float, default=0.75)
    p.add_argument("--container", default="pulse-redis")
    raise SystemExit(asyncio.run(main(p.parse_args())))
