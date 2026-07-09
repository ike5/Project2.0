# Max Area of Island - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

You are given an `m x n` binary matrix `grid`. An island is a group of `1`s connected 4-directionally. The **area** of an island is the number of cells with a value of 1 in it. Return the maximum area of an island in `grid`. If there is no island, return 0.

## Examples

- `grid = [[0,0,1,0,0,0,0,1,0,0,0,0,0],[0,0,0,0,0,0,0,1,1,1,0,0,0],[0,1,1,0,1,0,0,0,0,0,0,0,0],[0,1,0,0,1,1,0,0,1,0,1,0,0],[0,1,0,0,1,1,0,0,1,1,1,0,0],[0,0,0,0,0,0,0,0,0,0,1,0,0],[0,0,0,0,0,0,0,1,2,4,4,0,0]]` &rarr; `6`

## Constraints

- m == grid.length, n == grid[i].length
- 1 <= m, n <= 50
- grid[i][j] is 0 or 1

## Intuition

Same as Number of Islands, but the DFS returns the area. Track
the maximum.

**Time:** O(m·n). **Space:** O(m·n) recursion.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
