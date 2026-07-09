# Kth Largest Element in an Array

**Difficulty:** Medium

## Problem

Given an integer array `nums` and an integer `k`, return the kth largest element in the array. Note that it is the kth largest in the sorted order, not the kth distinct element. You must solve it in O(n) time on average.

## Examples

```
Input:  nums = [3,2,1,5,6,4], k = 2
Output: 5
```

```
Input:  nums = [3,2,3,1,2,4,5,5,6], k = 4
Output: 4
```

## Constraints

- 1 <= k <= len(nums) <= 10^5
- -10^4 <= nums[i] <= 10^4

## Hints

1. Min-heap of size k: O(n log k) — easy.
2. Quickselect: O(n) average, O(n^2) worst.

## Solution

See [`../../solutions/04-kth-largest-element-in-an-array/`](../../solutions/04-kth-largest-element-in-an-array/) for the Python and Java 21 solutions and a step-by-step walkthrough.
