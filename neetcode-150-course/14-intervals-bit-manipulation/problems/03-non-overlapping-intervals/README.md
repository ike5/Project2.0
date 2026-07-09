# Non-Overlapping Intervals

**Difficulty:** Medium

## Problem

Given an array of intervals `intervals` where `intervals[i] = [start_i, end_i]`, return the minimum number of intervals you need to remove to make the rest non-overlapping.

## Examples

```
Input:  intervals = [[1,2],[2,3],[3,4],[1,3]]
Output: 1
```

```
Input:  intervals = [[1,2],[1,2],[1,2]]
Output: 2
```

```
Input:  intervals = [[1,2],[2,3]]
Output: 0
```

## Constraints

- 1 <= intervals.length <= 10^5
- intervals[i].length == 2
- -5 * 10^4 <= start_i < end_i <= 5 * 10^4

## Hints

1. Sort by end. Greedily keep intervals that end earliest.

## Solution

See [`../../solutions/03-non-overlapping-intervals/`](../../solutions/03-non-overlapping-intervals/) for the Python and Java 21 solutions and a step-by-step walkthrough.
