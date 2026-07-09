# Challenge 01 — Dicts as hash maps

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `two_sum(nums, target)` from scratch.** Put it in `01-dicts-as-maps/code/two_sum_mine.py`. Use a single pass + `dict`. Return the two indices in any order.
2. **Implement `first_unique_char(s)`.** Given a string, return the index of the first non-repeating character. Use `Counter` (or a `dict`). If none, return `-1`.
3. **Implement `group_by_parity(nums)`.** Given a list of ints, return a dict with two keys: `"even"` and `"odd"`, each holding a list of the matching numbers in original order. Use a `defaultdict` or manual `dict.setdefault`.
4. **Write `pytest` tests for all three.** Save as `01-dicts-as-maps/code/test_mine.py`.

## LeetCode

Open [1. Two Sum](https://leetcode.com/problems/two-sum/) and submit your `two_sum` (or the LeetCode-style class version) until it passes.

## Success criteria

- [ ] `two_sum` is O(n) and passes the four test cases in the lab's `test_two_sum.py` plus your own.
- [ ] `first_unique_char("loveleetcode")` returns `2`.
- [ ] `group_by_parity([1, 2, 3, 4])` returns `{"odd": [1, 3], "even": [2, 4]}`.
- [ ] All tests pass with `python -m pytest`.
