# Search in Rotated Sorted Array - walkthrough

**Difficulty:** Medium &middot; **Module:** 05 Binary Search

## Brief

There is an integer array `nums` sorted in ascending order (with distinct values). Prior to being passed to your function, `nums` is possibly rotated at an unknown pivot. Given the array `nums` and an integer `target`, return the index of `target` if it is in `nums`, or `-1` if it is not. You must write an algorithm with O(log n) runtime.

## Examples

- `nums = [4,5,6,7,0,1,2], target = 0` &rarr; `4`
- `nums = [4,5,6,7,0,1,2], target = 3` &rarr; `-1`
- `nums = [1], target = 0` &rarr; `-1`

## Constraints

- 1 <= n <= 5000
- -10^4 <= nums[i] <= 10^4
- All values in nums are unique
- nums is an ascending array that is possibly rotated

## Intuition

At every step one half is sorted. Decide which half to keep based
on whether the target lies in the sorted range.

**Time:** O(log n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
