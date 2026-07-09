# Spiral Matrix - walkthrough

**Difficulty:** Medium &middot; **Module:** 14 Intervals Bit Manipulation

## Brief

Given an `m x n` matrix, return all elements of the matrix in spiral order.

## Examples

- `matrix = [[1,2,3],[4,5,6],[7,8,9]]` &rarr; `[1,2,3,6,9,8,7,4,5]`
- `matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]]` &rarr; `[1,2,3,4,8,12,11,10,9,5,6,7]`

## Constraints

- m == matrix.length, n == matrix[i].length
- 1 <= m, n <= 10
- -100 <= matrix[i][j] <= 100

## Intuition

Four boundaries: `top`, `bottom`, `left`, `right`. Walk the
top row, right column, bottom row, left column, then shrink the
boundaries.

**Time:** O(m · n). **Space:** O(1) (output not counted).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
