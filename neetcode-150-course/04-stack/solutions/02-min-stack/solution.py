"""Min Stack.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-min-stack/solution.py
"""



class MinStack:
    def __init__(self) -> None:
        self._data: list[int] = []
        self._mins: list[int] = []

    def push(self, x: int) -> None:
        self._data.append(x)
        if not self._mins or x <= self._mins[-1]:
            self._mins.append(x)

    def pop(self) -> None:
        x = self._data.pop()
        if x == self._mins[-1]:
            self._mins.pop()

    def top(self) -> int:
        return self._data[-1]

    def get_min(self) -> int:
        return self._mins[-1]


def _self_test() -> None:
    pass  # no tests
    print(f"all 0 tests passed for MinStack")


if __name__ == "__main__":
    _self_test()
