# Word Break

**Difficulty:** Medium

## Problem

Given a string `s` and a dictionary of strings `wordDict`, return `True` if `s` can be segmented into a space-separated sequence of one or more dictionary words.

## Examples

```
Input:  s = 'leetcode', wordDict = ['leet','code']
Output: True
```

```
Input:  s = 'applepenapple', wordDict = ['apple','pen']
Output: True
```

```
Input:  s = 'catsandog', wordDict = ['cats','dog','sand','and','cat']
Output: False
```

## Constraints

- 1 <= len(s) <= 300
- 1 <= wordDict.length <= 1000
- 1 <= wordDict[i].length <= 20
- s and wordDict[i] consist of only lowercase English letters

## Hints

1. `dp[i] = True` if `s[:i]` can be segmented. For each `j < i` with `dp[j] = True` and `s[j:i]` in the dict, set `dp[i] = True`.

## Solution

See [`../../solutions/10-word-break/`](../../solutions/10-word-break/) for the Python and Java 21 solutions and a step-by-step walkthrough.
