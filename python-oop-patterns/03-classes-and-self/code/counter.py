"""Your turn: implement the Hits class.

Run me: python 03-classes-and-self/code/counter.py
"""


class Hits:
    def __init__(self) -> None:
        self.count = 0

    def record(self) -> None:
        self.count += 1

    def record_n(self, k: int) -> None:
        self.count += k

    def total(self) -> int:
        return self.count

    def reset(self) -> None:
        self.count = 0


def main() -> None:
    h = Hits()
    h.record()
    h.record()
    h.record_n(3)
    assert h.total() == 5
    h.reset()
    assert h.total() == 0
    print("OK: Hits works as expected.")


if __name__ == "__main__":
    main()
