# Contains Duplicate - walkthrough

**Difficulty:** Easy &middot; **Module:** 01 Arrays Hashing

## Brief

Given an integer array `nums`, return `True` if any value appears at least twice. Return `False` if every element is distinct.

## Examples

- `nums = [1, 2, 3, 1]` &rarr; `True`
- `nums = [1, 2, 3, 4]` &rarr; `False`
- `nums = [1, 1, 1, 3, 3, 4, 3, 2, 4, 2]` &rarr; `True`

## Constraints

- 1 <= len(nums) <= 10^5
- -10^9 <= nums[i] <= 10^9

## Intuition

We only need to detect *one* duplicate, so we don't need to count. A hash set
gives O(1) membership checks.

## Approach
Walk the array. If the current value is already in the set, return True.
Otherwise, add it. If we finish the loop, every element was unique.

## Complexity
- **Time:** O(n) — one pass; each set op is amortized O(1).
- **Space:** O(n) worst case (no duplicates).

## Follow-ups
- *What if the array is sorted?* Then a one-pass O(1)-space check works: any
  `nums[i] == nums[i+1]` is a duplicate.
- *What if memory is the bottleneck?* Sort the array in place (O(1) extra
  bytes if you count the input's own space) and then check adjacent pairs.
- *What if duplicates are *allowed* but you want to know the count?* Use a
  `Counter` / `Map<K,Integer>` instead of a set.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
