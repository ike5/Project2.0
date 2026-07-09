# Challenge 11 — Composition

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `Twitter`** in `11-composition/code/twitter_mine.py` from scratch. Submit to LeetCode 355.
2. **Build a `RateLimiter`** class that allows at most `N` operations per `W` seconds. Use a `deque` of timestamps; on each `allow()` call, evict old timestamps, then return `True` if the deque has fewer than `N` items, else `False`.
3. **Write `pytest` tests** for both in `11-composition/code/test_mine.py`.

## Success criteria

- [ ] LeetCode 355 accepts your `Twitter`.
- [ ] `RateLimiter(3, 1.0).allow()` returns `True, True, True, False` if you call it four times in a row.
- [ ] All tests pass.
