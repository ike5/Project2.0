# Challenge 00 — Setup & Orientation

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Add a new class.** Create `00-setup/code/cat.py` with a `Cat` class that takes a `name` in `__init__` and has a `meow()` method returning `f"{self.name} says meow!"`. Include the `if __name__ == "__main__":` guard. (hint: copy the `Dog` class as a starting point.)
2. **Add a test.** Create `00-setup/code/test_cat.py` that imports `Cat` and asserts `Cat("Mia").meow() == "Mia says meow!"`.
3. **Run the test.** Use `pytest` to run only that test file with `-v`.
4. **Check the version.** Run `python --version` and `pytest --version` and report the output. (hint: a one-line `print()` script in `00-setup/code/versions.py` is a clean way to capture it.)

## Success criteria

- [ ] `python 00-setup/code/cat.py` prints `Mia says meow!` (or whatever name you picked).
- [ ] `pytest 00-setup/code/test_cat.py -v` shows one passing test.
- [ ] `00-setup/code/versions.py` exists and prints both versions.
