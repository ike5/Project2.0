# Max Area of Island

**Difficulty:** Medium

## Problem

You are given an `m x n` binary matrix `grid`. An island is a group of `1`s connected 4-directionally. The **area** of an island is the number of cells with a value of 1 in it. Return the maximum area of an island in `grid`. If there is no island, return 0.

## Examples

```
Input:  grid = [[0,0,1,0,0,0,0,1,0,0,0,0,0],[0,0,0,0,0,0,0,1,1,1,0,0,0],[0,1,1,0,1,0,0,0,0,0,0,0,0],[0,1,0,0,1,1,0,0,1,0,1,0,0],[0,1,0,0,1,1,0,0,1,1,1,0,0],[0,0,0,0,0,0,0,0,0,0,1,0,0],[0,0,0,0,0,0,0,1,2,4,4,0,0]]
Output: 6
```

## Constraints

- m == grid.length, n == grid[i].length
- 1 <= m, n <= 50
- grid[i][j] is 0 or 1

## Hints

1. Same DFS as Number of Islands, but return the size of each island.

## Solution

See [`../../solutions/02-max-area-of-island/`](../../solutions/02-max-area-of-island/) for the Python and Java 21 solutions and a step-by-step walkthrough.
