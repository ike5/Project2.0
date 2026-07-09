# Longest Increasing Subsequence - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given an integer array `nums`, return the length of the longest **strictly increasing** subsequence.

## Examples

- `nums = [10,9,2,5,3,7,101,18]` &rarr; `4`
- `nums = [0,1,0,3,2,3]` &rarr; `4`
- `nums = [7,7,7,7,7,7,7]` &rarr; `1`

## Constraints

- 1 <= len(nums) <= 2500
- -10^4 <= nums[i] <= 10^4

## Intuition

**Patience sorting.** Maintain a `tails` array: the smallest
tail of an increasing subsequence of each length. `bisect_left` finds
where to update.

**Time:** O(n log n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
