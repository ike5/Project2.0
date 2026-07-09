# Word Ladder - walkthrough

**Difficulty:** Hard &middot; **Module:** 11 Graphs

## Brief

A **transformation sequence** from word `beginWord` to word `endWord` using a dictionary `wordList` is a sequence of words `beginWord -> s1 -> s2 -> ... -> sk` such that: every adjacent pair differs by a single letter, and every `si` (for 1 <= i <= k) is in `wordList`. Given two words, `beginWord` and `endWord`, and a dictionary `wordList`, return the **number of words** in the **shortest transformation sequence** from `beginWord` to `endWord`, or 0 if no such sequence exists.

## Examples

- `beginWord = 'hit', endWord = 'cog', wordList = ['hot','dot','dog','lot','log','cog']` &rarr; `5`
- `beginWord = 'hit', endWord = 'cog', wordList = ['hot','dot','dog','lot','log']` &rarr; `0`

## Constraints

- 1 <= len(beginWord) == len(endWord) <= 10
- 1 <= len(wordList) <= 5000
- All words consist of lowercase English letters

## Intuition

BFS from `beginWord`. At each word, try all single-letter
substitutions. The first time we reach `endWord`, the BFS depth is the
answer.

**Time:** O(L · 26 · N) where L is the word length and N is the number
of words. **Space:** O(N) for the queue + visited.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
