# Challenge 10 — Magic methods & iteration

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `MyCircularQueue`** in `10-magic-methods/code/circular_queue_mine.py` from scratch. Submit to LeetCode 622.
2. **Build a `BoundedStack(capacity)`** that adds `__len__`, `__iter__`, `__contains__`, `__getitem__`, and `__repr__` to a `list` — and refuses to push past capacity. Use the adapter pattern from Module 08.
3. **Write `pytest` tests** for both in `10-magic-methods/code/test_mine.py`.

## Success criteria

- [ ] LeetCode 622 accepts your `MyCircularQueue`.
- [ ] `BoundedStack(3)` lets you push 3 items and refuses a 4th; supports `len`, `for x in s`, `2 in s`, `s[0]`.
- [ ] All tests pass.
