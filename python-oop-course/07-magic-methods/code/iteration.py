"""Iteration: a Countdown class and a paginate helper.

Run:
    python 07-magic-methods/code/iteration.py
"""


class Countdown:
    def __init__(self, n: int) -> None:
        self.n = n

    def __iter__(self):
        return self                            # object is its own iterator

    def __next__(self) -> int:
        if self.n <= 0:
            raise StopIteration
        self.n -= 1
        return self.n + 1


def paginate(items, page_size: int):
    """Yield successive pages of size page_size."""
    for i in range(0, len(items), page_size):
        yield items[i : i + page_size]


def main() -> None:
    print("Countdown(3):", end=" ")
    for x in Countdown(3):
        print(x, end=" ")
    print()

    print("\npaginate([1..10], 3):")
    for page in paginate(list(range(1, 11)), 3):
        print(" ", page)


if __name__ == "__main__":
    main()
