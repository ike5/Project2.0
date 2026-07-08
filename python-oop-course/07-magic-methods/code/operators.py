"""Vector with __add__ and __mul__.

Run:
    python 07-magic-methods/code/operators.py
"""


class Vector:
    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)

    def __mul__(self, k: float) -> "Vector":
        return Vector(self.x * k, self.y * k)


def main() -> None:
    a = Vector(1, 2)
    b = Vector(3, 4)
    print("a + b   =", a + b)
    print("a * 3   =", a * 3)
    print("(a+b)*2 =", (a + b) * 2)


if __name__ == "__main__":
    main()
