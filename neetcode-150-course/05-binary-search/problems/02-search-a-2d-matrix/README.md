# Search a 2D Matrix

**Difficulty:** Medium

## Problem

You are given an `m x n` integer matrix `matrix` with the following two properties: (1) each row is sorted in non-decreasing order; (2) the first integer of each row is greater than the last integer of the previous row. Given an integer `target`, return `True` if `target` is in `matrix`, or `False` otherwise. You must write a solution in O(log(m*n)) time.

## Examples

```
Input:  matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 3
Output: True
```

```
Input:  matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 13
Output: False
```

## Constraints

- m == matrix.length, n == matrix[i].length
- 1 <= m, n <= 100
- -10^4 <= matrix[i][j], target <= 10^4

## Hints

1. Treat the matrix as a flat sorted array of size m*n.
2. Index `(i, j)` becomes `i * n + j` in the flat array.

## Solution

See [`../../solutions/02-search-a-2d-matrix/`](../../solutions/02-search-a-2d-matrix/) for the Python and Java 21 solutions and a step-by-step walkthrough.
