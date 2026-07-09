"""LeetCode 460 — LFU Cache.

Run me: python 12-capstone/code/lfu_cache.py
"""

from collections import OrderedDict, defaultdict


class LFUCache:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.vals: dict[int, int] = {}
        self.counts: dict[int, int] = {}
        self.buckets: dict[int, "OrderedDict[int, None]"] = defaultdict(OrderedDict)
        self.min_freq = 0

    def _bump(self, key: int) -> None:
        f = self.counts[key]
        del self.buckets[f][key]
        if not self.buckets[f] and self.min_freq == f:
            self.min_freq += 1
        self.counts[key] = f + 1
        self.buckets[f + 1][key] = None

    def get(self, key: int) -> int:
        if key not in self.vals:
            return -1
        self._bump(key)
        return self.vals[key]

    def put(self, key: int, value: int) -> None:
        if self.cap == 0:
            return
        if key in self.vals:
            self.vals[key] = value
            self._bump(key)
            return
        if len(self.vals) >= self.cap:
            evict_key, _ = self.buckets[self.min_freq].popitem(last=False)
            del self.vals[evict_key]
            del self.counts[evict_key]
        self.vals[key] = value
        self.counts[key] = 1
        self.buckets[1][key] = None
        self.min_freq = 1


def main() -> None:
    lfu = LFUCache(2)
    lfu.put(1, 1)
    lfu.put(2, 2)
    print("get(1) =", lfu.get(1))   # 1   (freq of 1 becomes 2)
    lfu.put(3, 3)                  # evicts key 2 (lower freq)
    print("get(2) =", lfu.get(2))   # -1
    print("get(3) =", lfu.get(3))   # 3   (freq of 3 becomes 2)
    lfu.put(4, 4)                  # evicts key 1 (lowest freq, tied with 3; LRU among them)
    print("get(1) =", lfu.get(1))   # -1
    print("get(3) =", lfu.get(3))   # 3
    print("get(4) =", lfu.get(4))   # 4


if __name__ == "__main__":
    main()
