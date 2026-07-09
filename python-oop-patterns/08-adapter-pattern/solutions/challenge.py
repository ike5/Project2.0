"""Reference solutions for challenge 08."""

import bisect


class MinStack:
    def __init__(self) -> None:
        self.stack: list[int] = []
        self.mins: list[int] = []

    def push(self, val: int) -> None:
        self.stack.append(val)
        if not self.mins:
            self.mins.append(val)
        else:
            self.mins.append(min(val, self.mins[-1]))

    def pop(self) -> None:
        self.stack.pop()
        self.mins.pop()

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.mins[-1]


class SortedStack:
    def __init__(self) -> None:
        self._data: list[int] = []

    def push(self, val: int) -> None:
        bisect.insort(self._data, val)   # O(n) per push, but list stays sorted

    def pop(self) -> int:
        return self._data.pop(0)         # smallest is at the front

    def peek(self) -> int:
        return self._data[0]

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"SortedStack({self._data})"
