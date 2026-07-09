# Challenge 06 — Decorator pattern

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `LRUCache`** in `06-decorator-pattern/code/lru_cache_mine.py` from scratch (no peeking at the lab). Submit to LeetCode 146.
2. **Implement `LFUCache` (easy version).** The least-frequently-used eviction policy. Use a `dict[key, value]`, a `dict[key, freq]`, and a `dict[freq, OrderedDict[key, value]]` for O(1) `get`/`put`. (This is the LFU "lite" version — the real LFU is in the capstone.)
3. **Write `pytest` tests** for both in `06-decorator-pattern/code/test_mine.py`.

## Success criteria

- [ ] LeetCode 146 accepts your `LRUCache`.
- [ ] `LFUCache(2).put(1,1)`, `.put(2,2)`, `.get(1)`, `.put(3,3)`, `.get(2) == -1`, `.get(3) == 3`. (After `get(1)`, key 1 has freq 2 and key 2 has freq 1, so adding key 3 evicts key 2.)
- [ ] All tests pass.
