# Maximal Square - walkthrough

**Difficulty:** Hard &middot; **Module:** 12 Dynamic Programming

## Brief

Given an `m x n` binary matrix `filled` with '0's and '1's, find the largest square containing only '1's and return its area.

## Examples

- `matrix = [['1','0','1','0','0'],['1','0','1','1','1'],['1','1','1','1','1'],['1','0','0','1','0']]` &rarr; `4`
- `matrix = [['0','1'],['1','0']]` &rarr; `1`

## Constraints

- m == matrix.length, n == matrix[i].length
- 1 <= m, n <= 300
- matrix[i][j] is '0' or '1'

## Intuition

`dp[i][j]` = side of largest square ending at `(i, j)`. The
recurrence is the minimum of the three neighbors + 1. Return `best²`.

**Time:** O(m · n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
