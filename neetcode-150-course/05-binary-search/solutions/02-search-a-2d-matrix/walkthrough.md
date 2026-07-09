# Search a 2D Matrix - walkthrough

**Difficulty:** Medium &middot; **Module:** 05 Binary Search

## Brief

You are given an `m x n` integer matrix `matrix` with the following two properties: (1) each row is sorted in non-decreasing order; (2) the first integer of each row is greater than the last integer of the previous row. Given an integer `target`, return `True` if `target` is in `matrix`, or `False` otherwise. You must write a solution in O(log(m*n)) time.

## Examples

- `matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 3` &rarr; `True`
- `matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 13` &rarr; `False`

## Constraints

- m == matrix.length, n == matrix[i].length
- 1 <= m, n <= 100
- -10^4 <= matrix[i][j], target <= 10^4

## Intuition

Map a flat index `k` to a 2D index via `(k // n, k % n)`. Then
standard binary search on the flat array.

**Time:** O(log(m*n)). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
