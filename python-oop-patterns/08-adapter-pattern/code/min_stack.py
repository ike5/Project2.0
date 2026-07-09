"""LeetCode 155 — Min Stack, parallel-list variant.

Run me: python 08-adapter-pattern/code/min_stack.py
"""


class MinStack:
    def __init__(self) -> None:
        self.stack: list[int] = []
        self.mins:  list[int] = []

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


def main() -> None:
    s = MinStack()
    s.push(-2)
    s.push(0)
    s.push(-3)
    print("getMin =", s.getMin())     # -3
    s.pop()
    print("top    =", s.top())        # 0
    print("getMin =", s.getMin())     # -2


if __name__ == "__main__":
    main()
