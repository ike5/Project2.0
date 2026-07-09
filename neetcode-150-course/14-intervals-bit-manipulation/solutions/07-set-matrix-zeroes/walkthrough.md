# Set Matrix Zeroes - walkthrough

**Difficulty:** Medium &middot; **Module:** 14 Intervals Bit Manipulation

## Brief

Given an `m x n` integer matrix `matrix`, if an element is 0, set its entire row and column to 0's. You must do it in place.

## Examples

- `matrix = [[1,1,1],[1,0,1],[1,1,1]]` &rarr; `[[1,0,1],[0,0,0],[1,0,1]]`
- `matrix = [[0,1,2,0],[3,4,5,2],[1,3,1,5]]` &rarr; `[[0,0,0,0],[0,4,5,0],[0,3,1,0]]`

## Constraints

- m == matrix.length, n == matrix[i].length
- 1 <= m, n <= 200
- -2^31 <= matrix[i][j] <= 2^31 - 1

## Intuition

Use the first row and column as flags:
- Record whether the first row / column itself has a zero.
- Use `matrix[i][0]` and `matrix[0][j]` to flag zeroed rows/columns.
- Sweep through, then zero the first row/column at the end.

**Time:** O(m · n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
