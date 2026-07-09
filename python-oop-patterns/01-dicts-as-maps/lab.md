# Lab 01 — Dicts as hash maps

**You'll:** build a dict-based `two_sum` from scratch, benchmark it against brute force, then try a `Counter` and a `defaultdict` exercise. ⏱️ ~40 min.

Run from the `python-oop-patterns/` folder with your venv active.

---

## Part A — Run the brute force and the hash map

```bash
python 01-dicts-as-maps/code/two_sum.py
```

✅ You should see something like:

```
brute:  [0, 1]   in 0.0123 s
hash:   [0, 1]   in 0.0001 s
hash is 100x faster on n=10000
```

The exact timings vary by machine. The point: the dict version is the same order of growth as the input, the brute force is quadratic.

## Part B — Read the script and tweak it

Open `01-dicts-as-maps/code/two_sum.py` in your editor.

1. Change `NS = (100, 1_000, 10_000)` to add `100_000`. What happens to the brute force timing? (You may need to Ctrl-C; it's intentionally slow.)
2. Add a third solution: a *two-pass* hash map. Hint: walk the list once to build `{value: index}`, then walk it again to look for complements.

## Part C — Counter and defaultdict

```bash
python 01-dicts-as-maps/code/counter_defaultdict.py
```

✅ You should see:

```
top 2 chars: [('a', 5), ('b', 2)]
groups by length: {1: ['a', 'i'], 2: ['to', 'be'], 3: ['the', 'and']}
```

Read the script. Note that `defaultdict(list)` lets you append without a key check. Try changing `groups = defaultdict(list)` to `groups = {}` and see what error you get when you run it.

## Part D — pytest

```bash
python -m pytest 01-dicts-as-maps/code/test_two_sum.py
```

✅ You should see all tests pass.

Now add a test case: `nums = [3, 3]`, `target = 6` should return `[0, 1]`. Add it to the file and re-run pytest.

---

When everything passes, move to the challenge.
