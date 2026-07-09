# House Robber II

**Difficulty:** Medium

## Problem

Same problem as House Robber, but the houses are arranged in a **circle**. That means the first and last houses are adjacent.

## Examples

```
Input:  nums = [2,3,2]
Output: 3
```

```
Input:  nums = [1,2,3,1]
Output: 4
```

```
Input:  nums = [0]
Output: 0
```

## Constraints

- 1 <= nums.length <= 100
- 0 <= nums[i] <= 1000

## Hints

1. Two cases: skip the first, or skip the last. Run House Robber on each.

## Solution

See [`../../solutions/04-house-robber-ii/`](../../solutions/04-house-robber-ii/) for the Python and Java 21 solutions and a step-by-step walkthrough.
