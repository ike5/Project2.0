# Meeting Rooms II

**Difficulty:** Medium

## Problem

Given an array of meeting time intervals `intervals` where `intervals[i] = [start_i, end_i]`, return the minimum number of conference rooms required to hold all the meetings.

## Examples

```
Input:  intervals = [[0,30],[5,10],[15,20]]
Output: 2
```

```
Input:  intervals = [[7,10],[2,4]]
Output: 1
```

## Constraints

- 1 <= intervals.length <= 10^4
- 0 <= start_i < end_i <= 10^6

## Hints

1. Sort starts and ends separately. Sweep: if start < earliest end, need a new room; else, reuse the room (advance earliest end).

## Solution

See [`../../solutions/04-meeting-rooms-ii/`](../../solutions/04-meeting-rooms-ii/) for the Python and Java 21 solutions and a step-by-step walkthrough.
