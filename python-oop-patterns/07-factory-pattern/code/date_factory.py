"""A tiny Date class with a @classmethod factory.

Run me: python 07-factory-pattern/code/date_factory.py
"""


class Date:
    def __init__(self, y: int, m: int, d: int) -> None:
        self.y, self.m, self.d = y, m, d

    def __repr__(self) -> str:
        return f"Date({self.y}-{self.m:02d}-{self.d:02d})"

    @classmethod
    def from_string(cls, s: str) -> "Date":
        y, m, d = map(int, s.split("-"))
        return cls(y, m, d)

    @classmethod
    def today(cls) -> "Date":
        import datetime
        t = datetime.date.today()
        return cls(t.year, t.month, t.day)


def main() -> None:
    a = Date(2024, 1, 15)
    b = Date.from_string("2024-01-15")
    c = Date.today()
    print(a)
    print(b)
    print(c)
    assert a.y == b.y and a.m == b.m and a.d == b.d


if __name__ == "__main__":
    main()
