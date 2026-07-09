# Rotting Oranges

**Difficulty:** Medium

## Problem

You are given an `m x n` grid where each cell can have one of three values: 0 (empty), 1 (fresh orange), or 2 (rotten orange). Every minute, any fresh orange 4-directionally adjacent to a rotten orange becomes rotten. Return the minimum number of minutes that must elapse until no cell with a fresh orange exists. If impossible, return -1.

## Examples

```
Input:  grid = [[2,1,1],[1,1,0],[0,1,1]]
Output: 4
```

```
Input:  grid = [[2,1,1],[0,1,1],[1,0,1]]
Output: -1
```

## Constraints

- m == grid.length, n == grid[i].length
- 1 <= m, n <= 10
- grid[i][j] is 0, 1, or 2

## Hints

1. Multi-source BFS from all rotten oranges. Count the BFS levels until no fresh remain.

## Solution

See [`../../solutions/05-rotting-oranges/`](../../solutions/05-rotting-oranges/) for the Python and Java 21 solutions and a step-by-step walkthrough.
