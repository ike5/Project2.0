#!/usr/bin/env python3
"""Decode a WebSocket frame given as hex.

Usage:
    ./decode_frame.py 8108 6563 686f 3a20 6869      # server->client "echo: hi"
    ./decode_frame.py 8182 37fa 213d 5f93           # masked client "hi"
"""
import sys

OPCODES = {0x0: "continuation", 0x1: "text", 0x2: "binary",
           0x8: "close", 0x9: "ping", 0xA: "pong"}

data = bytes.fromhex("".join(sys.argv[1:]).replace(" ", ""))
b0, b1 = data[0], data[1]

fin    = (b0 & 0b10000000) >> 7
rsv    = (b0 & 0b01110000) >> 4
opcode = b0 & 0b00001111
masked = (b1 & 0b10000000) >> 7
length = b1 & 0b01111111

i = 2
if length == 126:
    length = int.from_bytes(data[2:4], "big"); i = 4
elif length == 127:
    length = int.from_bytes(data[2:10], "big"); i = 10

key = b""
if masked:
    key = data[i:i + 4]; i += 4

payload = data[i:i + length]
if masked:
    payload = bytes(b ^ key[j % 4] for j, b in enumerate(payload))

print(f"FIN      : {fin}")
print(f"RSV      : {rsv:03b}   (nonzero means an extension like permessage-deflate)")
print(f"opcode   : 0x{opcode:x} ({OPCODES.get(opcode, '?')})")
print(f"MASK     : {masked}" + (f"  key={key.hex()}" if masked else ""))
print(f"length   : {length}")
print(f"overhead : {i} bytes for {length} bytes of payload")
print(f"payload  : {payload!r}")
