# Find the Duplicate Number

**Difficulty:** Medium

## Problem

Given an array of integers `nums` containing `n + 1` integers where each integer is in the range `[1, n]` inclusive, prove that at least one duplicate number must exist. Return the duplicate. You must solve it without modifying the array and using only O(1) extra space.

## Examples

```
Input:  nums = [1,3,4,2,2]
Output: 2
```

```
Input:  nums = [3,1,3,4,2]
Output: 3
```

## Constraints

- 1 <= n <= 10^5
- nums.length == n + 1
- 1 <= nums[i] <= n
- Only one duplicate, but it could appear more than once

## Hints

1. Treat the array as a linked list: `next(i) = nums[i]`. The duplicate is the entry point of the cycle.
2. Floyd's: first find a meeting point inside the cycle, then find the cycle's start.

## Solution

See [`../../solutions/08-find-the-duplicate-number/`](../../solutions/08-find-the-duplicate-number/) for the Python and Java 21 solutions and a step-by-step walkthrough.
