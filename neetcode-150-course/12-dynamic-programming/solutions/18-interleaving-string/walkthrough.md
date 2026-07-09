# Interleaving String - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given strings `s1`, `s2`, and `s3`, find whether `s3` is formed by an interleaving of `s1` and `s2`. An interleaving of two strings `s` and `t` is a configuration where `s` and `t` are divided into non-empty substrings respectively, and the resulting string is `s` and `t` concatenated.

## Examples

- `s1 = 'aabcc', s2 = 'dbbca', s3 = 'aadbbcbcac'` &rarr; `True`
- `s1 = 'aabcc', s2 = 'dbbca', s3 = 'aadbbbaccc'` &rarr; `False`

## Constraints

- 0 <= len(s1), len(s2) <= 100
- 0 <= len(s3) <= 200
- s1, s2, s3 consist of lowercase English letters

## Intuition

2D DP reduced to one row. `dp[i][j]` = can `s1[:i]` and `s2[:j]`
form `s3[:i+j]`.

**Time:** O(m · n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
