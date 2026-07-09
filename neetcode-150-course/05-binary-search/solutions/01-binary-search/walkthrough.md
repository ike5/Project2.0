# Binary Search - walkthrough

**Difficulty:** Easy &middot; **Module:** 05 Binary Search

## Brief

Given a **sorted** array of integers `nums` of length `n` and a target, return the index of `target` if it is in `nums`, or `-1` if it is not. You must write an algorithm with O(log n) runtime.

## Examples

- `nums = [-1,0,3,5,9,12], target = 9` &rarr; `4`
- `nums = [-1,0,3,5,9,12], target = 2` &rarr; `-1`

## Constraints

- 1 <= n <= 10^4
- -10^4 < nums[i], target < 10^4
- All integers in nums are unique
- nums is sorted in ascending order

## Intuition

The classic. Two things to internalize:

- **Loop guard:** `while lo <= hi`. If `lo > hi`, the target isn't there.
- **Midpoint:** `lo + (hi - lo) // 2` (Java: `/ 2`). Avoids `int` overflow
  in languages where `(lo + hi) / 2` could overflow.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
