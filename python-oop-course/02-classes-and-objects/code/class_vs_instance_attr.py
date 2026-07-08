"""The mutable-class-attribute trap, and how to avoid it.

Run:
    python 02-classes-and-objects/code/class_vs_instance_attr.py
"""


class BadBag:
    items = []                              # shared by every instance!

    def add(self, item):
        self.items.append(item)


class GoodBag:
    def __init__(self) -> None:
        self.items = []                     # each instance gets its own list

    def add(self, item):
        self.items.append(item)


def main() -> None:
    print("--- BadBag: class attribute is shared ---")
    a = BadBag()
    b = BadBag()
    a.add("apple")
    b.add("banana")
    print("a.items:", a.items)
    print("b.items:", b.items)
    print("same list?", a.items is b.items)

    print("\n--- GoodBag: instance attribute is private ---")
    c = GoodBag()
    d = GoodBag()
    c.add("apple")
    d.add("banana")
    print("c.items:", c.items)
    print("d.items:", d.items)
    print("same list?", c.items is d.items)


if __name__ == "__main__":
    main()
