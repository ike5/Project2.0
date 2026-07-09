# Merge Intervals - walkthrough

**Difficulty:** Medium &middot; **Module:** 14 Intervals Bit Manipulation

## Brief

Given an array of `intervals` where `intervals[i] = [start_i, end_i]`, merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the input.

## Examples

- `intervals = [[1,3],[2,6],[8,10],[15,18]]` &rarr; `[[1,6],[8,10],[15,18]]`
- `intervals = [[1,4],[4,5]]` &rarr; `[[1,5]]`

## Constraints

- 1 <= intervals.length <= 10^4
- intervals[i].length == 2
- 0 <= start_i <= end_i <= 10^4

## Intuition

Sort by start. Sweep; if the current interval starts at or
before the last merged end, extend the end. Otherwise, start a new
merged interval.

**Time:** O(n log n) for the sort. **Space:** O(n) for the output.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
