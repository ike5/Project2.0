# VERIFY — confirm your environment works

Run these before Module 00. Each has an expected result. If one fails, the fix is noted.

---

## 1. Python version

```bash
python3 --version
```

✅ You should see `Python 3.10` or higher. (Some exercises use `match` statements and `|` union types, which require 3.10+.)

> If you have an older version, install Python 3.11+ from https://www.python.org/downloads/ or via `pyenv`.

## 2. Create the course virtual environment

```bash
cd python-oop-course
python3 -m venv .venv
source .venv/bin/activate
```

✅ Your prompt should now be prefixed with `(.venv)`.

> On Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

✅ You should see `Successfully installed pytest-... pytest-cov-...`.

## 4. Confirm pytest is available

```bash
pytest --version
```

✅ You should see `pytest 7.x` or higher.

## 5. Confirm you can run a small script

```bash
python -c "print('hello, oop')"
```

✅ You should see `hello, oop`.

## 6. Confirm a class can be defined and instantiated

```bash
python -c "class Dog: pass; d = Dog(); print(type(d).__name__)"
```

✅ You should see `Dog`.

If 1–6 pass, you're ready.

👉 **[Module 00: Setup & Orientation](./00-setup/)**
