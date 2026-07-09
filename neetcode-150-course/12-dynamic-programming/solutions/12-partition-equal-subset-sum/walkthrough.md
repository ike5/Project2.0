# Partition Equal Subset Sum - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given a non-empty array `nums` containing only positive integers, find if the array can be partitioned into two subsets such that the sum of elements in both subsets is equal.

## Examples

- `nums = [1,5,11,5]` &rarr; `True`
- `nums = [1,2,3,5]` &rarr; `False`

## Constraints

- 1 <= len(nums) <= 200
- 1 <= nums[i] <= 100

## Intuition

Subset-sum DP. The target is `total / 2` (must be even). Each
number is either in or out of the subset.

**Time:** O(n · sum). **Space:** O(sum).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
