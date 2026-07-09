# Lab 10 — Magic methods & iteration

**You'll:** build a `Stack` class with `__repr__`/`__len__`/`__iter__`/`__getitem__`/`__contains__`, then build the LeetCode 622 circular queue. ⏱️ ~40 min.

---

## Part A — Stack with magic methods

```bash
python 10-magic-methods/code/stack.py
```

✅ You should see the stack work as a real list-like object: `len(s)`, `for x in s`, `2 in s`, `s[-1]`, etc.

## Part B — Circular queue

```bash
python 10-magic-methods/code/circular_queue.py
```

✅ You should see enqueue/dequeue/Front/Rear work; the queue refuses to overflow.

## Part C — pytest

```bash
python -m pytest 10-magic-methods/code/test_circular_queue.py
```

✅ All tests pass.

---

When everything passes, move to the challenge.
