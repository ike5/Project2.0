# Search in Rotated Sorted Array

**Difficulty:** Medium

## Problem

There is an integer array `nums` sorted in ascending order (with distinct values). Prior to being passed to your function, `nums` is possibly rotated at an unknown pivot. Given the array `nums` and an integer `target`, return the index of `target` if it is in `nums`, or `-1` if it is not. You must write an algorithm with O(log n) runtime.

## Examples

```
Input:  nums = [4,5,6,7,0,1,2], target = 0
Output: 4
```

```
Input:  nums = [4,5,6,7,0,1,2], target = 3
Output: -1
```

```
Input:  nums = [1], target = 0
Output: -1
```

## Constraints

- 1 <= n <= 5000
- -10^4 <= nums[i] <= 10^4
- All values in nums are unique
- nums is an ascending array that is possibly rotated

## Hints

1. At each step, one half is sorted. Check if the target is in the sorted half; if so, search there; else, search the other half.

## Solution

See [`../../solutions/05-search-in-rotated-sorted-array/`](../../solutions/05-search-in-rotated-sorted-array/) for the Python and Java 21 solutions and a step-by-step walkthrough.
