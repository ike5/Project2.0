# Number of Islands

**Difficulty:** Medium

## Problem

Given an `m x n` 2D binary grid `grid` which represents a map of '1's (land) and '0's (water), return the number of islands. An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.

## Examples

```
Input:  grid = [['1','1','1','1','0'],['1','1','0','1','0'],['1','1','0','0','0'],['0','0','0','0','0']]
Output: 1
```

```
Input:  grid = [['1','1','0','0','0'],['1','1','0','0','0'],['0','0','1','0','0'],['0','0','0','1','1']]
Output: 3
```

## Constraints

- m == grid.length, n == grid[i].length
- 1 <= m, n <= 300
- grid[i][j] is '0' or '1'

## Hints

1. Iterate the grid; on each unvisited '1', DFS to mark the whole island and increment count.

## Solution

See [`../../solutions/01-number-of-islands/`](../../solutions/01-number-of-islands/) for the Python and Java 21 solutions and a step-by-step walkthrough.
