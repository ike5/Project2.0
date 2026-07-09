# Lab 02 — Loops & iteration patterns

**You'll:** build the three solutions to Best Time to Buy and Sell Stock and compare timings, then try a two-pointer and a sliding-window exercise. ⏱️ ~40 min.

---

## Part A — Three solutions to one problem

```bash
python 02-loops-and-iteration/code/stock.py
```

✅ You should see the same answer from all three solutions and a clear timing gap.

Read `02-loops-and-iteration/code/stock.py`. The O(n) "track the minimum" solution is the one to internalize — it's the same shape as a *lot* of LeetCode problems.

## Part B — Add a test

```bash
python -m pytest 02-loops-and-iteration/code/test_stock.py
```

Add a test case: `prices = [7, 6, 4, 3, 1]` (monotonically decreasing) should give `0` profit.

## Part C — Two-pointer exercise

```bash
python 02-loops-and-iteration/code/two_sum_sorted.py
```

You're given a *sorted* list and a target. Return the two indices whose values sum to the target. Read the two-pointer solution, then try the one-pass-hash-map version. Both are O(n) — the hash map version doesn't need the list sorted.

## Part D — Sliding-window warm-up

Open `02-loops-and-iteration/code/max_sum_subarray.py`. Implement `max_sum(nums, k)` — the maximum sum of any contiguous subarray of length `k`. There's a one-line O(n) solution with a sliding window. Bonus: implement the general `max_sum_k` with a `deque`-based sliding window that supports any `k`.

---

When everything passes, move to the challenge.
