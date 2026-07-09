# Word Search II - walkthrough

**Difficulty:** Hard &middot; **Module:** 08 Tries

## Brief

Given an `m x n` board of characters and a list of strings `words`, return all words on the board. Each word must be constructed from letters of sequentially adjacent cells (horizontally or vertically). The same cell may not be used more than once in a word.

## Examples

- `board = [['o','a','a','n'],['e','t','a','e'],['i','h','k','r'],['i','f','l','v']], words = ['oath','pea','eat','rain']` &rarr; `['eat','oath']`

## Constraints

- m == board.length, n == board[i].length
- 1 <= m, n <= 12
- 1 <= words[i].length <= 10
- 1 <= sum(words[i].length) <= 10^4

## Intuition

Build a trie of the words. DFS the board starting from every cell;
when we land on a trie node that has a `word` field, record it (and clear
the field to de-dupe). Mark the cell as visited by writing `'#'`, then
unmark on the way back.

**Time:** O(m · n · 4^L) where L is the max word length, but trie
pruning makes it fast in practice.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
