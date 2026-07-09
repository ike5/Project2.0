"""Time Based Key-Value Store.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-time-based-key-value-store/solution.py
"""



class TimeMap:
    def __init__(self) -> None:
        self._data: dict[str, list[tuple[int, str]]] = {}

    def set(self, key: str, value: str, timestamp: int) -> None:
        self._data.setdefault(key, []).append((timestamp, value))

    def get(self, key: str, timestamp: int) -> str:
        if key not in self._data:
            return ""
        entries = self._data[key]
        lo, hi = 0, len(entries) - 1
        best = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            if entries[mid][0] <= timestamp:
                best = entries[mid][1]
                lo = mid + 1
            else:
                hi = mid - 1
        return best


def _self_test() -> None:
    pass  # no tests
    print(f"all 0 tests passed for TimeMap")


if __name__ == "__main__":
    _self_test()
