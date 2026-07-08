"""@property in two flavors: computed (read-only) and validated (read/write).

Run:
    python 03-encapsulation/code/property_demo.py
"""

import math


class Circle:
    def __init__(self, radius: float) -> None:
        if radius < 0:
            raise ValueError("radius must be >= 0")
        self.radius = radius

    @property
    def area(self) -> float:                  # read-only, computed
        return math.pi * self.radius ** 2


class Celsius:
    def __init__(self, temp: float) -> None:
        self.temp = temp                      # uses the setter

    @property
    def temp(self) -> float:
        return self._temp

    @temp.setter
    def temp(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("below absolute zero")
        self._temp = value


def main() -> None:
    c = Circle(2.0)
    print(f"c.radius = {c.radius}   c.area = {c.area:.3f}")
    try:
        c.area = 999
    except AttributeError as e:
        print("setting c.area ->", e)

    t = Celsius(20)
    print("t.temp =", t.temp)
    t.temp = -50
    print("t.temp =", t.temp)
    try:
        t.temp = -300
    except ValueError as e:
        print("setting t.temp = -300 ->", e)


if __name__ == "__main__":
    main()
