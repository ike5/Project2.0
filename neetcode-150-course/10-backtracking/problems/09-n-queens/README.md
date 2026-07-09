# N-Queens

**Difficulty:** Hard

## Problem

The n-queens puzzle is the problem of placing `n` queens on an `n x n` chessboard such that no two queens attack each other. Given an integer `n`, return all distinct solutions to the n-queens puzzle. Each solution contains a distinct board configuration of the n-queens' placement, where 'Q' and '.' both indicate a queen and an empty space respectively.

## Examples

```
Input:  n = 4
Output: [['.Q..','...Q','Q...','..Q.'],['..Q.','Q...','...Q','.Q..']]
```

```
Input:  n = 1
Output: [['Q']]
```

## Constraints

- 1 <= n <= 9

## Hints

1. Backtrack row by row. Track attacked columns and diagonals with sets.

## Solution

See [`../../solutions/09-n-queens/`](../../solutions/09-n-queens/) for the Python and Java 21 solutions and a step-by-step walkthrough.
