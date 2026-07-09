# Challenge 02 — Loops & iteration patterns

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `max_profit(prices)` yourself.** Save in `02-loops-and-iteration/code/max_profit_mine.py`. The O(n) "track the running minimum" version. Submit it to LeetCode 121.
2. **Implement `two_sum_ii(nums, target)`** (LeetCode 167). The input is a **1-indexed sorted array**. Return 1-indexed positions. Use two pointers — not a hash map, since the sorted property is the point.
3. **Implement `length_of_longest_substring(s)`** (LeetCode 3). Use a sliding window + a `set` (or a `dict` storing the last index). Aim for O(n).
4. **Write `pytest` tests** in `02-loops-and-iteration/code/test_mine.py`.

## LeetCode

- [121. Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) — submit your `max_profit`.
- [167. Two Sum II](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/) — bonus.
- [3. Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) — bonus.

## Success criteria

- [ ] `max_profit([7,1,5,3,6,4]) == 5`.
- [ ] `two_sum_ii([2,7,11,15], 9) == [1, 2]` (1-indexed).
- [ ] `length_of_longest_substring("pwwkew") == 3`.
- [ ] All tests pass with `python -m pytest`.
