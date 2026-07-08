# Solution 04 — Inheritance

Reference answers. Try first.

## Key points

### `vehicles.py`

```python
"""A Vehicle -> Car / Motorcycle hierarchy.

Run:
    python 04-inheritance/code/vehicles.py
"""


class Vehicle:
    def __init__(self, make: str, model: str, year: int) -> None:
        self.make = make
        self.model = model
        self.year = year

    def description(self) -> str:
        return f"{self.year} {self.make} {self.model}"

    def start(self) -> str:
        return f"{self.model} started"

    def __str__(self) -> str:
        return self.description()


class Car(Vehicle):
    def __init__(self, make: str, model: str, year: int, doors: int) -> None:
        super().__init__(make, model, year)
        self.doors = doors


class Motorcycle(Vehicle):
    def start(self) -> str:
        return f"{self.model} roars to life"


def describe_any(v: Vehicle) -> str:
    if isinstance(v, Motorcycle):
        return v.start()
    return v.description()


def main() -> None:
    c = Car("Toyota", "Corolla", 2018, 4)
    m = Motorcycle("Honda", "CBR", 2021)

    print(c)                              # 2018 Toyota Corolla
    print(m)                              # 2021 Honda CBR
    print("Car.start():     ", c.start())
    print("Motorcycle.start:", m.start())

    print()
    print("MRO Car:       ", [k.__name__ for k in Car.mro()])
    print("MRO Motorcycle:", [k.__name__ for k in Motorcycle.mro()])

    print()
    print("describe_any(c):", describe_any(c))
    print("describe_any(m):", describe_any(m))


if __name__ == "__main__":
    main()
```

## Common pitfalls

- **Forgetting `super().__init__()`.** A subclass that doesn't call it can leave its instance half-built. Always include the call.
- **Naming the parameter `self` something else.** It works, but linters and humans will be sad. Stick with `self`.
- **Putting business logic in the base class that only one subclass needs.** Inheritance is for *shared* behavior, not a grab-bag.
- **The `isinstance` chain in `describe_any`.** This works for two subclasses, but with five it gets ugly. The next module shows you the right way: just call the method and let polymorphism do its thing.
