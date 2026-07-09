"""LRU Cache.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/09-lru-cache/solution.py
"""



class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self._data: dict[int, int] = {}
        self._order: list[int] = []   # most recent first

    def get(self, key: int) -> int:
        if key not in self._data:
            return -1
        self._order.remove(key)
        self._order.insert(0, key)
        return self._data[key]

    def put(self, key: int, value: int) -> None:
        if key in self._data:
            self._order.remove(key)
        elif len(self._data) >= self.cap:
            lru = self._order.pop()
            del self._data[lru]
        self._data[key] = value
        self._order.insert(0, key)


def _self_test() -> None:
    pass  # no tests
    print(f"all 0 tests passed for LRUCache")


if __name__ == "__main__":
    _self_test()
