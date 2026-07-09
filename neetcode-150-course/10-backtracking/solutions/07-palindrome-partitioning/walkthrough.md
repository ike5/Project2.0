# Palindrome Partitioning - walkthrough

**Difficulty:** Medium &middot; **Module:** 10 Backtracking

## Brief

Given a string `s`, partition `s` such that every substring of the partition is a palindrome. Return all possible palindrome partitionings of `s`.

## Examples

- `s = 'aab'` &rarr; `[['a','a','b'],['aa','b']]`
- `s = 'a'` &rarr; `[['a']]`

## Constraints

- 1 <= len(s) <= 16
- s contains only lowercase English letters

## Intuition

Precompute `is_pal[i][j]` in O(n²) via DP. Then backtrack: at
position `i`, try every `j` such that `s[i..j]` is a palindrome.

**Time:** O(n · 2^n) for backtracking. **Space:** O(n²) for the table.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
