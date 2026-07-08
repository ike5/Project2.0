# Lab 00 — Setup & Orientation

**You'll:** create a venv, install `pytest`, run a "hello" script, and run a "hello" test. ⏱️ ~20 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Create and activate the venv

```bash
cd python-oop-course
python3 -m venv .venv
source .venv/bin/activate
```

✅ Your prompt should be prefixed with `(.venv)`.

> On Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
> To deactivate later, just run `deactivate`.

## Part B — Install the course dependencies

```bash
pip install -r requirements.txt
```

✅ You should see `Successfully installed pytest-... pytest-cov-...`.

## Part C — Run a "hello" Python script

```bash
python 00-setup/code/hello_oop.py
```

✅ You should see output like:

```
hello, oop
Dog('Rex') says woof!
```

## Part D — Run the smoke test with pytest

```bash
pytest 00-setup/code/run_with_pytest.py -q
```

✅ You should see `1 passed` (or similar). `-q` is "quiet" — just the summary line.

> Optional: `pytest 00-setup/code/run_with_pytest.py -v` shows the test name.

## Part E — Run a "no tests collected" check (sanity)

```bash
python -m pytest 00-setup/code/hello_oop.py -q
```

✅ This will say `no tests ran` (or `no tests collected`). That confirms pytest can be invoked through `python -m` and that you can selectively target files.

## Cleanup

Nothing to clean up — the venv is gitignored and lives inside the project. To remove it entirely later: `rm -rf .venv`.

## What you learned

- A venv isolates per-project Python dependencies.
- `pip install -r requirements.txt` installs the course's two packages: `pytest` and `pytest-cov`.
- `python path/to/script.py` runs a file directly.
- `pytest path/to/test.py` runs tests and prints a one-line summary with `-q`.
- The `if __name__ == "__main__":` idiom separates "run as a script" from "import as a module."

➡️ **[challenge.md](./challenge.md)** then [Module 01: OOP Foundations](../01-oop-foundations/).
