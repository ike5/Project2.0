"""
code/locust_storm.py — the presence storm and the thundering herd, in Locust.

    locust -f code/locust_storm.py --headless -u 2000 -r 2000 \
           --run-time 3m --host http://localhost:8000

Two shapes in one file, selected by PULSE_STORM:

    PULSE_STORM=herd      every user disconnects at T+60s and reconnects with the
                          backoff policy in PULSE_BACKOFF (fixed | base_jitter |
                          full_jitter). This is the deploy/failover shape.

    PULSE_STORM=steady    users connect once and heartbeat. This is the baseline
                          you subtract from the herd numbers.

WHY LOCUST AND NOT k6 HERE
--------------------------
k6 remains the primary load generator in this course (Module 06) and it is the
better tool for a raw connection-count wall: it is Go, one goroutine per VU, and
it will happily hold 20,000 sockets on a laptop. Locust is Python, and at these
counts a Python load generator competes with the Python server for the same CPU.

Use it anyway, for two honest reasons. First, this audience writes Python, and a
load scenario you can actually modify beats one you copy-paste. Second — and this
is the pedagogical point — Locust's per-user model makes *stateful* client
behaviour (a cursor, a backoff schedule, a heartbeat timer) natural to express,
where k6's model does not.

⚠️ COORDINATED OMISSION. Locust measures the time from "I sent the request" to
"I got a response," and a user that is blocked waiting does not start its next
request. When the server slows down, Locust slows down with it and stops
generating the load that would have revealed how bad it is. Module 06 covers this
at length. The rule here: **use Locust for the shape of the storm, use k6 and the
server's own histograms for the latency numbers.** Every latency figure in this
module's lab comes from `pulse_*_seconds` on the server side, not from Locust.
"""

from __future__ import annotations

import json
import os
import random
import time

import gevent
from locust import User, between, events, task
from websocket import WebSocketException, create_connection

HOST = os.environ.get("PULSE_WS_HOST", "localhost:8000")
STORM = os.environ.get("PULSE_STORM", "herd")
BACKOFF = os.environ.get("PULSE_BACKOFF", "full_jitter")
ROOMS = int(os.environ.get("PULSE_ROOMS", "100"))
ROOMS_PER_USER = int(os.environ.get("PULSE_ROOMS_PER_USER", "1"))
CUT_AT_S = float(os.environ.get("PULSE_CUT_AT", "60"))

_start = time.time()


def backoff_delay(attempt: int) -> float:
    base = min(30.0, 1.0 * 2**attempt)
    if BACKOFF == "fixed":
        return 1.0
    if BACKOFF == "base_jitter":
        # The one that FEELS like jitter and is not: everyone still waits at
        # least `base`, then arrives inside a narrow window. You delayed the
        # herd; you did not disperse it.
        return base + random.random()
    return random.random() * base  # full jitter


class PulseUser(User):
    wait_time = between(1, 1)

    def on_start(self) -> None:
        self.uid = f"u{random.randrange(1_000_000)}"
        self.rooms = random.sample(range(ROOMS), ROOMS_PER_USER)
        self.attempt = 0
        self.cut_done = False
        self.ws = None
        self._connect()
        gevent.spawn(self._heartbeat_forever)

    def _connect(self) -> None:
        room = self.rooms[0]
        started = time.perf_counter()
        try:
            self.ws = create_connection(
                f"ws://{HOST}/ws/room/{room}/?as={self.uid}",
                subprotocols=["pulse.v1"],
                timeout=30,
            )
            for r in self.rooms:
                self.ws.send(json.dumps(
                    {"v": 1, "type": "join", "room": f"room.{r}", "data": {}}))
            events.request.fire(
                request_type="WS", name="connect",
                response_time=(time.perf_counter() - started) * 1000,
                response_length=0, exception=None, context={})
            self.attempt = 0
        except (WebSocketException, OSError) as exc:
            events.request.fire(
                request_type="WS", name="connect",
                response_time=(time.perf_counter() - started) * 1000,
                response_length=0, exception=exc, context={})
            self.attempt += 1
            gevent.sleep(backoff_delay(self.attempt))
            self._connect()

    def _heartbeat_forever(self) -> None:
        """protocol §3.4: a ping every 10 s, which also refreshes presence AND
        the channel-layer group membership (the group_expiry fix)."""
        while True:
            gevent.sleep(10)
            try:
                for r in self.rooms:
                    self.ws.send(json.dumps(
                        {"v": 1, "type": "ping", "room": f"room.{r}",
                         "data": {"ts": int(time.time() * 1000)}}))
            except Exception:
                return

    @task
    def talk(self) -> None:
        if STORM == "herd" and not self.cut_done and time.time() - _start > CUT_AT_S:
            # THE HERD. Every user drops at the same instant — a deploy, a
            # failover, an nginx reload. What happens next is entirely decided by
            # the backoff policy.
            self.cut_done = True
            try:
                self.ws.close()
            except Exception:
                pass
            self.attempt = 1
            gevent.sleep(backoff_delay(self.attempt))
            self._connect()
            return

        room = f"room.{random.choice(self.rooms)}"
        started = time.perf_counter()
        try:
            self.ws.send(json.dumps({
                "v": 1, "type": "message.create", "room": room,
                "data": {"client_id": f"{self.uid}-{time.time_ns()}",
                         "body": "locust"},
            }))
            events.request.fire(
                request_type="WS", name="message.create",
                response_time=(time.perf_counter() - started) * 1000,
                response_length=0, exception=None, context={})
        except Exception as exc:
            events.request.fire(
                request_type="WS", name="message.create",
                response_time=(time.perf_counter() - started) * 1000,
                response_length=0, exception=exc, context={})
            self._connect()
