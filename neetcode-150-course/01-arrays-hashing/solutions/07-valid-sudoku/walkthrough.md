# Valid Sudoku - walkthrough

**Difficulty:** Medium &middot; **Module:** 01 Arrays Hashing

## Brief

Determine if a 9x9 Sudoku board is valid. Only the filled cells need to be validated: each row, each column, and each of the nine 3x3 sub-boxes must contain the digits 1-9 without repetition.

## Examples

- `A standard 9x9 valid board` &rarr; `True`
- `A standard 9x9 board with one duplicate in a sub-box` &rarr; `False`

## Constraints

- board.length == 9, board[i].length == 9
- board[i][j] is a digit '1'-'9' or '.'

## Intuition

The board is 9x9. The 3x3 sub-box index for cell `(r, c)` is
`(r // 3) * 3 + (c // 3)`. We track what we've seen in each row, each
column, and each sub-box.

## Approach
Three sets per dimension. For each filled cell, check that its digit is
absent from all three. (Or use the trick that `Set.add` returns `false` on
duplicate, as in the Java version above.)

## Complexity
- **Time:** O(81) = O(1) — board is fixed-size.
- **Space:** O(81) = O(1) — three sets of up to 9 elements each.

## Follow-ups
- *What if the board is N x N and boxes are √N x √N?* Same approach, with
  `int sqrtN = (int) Math.sqrt(N)`.
- *Solve the sudoku (place the empty cells)?* Backtracking — Module 10.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
