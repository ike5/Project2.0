# Longest Common Subsequence - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given two strings `text1` and `text2`, return the length of their longest **common subsequence**. A *subsequence* of a string is a new string generated from the original string with some characters (can be none) deleted without changing the relative order of the remaining characters.

## Examples

- `text1 = 'abcde', text2 = 'ace'` &rarr; `3`
- `text1 = 'abc', text2 = 'abc'` &rarr; `3`
- `text1 = 'abc', text2 = 'def'` &rarr; `0`

## Constraints

- 1 <= len(text1), len(text2) <= 1000

## Intuition

Classic 2D DP, reduced to one row. The `prev` variable holds
`dp[i-1][j-1]` from the previous row.

**Time:** O(m · n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
