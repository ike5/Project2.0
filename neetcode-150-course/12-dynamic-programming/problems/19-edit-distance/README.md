# Edit Distance

**Difficulty:** Medium

## Problem

Given two strings `word1` and `word2`, return the minimum number of operations required to convert `word1` to `word2`. You have the following three operations permitted on a word: insert, delete, or replace a character.

## Examples

```
Input:  word1 = 'horse', word2 = 'ros'
Output: 3
```

```
Input:  word1 = 'intention', word2 = 'execution'
Output: 5
```

## Constraints

- 0 <= word1.length, word2.length <= 500
- word1 and word2 consist of lowercase English letters

## Hints

1. `dp[i][j] = dp[i-1][j-1]` if chars match; else `1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])`.

## Solution

See [`../../solutions/19-edit-distance/`](../../solutions/19-edit-distance/) for the Python and Java 21 solutions and a step-by-step walkthrough.
