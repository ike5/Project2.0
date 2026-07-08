"""__slots__ vs. a regular class.

Run:
    python 08-advanced-oop/code/slots_demo.py
"""


class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y): self.x, self.y = x, y


class LoosePoint:
    def __init__(self, x, y): self.x, self.y = x, y


def main() -> None:
    p = Point(1, 2)
    lp = LoosePoint(1, 2)

    try:
        p.z = 3
    except AttributeError as e:
        print("Point rejects new attribute:", e)

    lp.z = 3
    print("LoosePoint accepted .z =", lp.z)


if __name__ == "__main__":
    main()
