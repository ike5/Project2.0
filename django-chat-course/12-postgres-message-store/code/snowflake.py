"""Snowflake ID generator for Pulse — Module 12.

64 bits, time-sortable, coordination-free:

  ┌────────────────────────────┬───────────┬──────────────┐
  │  41-bit millisecond time   │ 10-bit    │  12-bit       │
  │  (since PULSE_EPOCH)       │ worker id │  per-ms seq   │
  └────────────────────────────┴───────────┴──────────────┘

The worker id comes from an env var (one per worker PROCESS — remember the
process-per-core model from Module 01), so two processes never collide without
ever coordinating. That property is what makes Module 14's sharding a migration
instead of an impossibility: a central bigserial cannot span independent
databases, a Snowflake can.

timestamp_of(id) recovers the creation time, which Module 13 uses to derive a
partition-pruning time hint for the scrollback query.
"""

from __future__ import annotations

import os
import threading
import time

# A fixed custom epoch buys ~69 years of 41-bit millisecond range from here
# rather than from 1970. 2024-01-01T00:00:00Z:
PULSE_EPOCH_MS = 1_704_067_200_000

WORKER_ID_BITS = 10
SEQUENCE_BITS = 12

MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1          # 1023
SEQUENCE_MASK = (1 << SEQUENCE_BITS) - 1           # 4095

WORKER_ID_SHIFT = SEQUENCE_BITS                    # 12
TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS   # 22


class Snowflake:
    """Thread-safe within a process. One instance per worker process."""

    def __init__(self, worker_id: int | None = None) -> None:
        if worker_id is None:
            worker_id = int(os.getenv("PULSE_WORKER_ID", "0"))
        if not 0 <= worker_id <= MAX_WORKER_ID:
            raise ValueError(f"worker_id must be 0..{MAX_WORKER_ID}, got {worker_id}")
        self._worker_id = worker_id
        self._lock = threading.Lock()
        self._last_ms = -1
        self._seq = 0

    def next_id(self) -> int:
        with self._lock:
            now = int(time.time() * 1000)
            if now < self._last_ms:
                # Clock moved backwards (NTP step). Wait it out rather than emit a
                # non-monotonic id — monotonicity is the whole point.
                now = self._wait_until(self._last_ms)
            if now == self._last_ms:
                self._seq = (self._seq + 1) & SEQUENCE_MASK
                if self._seq == 0:                 # 4096 ids this ms; spill to next
                    now = self._wait_until(self._last_ms + 1)
            else:
                self._seq = 0
            self._last_ms = now
            return (((now - PULSE_EPOCH_MS) << TIMESTAMP_SHIFT)
                    | (self._worker_id << WORKER_ID_SHIFT)
                    | self._seq)

    @staticmethod
    def _wait_until(target_ms: int) -> int:
        now = int(time.time() * 1000)
        while now < target_ms:
            time.sleep((target_ms - now) / 1000.0)
            now = int(time.time() * 1000)
        return now


def timestamp_of(snowflake_id: int) -> int:
    """Unix-ms creation time embedded in a Snowflake id. Used by Module 13's
    scrollback time hint to prune partitions."""
    return (snowflake_id >> TIMESTAMP_SHIFT) + PULSE_EPOCH_MS
