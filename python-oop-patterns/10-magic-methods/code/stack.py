"""A stack that behaves like a Python list.

Run me: python 10-magic-methods/code/stack.py
"""


class Stack:
    def __init__(self) -> None:
        self._data: list[int] = []

    def push(self, x: int) -> None:
        self._data.append(x)

    def pop(self) -> int:
        return self._data.pop()

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, i):
        return self._data[i]

    def __contains__(self, x) -> bool:
        return x in self._data

    def __iter__(self):
        return iter(self._data)

    def __repr__(self) -> str:
        return f"Stack({self._data!r})"


def main() -> None:
    s: Stack = Stack()
    for x in (1, 2, 3, 2, 1):
        s.push(x)

    print("s          =", s)
    print("len(s)     =", len(s))
    print("s[-1]      =", s[-1])
    print("2 in s     =", 2 in s)
    print("for x in s =", list(s))


if __name__ == "__main__":
    main()
