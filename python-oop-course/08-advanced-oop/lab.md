# Lab 08 — Advanced OOP

**You'll:** see `__slots__`, class/staticmethods, a descriptor, and a tiny plugin system. ⏱️ ~40 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — `__slots__`

```bash
python 08-advanced-oop/code/slots_demo.py
```

✅ You should see the `Point` (slots) reject `p.z = 3` with `AttributeError`, and the regular `LoosePoint` accept `lp.z = 3`.

## Part B — Class and static methods

```bash
python 08-advanced-oop/code/class_static_methods.py
```

✅ You should see `Date.from_string("2026-07-07")` produce a `Date` and `Date.is_leap(2024)` print `True`.

## Part C — Descriptor

```bash
python 08-advanced-oop/code/descriptor_validation.py
```

✅ You should see the descriptor reject negative values and accept positive ones, for both fields.

## Part D — Plugin registry

```bash
python 08-advanced-oop/code/init_subclass_plugin.py
```

✅ You should see a small dict of registered plugins printed at the end.

## Cleanup

Nothing to clean up.

## What you learned

- `__slots__` is a fixed attribute list; using it saves memory and rejects typos.
- `@classmethod` is great for alternative constructors; `@staticmethod` is a free function in class clothing — use it sparingly.
- Descriptors power `property` and let you write reusable validators.
- `__init_subclass__` lets a base class customize its subclasses at *creation* time, no metaclass needed.

➡️ **[challenge.md](./challenge.md)** then [Module 09: Design Patterns](../09-design-patterns/).
