# Word Search II

**Difficulty:** Hard

## Problem

Given an `m x n` board of characters and a list of strings `words`, return all words on the board. Each word must be constructed from letters of sequentially adjacent cells (horizontally or vertically). The same cell may not be used more than once in a word.

## Examples

```
Input:  board = [['o','a','a','n'],['e','t','a','e'],['i','h','k','r'],['i','f','l','v']], words = ['oath','pea','eat','rain']
Output: ['eat','oath']
```

## Constraints

- m == board.length, n == board[i].length
- 1 <= m, n <= 12
- 1 <= words[i].length <= 10
- 1 <= sum(words[i].length) <= 10^4

## Hints

1. Build a trie of the words. DFS on the board; prune when the current path can't lead to any word.

## Solution

See [`../../solutions/03-word-search-ii/`](../../solutions/03-word-search-ii/) for the Python and Java 21 solutions and a step-by-step walkthrough.
