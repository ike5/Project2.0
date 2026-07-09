# 3Sum - walkthrough

**Difficulty:** Medium &middot; **Module:** 02 Two Pointers

## Brief

Given an integer array `nums`, return all the triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`. The solution set must not contain duplicate triplets.

## Examples

- `nums = [-1,0,1,2,-1,-4]` &rarr; `[[-1,-1,2],[-1,0,1]]`
- `nums = [0,1,1]` &rarr; `[]`
- `nums = [0,0,0]` &rarr; `[[0,0,0]]`

## Constraints

- 3 <= len(nums) <= 3000
- -10^5 <= nums[i] <= 10^5

## Intuition

Sort, then fix `i` and run a two-pointer search on the rest. Skip
duplicates at every level.

**Time:** O(n²) — O(n log n) to sort, O(n²) for the nested loops (each pair
of `l, r` moves at most n times). **Space:** O(1) extra (output not counted).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
