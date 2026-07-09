# Longest Consecutive Sequence

**Difficulty:** Medium

## Problem

Given an unsorted array of integers `nums`, return the length of the longest sequence of consecutive elements. The algorithm must run in O(n) time.

## Examples

```
Input:  nums = [100,4,200,1,3,2]
Output: 4
```

```
Input:  nums = [0,3,7,2,5,8,4,6,0,1]
Output: 9
```

```
Input:  nums = []
Output: 0
```

## Constraints

- 0 <= nums.length <= 10^5
- -10^9 <= nums[i] <= 10^9

## Hints

1. Sort then walk — O(n log n). We can do better with a set.
2. For each x, only start counting if x-1 is NOT in the set (i.e. x is the start of a run). Then walk x+1, x+2, ...

## Solution

See [`../../solutions/09-longest-consecutive-sequence/`](../../solutions/09-longest-consecutive-sequence/) for the Python and Java 21 solutions and a step-by-step walkthrough.
