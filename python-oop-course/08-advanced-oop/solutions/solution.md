# Solution 08 — Advanced OOP

Reference answers. Try first.

## Key points

### Task 1 — `pixel.py`

```python
"""Pixel uses __slots__ to lock down its attributes.

Run:
    python 08-advanced-oop/code/pixel.py
"""


class Pixel:
    __slots__ = ("x", "y", "color")

    def __init__(self, x: int, y: int, color: str) -> None:
        self.x = x
        self.y = y
        self.color = color

    def __repr__(self) -> str:
        return f"Pixel(x={self.x}, y={self.y}, color={self.color!r})"


def main() -> None:
    p = Pixel(1, 2, "red")
    print(p)
    p.color = "blue"
    print(p)
    try:
        p.z = 3
    except AttributeError as e:
        print("blocked:", e)


if __name__ == "__main__":
    main()
```

### Task 2 — `email.py`

```python
"""Email with a classmethod (alt constructor) and a staticmethod (validator).

Run:
    python 08-advanced-oop/code/email.py
"""


class Email:
    def __init__(self, local: str, domain: str) -> None:
        self.local, self.domain = local, domain

    def __repr__(self) -> str:
        return f"Email({self.local!r}, {self.domain!r})"

    @classmethod
    def from_string(cls, s: str) -> "Email":
        local, _, domain = s.partition("@")
        if not cls.is_valid(s):
            raise ValueError(f"invalid email: {s!r}")
        return cls(local, domain)

    @staticmethod
    def is_valid(s: str) -> bool:
        local, sep, domain = s.partition("@")
        return bool(sep) and bool(local) and bool(domain)


def main() -> None:
    e = Email.from_string("ana@example.com")
    print(e)
    print("valid 'a@b.com'?", Email.is_valid("a@b.com"))
    print("valid 'nope'?", Email.is_valid("nope"))


if __name__ == "__main__":
    main()
```

### Task 3 — `ranges.py`

```python
"""A Range base that registers subclasses by name in a registry.

Run:
    python 08-advanced-oop/code/ranges.py
"""


class Range:
    registry: dict = {}

    def __init_subclass__(cls, *, name, **kwargs):
        super().__init_subclass__(**kwargs)
        Range.registry[name] = cls

    def contains(self, x: float) -> bool:      # subclasses override
        raise NotImplementedError


class OpenRange(Range, name="open"):
    def __init__(self, lo: float, hi: float) -> None:
        self.lo, self.hi = lo, hi

    def contains(self, x: float) -> bool:
        return self.lo < x < self.hi


class ClosedRange(Range, name="closed"):
    def __init__(self, lo: float, hi: float) -> None:
        self.lo, self.hi = lo, hi

    def contains(self, x: float) -> bool:
        return self.lo <= x <= self.hi


def main() -> None:
    print("registry:", {k: v.__name__ for k, v in Range.registry.items()})
    o = OpenRange(0, 10)
    c = ClosedRange(0, 10)
    for x in (0, 5, 10):
        print(f"  x={x:>2}  open={o.contains(x)}  closed={c.contains(x)}")


if __name__ == "__main__":
    main()
```

## Common pitfalls

- **Forgetting to forward `**kwargs` in `__init_subclass__`.** If your base has an `__init_subclass__` and you don't pass extras along, future composition will silently break.
- **Defining `__init_subclass__` as a regular method.** It's a *classmethod*; don't add `self`. Inside it, you usually call `super().__init_subclass__(**kwargs)`.
- **Reaching for `__slots__` on a class meant to be subclassed with new attributes.** Each subclass must redeclare the slots it needs.
