"""A minimal Counter class.

Run:
    python 02-classes-and-objects/code/counter.py
"""


class Counter:
    def __init__(self, start: int = 0) -> None:
        self.value = start

    def increment(self, by: int = 1) -> None:
        self.value += by

    def reset(self) -> None:
        self.value = 0

    def current(self) -> int:
        return self.value


def main() -> None:
    c = Counter()
    print("initial:", c.current())
    c.increment()
    c.increment()
    c.increment()
    print("after three increments:", c.current())
    c.reset()
    print("after reset:", c.current())


if __name__ == "__main__":
    main()
