# Min Cost Climbing Stairs - walkthrough

**Difficulty:** Easy &middot; **Module:** 12 Dynamic Programming

## Brief

You are given an integer array `cost` where `cost[i]` is the cost of ith step on a staircase. Once you pay the cost, you can either climb one or two steps. You can either start from the step with index 0, or the step with index 1. Return the minimum cost to reach the top of the floor.

## Examples

- `cost = [10,15,20]` &rarr; `15`
- `cost = [1,100,1,1,1,100,1,1,100,1]` &rarr; `6`

## Constraints

- 2 <= len(cost) <= 1000
- 0 <= cost[i] <= 999

## Intuition

Same as climbing stairs, but with costs. `dp[i] = cost[i] + min(dp[i-1], dp[i-2])`.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
