# Permutations

**Difficulty:** Medium

## Problem

Given an array `nums` of distinct integers, return all the possible permutations. You may return the answer in **any order**.

## Examples

```
Input:  nums = [1,2,3]
Output: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
```

```
Input:  nums = [0,1]
Output: [[0,1],[1,0]]
```

## Constraints

- 1 <= nums.length <= 6
- -10 <= nums[i] <= 10

## Hints

1. Backtrack, swapping each unused element to the front, or use a used set.

## Solution

See [`../../solutions/04-permutations/`](../../solutions/04-permutations/) for the Python and Java 21 solutions and a step-by-step walkthrough.
