# Lab 05 — Polymorphism

**You'll:** see duck typing, an ABC, and a Protocol in action. ⏱️ ~35 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Duck typing

```bash
python 05-polymorphism/code/duck_typing.py
```

✅ You should see `quack!` from both the `Duck` and the `Person` (or whichever stand-in you implemented). Same function call, different objects.

## Part B — Abstract base class

```bash
python 05-polymorphism/code/abstract_shape.py
```

✅ You should see three `area:` lines, one per shape. Trying to instantiate `Shape` directly should fail with `TypeError`. (The script will demonstrate that.)

## Part C — Protocol-based polymorphism

```bash
python 05-polymorphism/code/protocol_render.py
```

✅ You should see three `draw()` outputs from three different classes, none of which inherit from a common `Drawable` base — only from `object`.

## Part D — Try to break duck typing in a REPL

```bash
python -i 05-polymorphism/code/duck_typing.py
```

```python
>>> make_it_quack("not a duck")
AttributeError: 'str' object has no attribute 'quack'
```

✅ This is what "duck typing bites" means: a type checker would have caught it; at runtime you get an `AttributeError`.

## Cleanup

Nothing to clean up.

## What you learned

- Duck typing is the default in Python: code that "just calls the method" works on any object that has it.
- ABCs (`abc.ABC` + `@abstractmethod`) enforce the contract at runtime; you can't instantiate them.
- `typing.Protocol` enforces the contract at type-check time, without requiring inheritance.
- The Liskov Substitution Principle is a useful sanity check when you reach for inheritance.

➡️ **[challenge.md](./challenge.md)** then [Module 06: Composition](../06-composition/).
