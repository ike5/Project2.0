# Two Sum - walkthrough

**Difficulty:** Easy &middot; **Module:** 01 Arrays Hashing

## Brief

Given an array `nums` and an integer `target`, return the **indices** of the two numbers such that they add up to `target`. Exactly one solution exists. You may not use the same element twice.

## Examples

- `nums = [2,7,11,15], target = 9` &rarr; `[0, 1]`
- `nums = [3,2,4],    target = 6` &rarr; `[1, 2]`
- `nums = [3,3],      target = 6` &rarr; `[0, 1]`

## Constraints

- 2 <= len(nums) <= 10^4
- -10^9 <= nums[i] <= 10^9
- Exactly one valid answer

## Intuition

For each `x`, the *complement* `target - x` must have appeared earlier. We can
check this in O(1) with a hash map from value to its index.

## Approach
Walk the array. Before inserting `x` at index `i`, check whether
`target - x` is in the map. If yes, we have our pair.

## Complexity
- **Time:** O(n) — one pass; each map op is amortized O(1).
- **Space:** O(n) worst case (no match until the end).

## Follow-ups
- *Return the values, not the indices?* Drop the index from the map.
- *Sorted input, return values in order?* Use the two-pointer technique
  (Module 02) — O(1) extra space, but O(n) time.
- *What if there are multiple valid pairs?* Keep going; collect all pairs.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
