# Challenge 08 — Adapter pattern

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `MinStack`** in `08-adapter-pattern/code/min_stack_mine.py` from scratch. Submit to LeetCode 155.
2. **Build a `SortedStack` adapter.** It wraps a list and supports `push(val)`, `pop()`, and `peek()`. After each push, the stack stays sorted ascending. Hint: just `insert` in the right place, or use `bisect.insort`.
3. **Write `pytest` tests** for both in `08-adapter-pattern/code/test_mine.py`.

## Success criteria

- [ ] LeetCode 155 accepts your `MinStack`.
- [ ] `SortedStack` keeps the stack sorted after every push. `peek()` returns the smallest element.
- [ ] All tests pass.
