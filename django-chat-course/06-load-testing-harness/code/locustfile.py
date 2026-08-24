#!/usr/bin/env python3
"""Pulse load generator, Locust edition -- the Python-native half of Module 06.

Two user classes, deliberately:

    ChatUser        the honest one. Paced sends, a dedicated receiver
                    greenlet, latency taken from the sender's clock carried
                    in the message body. This is what you run.

    ClosedLoopUser  the obvious one, and the wrong one. Send, block on recv,
                    repeat. It exists so you can watch coordinated omission
                    happen to your own numbers rather than reading about it.

    locust -f code/locustfile.py ChatUser       --processes 8 --headless \
           -u 20000 -r 500 -t 6m --csv=/tmp/pulse
    locust -f code/locustfile.py ClosedLoopUser --processes 8 --headless \
           -u 2000 -r 200 -t 3m

Conforms to ../../05-protocol-and-domain-design/code/pulse-protocol-v1.md:
frames are `{"v":1,"type":...,"data":{...}}`, message.create carries
`client_id` + `body` and nothing else (the server's allowlist rejects extras),
and the room slug in the URL is the BARE handle while the envelope's `room`
field is the composed `room.<slug>`.

Locust is gevent, so `websocket-client`'s blocking calls are cooperative. Two
consequences you must hold in your head:
  * one Locust process is one core, same GIL story as your server -- use
    `--processes N` and watch generator CPU every run;
  * an unpatched C extension inside a task blocks every other user in that
    process, which is the event-loop lesson wearing a different hat.
"""

from __future__ import annotations

import json
import os
import random
import statistics
import time
import uuid

import gevent
import websocket
from locust import User, constant_throughput, events, task

HOST = os.getenv("PULSE_HOST", "localhost:8000")
WS_PATH = os.getenv("WS_PATH", "/ws/room")
ROOMS = int(os.getenv("ROOMS", "100"))
SEND_EVERY = float(os.getenv("SEND_EVERY", "60000")) / 1000.0   # seconds
BODY_PAD = "x" * int(os.getenv("BODY_PAD", "40"))

# Raw samples, so the report at the end does not depend on Locust's rounded
# response-time buckets. Locust's console percentiles are approximations built
# from those buckets: fine at p50, increasingly wrong at p99.9, which is
# precisely the number this course argues about.
FANOUT_SAMPLES: list[float] = []


class PulseSocketMixin:
    """Everything both user classes share: connect, envelope, teardown."""

    abstract = True

    def _open(self) -> None:
        self.slug = str(random.randrange(ROOMS))
        self.room = f"room.{self.slug}"          # the composed key: group name
        self.username = f"lu{uuid.uuid4().hex[:10]}"  # and envelope `room`
        self.cid_prefix = uuid.uuid4().hex[:8]
        self.counter = 0
        self.last_seq = 0
        # The DEBUG-only ?as= shim from Module 04. Module 21 replaces it with
        # a signed single-use ticket and this becomes ?ticket=<...>.
        self.ws = websocket.create_connection(
            f"ws://{HOST}{WS_PATH}/{self.slug}/?as={self.username}",
            timeout=15,
            subprotocols=["pulse.v1"],
        )

    def _frame(self) -> str:
        self.counter += 1
        return json.dumps({
            "v": 1,
            "type": "message.create",
            "data": {
                "client_id": f"{self.cid_prefix}-{self.counter}-{time.time_ns()}",
                # The sender's clock, inside the body, because the protocol's
                # allowlist has nowhere else to put it. The receiver subtracts.
                "body": f"t={time.time():.6f} {BODY_PAD}",
            },
        })

    def _fire(self, name: str, ms: float, length: int = 0, exc=None) -> None:
        events.request.fire(
            request_type="WS", name=name, response_time=ms,
            response_length=length, exception=exc, context={"room": self.room},
        )

    def _handle(self, raw: str, now: float) -> None:
        try:
            env = json.loads(raw)
        except ValueError:
            return
        etype = env.get("type")
        if etype == "message.new":
            data = env.get("data", {})
            body = data.get("body", "")
            if body.startswith("t="):
                sent_at = float(body.split(None, 1)[0][2:])
                ms = (now - sent_at) * 1000.0
                FANOUT_SAMPLES.append(ms)
                # THE NUMBER: a sender's send() -> THIS receiver's socket.
                self._fire("fanout", ms, length=len(raw))
            seq = data.get("seq", 0)
            if self.last_seq and seq > self.last_seq + 1:
                self._fire("sequence_gap", 0, exc=Exception(
                    f"gap {self.last_seq + 1}..{seq - 1} in {self.room}"))
            self.last_seq = max(self.last_seq, seq)
        elif etype == "error":
            self._fire("error_frame", 0, exc=Exception(
                env.get("data", {}).get("code", "?")))

    def on_stop(self) -> None:
        self._stop = True
        try:
            self.ws.close()
        except Exception:
            pass


class ChatUser(PulseSocketMixin, User):
    """The honest user. Sends on a pace; never blocks a send on a receive."""

    # constant_throughput targets N iterations/second per user regardless of
    # how long the last one took. If an iteration overruns the period it waits
    # zero -- and the resulting shortfall in achieved RPS is the honest signal
    # that you failed to offer the load you intended. Look at it every run.
    wait_time = constant_throughput(1.0 / SEND_EVERY)

    def on_start(self) -> None:
        self._open()
        self._stop = False
        # The line that makes this open-ish: a receiver greenlet, so a slow
        # server slows down deliveries WITHOUT slowing down our send rate.
        self._pump = gevent.spawn(self._receive_loop)

    def _receive_loop(self) -> None:
        while not self._stop:
            try:
                raw = self.ws.recv()
            except (websocket.WebSocketConnectionClosedException, OSError) as exc:
                if not self._stop:
                    self._fire("ws_recv", 0, exc=exc)
                return
            if not raw:
                return
            self._handle(raw, time.time())

    @task
    def send_message(self) -> None:
        payload = self._frame()
        t0 = time.time()
        try:
            self.ws.send(payload)
        except Exception as exc:                       # noqa: BLE001
            self._fire("ws_send", (time.time() - t0) * 1000, exc=exc)
            return
        # Record the SEND cost only. Do NOT recv() here -- that is the trap.
        self._fire("ws_send", (time.time() - t0) * 1000, length=len(payload))

    def on_stop(self) -> None:
        super().on_stop()
        self._pump.kill(block=False)


class ClosedLoopUser(PulseSocketMixin, User):
    """The trap, kept runnable so you can measure how much it lies.

    Send, then block until something comes back, then send again. When the
    server slows down, this user sends LESS -- it responds to overload by
    reducing load -- and it only records latencies for requests that made it
    through. Every sample it *would* have taken during a stall is simply
    absent from the data.
    """

    wait_time = constant_throughput(1.0 / SEND_EVERY)

    def on_start(self) -> None:
        self._open()
        self._stop = False
        self.ws.settimeout(30)

    @task
    def send_and_wait(self) -> None:
        payload = self._frame()
        t0 = time.time()
        try:
            self.ws.send(payload)
            while True:                      # <-- the coordinated omission
                raw = self.ws.recv()         #     lives on this line
                env = json.loads(raw)
                if env.get("type") == "message.new":
                    break
        except Exception as exc:                       # noqa: BLE001
            self._fire("closed_loop_rt", (time.time() - t0) * 1000, exc=exc)
            return
        ms = (time.time() - t0) * 1000.0
        FANOUT_SAMPLES.append(ms)
        self._fire("closed_loop_rt", ms, length=len(raw))


@events.quitting.add_listener
def _report(environment, **_kw) -> None:
    """Percentiles from RAW samples, not from Locust's rounded buckets."""
    if not FANOUT_SAMPLES:
        return
    s = sorted(FANOUT_SAMPLES)

    def pct(p: float) -> float:
        return s[min(len(s) - 1, int(len(s) * p / 100.0))]

    print("\n--- fan-out latency, raw samples ------------------------------")
    print(f"  samples : {len(s):,}")
    print(f"  mean    : {statistics.fmean(s):8.1f} ms")
    for p in (50, 95, 99, 99.9):
        print(f"  p{p:<6}: {pct(p):8.1f} ms")
    print(f"  max     : {s[-1]:8.1f} ms")
    print("---------------------------------------------------------------\n")
