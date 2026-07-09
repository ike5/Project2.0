"""Reference solution for challenge 12."""

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

    def put(self, key: int, value: int) -> bool:
        """Return True if an eviction happened."""
        if self.cap == 0:
            return False
        if key in self.vals:
            self.vals[key] = value
            self._bump(key)
            return False
        evicted = False
        if len(self.vals) >= self.cap:
            evict_key, _ = self.buckets[self.min_freq].popitem(last=False)
            del self.vals[evict_key]
            del self.counts[evict_key]
            evicted = True
        self.vals[key] = value
        self.counts[key] = 1
        self.buckets[1][key] = None
        self.min_freq = 1
        return evicted

    def clear(self) -> None:
        self.vals.clear()
        self.counts.clear()
        self.buckets.clear()
        self.min_freq = 0

    def __contains__(self, key: int) -> bool:
        return key in self.vals

    def __repr__(self) -> str:
        return f"LFUCache(cap={self.cap}, size={len(self.vals)}, min_freq={self.min_freq})"
