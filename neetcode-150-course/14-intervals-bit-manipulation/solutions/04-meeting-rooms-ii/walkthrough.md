# Meeting Rooms II - walkthrough

**Difficulty:** Medium &middot; **Module:** 14 Intervals Bit Manipulation

## Brief

Given an array of meeting time intervals `intervals` where `intervals[i] = [start_i, end_i]`, return the minimum number of conference rooms required to hold all the meetings.

## Examples

- `intervals = [[0,30],[5,10],[15,20]]` &rarr; `2`
- `intervals = [[7,10],[2,4]]` &rarr; `1`

## Constraints

- 1 <= intervals.length <= 10^4
- 0 <= start_i < end_i <= 10^6

## Intuition

Sort starts and ends. For each start, if it's at or after the
earliest end, we can reuse that room. Otherwise, we need a new one.

**Time:** O(n log n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
