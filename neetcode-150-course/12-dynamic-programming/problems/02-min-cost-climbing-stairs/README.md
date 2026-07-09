# Min Cost Climbing Stairs

**Difficulty:** Easy

## Problem

You are given an integer array `cost` where `cost[i]` is the cost of ith step on a staircase. Once you pay the cost, you can either climb one or two steps. You can either start from the step with index 0, or the step with index 1. Return the minimum cost to reach the top of the floor.

## Examples

```
Input:  cost = [10,15,20]
Output: 15
```

```
Input:  cost = [1,100,1,1,1,100,1,1,100,1]
Output: 6
```

## Constraints

- 2 <= len(cost) <= 1000
- 0 <= cost[i] <= 999

## Hints

1. `dp[i] = cost[i] + min(dp[i-1], dp[i-2])`.

## Solution

See [`../../solutions/02-min-cost-climbing-stairs/`](../../solutions/02-min-cost-climbing-stairs/) for the Python and Java 21 solutions and a step-by-step walkthrough.
