# Combination Sum II - walkthrough

**Difficulty:** Medium &middot; **Module:** 10 Backtracking

## Brief

Given a collection of candidate numbers (`candidates`) and a target number (`target`), find all unique combinations in `candidates` where the candidate numbers sum to `target`. Each number in `candidates` may only be used **once** in the combination. Note: The solution set must not contain duplicate combinations.

## Examples

- `candidates = [10,1,2,7,6,1,5], target = 8` &rarr; `[[1,1,6],[1,2,5],[1,7],[2,6]]`
- `candidates = [2,5,2,1,2], target = 5` &rarr; `[[1,2,2],[5]]`

## Constraints

- 1 <= candidates.length <= 100
- 1 <= candidates[i] <= 50
- 1 <= target <= 30

## Intuition

Sort. Loop over remaining candidates. To avoid duplicates at the
same depth, track the previous value picked (`prev`) and skip if the
current is equal.

**Time:** O(2^n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
