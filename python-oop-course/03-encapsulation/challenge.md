# Challenge 03 — Encapsulation

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Build a `PositiveNumber` property by hand.** Create `03-encapsulation/code/positive.py` with a class `Box` that has a single integer attribute `_value` stored directly. Use a `@property` and a `@value.setter` so the property `value` always returns the stored number, but assigning a non-positive number raises `ValueError`. (hint: this is the same trick as `Celsius` from the README, but for ints.)
2. **Build a `Rectangle` with a read-only `area`.** Create `03-encapsulation/code/rectangle.py` with a `Rectangle(width, height)`. Expose `area` and `perimeter` as **read-only properties** computed from `width` and `height`. The constructor should validate that width and height are positive.
3. **Build a `Thermometer` with bounds.** Create `03-encapsulation/code/thermometer.py`. The class has a `celsius` property with bounds: setting anything below `-273.15` raises `ValueError`. The property has a *getter and setter* — both real. The constructor accepts an optional initial value (default `0`).

## Success criteria

- [ ] `Box(0).value = -3` raises `ValueError`; `Box(0).value = 5` works.
- [ ] `Rectangle(3, 4).area == 12` and `Rectangle(3, 4).perimeter == 14`. Setting `r.area` raises `AttributeError`.
- [ ] `Thermometer(-300)` raises at construction; `Thermometer(20).celsius == 20`; setting `t.celsius = -300` raises.
