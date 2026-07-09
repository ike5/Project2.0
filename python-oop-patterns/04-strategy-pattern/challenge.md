# Challenge 04 — Strategy pattern

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `BrowserHistory`** in `04-strategy-pattern/code/browser_history_mine.py` from scratch (no peeking at the lab). Submit to LeetCode 1472.
2. **Build a `Sorter` class** that takes a `key=` function in `__init__` and exposes `sort(xs)`. Use `sorted(xs, key=self.key)`. Add at least three key functions (`identity`, `length`, `last_char`) and demonstrate each.
3. **Write `pytest` tests** in `04-strategy-pattern/code/test_mine.py`.

## Success criteria

- [ ] `BrowserHistory` passes LeetCode 1472.
- [ ] `Sorter(key=length).sort(["the", "a", "and"])` returns `["a", "the", "and"]`.
- [ ] All tests pass.
