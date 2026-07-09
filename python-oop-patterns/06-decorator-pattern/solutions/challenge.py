"""Reference solutions for challenge 06."""

from collections import OrderedDict, defaultdict


class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.cache: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)


class LFUCache:
    """O(1) average LFU.

    - vals[k]            -> value
    - counts[k]          -> frequency
    - buckets[f][k]      -> OrderedDict of keys with frequency f
    - min_freq           -> smallest non-empty frequency
    """

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
