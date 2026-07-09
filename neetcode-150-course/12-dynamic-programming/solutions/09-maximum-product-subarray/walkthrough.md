# Maximum Product Subarray - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given an integer array `nums`, find a subarray that has the largest product, and return the product.

## Examples

- `nums = [2,3,-2,4]` &rarr; `6`
- `nums = [-2,0,-1]` &rarr; `0`

## Constraints

- 1 <= len(nums) <= 2 * 10^4
- -10 <= nums[i] <= 10

## Intuition

Track both max and min ending at the current position. On a
negative, swap them. The min can become the max after a sign flip.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
