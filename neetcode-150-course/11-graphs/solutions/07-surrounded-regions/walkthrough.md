# Surrounded Regions - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

Given an `m x n` matrix `board` containing 'X' and 'O', capture all regions that are 4-directionally surrounded by 'X'. A region is captured by flipping all 'O's into 'X's in that surrounded region.

## Examples

- `board = [['X','X','X','X'],['X','O','O','X'],['X','X','O','X'],['X','O','X','X']]` &rarr; `[['X','X','X','X'],['X','X','X','X'],['X','X','X','X'],['X','O','X','X']]`

## Constraints

- m == board.length, n == board[i].length
- 1 <= m, n <= 200
- board[i][j] is 'X' or 'O'

## Intuition

Mark all 'O's connected to the boundary with `'#'`. Then sweep
the board: `'O'` (surrounded) becomes `'X'`; `'#'` (boundary) becomes
`'O'`.

**Time:** O(m·n). **Space:** O(m·n) recursion.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
