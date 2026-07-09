# Challenge 12 — Capstone: LFU Cache

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `LFUCache`** in `12-capstone/code/lfu_cache_mine.py` from scratch (no peeking at the lab). Submit to LeetCode 460.
2. **Refactor.** Pick one improvement from the list below and apply it. Write a test that exercises the change.
   - Add `__repr__` so `lfu` prints its state.
   - Make `put` return a bool indicating whether an eviction happened.
   - Add a `__contains__` so `key in lfu` works.
   - Add a `clear()` method.

## Success criteria

- [ ] LeetCode 460 accepts your `LFUCache`.
- [ ] Stress test passes for at least 50,000 operations.
- [ ] Refactor: at least one new method, with a test.
- [ ] All tests pass.
