# Find Minimum in Rotated Sorted Array

**Difficulty:** Medium

## Problem

Suppose an array of length `n` sorted in ascending order is rotated between 1 and n times. Given the sorted rotated array `nums` of unique elements, return the minimum element of this array. You must write an algorithm that runs in O(log n) time.

## Examples

```
Input:  nums = [3,4,5,1,2]
Output: 1
```

```
Input:  nums = [4,5,6,7,0,1,2]
Output: 0
```

```
Input:  nums = [11,13,15,17]
Output: 11
```

## Constraints

- n == nums.length
- 1 <= n <= 5000
- -5000 <= nums[i] <= 5000
- All integers in nums are unique
- nums is sorted and rotated between 1 and n times

## Hints

1. Compare `nums[mid]` to `nums[hi]`. If `nums[mid] > nums[hi]`, the min is in the right half; else in the left.

## Solution

See [`../../solutions/04-find-minimum-in-rotated-sorted-array/`](../../solutions/04-find-minimum-in-rotated-sorted-array/) for the Python and Java 21 solutions and a step-by-step walkthrough.
