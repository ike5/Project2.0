# Subsets II

**Difficulty:** Medium

## Problem

Given an integer array `nums` that may contain duplicates, return all possible subsets (the power set). The solution set **must not** contain duplicate subsets. Return the subsets in any order.

## Examples

```
Input:  nums = [1,2,2]
Output: [[],[1],[1,2],[1,2,2],[2],[2,2]]
```

```
Input:  nums = [0]
Output: [[],[0]]
```

## Constraints

- 1 <= len(nums) <= 10
- -10 <= nums[i] <= 10

## Hints

1. Sort. Skip duplicates at the same depth.

## Solution

See [`../../solutions/05-subsets-ii/`](../../solutions/05-subsets-ii/) for the Python and Java 21 solutions and a step-by-step walkthrough.
