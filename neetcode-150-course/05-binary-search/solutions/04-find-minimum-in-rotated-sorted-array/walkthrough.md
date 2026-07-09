# Find Minimum in Rotated Sorted Array - walkthrough

**Difficulty:** Medium &middot; **Module:** 05 Binary Search

## Brief

Suppose an array of length `n` sorted in ascending order is rotated between 1 and n times. Given the sorted rotated array `nums` of unique elements, return the minimum element of this array. You must write an algorithm that runs in O(log n) time.

## Examples

- `nums = [3,4,5,1,2]` &rarr; `1`
- `nums = [4,5,6,7,0,1,2]` &rarr; `0`
- `nums = [11,13,15,17]` &rarr; `11`

## Constraints

- n == nums.length
- 1 <= n <= 5000
- -5000 <= nums[i] <= 5000
- All integers in nums are unique
- nums is sorted and rotated between 1 and n times

## Intuition

Comparing `nums[mid]` to `nums[hi]` (not `nums[lo]`) makes the
analysis cleaner: if `nums[mid] > nums[hi]`, the min is in the right
half (the rotation pivot is to the right of mid); otherwise it's in the
left half (including mid).

**Time:** O(log n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
