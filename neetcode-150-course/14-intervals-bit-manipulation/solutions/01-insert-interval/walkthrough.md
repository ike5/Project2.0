# Insert Interval - walkthrough

**Difficulty:** Medium &middot; **Module:** 14 Intervals Bit Manipulation

## Brief

You are given an array of non-overlapping intervals `intervals` where `intervals[i] = [start_i, end_i]` represent the start and the end of the ith interval and `intervals` is sorted in ascending order by `start_i`. You are also given an interval `newInterval = [start, end]` that represents the start and end of another interval. Insert `newInterval` into `intervals` such that `intervals` is still sorted in ascending order by `start_i` and `intervals` still does not have any overlapping intervals (merge overlapping intervals if necessary). Return `intervals` after the insertion.

## Examples

- `intervals = [[1,3],[6,9]], newInterval = [2,5]` &rarr; `[[1,5],[6,9]]`
- `intervals = [[1,2],[3,5],[6,7],[8,10],[12,16]], newInterval = [4,8]` &rarr; `[[1,2],[3,10],[12,16]]`

## Constraints

- 0 <= intervals.length <= 10^4
- intervals[i].length == 2
- 0 <= start_i <= end_i <= 10^5
- intervals is sorted and non-overlapping
- 0 <= start <= end <= 10^5

## Intuition

Three sections:
1. `b < new[0]` — entirely before newInterval, keep as-is.
2. `a > new[1]` — entirely after, append newInterval then the rest.
3. Else — overlap; merge.

**Time:** O(n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
