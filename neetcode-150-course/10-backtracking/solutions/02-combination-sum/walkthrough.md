# Combination Sum - walkthrough

**Difficulty:** Medium &middot; **Module:** 10 Backtracking

## Brief

Given an array of **distinct** integers `candidates` and a target integer `target`, return a list of all unique combinations of `candidates` where the chosen numbers sum to `target`. The same number may be chosen from `candidates` an unlimited number of times. Two combinations are unique if the frequency of at least one of the chosen numbers is different.

## Examples

- `candidates = [2,3,6,7], target = 7` &rarr; `[[2,2,3],[7]]`
- `candidates = [2,3,5], target = 8` &rarr; `[[2,2,2,2],[2,3,3],[3,5]]`

## Constraints

- 1 <= candidates.length <= 30
- 2 <= candidates[i] <= 40
- All elements of candidates are distinct
- 1 <= target <= 40

## Intuition

Backtrack. At index `i`, either skip `candidates[i]` or include
it (and recurse on the same `i` to allow reuse).

**Time:** O(2^target) worst case. **Space:** O(target) recursion.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
