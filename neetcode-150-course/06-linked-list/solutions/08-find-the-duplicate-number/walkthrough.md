# Find the Duplicate Number - walkthrough

**Difficulty:** Medium &middot; **Module:** 06 Linked List

## Brief

Given an array of integers `nums` containing `n + 1` integers where each integer is in the range `[1, n]` inclusive, prove that at least one duplicate number must exist. Return the duplicate. You must solve it without modifying the array and using only O(1) extra space.

## Examples

- `nums = [1,3,4,2,2]` &rarr; `2`
- `nums = [3,1,3,4,2]` &rarr; `3`

## Constraints

- 1 <= n <= 10^5
- nums.length == n + 1
- 1 <= nums[i] <= n
- Only one duplicate, but it could appear more than once

## Intuition

Treat the array as a linked list: index `i` is a node, `nums[i]` is
its `next` pointer. The duplicate is the start of the cycle. Floyd's
algorithm finds it without modifying the array.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
