# Product of Array Except Self

**Difficulty:** Medium

## Problem

Given an integer array `nums`, return an array `answer` such that `answer[i]` equals the product of all the elements of `nums` except `nums[i]`. Solve it in O(n) time without using the division operator.

## Examples

```
Input:  nums = [1,2,3,4]
Output: [24,12,8,6]
```

```
Input:  nums = [-1,1,0,-3,3]
Output: [0,0,9,0,0]
```

## Constraints

- 2 <= len(nums) <= 10^5
- -30 <= nums[i] <= 30
- The product of any prefix or suffix fits in a 32-bit int

## Hints

1. Compute prefix products and suffix products in two passes.
2. You can do it in O(1) extra space by reusing `answer` for the prefix and a running suffix variable.

## Solution

See [`../../solutions/06-product-of-array-except-self/`](../../solutions/06-product-of-array-except-self/) for the Python and Java 21 solutions and a step-by-step walkthrough.
