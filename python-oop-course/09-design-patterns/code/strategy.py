"""Strategy: a Sorter that delegates to a function.

Run:
    python 09-design-patterns/code/strategy.py
"""


class Sorter:
    def __init__(self, strategy):
        self.strategy = strategy

    def sort(self, items): return self.strategy(items)


def main() -> None:
    items = [3, 1, 4, 1, 5, 9, 2, 6]
    print("asc:  ", Sorter(sorted).sort(items))
    print("desc: ", Sorter(lambda xs: list(reversed(sorted(xs)))).sort(items))
    print("even: ", Sorter(lambda xs: [x for x in xs if x % 2 == 0]).sort(items))


if __name__ == "__main__":
    main()
