# Word Search - walkthrough

**Difficulty:** Medium &middot; **Module:** 10 Backtracking

## Brief

Given an `m x n` grid of characters `board` and a string `word`, return `True` if `word` exists in the grid. The word can be constructed from letters of sequentially adjacent cells (horizontally or vertically). The same cell may not be used more than once.

## Examples

- `board = [['A','B','C','E'],['S','F','C','S'],['A','D','E','E']], word = 'ABCCED'` &rarr; `True`
- `board = same, word = 'ABCB'` &rarr; `False`

## Constraints

- m == board.length, n == board[i].length
- 1 <= m, n <= 6
- 1 <= word.length <= 15
- board and word consist of only lowercase and uppercase English letters

## Intuition

DFS from each cell. Mark with `'#'` to avoid re-using; unmark on
the way back.

**Time:** O(m · n · 4^L) where L is the word length. **Space:** O(L).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
