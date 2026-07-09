# Walls and Gates

**Difficulty:** Medium

## Problem

You are given an `m x n` grid `rooms` initialized with these three possible values: -1 (a wall or obstacle), 0 (a gate), and INF (an empty room). Fill each empty room with the distance to its nearest gate. If it is impossible to reach a gate, leave it as INF.

## Examples

```
Input:  rooms = [[2147483647,-1,0,2147483647],[2147483647,2147483647,2147483647,-1],[2147483647,-1,2147483647,-1],[0,-1,2147483647,2147483647]]
Output: rooms with each empty cell = distance to nearest 0
```

## Constraints

- m == rooms.length, n == rooms[i].length
- 1 <= m, n <= 250
- rooms[i][j] is -1, 0, or 2^31 - 1

## Hints

1. Multi-source BFS from all gates simultaneously.

## Solution

See [`../../solutions/04-walls-and-gates/`](../../solutions/04-walls-and-gates/) for the Python and Java 21 solutions and a step-by-step walkthrough.
