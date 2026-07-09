"""LeetCode 146 — LRU Cache.

Run me: python 06-decorator-pattern/code/lru_cache.py
"""

from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.cache: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)        # mark as recently used
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False) # evict LRU


def main() -> None:
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    print("get(1) =", cache.get(1))     # 1
    cache.put(3, 3)                     # evicts key 2
    print("get(2) =", cache.get(2))     # -1
    cache.put(4, 4)                     # evicts key 1
    print("get(1) =", cache.get(1))     # -1
    print("get(3) =", cache.get(3))     # 3
    print("get(4) =", cache.get(4))     # 4


if __name__ == "__main__":
    main()
