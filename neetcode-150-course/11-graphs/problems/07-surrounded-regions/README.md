# Surrounded Regions

**Difficulty:** Medium

## Problem

Given an `m x n` matrix `board` containing 'X' and 'O', capture all regions that are 4-directionally surrounded by 'X'. A region is captured by flipping all 'O's into 'X's in that surrounded region.

## Examples

```
Input:  board = [['X','X','X','X'],['X','O','O','X'],['X','X','O','X'],['X','O','X','X']]
Output: [['X','X','X','X'],['X','X','X','X'],['X','X','X','X'],['X','O','X','X']]
```

## Constraints

- m == board.length, n == board[i].length
- 1 <= m, n <= 200
- board[i][j] is 'X' or 'O'

## Hints

1. Mark boundary 'O's and their connected 'O's as unsurroundable. Flip the rest.

## Solution

See [`../../solutions/07-surrounded-regions/`](../../solutions/07-surrounded-regions/) for the Python and Java 21 solutions and a step-by-step walkthrough.
