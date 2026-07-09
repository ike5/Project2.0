# Longest Substring Without Repeating Characters - walkthrough

**Difficulty:** Medium &middot; **Module:** 03 Sliding Window

## Brief

Given a string `s`, find the length of the longest substring without repeating characters.

## Examples

- `s = 'abcabcbb'` &rarr; `3`
- `s = 'bbbbb'` &rarr; `1`
- `s = 'pwwkew'` &rarr; `3`

## Constraints

- 0 <= len(s) <= 5 * 10^4
- s consists of English letters, digits, symbols, and spaces

## Intuition

Sliding window. Two implementations:

- **Set-based** (Python): when a repeat is seen, pop from the left until
  the repeat is gone.
- **Index-based** (Java): `last[c]` stores the last index where char `c`
  appeared. Jump `l` past it if `last[c] >= l`.

Both are O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
