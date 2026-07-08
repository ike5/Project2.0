# Lab 09 — Design Patterns

**You'll:** see each of the five patterns in a small, runnable script. ⏱️ ~45 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Strategy

```bash
python 09-design-patterns/code/strategy.py
```

✅ You should see the same list sorted ascending and descending by swapping a single argument.

## Part B — Observer

```bash
python 09-design-patterns/code/observer.py
```

✅ Two observer functions print the new value each time the subject's `value` is set.

## Part C — Decorator pattern

```bash
python 09-design-patterns/code/decorator_pattern.py
```

✅ A "hi" wrapped in `<b>` and `<i>` should render to `<b><i>hi</i></b>`.

## Part D — Factory

```bash
python 09-design-patterns/code/factory.py
```

✅ A `JSONParser` for `.json`, a `CSVParser` for `.csv`, and `ValueError` for unknown extensions.

## Part E — Adapter

```bash
python 09-design-patterns/code/adapter.py
```

✅ A 25°C source should come out as 77.0°F.

## Cleanup

Nothing to clean up.

## What you learned

- Strategy swaps algorithms by reference; in Python, the strategy is often just a function.
- Observer keeps a list of subscribers and broadcasts on change.
- The GoF Decorator pattern wraps an object with the same interface to add behavior.
- Factory centralizes object construction.
- Adapter translates one interface to another.

➡️ **[challenge.md](./challenge.md)** then [Module 10: Testing OOP](../10-testing-oop/).
