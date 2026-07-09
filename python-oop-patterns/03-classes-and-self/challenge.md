# Challenge 03 — Classes & `self`

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `class Hits` from scratch** (no peeking at the lab) in `03-classes-and-self/code/counter_mine.py`. It should have the same five methods as the lab version.
2. **Implement `class RecentCounter`** (LeetCode 933). It has a `ping(t)` method; return the number of pings in `[t - 3000, t]`. Hint: a `deque` of past timestamps — pop from the left while they're outside the window.
3. **Submit `RecentCounter`** to LeetCode.
4. **Write `pytest` tests** for both classes in `03-classes-and-self/code/test_mine.py`.

## Success criteria

- [ ] `Hits()` works: `record`, `record_n`, `total`, `reset`.
- [ ] `RecentCounter().ping(1)` returns `1`, `.ping(10)` returns `2`, `.ping(3001)` returns `3`, `.ping(3002)` returns `3`.
- [ ] All tests pass with `python -m pytest`.
- [ ] LeetCode 933 accepts your submission.
