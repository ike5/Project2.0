# Median of Two Sorted Arrays

**Difficulty:** Hard

## Problem

Given two sorted arrays `nums1` and `nums2` of size `m` and `n` respectively, return the median of the two sorted arrays. The overall run time complexity should be O(log (m+n)).

## Examples

```
Input:  nums1 = [1,3], nums2 = [2]
Output: 2.0
```

```
Input:  nums1 = [1,2], nums2 = [3,4]
Output: 2.5
```

## Constraints

- 0 <= m, n <= 1000
- 1 <= m + n <= 2000
- -10^6 <= nums1[i], nums2[i] <= 10^6

## Hints

1. Binary search the smaller array for the partition that correctly splits the combined sorted array.
2. Left of partition (combined) has half the elements; right has the other half.

## Solution

See [`../../solutions/07-median-of-two-sorted-arrays/`](../../solutions/07-median-of-two-sorted-arrays/) for the Python and Java 21 solutions and a step-by-step walkthrough.
