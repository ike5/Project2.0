# Challenge 08 — Advanced OOP

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **`Pixel` with `__slots__`.** Create `08-advanced-oop/code/pixel.py` with a `Pixel` class that uses `__slots__ = ("x", "y", "color")`. The constructor takes `x`, `y`, and `color` (a string). Confirm that `p.z = 3` raises `AttributeError` and that `p.color = "red"` works.
2. **`Email` with a classmethod and a staticmethod.** Create `08-advanced-oop/code/email.py` with a class `Email(local, domain)`. Add a classmethod `from_string("ana@example.com")` that splits on `@` and a staticmethod `is_valid("ana@example.com")` that checks the address has an `@` and a non-empty local part and domain.
3. **`Range` with a `__init_subclass__` registry.** Create `08-advanced-oop/code/ranges.py` with a base `Range` class that registers subclasses by name in a `Range.registry` dict. Define two subclasses — `OpenRange` and `ClosedRange` — each with a `contains(x)` method (one strict, one inclusive). Show that the registry contains both.

## Success criteria

- [ ] `Pixel` rejects unknown attributes; allowed ones are settable.
- [ ] `Email.from_string("a@b.com").local == "a"`; `Email.is_valid("a@b.com") is True`; `Email.is_valid("nope") is False`.
- [ ] `Range.registry` is `{"open": OpenRange, "closed": ClosedRange}` and `OpenRange().contains(5)` and `ClosedRange(0, 10).contains(10)` both behave correctly.
