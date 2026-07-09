# House Robber

**Difficulty:** Medium

## Problem

You are a professional robber planning to rob houses along a street. Each house has a certain amount of money stashed, the only constraint stopping you from robbing each of them is that adjacent houses have security systems connected and **it will automatically contact the police if two adjacent houses were broken into on the same night**. Given an integer array `nums` representing the amount of money at each house, return the maximum amount of money you can rob tonight **without alerting the police**.

## Examples

```
Input:  nums = [1,2,3,1]
Output: 4
```

```
Input:  nums = [2,7,9,3,1]
Output: 12
```

## Constraints

- 1 <= nums.length <= 100
- 0 <= nums[i] <= 400

## Hints

1. `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`.

## Solution

See [`../../solutions/03-house-robber/`](../../solutions/03-house-robber/) for the Python and Java 21 solutions and a step-by-step walkthrough.
