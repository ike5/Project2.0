#!/usr/bin/env python3
"""Pulse wire protocol v1 — the codec, as a standalone module.

This is the reference copy of what the lab writes into `chat/protocol.py`. It
has no Django imports, so it can be used by load generators (Module 06), the
Streams consumer (Module 09), the outbox relay (Module 13), the Kafka
comparison (Module 16), and tests — all of which need to speak the protocol
without booting Django.

Normative reference: ./pulse-protocol-v1.md

The one rule this file exists to enforce:

    STRICT inbound (client -> server): unknown types and unexpected fields are
    errors, because a client sending a field you do not honour is a client
    whose author believes it works.

    TOLERANT outbound-shaped parsing: unknown keys are ignored and preserved,
    because forward compatibility means surviving fields you have never heard
    of.

Run it directly for a self-test:

    python envelope.py
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

PROTOCOL_VERSION = 1
SUBPROTOCOL = f"pulse.v{PROTOCOL_VERSION}"

MAX_BODY = 4096                 # characters, after .strip()
MIN_CLIENT_ID = 10
MAX_CLIENT_ID = 64

# The allowlist IS the schema. Nothing outside it may reach a group_send.
CLIENT_FIELDS: dict[str, set[str]] = {
    "message.create": {"client_id", "body", "reply_to"},
    "message.edit":   {"id", "body"},
    "message.delete": {"id"},
    "typing.start":   set(),
    "read.upto":      {"seq"},
    "resume":         {"from_seq"},
    "ping":           {"ts"},
}

REQUIRED_FIELDS: dict[str, set[str]] = {
    "message.create": {"client_id", "body"},
    "message.edit":   {"id", "body"},
    "message.delete": {"id"},
    "read.upto":      {"seq"},
    "resume":         {"from_seq"},
}

# Internal channel-layer event types. These MUST NOT be accepted from a client;
# they are listed here so the rejection is explicit rather than incidental.
INTERNAL_TYPES = frozenset({
    "chat.message", "chat.revoke", "chat.overflow", "chat.control", "worker.beat",
})


def now_ms() -> int:
    return int(time.time() * 1000)


class ProtocolError(Exception):
    """A protocol violation that becomes an `error` FRAME, never a disconnect."""

    def __init__(self, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.extra = extra

    def frame(self, room: str = "", client_id: str | None = None) -> dict:
        data: dict[str, Any] = {"code": self.code, "message": self.message}
        data.update(self.extra)
        if client_id:
            data["client_id"] = client_id
        return envelope("error", room, now_ms(), **data)


@dataclass(slots=True)
class Inbound:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


def parse_inbound(raw: Any) -> Inbound:
    """Validate one client -> server frame. Raises ProtocolError."""
    if not isinstance(raw, dict):
        raise ProtocolError("bad_frame", "frame must be a JSON object")

    v = raw.get("v", PROTOCOL_VERSION)
    if not isinstance(v, int) or v > PROTOCOL_VERSION:
        raise ProtocolError(
            "unsupported_version",
            f"this server speaks protocol v{PROTOCOL_VERSION}",
            server_version=PROTOCOL_VERSION, client_version=v)

    mtype = raw.get("type")
    if mtype in INTERNAL_TYPES:
        # Explicit, because "it happens not to be in CLIENT_FIELDS" is a
        # property that a future refactor could silently remove.
        raise ProtocolError("unknown_type",
                            f"{mtype!r} is an internal event type")

    allowed = CLIENT_FIELDS.get(mtype)
    if allowed is None:
        raise ProtocolError("unknown_type", f"unknown type {mtype!r}")

    data = raw.get("data")
    if data is None:
        # Module 04 spoke flat frames (no `data` wrapper). Accept both shapes so
        # a pre-v1 client is not broken by this module landing.
        data = {k: val for k, val in raw.items()
                if k not in {"v", "type", "room", "ts"}}
    if not isinstance(data, dict):
        raise ProtocolError("bad_frame", "`data` must be an object")

    extra = set(data) - allowed
    if extra:
        raise ProtocolError("unexpected_fields",
                            "fields this server does not honour",
                            fields=sorted(extra)[:8])

    missing = REQUIRED_FIELDS.get(mtype, set()) - set(data)
    if missing:
        raise ProtocolError("missing_fields", "required fields absent",
                            fields=sorted(missing))

    if mtype == "message.create":
        _validate_create(data)
    elif mtype in {"read.upto", "resume"}:
        key = "seq" if mtype == "read.upto" else "from_seq"
        if not isinstance(data[key], int) or data[key] < 0:
            raise ProtocolError("bad_field", f"{key} must be a non-negative int")

    return Inbound(type=mtype, data=data)


def _validate_create(data: dict) -> None:
    body = data.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ProtocolError("empty_body", "body must be a non-empty string")
    if len(body) > MAX_BODY:
        raise ProtocolError("body_too_long", f"body exceeds {MAX_BODY} chars",
                            max=MAX_BODY, got=len(body))
    cid = data.get("client_id")
    if not isinstance(cid, str) or not (MIN_CLIENT_ID <= len(cid) <= MAX_CLIENT_ID):
        raise ProtocolError(
            "bad_client_id",
            f"client_id must be a {MIN_CLIENT_ID}-{MAX_CLIENT_ID} char string")
    reply_to = data.get("reply_to")
    if reply_to is not None and not isinstance(reply_to, int):
        raise ProtocolError("bad_field", "reply_to must be an int or absent")


def envelope(mtype: str, room: str, ts: int, **data: Any) -> dict:
    """Build one server -> client frame. Every outbound frame goes through here."""
    return {"v": PROTOCOL_VERSION, "type": mtype, "room": room, "ts": ts,
            "data": data}


def dumps(frame: dict) -> str:
    """Compact encoding. `separators` is free and saves ~8% on the wire.

    Module 15 swaps this for orjson.dumps (4.2x on the reference machine); the
    call site is here precisely so that swap is one line.
    """
    return json.dumps(frame, separators=(",", ":"), ensure_ascii=False)


# --------------------------------------------------------------------------
# Client-side helpers: gap detection. The server cannot do this for you --
# only the receiver knows what it received.
# --------------------------------------------------------------------------
class GapDetector:
    """Track per-room seq continuity. `observe()` returns the missing range."""

    def __init__(self) -> None:
        self._last: dict[str, int] = {}

    def observe(self, room: str, seq: int) -> tuple[int, int] | None:
        last = self._last.get(room)
        self._last[room] = max(seq, last or seq)
        if last is None or seq <= last:
            return None                      # first message, or a duplicate
        if seq == last + 1:
            return None                      # contiguous
        return (last + 1, seq - 1)           # inclusive range of missing seqs

    def cursor(self, room: str) -> int:
        return self._last.get(room, 0)


def _selftest() -> None:
    from itertools import count

    ok = {"v": 1, "type": "message.create",
          "data": {"client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH", "body": "hi"}}
    assert parse_inbound(ok).type == "message.create"

    bad = [
        ({"type": "chat.message", "data": {}}, "unknown_type"),
        ({"type": "message.create",
          "data": {"client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH",
                   "body": "x", "sender": "admin"}}, "unexpected_fields"),
        ({"type": "message.create",
          "data": {"client_id": "short", "body": "x"}}, "bad_client_id"),
        ({"type": "message.create",
          "data": {"client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH",
                   "body": " "}}, "empty_body"),
        ({"v": 9, "type": "ping", "data": {}}, "unsupported_version"),
        ({"type": "message.create", "data": {"body": "x"}}, "missing_fields"),
        ("not a dict", "bad_frame"),
    ]
    for frame, expected in bad:
        try:
            parse_inbound(frame)
        except ProtocolError as exc:
            assert exc.code == expected, f"{frame} -> {exc.code}, want {expected}"
        else:                                             # pragma: no cover
            raise AssertionError(f"{frame} should have raised {expected}")

    # Pre-v1 flat frames still parse.
    flat = {"type": "message.create",
            "client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH", "body": "hi"}
    assert parse_inbound(flat).data["body"] == "hi"

    g = GapDetector()
    seqs, gaps = [1, 2, 3, 7, 8, 12], []
    for s in seqs:
        r = g.observe("room.7", s)
        if r:
            gaps.append(r)
    assert gaps == [(4, 6), (9, 11)], gaps
    assert g.cursor("room.7") == 12

    env = envelope("message.new", "room.7", 1735689600123,
                   id=next(count(7241938)), seq=48213, client_id="01JQ",
                   sender="alice", body="ok")
    encoded = dumps(env)
    assert json.loads(encoded)["data"]["seq"] == 48213
    print(f"selftest OK   envelope={len(encoded)} bytes for a "
          f"{len(env['data']['body'])}-byte body "
          f"({len(encoded) / len(env['data']['body']):.0f}x overhead)")


if __name__ == "__main__":
    _selftest()
