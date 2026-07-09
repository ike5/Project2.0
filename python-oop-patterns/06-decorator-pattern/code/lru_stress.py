"""Stress test — compare LRUCache against a naive reference.

Run me: python 06-decorator-pattern/code/lru_stress.py
"""

import random
from lru_cache import LRUCache


class NaiveLRU:
    """Reference implementation: O(n) per op, but obviously correct."""

    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.data: dict[int, int] = {}
        self.order: list[int] = []     # index 0 = LRU

    def get(self, key: int) -> int:
        if key not in self.data:
            return -1
        self.order.remove(key)
        self.order.append(key)
        return self.data[key]

    def put(self, key: int, value: int) -> None:
        if key in self.data:
            self.order.remove(key)
        self.data[key] = value
        self.order.append(key)
        if len(self.data) > self.cap:
            evict = self.order.pop(0)
            del self.data[evict]


def stress(seed: int = 0, n_ops: int = 10_000, cap: int = 50) -> None:
    random.seed(seed)
    real = LRUCache(cap)
    ref = NaiveLRU(cap)
    for _ in range(n_ops):
        op = random.choice(("get", "put"))
        if op == "get":
            k = random.randint(0, 100)
            assert real.get(k) == ref.get(k), f"mismatch on get({k})"
        else:
            k = random.randint(0, 100)
            v = random.randint(0, 10_000)
            real.put(k, v)
            ref.put(k, v)
    print(f"OK: {n_ops} ops, capacity {cap}, all consistent.")


if __name__ == "__main__":
    stress()
