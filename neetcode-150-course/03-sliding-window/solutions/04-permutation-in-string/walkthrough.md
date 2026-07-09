# Permutation in String - walkthrough

**Difficulty:** Medium &middot; **Module:** 03 Sliding Window

## Brief

Given two strings `s1` and `s2`, return `True` if `s2` contains a permutation of `s1`. In other words, return `True` if one of `s1`'s permutations is a substring of `s2`.

## Examples

- `s1 = 'ab', s2 = 'eidbaooo'` &rarr; `True`
- `s1 = 'ab', s2 = 'eidboaoo'` &rarr; `False`

## Constraints

- 1 <= len(s1), len(s2) <= 10^4
- Strings consist of lowercase English letters

## Intuition

Fixed-size window of length `len(s1)`. Maintain a count of the window's
characters and compare to `s1`'s count. O(n · 26) is fine for ASCII.

**Time:** O(n · 26) = O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
