# Challenge 04 — Inheritance

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Build a `Vehicle` hierarchy.** Create `04-inheritance/code/vehicles.py` with:
   - `Vehicle` (base) — takes `make`, `model`, `year`. Has `description()` returning `f"{year} {make} {model}"` and a `start()` returning `f"{self.model} started"`.
   - `Car(Vehicle)` — overrides nothing, but accepts an extra `doors` argument in `__init__` and exposes it.
   - `Motorcycle(Vehicle)` — overrides `start()` to return `f"{self.model} roars to life"`.
   - Include a `__str__` on `Vehicle` that returns the description. Print a `Car` and a `Motorcycle` and demonstrate `super().__init__()` is being used.
2. **Inspect the MRO.** In the same script (or a small extra), print `Car.mro()` and `Motorcycle.mro()` and confirm both end in `object`.
3. **Use `isinstance` properly.** In a `def describe_any(v: Vehicle)` function, return `v.description()` if it's a `Car`, `v.start()` if it's a `Motorcycle`, else `v.description()`. Call it with each of your classes. (hint: this is starting to look like polymorphism — that's the next module. For now, a chain of `isinstance` checks is fine to demonstrate the point.)

## Success criteria

- [ ] `Car` and `Motorcycle` both inherit from `Vehicle`, and `super().__init__()` is called in each.
- [ ] `Motorcycle(...).start()` returns the roar line; `Car(...).start()` returns the parent's line.
- [ ] `describe_any(...)` works for all three classes.
