# Lab 00 — Setup

**You'll:** set up the venv, run the smoke test, poke at a few Python objects in the REPL. ⏱️ ~20 min.

Run from the `python-oop-patterns/` folder with your venv active.

---

## Part A — Install + smoke test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python 00-setup/code/smoke_test.py
```

✅ You should see `OK: Python is ready for LeetCode.`

## Part B — Tour the standard containers

```bash
python 00-setup/code/containers_tour.py
```

Read through the script. It walks through `list`, `dict`, `set`, `tuple`, `Counter`, `defaultdict`, `deque`, and `heapq` — the full cast of containers we'll use in this course. Don't worry about memorizing everything; the goal is to know *which container does what* at a glance.

## Part C — REPL warm-up

```bash
python
```

In the REPL, type these (one at a time — REPLs don't handle multi-line input well from copy-paste):

```python
xs = [3, 1, 4, 1, 5, 9, 2, 6]
xs.sort()
xs
xs[2:5]
xs[::-1]            # reversed copy
```

Then:

```python
d = {"a": 1, "b": 2}
d["c"] = 3
d.get("z", 0)
for k, v in d.items():
    print(k, v)
```

Then exit with `exit()` or Ctrl-D.

## Part D — Run pytest once

```bash
python -m pytest 00-setup/code/test_smoke.py
```

✅ You should see `1 passed`.

That's the test pattern we'll reuse in later labs.

---

When everything passes, move to the challenge.
