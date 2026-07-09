# Two Sum II — Input Array Is Sorted - walkthrough

**Difficulty:** Easy &middot; **Module:** 02 Two Pointers

## Brief

Given a **1-indexed** array of integers `numbers` that is already sorted in non-decreasing order, find two numbers such that they add up to a specific `target`. Return the indices of the two numbers as a 1-indexed array `[i, j]`. You may not use the same element twice.

## Examples

- `numbers = [2,7,11,15], target = 9` &rarr; `[1, 2]`
- `numbers = [2,3,4],     target = 6` &rarr; `[1, 3]`
- `numbers = [-1,0],      target = -1` &rarr; `[1, 2]`

## Constraints

- 2 <= len(numbers) <= 3 * 10^4
- -1000 <= numbers[i] <= 1000
- numbers is sorted in non-decreasing order
- Exactly one valid answer

## Intuition

Two pointers from opposite ends. The array is sorted, so adjusting one
pointer monotonically moves the sum in the right direction.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
