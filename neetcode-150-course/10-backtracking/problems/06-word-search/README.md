# Word Search

**Difficulty:** Medium

## Problem

Given an `m x n` grid of characters `board` and a string `word`, return `True` if `word` exists in the grid. The word can be constructed from letters of sequentially adjacent cells (horizontally or vertically). The same cell may not be used more than once.

## Examples

```
Input:  board = [['A','B','C','E'],['S','F','C','S'],['A','D','E','E']], word = 'ABCCED'
Output: True
```

```
Input:  board = same, word = 'ABCB'
Output: False
```

## Constraints

- m == board.length, n == board[i].length
- 1 <= m, n <= 6
- 1 <= word.length <= 15
- board and word consist of only lowercase and uppercase English letters

## Hints

1. DFS from each cell. Mark visited, recurse in 4 directions, unmark on the way back.

## Solution

See [`../../solutions/06-word-search/`](../../solutions/06-word-search/) for the Python and Java 21 solutions and a step-by-step walkthrough.
