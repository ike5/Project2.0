# Minimum Size Subarray Sum - walkthrough

**Difficulty:** Medium &middot; **Module:** 03 Sliding Window

## Brief

Given an array of positive integers `nums` and a positive integer `target`, return the minimal length of a **contiguous** subarray of which the sum is at least `target`. If no such subarray exists, return 0.

## Examples

- `target = 7, nums = [2,3,1,2,4,3]` &rarr; `2`
- `target = 4, nums = [1,4,4]` &rarr; `1`
- `target = 11, nums = [1,1,1,1,1,1,1,1]` &rarr; `0`

## Constraints

- 1 <= target <= 10^9
- 1 <= len(nums) <= 10^5
- 1 <= nums[i] <= 10^4

## Intuition

Variable window. Extend `r`; while the sum is at least `target`,
shrink from the left and update the best length. O(n) because each
element is added and removed at most once.

> *With negative numbers?* Sliding window doesn't apply; you need
> prefix sums + hash map, or a different technique.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
