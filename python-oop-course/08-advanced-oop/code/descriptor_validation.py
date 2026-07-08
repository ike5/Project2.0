"""A reusable Positive descriptor applied to several fields.

Run:
    python 08-advanced-oop/code/descriptor_validation.py
"""


class Positive:
    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, obj, owner):
        if obj is None:
            return self
        return getattr(obj, self._name, None)

    def __set__(self, obj, value):
        if value < 0:
            raise ValueError(f"{self._name[1:]} must be >= 0")
        setattr(obj, self._name, value)


class Product:
    price = Positive()
    stock = Positive()

    def __init__(self, name: str, price: float, stock: int) -> None:
        self.name = name
        self.price = price
        self.stock = stock


def main() -> None:
    p = Product("Widget", 9.99, 10)
    print(p.name, p.price, p.stock)
    try:
        p.stock = -1
    except ValueError as e:
        print("blocked:", e)


if __name__ == "__main__":
    main()
