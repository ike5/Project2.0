# Subsets II - walkthrough

**Difficulty:** Medium &middot; **Module:** 10 Backtracking

## Brief

Given an integer array `nums` that may contain duplicates, return all possible subsets (the power set). The solution set **must not** contain duplicate subsets. Return the subsets in any order.

## Examples

- `nums = [1,2,2]` &rarr; `[[],[1],[1,2],[1,2,2],[2],[2,2]]`
- `nums = [0]` &rarr; `[[],[0]]`

## Constraints

- 1 <= len(nums) <= 10
- -10 <= nums[i] <= 10

## Intuition

Same as Subsets, but skip `nums[j] == nums[j-1]` at the same
recursion depth to avoid duplicates.

**Time:** O(n · 2^n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
