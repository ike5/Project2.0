# Rotting Oranges - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

You are given an `m x n` grid where each cell can have one of three values: 0 (empty), 1 (fresh orange), or 2 (rotten orange). Every minute, any fresh orange 4-directionally adjacent to a rotten orange becomes rotten. Return the minimum number of minutes that must elapse until no cell with a fresh orange exists. If impossible, return -1.

## Examples

- `grid = [[2,1,1],[1,1,0],[0,1,1]]` &rarr; `4`
- `grid = [[2,1,1],[0,1,1],[1,0,1]]` &rarr; `-1`

## Constraints

- m == grid.length, n == grid[i].length
- 1 <= m, n <= 10
- grid[i][j] is 0, 1, or 2

## Intuition

Multi-source BFS. Each "level" of the BFS represents one minute.
At each level, all the fresh oranges adjacent to current rotten ones
become rotten. If we exit the loop and `fresh > 0`, it's impossible.

**Time:** O(m·n). **Space:** O(m·n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
