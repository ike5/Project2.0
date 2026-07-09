# Subsets

**Difficulty:** Medium

## Problem

Given an integer array `nums` of unique elements, return all possible subsets (the power set). The solution set must not contain duplicate subsets. Return the subsets in any order.

## Examples

```
Input:  nums = [1,2,3]
Output: [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]
```

```
Input:  nums = [0]
Output: [[],[0]]
```

## Constraints

- 1 <= len(nums) <= 10
- -10 <= nums[i] <= 10
- All the numbers of nums are unique

## Hints

1. For each element, choose to include it or not. Backtrack on both.

## Solution

See [`../../solutions/01-subsets/`](../../solutions/01-subsets/) for the Python and Java 21 solutions and a step-by-step walkthrough.
