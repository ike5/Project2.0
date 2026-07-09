# Jump Game - walkthrough

**Difficulty:** Medium &middot; **Module:** 13 Greedy

## Brief

You are given an integer array `nums`. You are initially positioned at the array's **first index**, and each element in the array represents your maximum jump length at that position. Return `True` if you can reach the last index, or `False` otherwise.

## Examples

- `nums = [2,3,1,1,4]` &rarr; `True`
- `nums = [3,2,1,0,4]` &rarr; `False`

## Constraints

- 1 <= len(nums) <= 10^4
- 0 <= nums[i] <= 10^5

## Intuition

Greedy. `farthest` = the rightmost index we can reach so far. If
at any point `i > farthest`, we're stuck.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
