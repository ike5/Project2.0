"""Stress test — compare LFUCache against a naive O(n) reference.

Run me: python 12-capstone/code/lfu_stress.py
"""

import random
from lfu_cache import LFUCache


class NaiveLFU:
    """Reference: track (freq, recency) per key, evict the min tuple."""

    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.vals: dict[int, int] = {}
        self.counts: dict[int, int] = {}
        self.recency: dict[int, int] = {}      # tick when key was last touched
        self._tick = 0

    def get(self, key: int) -> int:
        if key not in self.vals:
            return -1
        self.counts[key] += 1
        self._tick += 1
        self.recency[key] = self._tick
        return self.vals[key]

    def put(self, key: int, value: int) -> None:
        if self.cap == 0:
            return
        self._tick += 1
        if key in self.vals:
            self.vals[key] = value
            self.counts[key] += 1
            self.recency[key] = self._tick
            return
        if len(self.vals) >= self.cap:
            # evict key with min (count, recency) — note: low recency = older = evict
            evict = min(self.vals, key=lambda k: (self.counts[k], self.recency[k]))
            del self.vals[evict]
            del self.counts[evict]
            del self.recency[evict]
        self.vals[key] = value
        self.counts[key] = 1
        self.recency[key] = self._tick


def stress(seed: int = 0, n_ops: int = 5_000, cap: int = 20) -> None:
    random.seed(seed)
    real = LFUCache(cap)
    ref = NaiveLFU(cap)
    for _ in range(n_ops):
        op = random.choice(("get", "put"))
        k = random.randint(0, 50)
        if op == "get":
            assert real.get(k) == ref.get(k), f"mismatch on get({k})"
        else:
            v = random.randint(0, 10_000)
            real.put(k, v)
            ref.put(k, v)
    print(f"OK: {n_ops} ops, capacity {cap}, all consistent.")


if __name__ == "__main__":
    stress()
