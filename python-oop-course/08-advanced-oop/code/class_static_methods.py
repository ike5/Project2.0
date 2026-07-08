"""A Date with a classmethod (alternative constructor) and a staticmethod (utility).

Run:
    python 08-advanced-oop/code/class_static_methods.py
"""


class Date:
    def __init__(self, year: int, month: int, day: int) -> None:
        self.year, self.month, self.day = year, month, day

    @classmethod
    def from_string(cls, s: str) -> "Date":
        y, m, d = map(int, s.split("-"))
        return cls(y, m, d)

    @staticmethod
    def is_leap(year: int) -> bool:
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def __repr__(self) -> str:
        return f"Date({self.year}-{self.month:02d}-{self.day:02d})"


def main() -> None:
    d = Date.from_string("2026-07-07")
    print("from string:", d)
    print("2024 leap?", Date.is_leap(2024))
    print("2025 leap?", Date.is_leap(2025))


if __name__ == "__main__":
    main()
