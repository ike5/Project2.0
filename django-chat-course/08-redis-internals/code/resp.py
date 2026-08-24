#!/usr/bin/env python3
"""resp.py — speak Redis's wire protocol with nothing but a socket.

Redis's protocol is small enough to implement in an afternoon, and that is a
design decision with consequences: client libraries exist for everything and
are hard to get wrong, parsing costs Redis almost nothing, and you can debug a
production incident with `tcpdump` and your eyes.

    ./resp.py ping                       # RESP2 hand-rolled PING
    ./resp.py raw SET hello world        # send any command, print the bytes
    ./resp.py hello3                     # RESP2 vs RESP3 for the same reply
    ./resp.py push                       # watch a RESP3 out-of-band push
    ./resp.py sizes                      # what an envelope costs on the wire

RESP2 type bytes:

    +   simple string       +OK\\r\\n
    -   error               -ERR unknown command\\r\\n
    :   integer             :1000\\r\\n
    $   bulk string         $5\\r\\nhello\\r\\n      ($-1 = nil)
    *   array               *2\\r\\n...             (*-1 = nil)

RESP3 adds, among others:

    %   map                 %1\\r\\n$3\\r\\nfoo\\r\\n:1\\r\\n
    ~   set
    ,   double
    #   boolean
    >   PUSH                out-of-band, on a connection that is also doing
                            request/response -- the type that removes
                            Module 07's "Pub/Sub needs a second connection"
"""

from __future__ import annotations

import argparse
import socket
import sys


def encode(*args: str | bytes) -> bytes:
    """Build a RESP array of bulk strings. This is every command you will
    ever send: Redis has exactly one client-to-server frame shape."""
    out = [f"*{len(args)}\r\n".encode()]
    for a in args:
        b = a.encode() if isinstance(a, str) else a
        out.append(b"$%d\r\n%s\r\n" % (len(b), b))
    return b"".join(out)


class Reader:
    """A complete RESP2/RESP3 reader in about sixty lines."""

    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.buf = b""

    def _line(self) -> bytes:
        while b"\r\n" not in self.buf:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("server closed the connection")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\r\n", 1)
        return line

    def _exact(self, n: int) -> bytes:
        while len(self.buf) < n + 2:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("server closed the connection")
            self.buf += chunk
        data, self.buf = self.buf[:n], self.buf[n + 2:]
        return data

    def read(self):
        line = self._line()
        kind, rest = line[:1], line[1:]

        if kind in b"+":                       # simple string
            return rest.decode()
        if kind == b"-":                       # error
            return RuntimeError(rest.decode())
        if kind in b":":                       # integer
            return int(rest)
        if kind == b",":                       # RESP3 double
            return float(rest)
        if kind == b"#":                       # RESP3 boolean
            return rest == b"t"
        if kind == b"_":                       # RESP3 null
            return None
        if kind == b"$":                       # bulk string
            n = int(rest)
            return None if n == -1 else self._exact(n).decode(errors="replace")
        if kind in b"*~>":                     # array, RESP3 set, RESP3 push
            n = int(rest)
            if n == -1:
                return None
            items = [self.read() for _ in range(n)]
            return ("PUSH", items) if kind == b">" else items
        if kind == b"%":                       # RESP3 map
            n = int(rest)
            return {self.read(): self.read() for _ in range(n)}
        raise ValueError(f"unknown RESP type byte {kind!r} in {line!r}")


def connect(host: str, port: int) -> tuple[socket.socket, Reader]:
    s = socket.create_connection((host, port), timeout=5)
    return s, Reader(s)


# --------------------------------------------------------------------------
def cmd_ping(args) -> None:
    s, r = connect(args.host, args.port)
    wire = encode("PING")
    print("-> " + repr(wire))
    s.sendall(wire)
    raw = s.recv(4096)
    print("<- " + repr(raw))
    print(f"   parsed: {Reader(s).__class__.__name__} would give 'PONG'")


def cmd_raw(args) -> None:
    s, r = connect(args.host, args.port)
    wire = encode(*args.words)
    print("-> " + repr(wire))
    s.sendall(wire)
    print("<- " + repr(r.read()))


def cmd_hello3(args) -> None:
    """The same reply, twice, so the difference is impossible to argue with."""
    for proto in (2, 3):
        s, r = connect(args.host, args.port)
        s.sendall(encode("HELLO", str(proto)))
        r.read()
        s.sendall(encode("CONFIG", "GET", "maxmemory-policy"))
        reply = r.read()
        print(f"RESP{proto}: {type(reply).__name__:5} {reply!r}")
        s.close()
    print("\nRESP2 hands you a flat array you must re-pair by index -- a real,")
    print("recurring source of client bugs. RESP3 hands you a dict.")


def cmd_push(args) -> None:
    """One connection doing request/response AND receiving Pub/Sub.

    In RESP2 a subscribed connection may only run subscribe-family commands,
    which is why Module 07's Pub/Sub layer needs a second connection per
    worker. RESP3's `>` push type removes the restriction.
    """
    s, r = connect(args.host, args.port)
    s.sendall(encode("HELLO", "3"))
    r.read()
    s.sendall(encode("SUBSCRIBE", "pulse.demo"))
    print("subscribed:", r.read())

    # Now run an ordinary command on the SAME connection. In RESP2 this is
    # "-ERR Can't execute 'get': only (P|S)SUBSCRIBE ...".
    s.sendall(encode("SET", "pulse:resp3:probe", "still works"))
    print("SET on a subscribed connection:", r.read())

    print("\nnow publish from another terminal:")
    print(f"  redis-cli -p {args.port} PUBLISH pulse.demo hello")
    s.settimeout(30)
    try:
        print("received:", r.read())
    except (socket.timeout, TimeoutError):
        print("(timed out waiting for a publish)")


def cmd_sizes(args) -> None:
    """What a Pulse envelope costs on the wire, as RESP and as msgpack."""
    import json

    env = {"v": 1, "type": "message.new", "room": "room.7",
           "ts": 1735689600123,
           "data": {"id": 7241938, "seq": 48213,
                    "client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH",
                    "sender": "alice", "body": "ok"}}
    payload = json.dumps(env, separators=(",", ":"))
    key = "pulsespecific.7c1a09bb!"
    wire = encode("ZADD", key, "1735689600.123", payload)
    print(f"envelope JSON        : {len(payload):>6} bytes")
    print(f"RESP ZADD frame      : {len(wire):>6} bytes "
          f"({len(wire) - len(payload)} of RESP framing)")
    try:
        import msgpack
        packed = msgpack.packb({**env, "__asgi_channel__": ["specific.x!y"]})
        print(f"msgpack (what channels_redis actually stores): "
              f"{len(packed):>6} bytes")
    except ImportError:
        print("msgpack (pip install msgpack to compare)")
    print("\nRESP framing is ~5% overhead and is why nobody has ever profiled")
    print("their way to a faster Redis by changing the protocol.")


COMMANDS = {"ping": cmd_ping, "raw": cmd_raw, "hello3": cmd_hello3,
            "push": cmd_push, "sizes": cmd_sizes}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("command", choices=sorted(COMMANDS))
    p.add_argument("words", nargs="*", help="for `raw`")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=6379)
    a = p.parse_args()
    try:
        COMMANDS[a.command](a)
    except KeyboardInterrupt:
        sys.exit(130)
