# Walls and Gates - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

You are given an `m x n` grid `rooms` initialized with these three possible values: -1 (a wall or obstacle), 0 (a gate), and INF (an empty room). Fill each empty room with the distance to its nearest gate. If it is impossible to reach a gate, leave it as INF.

## Examples

- `rooms = [[2147483647,-1,0,2147483647],[2147483647,2147483647,2147483647,-1],[2147483647,-1,2147483647,-1],[0,-1,2147483647,2147483647]]` &rarr; `rooms with each empty cell = distance to nearest 0`

## Constraints

- m == rooms.length, n == rooms[i].length
- 1 <= m, n <= 250
- rooms[i][j] is -1, 0, or 2^31 - 1

## Intuition

Multi-source BFS. Start a queue with all gates; BFS out from
each, writing the distance to each empty cell. The first time we
visit a cell, the distance is the shortest.

**Time:** O(m·n). **Space:** O(m·n) for the queue.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
