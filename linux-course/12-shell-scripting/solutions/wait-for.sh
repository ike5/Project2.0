#!/usr/bin/env bash
# Challenge 12, task 3: wait until host:port is reachable, or time out.
set -euo pipefail

host="${1:?usage: $0 <host> <port> [timeout-seconds]}"
port="${2:?usage: $0 <host> <port> [timeout-seconds]}"
timeout="${3:-30}"

echo "waiting up to ${timeout}s for ${host}:${port} ..."
for (( i=0; i<timeout; i++ )); do
  if nc -z -w1 "$host" "$port" 2>/dev/null; then
    echo "${host}:${port} is up (after ${i}s)"
    exit 0
  fi
  sleep 1
done

echo "timed out waiting for ${host}:${port}" >&2
exit 1
