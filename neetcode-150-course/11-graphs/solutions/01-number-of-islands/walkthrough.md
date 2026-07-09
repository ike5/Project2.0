# Number of Islands - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

Given an `m x n` 2D binary grid `grid` which represents a map of '1's (land) and '0's (water), return the number of islands. An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.

## Examples

- `grid = [['1','1','1','1','0'],['1','1','0','1','0'],['1','1','0','0','0'],['0','0','0','0','0']]` &rarr; `1`
- `grid = [['1','1','0','0','0'],['1','1','0','0','0'],['0','0','1','0','0'],['0','0','0','1','1']]` &rarr; `3`

## Constraints

- m == grid.length, n == grid[i].length
- 1 <= m, n <= 300
- grid[i][j] is '0' or '1'

## Intuition

Iterate the grid. On each unvisited `'1'`, increment the count
and DFS-mark the connected component (replace `'1'` with `'#'`).

**Time:** O(m·n). **Space:** O(m·n) for the recursion in the worst case
(degenerate single-line island).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
