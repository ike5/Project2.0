# Rotate Image - walkthrough

**Difficulty:** Medium &middot; **Module:** 14 Intervals Bit Manipulation

## Brief

You are given an `n x n` 2D matrix representing an image, rotate the image by 90 degrees (clockwise). You have to rotate the image in-place, which means you have to modify the input 2D matrix directly. DO NOT allocate another 2D matrix and do the rotation.

## Examples

- `matrix = [[1,2,3],[4,5,6],[7,8,9]]` &rarr; `[[7,4,1],[8,5,2],[9,6,3]]`
- `matrix = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]` &rarr; `[[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]`

## Constraints

- n == matrix.length == matrix[i].length
- 1 <= n <= 20
- -1000 <= matrix[i][j] <= 1000

## Intuition

Two in-place operations:
1. **Transpose** the matrix: `matrix[i][j] <-> matrix[j][i]`.
2. **Reverse each row**.

The combination is a 90° clockwise rotation.

**Time:** O(n²). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
