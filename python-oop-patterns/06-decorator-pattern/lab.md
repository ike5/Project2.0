# Lab 06 — Decorator pattern

**You'll:** stack two logger wrappers, then build the LeetCode 146 LRU Cache. ⏱️ ~40 min.

---

## Part A — Stack the loggers

```bash
python 06-decorator-pattern/code/logged.py
```

✅ You should see one line that is both uppercased *and* timestamped.

## Part B — Build the LRU cache

```bash
python 06-decorator-pattern/code/lru_cache.py
```

✅ You should see the LeetCode 146 example: `get(1) -> -1` (evicted), `get(3) -> 3`, `get(4) -> 4`.

Read the implementation. Note the `move_to_end` and `popitem(last=False)` calls. Try wrapping the inner `OrderedDict` in a `dict` to confirm `move_to_end` is unique to `OrderedDict`.

## Part C — pytest

```bash
python -m pytest 06-decorator-pattern/code/test_lru_cache.py
```

✅ All tests pass.

## Part D — Stress test

Open `06-decorator-pattern/code/lru_stress.py`. It generates a long random sequence of `get`/`put` calls and checks that your `LRUCache` agrees with a naive (but correct) reference implementation. Run it. If it passes in reasonable time, your solution is O(1) per op.

---

When everything passes, move to the challenge.
