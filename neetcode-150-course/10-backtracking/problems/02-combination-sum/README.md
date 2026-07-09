# Combination Sum

**Difficulty:** Medium

## Problem

Given an array of **distinct** integers `candidates` and a target integer `target`, return a list of all unique combinations of `candidates` where the chosen numbers sum to `target`. The same number may be chosen from `candidates` an unlimited number of times. Two combinations are unique if the frequency of at least one of the chosen numbers is different.

## Examples

```
Input:  candidates = [2,3,6,7], target = 7
Output: [[2,2,3],[7]]
```

```
Input:  candidates = [2,3,5], target = 8
Output: [[2,2,2,2],[2,3,3],[3,5]]
```

## Constraints

- 1 <= candidates.length <= 30
- 2 <= candidates[i] <= 40
- All elements of candidates are distinct
- 1 <= target <= 40

## Hints

1. Backtrack. At each step, try every candidate (with reuse).

## Solution

See [`../../solutions/02-combination-sum/`](../../solutions/02-combination-sum/) for the Python and Java 21 solutions and a step-by-step walkthrough.
