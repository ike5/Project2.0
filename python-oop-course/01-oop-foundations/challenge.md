# Challenge 01 — OOP Foundations

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **List the four pillars.** In a file called `01-oop-foundations/code/pillars.md`, write a 2-3 sentence plain-English summary of each: encapsulation, abstraction, inheritance, polymorphism. (hint: don't quote a textbook — explain them as if to a friend who's never coded.)
2. **Find three real objects in Python's standard library.** In `01-oop-foundations/code/standard_lib_objects.py`, import three different things from the standard library, call `type()` on each, and `print()` a label and the type. (hint: e.g. `pathlib.Path(".")` and `datetime.date.today()` and `collections.Counter()`.)
3. **Mirror the demo with a different domain.** Create `01-oop-foundations/code/lightbulb.py` with a `Lightbulb` class that has a `state` attribute (`"on"` or `"off"`) set in `__init__`, and a `toggle()` method that flips the state. Also include a `__str__` method that returns the current state. (hint: module 07 covers `__str__` properly; for now just return a string.)

## Success criteria

- [ ] `cat 01-oop-foundations/code/pillars.md` shows your four plain-English summaries.
- [ ] `python 01-oop-foundations/code/standard_lib_objects.py` prints three labeled types.
- [ ] `python 01-oop-foundations/code/lightbulb.py` shows two toggles, starting `off` → `on` → `off`.
