# Longest Repeating Character Replacement - walkthrough

**Difficulty:** Medium &middot; **Module:** 03 Sliding Window

## Brief

You are given a string `s` and an integer `k`. You can choose any character of the string and change it to any other uppercase English character. You can perform this operation at most `k` times. Return the length of the longest substring containing the same letter you can get after performing the above operations.

## Examples

- `s = 'ABAB', k = 2` &rarr; `4`
- `s = 'AABABBA', k = 1` &rarr; `4`

## Constraints

- 1 <= len(s) <= 10^5
- 0 <= k <= len(s)
- s consists of only uppercase English letters

## Intuition

For each window, the number of replacements needed is
`window_length - max_count_of_any_char_in_window`. While that exceeds `k`,
shrink from the left. The `max_count` only ever needs to go up (a smaller
window never has a *larger* max count than a super-window, so we don't
recompute on shrink) — that's the O(n) trick.

**Time:** O(n). **Space:** O(1) (26-letter alphabet) / O(k) general.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
