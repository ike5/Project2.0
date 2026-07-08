"""@dataclass in three flavors: basic, frozen, and with default_factory.

Run:
    python 06-composition/code/dataclass_demo.py
"""

from dataclasses import dataclass, field


@dataclass
class Point:
    x: float
    y: float = 0.0


@dataclass(frozen=True)
class Money:
    amount: int                              # cents
    currency: str = "USD"


@dataclass
class Order:
    id: int
    items: list[str] = field(default_factory=list)
    total: Money = field(default_factory=lambda: Money(0))


def main() -> None:
    p = Point(3)
    print("p =", p)
    print("p == Point(3, 0.0) ->", p == Point(3, 0.0))

    m1 = Money(100)
    m2 = Money(100, "USD")
    print("m1 == m2 ->", m1 == m2)
    print("repr(m1) ->", repr(m1))

    a = Order(1)
    b = Order(2)
    a.items.append("apple")
    print("a.items:", a.items)
    print("b.items:", b.items, "  (still empty — default_factory gave each a fresh list)")


if __name__ == "__main__":
    main()
