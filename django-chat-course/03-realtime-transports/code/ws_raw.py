#!/usr/bin/env python3
"""A minimal WebSocket client: handshake + frame codec, no libraries.

Talks to the Module 03 lab's /ws-raw echo consumer under Uvicorn on :8000.
Demonstrates that the handshake and framing are just bytes — the same bytes
Uvicorn's `websockets` layer produces and accepts.
"""
import base64
import hashlib
import os
import socket
import struct

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def encode(payload: bytes, opcode: int = 0x1, mask: bool = True) -> bytes:
    frame = bytearray()
    frame.append(0x80 | opcode)                       # FIN=1

    n = len(payload)
    mask_bit = 0x80 if mask else 0x00
    if n < 126:
        frame.append(mask_bit | n)
    elif n < 65536:
        frame.append(mask_bit | 126)
        frame += struct.pack(">H", n)                 # 16-bit
    else:
        frame.append(mask_bit | 127)
        frame += struct.pack(">Q", n)                 # 64-bit

    if mask:
        key = os.urandom(4)
        frame += key
        frame += bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    else:
        frame += payload
    return bytes(frame)


def handshake(sock, host, path):
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f"GET {path} HTTP/1.1\r\n"
           f"Host: {host}\r\n"
           f"Upgrade: websocket\r\n"
           f"Connection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\n"
           f"Sec-WebSocket-Version: 13\r\n\r\n")
    sock.sendall(req.encode())

    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += sock.recv(4096)
    head = resp.split(b"\r\n\r\n")[0].decode()
    assert "101" in head.split("\r\n")[0], head

    expected = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    got = [l.split(": ", 1)[1] for l in head.split("\r\n")
           if l.lower().startswith("sec-websocket-accept")][0]
    assert got == expected, f"accept mismatch: {got} != {expected}"
    print(f"handshake OK  key={key}  accept={got}")
    return resp.split(b"\r\n\r\n", 1)[1]


def read_frame(sock, buffered=b""):
    def need(n, buf):
        while len(buf) < n:
            buf += sock.recv(4096)
        return buf

    buf = need(2, buffered)
    length = buf[1] & 0x7F
    i = 2
    if length == 126:
        buf = need(4, buf); length = struct.unpack(">H", buf[2:4])[0]; i = 4
    elif length == 127:
        buf = need(10, buf); length = struct.unpack(">Q", buf[2:10])[0]; i = 10
    buf = need(i + length, buf)
    return buf[i:i + length], buf[i + length:]


if __name__ == "__main__":
    s = socket.create_connection(("localhost", 8000))
    rest = handshake(s, "localhost:8000", "/ws-raw")
    payload, rest = read_frame(s, rest)
    print("server said:", payload.decode())

    for size in (2, 200, 70000):
        body = b"x" * size
        frame = encode(body)
        header_len = len(frame) - size - 4       # minus the 4-byte mask key
        print(f"payload={size:6d}  header={header_len} bytes  first_bytes={frame[:4].hex()}")

    s.sendall(encode(b"hello from raw python"))
    payload, rest = read_frame(s, rest)
    print("echo:", payload.decode())
    s.sendall(encode(b"", opcode=0x8))           # close
    s.close()
