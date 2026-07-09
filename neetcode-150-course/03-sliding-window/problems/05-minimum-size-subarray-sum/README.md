# Minimum Size Subarray Sum

**Difficulty:** Medium

## Problem

Given an array of positive integers `nums` and a positive integer `target`, return the minimal length of a **contiguous** subarray of which the sum is at least `target`. If no such subarray exists, return 0.

## Examples

```
Input:  target = 7, nums = [2,3,1,2,4,3]
Output: 2
```

```
Input:  target = 4, nums = [1,4,4]
Output: 1
```

```
Input:  target = 11, nums = [1,1,1,1,1,1,1,1]
Output: 0
```

## Constraints

- 1 <= target <= 10^9
- 1 <= len(nums) <= 10^5
- 1 <= nums[i] <= 10^4

## Hints

1. Variable-size sliding window: extend `r`, shrink `l` while sum >= target.
2. All values are positive, so a window that satisfies the condition cannot include any element that makes the sum smaller.

## Solution

See [`../../solutions/05-minimum-size-subarray-sum/`](../../solutions/05-minimum-size-subarray-sum/) for the Python and Java 21 solutions and a step-by-step walkthrough.
