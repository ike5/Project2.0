# Lab 05 — Observer pattern

**You'll:** build a `Newsfeed` with subscribers, then build the LeetCode 362 `HitCounter`. ⏱️ ~30 min.

---

## Part A — Newsfeed

```bash
python 05-observer-pattern/code/newsfeed.py
```

✅ You should see two subscribers (a `print` and a counter) react to three headlines. The counter ends at `3`.

## Part B — Add a third subscriber

Open `05-observer-pattern/code/newsfeed.py`. Add a third subscriber that uppercases the headline before printing. Re-run and confirm it works.

## Part C — HitCounter

```bash
python 05-observer-pattern/code/hit_counter.py
```

✅ You should see counts that match LeetCode 362's example.

## Part D — pytest

```bash
python -m pytest 05-observer-pattern/code/test_hit_counter.py
```

✅ All tests pass.

---

When everything passes, move to the challenge.
