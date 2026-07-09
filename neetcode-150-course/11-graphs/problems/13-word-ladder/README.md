# Word Ladder

**Difficulty:** Hard

## Problem

A **transformation sequence** from word `beginWord` to word `endWord` using a dictionary `wordList` is a sequence of words `beginWord -> s1 -> s2 -> ... -> sk` such that: every adjacent pair differs by a single letter, and every `si` (for 1 <= i <= k) is in `wordList`. Given two words, `beginWord` and `endWord`, and a dictionary `wordList`, return the **number of words** in the **shortest transformation sequence** from `beginWord` to `endWord`, or 0 if no such sequence exists.

## Examples

```
Input:  beginWord = 'hit', endWord = 'cog', wordList = ['hot','dot','dog','lot','log','cog']
Output: 5
```

```
Input:  beginWord = 'hit', endWord = 'cog', wordList = ['hot','dot','dog','lot','log']
Output: 0
```

## Constraints

- 1 <= len(beginWord) == len(endWord) <= 10
- 1 <= len(wordList) <= 5000
- All words consist of lowercase English letters

## Hints

1. BFS from `beginWord`. Two optimization tricks: (1) convert all words to lowercase and use a set; (2) for each word, try all single-letter substitutions.
2. Better: precompute adjacency using intermediate 'wildcard' patterns (e.g. 'h_t' matches 'hot' and 'hat').

## Solution

See [`../../solutions/13-word-ladder/`](../../solutions/13-word-ladder/) for the Python and Java 21 solutions and a step-by-step walkthrough.
