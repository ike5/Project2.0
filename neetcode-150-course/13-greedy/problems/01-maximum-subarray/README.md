# Maximum Subarray

**Difficulty:** Easy

## Problem

Given an integer array `nums`, find the subarray with the largest sum, and return its sum.

## Examples

```
Input:  nums = [-2,1,-3,4,-1,2,1,-5,4]
Output: 6
```

```
Input:  nums = [1]
Output: 1
```

```
Input:  nums = [5,4,-1,7,8]
Output: 23
```

## Constraints

- 1 <= len(nums) <= 10^5
- -10^4 <= nums[i] <= 10^4

## Hints

1. Kadane's algorithm: keep a running sum; reset to 0 when it goes negative.

## Solution

See [`../../solutions/01-maximum-subarray/`](../../solutions/01-maximum-subarray/) for the Python and Java 21 solutions and a step-by-step walkthrough.
