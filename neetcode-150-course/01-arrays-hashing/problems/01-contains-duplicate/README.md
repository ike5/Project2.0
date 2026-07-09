# Contains Duplicate

**Difficulty:** Easy

## Problem

Given an integer array `nums`, return `True` if any value appears at least twice. Return `False` if every element is distinct.

## Examples

```
Input:  nums = [1, 2, 3, 1]
Output: True
```

```
Input:  nums = [1, 2, 3, 4]
Output: False
```

```
Input:  nums = [1, 1, 1, 3, 3, 4, 3, 2, 4, 2]
Output: True
```

## Constraints

- 1 <= len(nums) <= 10^5
- -10^9 <= nums[i] <= 10^9

## Hints

1. What structure gives O(1) membership checks?
2. You don't need to count occurrences — one duplicate is enough.

## Solution

See [`../../solutions/01-contains-duplicate/`](../../solutions/01-contains-duplicate/) for the Python and Java 21 solutions and a step-by-step walkthrough.
