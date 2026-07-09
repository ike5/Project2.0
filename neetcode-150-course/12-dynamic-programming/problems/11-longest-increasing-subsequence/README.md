# Longest Increasing Subsequence

**Difficulty:** Medium

## Problem

Given an integer array `nums`, return the length of the longest **strictly increasing** subsequence.

## Examples

```
Input:  nums = [10,9,2,5,3,7,101,18]
Output: 4
```

```
Input:  nums = [0,1,0,3,2,3]
Output: 4
```

```
Input:  nums = [7,7,7,7,7,7,7]
Output: 1
```

## Constraints

- 1 <= len(nums) <= 2500
- -10^4 <= nums[i] <= 10^4

## Hints

1. Standard O(n²) DP: `dp[i] = max(dp[j] + 1)` for `j < i` and `nums[j] < nums[i]`.
2. O(n log n) with patience sorting: `bisect_left` on a 'tails' array.

## Solution

See [`../../solutions/11-longest-increasing-subsequence/`](../../solutions/11-longest-increasing-subsequence/) for the Python and Java 21 solutions and a step-by-step walkthrough.
