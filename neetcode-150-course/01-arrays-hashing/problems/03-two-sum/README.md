# Two Sum

**Difficulty:** Easy

## Problem

Given an array `nums` and an integer `target`, return the **indices** of the two numbers such that they add up to `target`. Exactly one solution exists. You may not use the same element twice.

## Examples

```
Input:  nums = [2,7,11,15], target = 9
Output: [0, 1]
```

```
Input:  nums = [3,2,4],    target = 6
Output: [1, 2]
```

```
Input:  nums = [3,3],      target = 6
Output: [0, 1]
```

## Constraints

- 2 <= len(nums) <= 10^4
- -10^9 <= nums[i] <= 10^9
- Exactly one valid answer

## Hints

1. Brute force is O(n²). Can you do it in one pass?
2. For each `x`, ask: have I seen `target - x`?

## Solution

See [`../../solutions/03-two-sum/`](../../solutions/03-two-sum/) for the Python and Java 21 solutions and a step-by-step walkthrough.
