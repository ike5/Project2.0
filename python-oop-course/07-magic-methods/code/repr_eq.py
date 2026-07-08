"""Point with __repr__, __eq__, and __hash__.

Run:
    python 07-magic-methods/code/repr_eq.py
"""


class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y

    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"

    def __eq__(self, other) -> bool:
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))


def main() -> None:
    p1 = Point(1, 2)
    p2 = Point(1, 2)
    p3 = Point(3, 4)
    print("p1 =", p1)
    print("p2 =", p2)
    print("p1 == p2 ->", p1 == p2)
    print("p1 == p3 ->", p1 == p3)
    print("p1 in {p1, p2, p3}?", p1 in {p1, p2, p3})


if __name__ == "__main__":
    main()
