"""An abstract Shape class and three concrete shapes.

Run:
    python 05-polymorphism/code/abstract_shape.py
"""

import math
from abc import ABC, abstractmethod


class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...
    @abstractmethod
    def perimeter(self) -> float: ...


class Square(Shape):
    def __init__(self, side: float) -> None:
        self.side = side
    def area(self) -> float:      return self.side ** 2
    def perimeter(self) -> float: return 4 * self.side


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius
    def area(self) -> float:      return math.pi * self.radius ** 2
    def perimeter(self) -> float: return 2 * math.pi * self.radius


class Triangle(Shape):
    def __init__(self, a: float, b: float, c: float) -> None:
        self.a, self.b, self.c = a, b, c
    def perimeter(self) -> float: return self.a + self.b + self.c
    def area(self) -> float:
        s = self.perimeter() / 2
        return math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))


def main() -> None:
    shapes: list[Shape] = [Square(2), Circle(3), Triangle(3, 4, 5)]
    for s in shapes:
        print(f"{type(s).__name__:>8}  area = {s.area():8.3f}   perim = {s.perimeter():.3f}")

    try:
        Shape()
    except TypeError as e:
        print("\nShape() raised:", e)


if __name__ == "__main__":
    main()
