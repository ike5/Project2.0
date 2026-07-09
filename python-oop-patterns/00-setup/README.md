# Module 00 — Setup & DSA workflow

**Goal:** get a clean Python + `pytest` environment, confirm you can run code in this repo, and build a tiny workflow you'll reuse on every LeetCode problem. ⏱️ ~30 min.

---

## 1. Install Python 3.10+

You need Python 3.10 or newer (we use `match` statements and `|` union types in some modules).

```bash
python --version
```

If you see `Python 3.10.x` or higher, you're good. Otherwise:

- **macOS:** `brew install python@3.12` (or use the official installer from python.org).
- **Linux:** `sudo apt install python3.12` (or your distro's equivalent).
- **Windows:** the official installer from python.org — tick "Add Python to PATH".

## 2. Set up the course venv

```bash
cd python-oop-patterns
python3 -m venv .venv
source .venv/bin/activate                  # macOS/Linux
.\.venv\Scripts\Activate.ps1               # Windows
pip install -r requirements.txt
```

`requirements.txt` only contains `pytest`. Everything else in the course uses the standard library.

## 3. Confirm with the smoke test

```bash
python 00-setup/code/smoke_test.py
```

✅ You should see:

```
OK: Python is ready for LeetCode.
```

## 4. Open the REPL — your new best friend

The Python REPL (`python` with no arguments) is the fastest way to check how a built-in works. Try:

```python
>>> d = {}
>>> d["x"] = 1
>>> d.get("y", 0)
0
>>> "x" in d
True
>>> for k, v in d.items():
...     print(k, v)
...
x 1
```

You will spend a lot of time in the REPL on LeetCode. Get comfortable with it.

## 5. A workflow for every LeetCode problem

When you click into a problem, do this:

1. **Read the prompt once for understanding.** What's the input? What's the output? What are the constraints? (`n` up to `10⁵` means `O(n²)` is too slow.)
2. **Pick a container.** Most problems are "given a list/array, return something". Ask: do I need to *look things up by value*? → `dict` or `set`. *Maintain order*? → `list` or `deque`. *Top-k*? → `heapq`.
3. **Pick a pattern.** Single pass + hash map → done. Sliding window? Two-pointer? Monotonic stack? Pick it before you code.
4. **Write the brute force first.** Get a correct `O(n²)` version. Then optimize if needed.
5. **Test with the examples.** Then with edge cases: empty input, single element, duplicates, all-same values.
6. **Submit.**

Modules 01–12 give you step 2 ("pick a container") and step 3 ("pick a pattern") on rails.

## 6. Sanity checks

Run the verification checklist:

```bash
cat ../VERIFY.md
```

If any item fails, fix it before moving on. The first lesson assumes `pytest` works.

---

**→ Next: [Module 01 — Dicts as hash maps](./../01-dicts-as-maps/)**
