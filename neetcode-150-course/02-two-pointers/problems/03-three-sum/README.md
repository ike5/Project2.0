# 3Sum

**Difficulty:** Medium

## Problem

Given an integer array `nums`, return all the triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`. The solution set must not contain duplicate triplets.

## Examples

```
Input:  nums = [-1,0,1,2,-1,-4]
Output: [[-1,-1,2],[-1,0,1]]
```

```
Input:  nums = [0,1,1]
Output: []
```

```
Input:  nums = [0,0,0]
Output: [[0,0,0]]
```

## Constraints

- 3 <= len(nums) <= 3000
- -10^5 <= nums[i] <= 10^5

## Hints

1. Sort first. Then for each i, run a two-pointer search on the rest.
2. Skip duplicates at i, l, and r to avoid emitting the same triplet twice.

## Solution

See [`../../solutions/03-three-sum/`](../../solutions/03-three-sum/) for the Python and Java 21 solutions and a step-by-step walkthrough.
