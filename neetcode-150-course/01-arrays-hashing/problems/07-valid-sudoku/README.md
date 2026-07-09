# Valid Sudoku

**Difficulty:** Medium

## Problem

Determine if a 9x9 Sudoku board is valid. Only the filled cells need to be validated: each row, each column, and each of the nine 3x3 sub-boxes must contain the digits 1-9 without repetition.

## Examples

```
Input:  A standard 9x9 valid board
Output: True
```

```
Input:  A standard 9x9 board with one duplicate in a sub-box
Output: False
```

## Constraints

- board.length == 9, board[i].length == 9
- board[i][j] is a digit '1'-'9' or '.'

## Hints

1. Validate rows, columns, and 3x3 boxes separately.
2. You can do all three in one pass with three sets per row/col/box — or one pass with a single set per (row, col, box) triple.

## Solution

See [`../../solutions/07-valid-sudoku/`](../../solutions/07-valid-sudoku/) for the Python and Java 21 solutions and a step-by-step walkthrough.
