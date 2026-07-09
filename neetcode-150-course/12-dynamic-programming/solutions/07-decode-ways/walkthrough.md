# Decode Ways - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

You have intercepted a secret message encoded as a string of digits 0-9 representing letters A-Z (1=A, ..., 26=Z). Return the number of ways to decode it.

## Examples

- `s = '12'` &rarr; `2`
- `s = '226'` &rarr; `3`
- `s = '06'` &rarr; `0`

## Constraints

- 1 <= len(s) <= 100
- s contains only digits

## Intuition

Two rolling variables. `dp[i]` is the number of ways to decode
`s[:i]`. The transition depends on `s[i-1]` (single digit) and
`s[i-2:i]` (two-digit pair).

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
