# Verify your setup

Run these checks before starting Module 00. Each should print a clear success line.

## 1. Python version

```bash
python --version
```

✅ Should print something like `Python 3.10.x` or newer.

## 2. venv is active

```bash
which python
```

✅ Should point inside `python-oop-patterns/.venv/bin/`. If it points to `/usr/bin/python` or `/opt/homebrew/bin/python`, your venv isn't active — re-run `source .venv/bin/activate` (macOS/Linux) or `.\.venv\Scripts\Activate.ps1` (Windows).

## 3. pytest is installed

```bash
python -m pytest --version
```

✅ Should print `pytest 7.x` or newer.

## 4. You can import the course helpers

There are none yet — but the smoke test in Module 00 should run:

```bash
python 00-setup/code/smoke_test.py
```

✅ Should print `OK: Python is ready for LeetCode.`

## 5. You can navigate this repo

```bash
ls
```

✅ Should list `00-setup  01-dicts-as-maps  ...  GLOSSARY.md  README.md  VERIFY.md  cheatsheets  requirements.txt`.

---

If any check fails, see `00-setup/README.md` for troubleshooting.
