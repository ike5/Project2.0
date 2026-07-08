# Lab 02 — Classes & Objects

**You'll:** build and use `Counter`, `Dog`, and a tiny class to study class- vs. instance-attribute sharing. ⏱️ ~45 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Run the counter

```bash
python 02-classes-and-objects/code/counter.py
```

✅ You should see:

```
initial: 0
after three increments: 3
after reset: 0
```

## Part B — Run the dog example

```bash
python 02-classes-and-objects/code/dog_methods.py
```

✅ You should see lines that look like:

```
Rex: woof!
Rex sniffs Buddy
Rex is a puppy: True
after birthday, Rex is 3
species of every dog: Canis familiaris
```

## Part C — Trigger the validation in `__init__`

In a Python REPL with the file imported:

```bash
python -i 02-classes-and-objects/code/dog_methods.py
```

```python
>>> Dog("Rex", -1)
Traceback (most recent call last):
  ...
ValueError: age must be >= 0
```

✅ You should see a `ValueError`.

## Part D — Watch the mutable-class-attribute trap

```bash
python 02-classes-and-objects/code/class_vs_instance_attr.py
```

✅ You should see the **bad** bag (using a mutable class attribute) where appending to one bag affects the other, and the **good** bag (using `default_factory` in `__init__`) where they don't.

## Cleanup

Nothing to clean up.

## What you learned

- How `self` works: it's just a parameter that Python fills in.
- The difference between instance and class attributes, and the mutable-class-attribute trap.
- The convention: mutators return `None`, accessors return a value.
- How to use `__init__` to validate input and reject bad states at construction time.

➡️ **[challenge.md](./challenge.md)** then [Module 03: Encapsulation](../03-encapsulation/).
