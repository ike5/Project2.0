#!/usr/bin/env bash
# A tiny long-running "service" for the systemd lab: logs a heartbeat every 5s.
# Install to /usr/local/bin/hello.sh and make it executable (chmod +x).
set -euo pipefail

while true; do
    echo "hello service alive at $(date -Is)"
    sleep 5
done
