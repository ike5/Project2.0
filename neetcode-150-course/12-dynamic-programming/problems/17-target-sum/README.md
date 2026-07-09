# Target Sum

**Difficulty:** Medium

## Problem

You are given an integer array `nums` and an integer `target`. You want to build an expression by placing a `+` or `-` sign in front of each integer in `nums` and then concatenate all the signed integers. Return the number of different expressions that you can build, which evaluate to `target`.

## Examples

```
Input:  nums = [1,1,1,1,1], target = 3
Output: 5
```

```
Input:  nums = [1], target = 1
Output: 1
```

## Constraints

- 1 <= nums.length <= 20
- 0 <= nums[i] <= 1000
- 0 <= sum(nums[i]) <= 1000
- -1000 <= target <= 1000

## Hints

1. Reduce to subset sum: partition nums into positive and negative groups. The sum condition becomes a subset-sum problem.

## Solution

See [`../../solutions/17-target-sum/`](../../solutions/17-target-sum/) for the Python and Java 21 solutions and a step-by-step walkthrough.
