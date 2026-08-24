#!/usr/bin/env bash
#
# The headline test of Module 10.
#
# Alice keeps talking. Bob's connection is severed at the network layer for two
# minutes. Bob must end up with EVERY message, exactly once, in order.
#
#   ./code/disconnect_test.sh              # with resume (the fix)
#   PULSE_NO_RESUME=1 ./code/disconnect_test.sh   # without (the break)
#
# The iptables rule uses DROP, not REJECT, deliberately: REJECT sends an RST and
# the client sees an immediate, clean close. DROP sends nothing, so the socket
# hangs exactly the way a phone entering a tunnel does — TCP retransmits, the
# kernel eventually gives up, and the close arrives tens of seconds late. That
# delay is the realistic case and it is where resume earns its keep.
#
# Needs sudo for iptables. On macOS use `pfctl` or run the whole thing inside a
# Linux container; the counts are identical.

set -euo pipefail

ROOM=${ROOM:-room.30}
OUT=${OUT:-/tmp/bob-seqs.txt}
BEFORE=${BEFORE:-40}
DURING=${DURING:-100}
AFTER=${AFTER:-20}
PORT=${PORT:-8000}

: > "$OUT"

cleanup() {
  sudo iptables -D OUTPUT -p tcp --dport "$PORT" -m owner --uid-owner "$(id -u)" -j DROP 2>/dev/null || true
  kill "${BOB:-0}" 2>/dev/null || true
}
trap cleanup EXIT

echo ">>> starting bob (resume=$([ -n "${PULSE_NO_RESUME:-}" ] && echo off || echo on))"
node code/bob_client.js "$ROOM" "$OUT" &
BOB=$!
sleep 3

echo ">>> $BEFORE messages before the cut"
for i in $(seq 1 "$BEFORE"); do
  python manage.py sendmsg "$ROOM" "before-$i" >/dev/null
  sleep 0.1
done

echo ">>> severing bob's connection for 120s"
sudo iptables -I OUTPUT -p tcp --dport "$PORT" -m owner --uid-owner "$(id -u)" -j DROP

for i in $(seq 1 "$DURING"); do
  python manage.py sendmsg "$ROOM" "during-$i" >/dev/null
  sleep 1
done

echo ">>> restoring the network"
sudo iptables -D OUTPUT -p tcp --dport "$PORT" -m owner --uid-owner "$(id -u)" -j DROP

for i in $(seq 1 "$AFTER"); do
  python manage.py sendmsg "$ROOM" "after-$i" >/dev/null
  sleep 0.2
done

echo ">>> waiting 15s for reconnect + resume to settle"
sleep 15
kill "$BOB" 2>/dev/null || true
BOB=0

TOTAL=$(( BEFORE + DURING + AFTER ))
RECEIVED=$(wc -l < "$OUT")
DISTINCT=$(sort -n "$OUT" | uniq | wc -l)
DUPES=$(( RECEIVED - DISTINCT ))
if sort -nc "$OUT" 2>/dev/null; then ORDERED=yes; else ORDERED=no; fi

echo
echo "expected: $TOTAL   received: $RECEIVED   distinct: $DISTINCT   duplicates: $DUPES   arrived in order: $ORDERED"
sort -n "$OUT" | uniq | awk 'NR>1 && $1 != prev+1 {print "GAP: " prev " -> " $1} {prev=$1}'
