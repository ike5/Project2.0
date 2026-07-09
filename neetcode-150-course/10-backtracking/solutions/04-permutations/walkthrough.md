# Permutations - walkthrough

**Difficulty:** Medium &middot; **Module:** 10 Backtracking

## Brief

Given an array `nums` of distinct integers, return all the possible permutations. You may return the answer in **any order**.

## Examples

- `nums = [1,2,3]` &rarr; `[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]`
- `nums = [0,1]` &rarr; `[[0,1],[1,0]]`

## Constraints

- 1 <= nums.length <= 6
- -10 <= nums[i] <= 10

## Intuition

Classic backtracking. At each step, try every unused element.

**Time:** O(n · n!). **Space:** O(n) recursion.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
