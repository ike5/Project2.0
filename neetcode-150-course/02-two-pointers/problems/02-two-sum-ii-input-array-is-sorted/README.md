# Two Sum II — Input Array Is Sorted

**Difficulty:** Easy

## Problem

Given a **1-indexed** array of integers `numbers` that is already sorted in non-decreasing order, find two numbers such that they add up to a specific `target`. Return the indices of the two numbers as a 1-indexed array `[i, j]`. You may not use the same element twice.

## Examples

```
Input:  numbers = [2,7,11,15], target = 9
Output: [1, 2]
```

```
Input:  numbers = [2,3,4],     target = 6
Output: [1, 3]
```

```
Input:  numbers = [-1,0],      target = -1
Output: [1, 2]
```

## Constraints

- 2 <= len(numbers) <= 3 * 10^4
- -1000 <= numbers[i] <= 1000
- numbers is sorted in non-decreasing order
- Exactly one valid answer

## Hints

1. Sorted input → two pointers from opposite ends.
2. If sum too small, advance `l`; if too large, retreat `r`.

## Solution

See [`../../solutions/02-two-sum-ii-input-array-is-sorted/`](../../solutions/02-two-sum-ii-input-array-is-sorted/) for the Python and Java 21 solutions and a step-by-step walkthrough.
