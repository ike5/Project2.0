# Maximum Subarray - walkthrough

**Difficulty:** Easy &middot; **Module:** 13 Greedy

## Brief

Given an integer array `nums`, find the subarray with the largest sum, and return its sum.

## Examples

- `nums = [-2,1,-3,4,-1,2,1,-5,4]` &rarr; `6`
- `nums = [1]` &rarr; `1`
- `nums = [5,4,-1,7,8]` &rarr; `23`

## Constraints

- 1 <= len(nums) <= 10^5
- -10^4 <= nums[i] <= 10^4

## Intuition

Kadane. `cur` = best sum ending at the current position. We
either extend the previous best (`cur + x`) or start fresh at `x`.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
