# Longest Common Subsequence

**Difficulty:** Medium

## Problem

Given two strings `text1` and `text2`, return the length of their longest **common subsequence**. A *subsequence* of a string is a new string generated from the original string with some characters (can be none) deleted without changing the relative order of the remaining characters.

## Examples

```
Input:  text1 = 'abcde', text2 = 'ace'
Output: 3
```

```
Input:  text1 = 'abc', text2 = 'abc'
Output: 3
```

```
Input:  text1 = 'abc', text2 = 'def'
Output: 0
```

## Constraints

- 1 <= len(text1), len(text2) <= 1000

## Hints

1. `dp[i][j] = dp[i-1][j-1] + 1` if chars match, else `max(dp[i-1][j], dp[i][j-1])`.

## Solution

See [`../../solutions/14-longest-common-subsequence/`](../../solutions/14-longest-common-subsequence/) for the Python and Java 21 solutions and a step-by-step walkthrough.
