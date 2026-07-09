# Maximal Square

**Difficulty:** Hard

## Problem

Given an `m x n` binary matrix `filled` with '0's and '1's, find the largest square containing only '1's and return its area.

## Examples

```
Input:  matrix = [['1','0','1','0','0'],['1','0','1','1','1'],['1','1','1','1','1'],['1','0','0','1','0']]
Output: 4
```

```
Input:  matrix = [['0','1'],['1','0']]
Output: 1
```

## Constraints

- m == matrix.length, n == matrix[i].length
- 1 <= m, n <= 300
- matrix[i][j] is '0' or '1'

## Hints

1. `dp[i][j]` = side of largest square with bottom-right at `(i, j)`. `dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])` if `matrix[i][j] == 1`.

## Solution

See [`../../solutions/22-maximal-square/`](../../solutions/22-maximal-square/) for the Python and Java 21 solutions and a step-by-step walkthrough.
