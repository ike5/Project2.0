# Lab 04 — Inheritance

**You'll:** run inheritance examples, inspect the MRO, and call `super()` from inside a subclass. ⏱️ ~35 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Run the basic inheritance example

```bash
python 04-inheritance/code/basic_inheritance.py
```

✅ You should see lines for each animal speaking, plus the MRO of every class printed.

## Part B — Try the `super()` demo

```bash
python 04-inheritance/code/super_demo.py
```

✅ Confirm that `super().__init__()` runs the parent's initializer, and `super().method()` runs the parent's version of the method.

## Part C — Run the employee hierarchy

```bash
python 04-inheritance/code/employee_hierarchy.py
```

✅ You should see `Engineer` and `Manager` instances both with `describe()` calls, each showing a role-specific line.

## Part D — MRO exploration in a REPL

```bash
python -i 04-inheritance/code/employee_hierarchy.py
```

```python
>>> Manager.mro()
[<class '__main__.Manager'>, <class '__main__.Employee'>, <class 'object'>]
>>> isinstance(Manager("Mia", 8, "eng"), Employee)
True
>>> issubclass(Engineer, Employee)
True
```

✅ The MRO list ends in `object`. The `isinstance` and `issubclass` calls return `True`.

## Cleanup

Nothing to clean up.

## What you learned

- A subclass inherits every method and attribute of its parent.
- Override by defining a method with the same name in the child.
- `super()` is how you call the parent's version — almost always in `__init__`.
- The MRO is the order Python searches for methods; read it with `Class.mro()`.
- `isinstance` and `issubclass` work through the whole inheritance chain.

➡️ **[challenge.md](./challenge.md)** then [Module 05: Polymorphism](../05-polymorphism/).
