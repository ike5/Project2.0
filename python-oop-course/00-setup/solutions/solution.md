# Solution 00 — Setup & Orientation

Reference answers for the four tasks. Try the lab and challenge first; only peek if you're stuck.

## Key points

### Task 1 — `cat.py`

The shape is the same as `Dog`. Replace `bark` with `meow` and the wording in the f-string. Always include the `if __name__ == "__main__":` guard — that's what lets you run it as a script and import it without side effects.

```python
"""Hello again: a Cat class parallel to Dog.

Run:
    python 00-setup/code/cat.py
"""


class Cat:
    def __init__(self, name: str) -> None:
        self.name = name

    def meow(self) -> str:
        return f"{self.name} says meow!"


def main() -> None:
    print(Cat("Mia").meow())


if __name__ == "__main__":
    main()
```

### Task 2 — `test_cat.py`

`pytest` discovers files named `test_*.py` and functions named `test_*`. The test imports `Cat` and makes a single assertion.

```python
from cat import Cat


def test_cat_meow() -> None:
    assert Cat("Mia").meow() == "Mia says meow!"
```

### Task 3 — Running pytest

```bash
pytest 00-setup/code/test_cat.py -v
```

✅ You should see something like `00-setup/code/test_cat.py::test_cat_meow PASSED`.

### Task 4 — Capturing versions

```python
# 00-setup/code/versions.py
import sys
import pytest

print("python:", sys.version.split()[0])
print("pytest:", pytest.__version__)
```

Run with `python 00-setup/code/versions.py`.

## Common pitfalls

- **Forgetting the `if __name__ == "__main__":` guard.** If you put the `print()` at module top level, importing the file (as the test does) will run the print on import. That's almost never what you want.
- **Importing without the right path.** The lab uses `pytest 00-setup/code/test_cat.py` from the repo root. The import `from cat import Cat` works because `pytest` adds the file's directory to `sys.path` automatically. If you ever need to import from `code/` outside pytest, add the path or use a package.
- **Test name not starting with `test_`.** `pytest` only collects functions whose name starts with `test`. A function called `check_meow()` is silently ignored.
