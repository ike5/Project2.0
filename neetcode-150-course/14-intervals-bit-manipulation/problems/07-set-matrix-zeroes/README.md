# Set Matrix Zeroes

**Difficulty:** Medium

## Problem

Given an `m x n` integer matrix `matrix`, if an element is 0, set its entire row and column to 0's. You must do it in place.

## Examples

```
Input:  matrix = [[1,1,1],[1,0,1],[1,1,1]]
Output: [[1,0,1],[0,0,0],[1,0,1]]
```

```
Input:  matrix = [[0,1,2,0],[3,4,5,2],[1,3,1,5]]
Output: [[0,0,0,0],[0,4,5,0],[0,3,1,0]]
```

## Constraints

- m == matrix.length, n == matrix[i].length
- 1 <= m, n <= 200
- -2^31 <= matrix[i][j] <= 2^31 - 1

## Hints

1. Use the first row and column as flags. Or: extra O(m+n) space.

## Solution

See [`../../solutions/07-set-matrix-zeroes/`](../../solutions/07-set-matrix-zeroes/) for the Python and Java 21 solutions and a step-by-step walkthrough.
