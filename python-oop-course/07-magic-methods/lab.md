# Lab 07 — Magic Methods

**You'll:** see `__repr__`/`__eq__`, operator overloading, iteration, and a context manager. ⏱️ ~40 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — `__repr__` and equality

```bash
python 07-magic-methods/code/repr_eq.py
```

✅ You should see two points with a useful `repr` form, and the equality check should print `True`. Then in a REPL:

```bash
python -i 07-magic-methods/code/repr_eq.py
```

```python
>>> p = Point(1, 2)
>>> {p: "found"}    # works because we implemented __hash__
{'Point(x=1, y=2)': 'found'}
```

## Part B — Operators

```bash
python 07-magic-methods/code/operators.py
```

✅ You should see `Vector(4, 6)`, `Vector(2, 3)`, and a scalar-multiplied result.

## Part C — Iteration

```bash
python 07-magic-methods/code/iteration.py
```

✅ You should see `3 2 1` from the `Countdown`, then a paginated walk through a list.

## Part D — Context manager

```bash
python 07-magic-methods/code/context_manager.py
```

✅ You should see one elapsed time printed for the class-based `Timer` and one for the `@contextmanager`-based one. Both should be a small positive number.

## Cleanup

Nothing to clean up.

## What you learned

- `__repr__` is the developer-facing string. Always implement it.
- `__eq__` removes the default `__hash__`; if you need hashable objects, add `__hash__` back.
- Operator dunders (`__add__`, `__mul__`) hook into Python's `+` and `*` syntax.
- `__iter__` / `__next__` make a custom object work in a `for` loop.
- `__enter__` / `__exit__` (or `@contextmanager`) make a custom object work in a `with` block.

➡️ **[challenge.md](./challenge.md)** then [Module 08: Advanced OOP](../08-advanced-oop/).
