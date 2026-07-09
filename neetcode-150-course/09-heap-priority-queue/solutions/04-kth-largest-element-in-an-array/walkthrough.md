# Kth Largest Element in an Array - walkthrough

**Difficulty:** Medium &middot; **Module:** 09 Heap Priority Queue

## Brief

Given an integer array `nums` and an integer `k`, return the kth largest element in the array. Note that it is the kth largest in the sorted order, not the kth distinct element. You must solve it in O(n) time on average.

## Examples

- `nums = [3,2,1,5,6,4], k = 2` &rarr; `5`
- `nums = [3,2,3,1,2,4,5,5,6], k = 4` &rarr; `4`

## Constraints

- 1 <= k <= len(nums) <= 10^5
- -10^4 <= nums[i] <= 10^4

## Intuition

The simplest is `heapq.nlargest(k, nums)[-1]` in Python or a
min-heap of size k. Quickselect is O(n) average but O(n^2) worst and
trickier to write.

**Time:** O(n log k) with heap; O(n) average with quickselect.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
