# Lab 06 — Composition

**You'll:** see a `Car`/`Engine` composition, a set of dataclasses, and a side-by-side "inheritance vs. composition" example. ⏱️ ~30 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Car with an Engine

```bash
python 06-composition/code/car_engine.py
```

✅ You should see `Toyota: engine (150 hp) running` (or similar) and the engine swapped out via `set_engine`.

## Part B — Dataclass demo

```bash
python 06-composition/code/dataclass_demo.py
```

✅ You should see:
- A `Point` constructed with defaults
- Two `Money` values compared with `==` (because `@dataclass` generated `__eq__`)
- A `repr()` line that shows the dataclass's auto-generated string form
- An `Order` with default items list (no shared list bug)

## Part C — Composition vs. inheritance

```bash
python 06-composition/code/composition_vs_inheritance.py
```

✅ Two short examples of the same "user has-a profile" idea, modeled the inheritance way and the composition way. The output should make the difference obvious.

## Part D — Frozen dataclass

```bash
python -i 06-composition/code/dataclass_demo.py
```

```python
>>> m = Money(100)
>>> m.amount = 200
FrozenInstanceError: cannot assign to field 'amount'
```

✅ Confirms the frozen dataclass is read-only.

## Cleanup

Nothing to clean up.

## What you learned

- Composition is "has-a"; the outer class holds a reference to an inner object and delegates work to it.
- A `@dataclass` auto-generates `__init__`, `__repr__`, and `__eq__` from annotations.
- `frozen=True` makes a dataclass immutable; `default_factory=list` solves the mutable-default problem.
- Prefer composition when the relationship is "has-a" and you want to swap parts.

➡️ **[challenge.md](./challenge.md)** then [Module 07: Magic Methods](../07-magic-methods/).
