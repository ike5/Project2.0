# Median of Two Sorted Arrays - walkthrough

**Difficulty:** Hard &middot; **Module:** 05 Binary Search

## Brief

Given two sorted arrays `nums1` and `nums2` of size `m` and `n` respectively, return the median of the two sorted arrays. The overall run time complexity should be O(log (m+n)).

## Examples

- `nums1 = [1,3], nums2 = [2]` &rarr; `2.0`
- `nums1 = [1,2], nums2 = [3,4]` &rarr; `2.5`

## Constraints

- 0 <= m, n <= 1000
- 1 <= m + n <= 2000
- -10^6 <= nums1[i], nums2[i] <= 10^6

## Intuition

Binary search the smaller array for the correct partition. A
correct partition has `left1 <= right2` and `left2 <= right1`. The
median is then derived from the four boundary values.

**Time:** O(log(min(m, n))). **Space:** O(1).

This is the canonical "binary search the answer space" problem and
shows up in interviews even when not asked directly — it teaches the
partition technique used in many other search problems.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
