# Subsets - walkthrough

**Difficulty:** Medium &middot; **Module:** 10 Backtracking

## Brief

Given an integer array `nums` of unique elements, return all possible subsets (the power set). The solution set must not contain duplicate subsets. Return the subsets in any order.

## Examples

- `nums = [1,2,3]` &rarr; `[[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]`
- `nums = [0]` &rarr; `[[],[0]]`

## Constraints

- 1 <= len(nums) <= 10
- -10 <= nums[i] <= 10
- All the numbers of nums are unique

## Intuition

Two choices per element: include or skip. Total subsets = 2^n.

**Time:** O(n · 2^n). **Space:** O(n) recursion depth.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
