# Lab 01 — OOP Foundations

**You'll:** poke at real Python objects with `type()` and `dir()`, then run the procedural-vs-OOP demo. ⏱️ ~30 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Confirm "everything is an object"

```bash
python 01-oop-foundations/code/explore_objects.py
```

✅ You should see lines like:

```
type(42)              -> <class 'int'>
type("hi")            -> <class 'str'>
type([1, 2])          -> <class 'list'>
type({"a": 1})        -> <class 'dict'>
type(print)           -> <class 'builtin_function_or_method'>
```

…and a long list of attributes for `(1, 2, 3)`. **Read the script and pick one attribute you don't recognize. Look it up.** That's the muscle we want to build.

## Part B — Run the side-by-side demo

```bash
python 01-oop-foundations/code/dog_procedural_vs_oop.py
```

✅ You should see two `Rex: woof!` lines — one from the procedural version, one from the OOP version.

> Open the file in your editor and read it. The whole point of this lab is to feel how similar the two versions are, and where the OOP version starts to win.

## Part C — Build a `Dog` and inspect it in the REPL

```bash
python -i 01-oop-foundations/code/dog_procedural_vs_oop.py
```

At the prompt:

```python
>>> rex = Dog("Rex", 4)
>>> type(rex)
<class '__main__.Dog'>
>>> rex.name, rex.age
('Rex', 4)
>>> rex.bark()
'Rex: woof!'
>>> isinstance(rex, Dog)
True
>>> Dog.mro()
[<class '__main__.Dog'>, <class 'object'>]
```

✅ Every command should produce the output shown (or something equivalent).

> Press `Ctrl-D` (or `Ctrl-Z` then Enter on Windows) to exit the REPL.

## Cleanup

Nothing to clean up.

## What you learned

- `type(obj)` tells you the class of any object.
- `isinstance(obj, Class)` is the standard "is this a …?" check.
- `Class.mro()` shows the method resolution order — for now it's just `[Dog, object]`.
- A class is a blueprint; an instance is a specific object built from that blueprint.
- Both procedural and OOP code can produce the same output. OOP pays off as code grows.

➡️ **[challenge.md](./challenge.md)** then [Module 02: Classes & Objects](../02-classes-and-objects/).
