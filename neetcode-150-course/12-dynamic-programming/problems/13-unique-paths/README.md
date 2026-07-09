# Unique Paths

**Difficulty:** Medium

## Problem

There is a robot on an `m x n` grid. The robot is initially located at the top-left corner (i.e., `grid[0][0]`). The robot tries to move to the bottom-right corner (i.e., `grid[m - 1][n - 1]`). The robot can only move either down or right at any point in time. Given the two integers `m` and `n`, return the number of possible unique paths that the robot can take to reach the bottom-right corner.

## Examples

```
Input:  m = 3, n = 7
Output: 28
```

```
Input:  m = 3, n = 2
Output: 3
```

## Constraints

- 1 <= m, n <= 100

## Hints

1. `dp[i][j] = dp[i-1][j] + dp[i][j-1]` (combinatorics: C(m+n-2, m-1)).

## Solution

See [`../../solutions/13-unique-paths/`](../../solutions/13-unique-paths/) for the Python and Java 21 solutions and a step-by-step walkthrough.
