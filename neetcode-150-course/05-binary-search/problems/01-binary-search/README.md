# Binary Search

**Difficulty:** Easy

## Problem

Given a **sorted** array of integers `nums` of length `n` and a target, return the index of `target` if it is in `nums`, or `-1` if it is not. You must write an algorithm with O(log n) runtime.

## Examples

```
Input:  nums = [-1,0,3,5,9,12], target = 9
Output: 4
```

```
Input:  nums = [-1,0,3,5,9,12], target = 2
Output: -1
```

## Constraints

- 1 <= n <= 10^4
- -10^4 < nums[i], target < 10^4
- All integers in nums are unique
- nums is sorted in ascending order

## Hints

1. Classic half-interval search.
2. Use `lo + (hi - lo) // 2` to avoid overflow in Java `int`.

## Solution

See [`../../solutions/01-binary-search/`](../../solutions/01-binary-search/) for the Python and Java 21 solutions and a step-by-step walkthrough.
