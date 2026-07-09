# Climbing Stairs - walkthrough

**Difficulty:** Easy &middot; **Module:** 12 Dynamic Programming

## Brief

You are climbing a staircase. It takes `n` steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?

## Examples

- `n = 2` &rarr; `2`
- `n = 3` &rarr; `3`

## Constraints

- 1 <= n <= 45

## Intuition

`dp[i] = dp[i-1] + dp[i-2]` (Fibonacci). O(1) space with two
rolling variables.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
