# Non-Overlapping Intervals - walkthrough

**Difficulty:** Medium &middot; **Module:** 14 Intervals Bit Manipulation

## Brief

Given an array of intervals `intervals` where `intervals[i] = [start_i, end_i]`, return the minimum number of intervals you need to remove to make the rest non-overlapping.

## Examples

- `intervals = [[1,2],[2,3],[3,4],[1,3]]` &rarr; `1`
- `intervals = [[1,2],[1,2],[1,2]]` &rarr; `2`
- `intervals = [[1,2],[2,3]]` &rarr; `0`

## Constraints

- 1 <= intervals.length <= 10^5
- intervals[i].length == 2
- -5 * 10^4 <= start_i < end_i <= 5 * 10^4

## Intuition

Sort by end. Greedily keep intervals whose start is at or after
the last kept end. Count what we keep; answer = `n - kept`.

**Time:** O(n log n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
