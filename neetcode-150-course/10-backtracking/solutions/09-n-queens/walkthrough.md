# N-Queens - walkthrough

**Difficulty:** Hard &middot; **Module:** 10 Backtracking

## Brief

The n-queens puzzle is the problem of placing `n` queens on an `n x n` chessboard such that no two queens attack each other. Given an integer `n`, return all distinct solutions to the n-queens puzzle. Each solution contains a distinct board configuration of the n-queens' placement, where 'Q' and '.' both indicate a queen and an empty space respectively.

## Examples

- `n = 4` &rarr; `[['.Q..','...Q','Q...','..Q.'],['..Q.','Q...','...Q','.Q..']]`
- `n = 1` &rarr; `[['Q']]`

## Constraints

- 1 <= n <= 9

## Intuition

Place queens row by row. For each column, check it's not under
attack (no queen in the same column or either diagonal). Three sets —
columns, `r - c`, `r + c` — give O(1) attack checks.

**Time:** O(n!) worst case, much less in practice. **Space:** O(n) for
the sets + board.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
