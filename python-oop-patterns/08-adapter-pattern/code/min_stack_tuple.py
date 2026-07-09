"""Min Stack, single-list (val, min) variant.

Run me: python 08-adapter-pattern/code/min_stack_tuple.py
"""


class MinStack:
    def __init__(self) -> None:
        self.stack: list[tuple[int, int]] = []   # (val, min-so-far)

    def push(self, val: int) -> None:
        cur_min = val if not self.stack else min(val, self.stack[-1][1])
        self.stack.append((val, cur_min))

    def pop(self) -> None:
        self.stack.pop()

    def top(self) -> int:
        return self.stack[-1][0]

    def getMin(self) -> int:
        return self.stack[-1][1]


def main() -> None:
    s = MinStack()
    for v in (-2, 0, -3):
        s.push(v)
    print("getMin =", s.getMin())
    s.pop()
    print("top    =", s.top())
    print("getMin =", s.getMin())


if __name__ == "__main__":
    main()
