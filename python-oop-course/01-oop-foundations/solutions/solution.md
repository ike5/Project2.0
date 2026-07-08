# Solution 01 — OOP Foundations

Reference answers for the three tasks. Try first.

## Key points

### Task 1 — `pillars.md`

Your file should look something like this. Use your own words; the lab isn't checking for specific phrasing.

```markdown
# The four pillars, in plain English

- **Encapsulation** — keep the data and the code that uses it in one place,
  and don't let random parts of the program reach in and mess with it.
- **Abstraction** — show callers a clean, simple interface, and hide the messy
  details. They don't need to know *how* it works, only *what* it does.
- **Inheritance** — let a new class reuse and extend an existing class
  instead of copying the code.
- **Polymorphism** — write code once that works on many different kinds of
  objects, as long as they expose the right methods.
```

### Task 2 — `standard_lib_objects.py`

```python
"""Three real objects from the standard library.

Run:
    python 01-oop-foundations/code/standard_lib_objects.py
"""

import datetime
import pathlib
import collections


def show(label: str, value) -> None:
    print(f"{label:>20}  ->  {type(value).__module__}.{type(value).__name__}")


def main() -> None:
    show("pathlib.Path('.')", pathlib.Path("."))
    show("datetime.date.today()", datetime.date.today())
    show("collections.Counter()", collections.Counter())
    show("dict()", dict())
    show("set()", set())


if __name__ == "__main__":
    main()
```

### Task 3 — `lightbulb.py`

```python
"""A lightbulb that toggles. The simplest non-trivial class.

Run:
    python 01-oop-foundations/code/lightbulb.py
"""


class Lightbulb:
    def __init__(self) -> None:
        self.state = "off"

    def toggle(self) -> None:
        self.state = "on" if self.state == "off" else "off"

    def __str__(self) -> str:
        return f"Lightbulb is {self.state}"


def main() -> None:
    bulb = Lightbulb()
    print(bulb)
    bulb.toggle()
    print(bulb)
    bulb.toggle()
    print(bulb)


if __name__ == "__main__":
    main()
```

Output:
```
Lightbulb is off
Lightbulb is on
Lightbulb is off
```

## Common pitfalls

- **Trying to find a perfect definition for each pillar.** There isn't one. The plain-English meaning is what matters; we'll deepen the vocabulary as the course goes on.
- **Forgetting `if __name__ == "__main__":`.** Same lesson as Module 00.
- **Calling `toggle()` a "function" instead of a "method".** It's a method because it's defined inside a class. The distinction is small but it's the vocabulary we'll use for the rest of the course.
