# Edit Distance - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given two strings `word1` and `word2`, return the minimum number of operations required to convert `word1` to `word2`. You have the following three operations permitted on a word: insert, delete, or replace a character.

## Examples

- `word1 = 'horse', word2 = 'ros'` &rarr; `3`
- `word1 = 'intention', word2 = 'execution'` &rarr; `5`

## Constraints

- 0 <= word1.length, word2.length <= 500
- word1 and word2 consist of lowercase English letters

## Intuition

Classic edit distance. Three operations: insert, delete,
replace. The recurrence picks the minimum.

**Time:** O(m · n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
