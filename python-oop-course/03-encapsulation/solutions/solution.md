# Solution 03 — Encapsulation

Reference answers. Try first.

## Key points

### Task 1 — `positive.py`

```python
"""A simple validated integer attribute.

Run:
    python 03-encapsulation/code/positive.py
"""


class Box:
    def __init__(self, value: int = 0) -> None:
        self._value = 0
        self.value = value                   # use the setter

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, new: int) -> None:
        if new <= 0:
            raise ValueError("value must be positive")
        self._value = new


def main() -> None:
    b = Box(5)
    print(b.value)
    b.value = 10
    print(b.value)
    try:
        b.value = -3
    except ValueError as e:
        print("blocked:", e)


if __name__ == "__main__":
    main()
```

### Task 2 — `rectangle.py`

```python
"""Read-only properties: area and perimeter derived from width/height.

Run:
    python 03-encapsulation/code/rectangle.py
"""


class Rectangle:
    def __init__(self, width: float, height: float) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        self.width = width
        self.height = height

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


def main() -> None:
    r = Rectangle(3, 4)
    print("area =", r.area)
    print("perimeter =", r.perimeter)
    try:
        r.area = 999
    except AttributeError as e:
        print("setting r.area:", e)


if __name__ == "__main__":
    main()
```

### Task 3 — `thermometer.py`

```python
"""A thermometer with bounds checking.

Run:
    python 03-encapsulation/code/thermometer.py
"""


class Thermometer:
    ABSOLUTE_ZERO = -273.15

    def __init__(self, celsius: float = 0) -> None:
        self.celsius = celsius                # use the setter

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < self.ABSOLUTE_ZERO:
            raise ValueError(f"below absolute zero ({self.ABSOLUTE_ZERO})")
        self._celsius = value


def main() -> None:
    t = Thermometer(20)
    print("t =", t.celsius)
    t.celsius = -10
    print("t =", t.celsius)
    try:
        Thermometer(-300)
    except ValueError as e:
        print("blocked at construction:", e)


if __name__ == "__main__":
    main()
```

## Common pitfalls

- **Writing `@value.setter` without first defining `@property` on the same name.** The setter decorator depends on the property existing on the class.
- **Forgetting to make `_value` exist before assigning in `__init__`.** The `self._value = 0` line is what guarantees the attribute exists for the getter to return. (Python would actually let you skip it for some classes, but it's a clean habit.)
- **Trying to "make it really private" with `__value`.** Don't. It just makes the code uglier. The leading underscore is enough.
